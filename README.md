# pickledonion
Python disk caching (using pickle) which encourages configuration on the outer layers of the program (like in the "onion" or "clean" architecture)

## Installation

It's up on PyPI, so you can just

```bash
pip3 install pickledonion
```

It might work in python2 but I haven't had any reason to check yet.

## How it works

First, mark the function you want to cache with the `@pickledonion.cacheable()` decorator. The input arguments and the return objects must be [picklable](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled). The input arguments will be serialized and hashed for use as the cache key, so keep that in mind if your input arguments are very large.

```python
import pickledonion

@pickledonion.cacheable()
def my_cached_function(arg1, arg2, arg3):
    return do_something_resource_intensive(arg1, arg2, arg3)
```

Now, preferably on the outermost layer of your program, set the directory you would like to use for your entire system's cache storage.

```python
if __name__ == "__main__":
    with pickledonion.CacheContext(cache_dir="_cache/"):
        # `my_cached_function()` now caches to the path `_cache/my_cached_function_[hashkey(arg1, arg2, arg3)].pkl`
        bigresult = my_cached_function(arg1, arg2, arg3)

        # You might as well stay in this context for the rest of your program. Then you
        # can add new `@pickledonion.cacheable()` functions willy-nilly
        main()
```

Caching can be completely disabled by setting the `cache_dir` to `None`, and all your `@pickledonion.cacheable()` functions will simply run uncached.

Having the cache configuration as far outside the architecture as possible means the deeper layers aren't tied to filesystem specifics. And that's the entire point of this package. I hope you enjoy.
