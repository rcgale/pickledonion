import hashlib
import os
import pickle

import pickledonion

CACHE_DIR = None # Note: Set the cache directory using `with pickledonion.CacheContext(cache_dir="/path/to/dir"):`


def cacheable(*cacheargs):
    def wrapper(function):
        def getinstance(*args, **kwargs):
            if CACHE_DIR is None:
                return function(*args, **kwargs)

            cache_key = "{fn}_{h}".format(
                fn=function.__name__,
                h=__get_hash((args, kwargs))
            )
            return __get_cached(
                dir=CACHE_DIR,
                filename=cache_key,
                get=lambda: function(*args, **kwargs),
            )
        getinstance.__dict__ = function.__dict__.copy() # Being friendly to other decorators
        getinstance.original_function = function # Pretty hacky. But this is useful information.
        return getinstance
    return wrapper


class CacheContext(object):
    def __init__(self, *args, cache_dir):
        self.previous_cache_dir = pickledonion.decorators.CACHE_DIR
        self.context_cache_dir = cache_dir

    def __enter__(self):
        pickledonion.decorators.CACHE_DIR = self.context_cache_dir

    def __exit__(self, *args):
        pickledonion.decorators.CACHE_DIR = self.previous_cache_dir


def __get_hash(args):
    picklestring = pickle.dumps(args)
    return hashlib.sha224(picklestring).hexdigest()


def __get_cached(dir, filename, get):
    full_path = os.path.join(dir, filename + ".pkl")
    if os.path.isfile(full_path):
        try:
            with open(full_path, "rb") as filehandle:
                return pickle.load(filehandle)
        except:
            pass

    obj = get()
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(full_path, "wb") as filehandle:
        pickle.dump(obj, filehandle, protocol=pickle.HIGHEST_PROTOCOL)
    return obj


# SANITY CHECK
assert(__get_hash((1,2,3,4,"a","b","c","d")) == "3aa9afff3e2a9fb63fead865517905583078f3f72bda3e22f8771a61")