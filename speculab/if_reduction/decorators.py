
import pathos.multiprocessing as mp
from functools import wraps


class StartPipe:
    pass


class Pipe:

    def __init__(self, func):
        self.func = func
        self.func._is_pipe = True    # Mark functions as decorated

    def __ror__(self, other):
        # "other" is the input from the left side of the pipe
        if other is not StartPipe:
            return self.func(other)
        else:
            return self.func()

    def __call__(self, *args, **kwargs):
        # Allow calling the function as usual
        return self.func(*args, **kwargs)


def parallel_yield(processes=None, chunksize=1):
    """
    Decorator to run a function in parallel inside a pipeline.
    Can be used without arguments, or with the processes and chunksize arguments
    """
    if callable(processes):
        return parallel_yield()(processes)
    else:
        def decorator(func):
            @wraps(func)
            def wrapper(stream):
                with mp.Pool(processes=processes or mp.cpu_count()) as pool:
                    for result in pool.imap(func, stream, chunksize=chunksize):
                        yield result
            return wrapper
        return decorator
