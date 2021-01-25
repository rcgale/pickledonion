import functools
import hashlib
import os
import pickle
import shutil
import sys
import time

import pickledonion

CACHE_DIR = None # Note: Set the cache directory using `with pickledonion.CacheContext(cache_dir="/path/to/dir"):`
_LOCK_DIR = "__cache_locks"

def cacheable(*cacheargs):
    def wrapper(function):
        @functools.wraps(function)
        def getinstance(*args, **kwargs):
            if CACHE_DIR is None:
                return function(*args, **kwargs)

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
                dir=CACHE_DIR,
                path=cache_key,
                get=lambda: function(*args, **kwargs),
            )
        return getinstance
    return wrapper


class CacheContext(object):
    def __init__(self, *args, cache_dir, clear_locks=False):
        self.previous_cache_dir = pickledonion.decorators.CACHE_DIR
        self.context_cache_dir = cache_dir
        self.clear_locks = clear_locks

    def __enter__(self):
        pickledonion.decorators.CACHE_DIR = self.context_cache_dir
        if self.clear_locks:
            self.__clear_locks()
        return self

    def __exit__(self, *args):
        self.__delete_empty_lock_dirs()
        pickledonion.decorators.CACHE_DIR = self.previous_cache_dir

    def __clear_locks(self):
        if pickledonion.decorators.CACHE_DIR is not None:
            lock_dir = os.path.join(self.context_cache_dir, _LOCK_DIR)
            if os.path.exists(lock_dir):
                shutil.rmtree(lock_dir)

    def __delete_empty_lock_dirs(self):
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
    def __init__(self, lock_path):
        self.lock_path = lock_path

    def __enter__(self):
        while True:
            try:
                os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
                self.fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except (FileExistsError, FileNotFoundError, OSError) as e:
                time.sleep(0.001)

    def __exit__(self, *args):
        try:
            os.close(self.fd)
            os.remove(self.lock_path)
        except OSError as e:
            print("pickledonion warning: tried to remove cache lock which didn't exist: {}. Inner exception: {}".format(
                self.lock_path, e
            ), file=sys.stderr)

def __get_hash(args):
    picklestring = pickle.dumps(args)
    return hashlib.sha224(picklestring).hexdigest()


def __get_cached(dir, path, get):
    with FileLock(os.path.join(dir, _LOCK_DIR, path + ".lock")):
        full_path = os.path.join(dir, path + ".pkl")
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