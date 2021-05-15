from time import time
from collections import Counter
from inspect import isgeneratorfunction


def timer(f):
    """
    Calculates time spent in each function in seconds. Recover times using timer.counter.
    To record a function decorate it with @timer. Example:
    >>> import numpy as np
    >>> @timer
    >>> def fun():
    >>>    a = np.array(np.arange(10_000_000))
    >>> fun()
    >>> print(timer.counter)
    >>> Counter({'__main__.fun': 0.02098822593688965})
    """
    if hasattr(f, '__self__'):
        name = f'{f.__module__}.{f.__self__.__class__.__name__}.{f.__name__}'
    else:
        name = f'{f.__module__}.{f.__name__}'
    if isgeneratorfunction(f):
        def inner(*args, **kwargs):
            start = time()
            try:
                res = f(*args, **kwargs)
                for i in res:
                    end = time()
                    timer.counter.update({name: end - start})
                    yield i
                    start = time()
            except Exception as e:
                end = time()
                timer.counter.update({name: end - start})
                raise e
            end = time()
            timer.counter.update({name: end - start})
    else:
        def inner(*args, **kwargs):
            start = time()
            try:
                res = f(*args, **kwargs)
            except Exception as e:
                end = time()
                timer.counter.update({name: end - start})
                raise e
            end = time()
            timer.counter.update({name: end - start})
            return res
    return inner


class timer_ctx:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time()
        timer.counter.update({self.name: end - self.start})


timer.counter = Counter()


