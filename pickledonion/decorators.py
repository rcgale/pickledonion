import functools
import hashlib
import os
import pickle
import shutil
import sys
import time

_LOCK_DIR = "__cache_locks"


def cacheable(*cacheargs):
    def wrapper(function):
        @functools.wraps(function)
        def getinstance(*args, **kwargs):
            if hasattr(function, '__module__') and hasattr(function, '__qualname__'):
                module_name = function.__module__
                qual_name = function.__qualname__
            else:
                raise NotImplementedError(f'Unsupported function type `{type(function).__qualname__}`')

            cache_key = "{m}/{fn}/{h}".format(
                m=module_name,
                fn=qual_name,
                h=__get_hash((args, kwargs))
            )
            return __get_cached(
                path=cache_key,
                get=lambda: function(*args, **kwargs),
            )
        return getinstance
    return wrapper


class CacheContext(object):
    current = None

    def __init__(self, *args, cache_dir, clear_locks=False, lock_timeout=None, lock_timeout_warning=30):
        self.outer_context = CacheContext.current
        self.context_cache_dir = cache_dir
        self.clear_locks = clear_locks
        self.lock_timeout = lock_timeout
        self.lock_timeout_warning = lock_timeout_warning

    def __enter__(self):
        CacheContext.current = self
        if self.clear_locks:
            self.__clear_locks()
        return self

    def __exit__(self, *args):
        self.__delete_empty_lock_dirs()
        CacheContext.current = self.outer_context

    def __clear_locks(self):
        if self.context_cache_dir:
            lock_dir = os.path.join(self.context_cache_dir, _LOCK_DIR)
            if os.path.exists(lock_dir):
                shutil.rmtree(lock_dir)

    def __delete_empty_lock_dirs(self):
        if self.context_cache_dir is None:
            return
        root = os.path.join(self.context_cache_dir, _LOCK_DIR)
        deleted = set()
        for path, subdirs, files in os.walk(root, topdown=False):
            still_has_subdirs = any(
                subdir for subdir in subdirs
                if os.path.join(path, subdir) not in deleted
            )
            if not len(files) and not still_has_subdirs:
                try:
                    os.rmdir(path)
                    deleted.add(path)
                except OSError:
                    pass  # Directory not empty. Ignore for concurrency.


class FileLock(object):
    def __init__(self, lock_path, lock_timeout_warning, lock_timeout):
        self.lock_path = os.path.abspath(lock_path)
        self.lock_timeout_warning = lock_timeout_warning
        self.lock_timeout = lock_timeout

    def __enter__(self):
        SLEEP_INTERVAL = 0.001
        total_slept = 0.0
        been_warned = False
        while True:
            try:
                os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
                self.fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except (FileExistsError, FileNotFoundError, OSError) as e:
                time.sleep(SLEEP_INTERVAL)
                been_warned = self._handle_timeouts(total_slept, been_warned)
                total_slept += SLEEP_INTERVAL

    def __exit__(self, *args):
        try:
            os.close(self.fd)
            os.remove(self.lock_path)
        except OSError as e:
            print("pickledonion warning: tried to remove cache lock which didn't exist: {}. Inner exception: {}".format(
                self.lock_path, e
            ), file=sys.stderr)

    def _handle_timeouts(self, total_slept, been_warned):
        if self.lock_timeout is not None and total_slept > self.lock_timeout:
            message = (
                "Could not acquire file lock after {} seconds.\n\n"
                "Force your way past this by deleting: {}"
            ).format(self.lock_timeout, self.lock_path)
            raise TimeoutError(message)
        elif not been_warned and self.lock_timeout_warning is not None and total_slept > self.lock_timeout_warning:
            if self.lock_timeout:
                message = (
                    "Warning: Could not acquire lock after {} seconds. "
                    "Error will be raised after {} seconds total.\n\n"
                    "Force your way past this by deleting: {}"
                ).format(self.lock_timeout_warning, self.lock_timeout, self.lock_path)
            else:
                message = (
                    "Warning: Could not acquire lock after {} seconds. "
                    "No error timeout specified, will wait for lock indefinitely.\n\n"
                    "Force your way past this by deleting: {}"
                ).format(self.lock_timeout_warning, self.lock_path)
            print(message, file=sys.stderr)
            been_warned = True
        return been_warned


def __get_hash(args):
    picklestring = pickle.dumps(args)
    return hashlib.sha224(picklestring).hexdigest()


def __get_cached(path, get):
    context: CacheContext = CacheContext.current
    if context is None or getattr(context, 'context_cache_dir', None) is None:
        return get()

    lock_path = os.path.join(context.context_cache_dir, _LOCK_DIR, path + ".lock")
    with FileLock(lock_path, lock_timeout_warning=context.lock_timeout_warning, lock_timeout=context.lock_timeout):
        full_path = os.path.join(context.context_cache_dir, path + ".pkl")
        if os.path.isfile(full_path):
            try:
                with open(full_path, "rb") as filehandle:
                    return pickle.load(filehandle)
            except:
                pass

        obj = get()
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as filehandle:
            pickle.dump(obj, filehandle, protocol=pickle.HIGHEST_PROTOCOL)
        return obj


# SANITY CHECK
assert(__get_hash((1,2,3,4,"a","b","c","d")) == "3aa9afff3e2a9fb63fead865517905583078f3f72bda3e22f8771a61")