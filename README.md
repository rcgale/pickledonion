# pickledonion
Python pickle disk caching which encourages configuration on the outer layers of an "onion" architecture

# How it works

First, mark the function you want to cache with the `@pickledonion.cacheable()` decorator. The input arguments and the return objects must be [https://docs.python.org/3/library/pickle.html|picklable]. The input arguments will be serialized and hashed for use as the cache key, so keep that in mind if your input arguments are very large.

```python
import pickledonion

@pickledonion.cacheable()
def my_cached_function(arg1, arg2, arg3):
    return do_something_resource_intensive(arg1, arg2, arg3)
```

Now, preferably on the outermost layer of your program, set the directory you would like to use for cache storage.

```python
if __name__ == "__main__":
    with pickledonion.CacheContext(cache_dir="_cache/"):
        bigresult = my_cached_function(arg1, arg2, arg3)
```

Having the cache configuration as far outside the architecture as possible means the deeper layers aren't tied to filesystem specifics. And that's the entire point of this package. I hope you enjoy.
