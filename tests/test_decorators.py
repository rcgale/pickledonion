import functools
from functools import lru_cache
from random import random
from tempfile import TemporaryDirectory

from pickledonion import cacheable, CacheContext


def test_no_cache():
    with CacheContext(cache_dir=None):
        counter_1 = EXAMPLE_FUNCTION()
        counter_2 = EXAMPLE_FUNCTION()
        assert counter_1 < counter_2


def test_function_cache():
    with TemporaryDirectory() as cache_dir:
        with CacheContext(cache_dir=cache_dir):
            counter_1 = EXAMPLE_FUNCTION()
            counter_2 = EXAMPLE_FUNCTION()
            assert counter_1 == counter_2


@cacheable()
def EXAMPLE_FUNCTION():
    global _GLOBAL_COUNTER
    _GLOBAL_COUNTER += 1
    return _GLOBAL_COUNTER


def test_instance_method_no_cache():
    with CacheContext(cache_dir=None):
        r = random()
        other_counter = EXAMPLE_FUNCTION()
        counter_1 = ExampleClass(r).EXAMPLE_FUNCTION()
        counter_2 = ExampleClass(r).EXAMPLE_FUNCTION()
        assert other_counter != counter_1
        assert other_counter != counter_2
        assert counter_1 == counter_2


def test_instance_method_cache():
    with TemporaryDirectory() as cache_dir:
        with CacheContext(cache_dir=cache_dir):
            r = random()
            other_counter = EXAMPLE_FUNCTION()
            counter_1 = ExampleClass(r).EXAMPLE_FUNCTION()
            counter_2 = ExampleClass(r).EXAMPLE_FUNCTION()
            assert other_counter != counter_1
            assert other_counter != counter_2
            assert counter_1 == counter_2


def test_staticmethod_cache_not_implemented():
    with TemporaryDirectory() as cache_dir:
        with CacheContext(cache_dir=cache_dir):
            try:
                counter_1 = ExampleClass.example_static_method()
                counter_2 = ExampleClass.example_static_method()
                assert False
            except NotImplementedError:
                assert True


class ExampleClass(object):
    def __init__(self, value):
        self.value = value

    @cacheable()
    def EXAMPLE_FUNCTION(self):
        self.value += 1
        return self.value

    @cacheable()
    @staticmethod
    def example_static_method():
        global _GLOBAL_COUNTER
        _GLOBAL_COUNTER += 1
        return _GLOBAL_COUNTER


def test_decorator_stacked_decorators_cacheable_outside_no_cache():
    counter_1 = EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_OUTSIDE()
    counter_2 = EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_OUTSIDE()
    assert counter_1 < counter_2
    assert hasattr(EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_OUTSIDE, 'some_attribute')


def test_decorator_stacked_decorators_cacheable_outside():
    with TemporaryDirectory() as cache_dir:
        with CacheContext(cache_dir=cache_dir):
            counter_1 = EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_OUTSIDE()
            counter_2 = EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_OUTSIDE()
            assert counter_1 == counter_2
            assert hasattr(EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_OUTSIDE, 'some_attribute')


def arbitrary_other_decorator():
    def wrapper(function):
        setattr(function, 'some_attribute', True)
        return function
    return wrapper


@cacheable()
@arbitrary_other_decorator()
def EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_OUTSIDE():
    global _GLOBAL_COUNTER
    _GLOBAL_COUNTER += 1
    return _GLOBAL_COUNTER


def test_decorator_stacked_decorators_cacheable_inside_no_cache():
    with CacheContext(cache_dir=None):
        counter_1 = EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_INSIDE()
        counter_2 = EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_INSIDE()
        assert counter_1 < counter_2
        assert hasattr(EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_INSIDE, 'some_attribute')


def test_decorator_stacked_decorators_cacheable_inside():
    with TemporaryDirectory() as cache_dir:
        with CacheContext(cache_dir=cache_dir):
            counter_1 = EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_INSIDE()
            counter_2 = EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_INSIDE()
            assert counter_1 == counter_2
            assert hasattr(EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_INSIDE, 'some_attribute')


@arbitrary_other_decorator()
@cacheable()
def EXAMPLE_FUNCTION_MULTIPLE_DECORATORS_CACHEABLE_INSIDE():
    global _GLOBAL_COUNTER
    _GLOBAL_COUNTER += 1
    return _GLOBAL_COUNTER

_GLOBAL_COUNTER = 0
