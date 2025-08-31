
from itertools import islice, tee
import os

import pathos.multiprocessing as mp
from functools import wraps

import inspect
from typing import Iterator, get_type_hints, Any, Literal



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


StepType = Literal["source", "transform", "sink", "generic"]

def classify_function(func) -> StepType:
    """
    Analyze a function based on its type hints and signature,
    returning its classification and parameter info.

    Returns:
        StepType: "source" | "transform" | "sink" | "generic",
    """
    if not callable(func):
        return None
    try:
        sig = inspect.signature(func)
        hints = get_type_hints(func)
    except (TypeError, ValueError):
        return None
    params_info = []
    takes_iterator = False

    # Extract parameter info
    for i, (name, param) in enumerate(sig.parameters.items()):
        annotation = hints.get(name, Any)
        params_info.append((name, annotation, param.default))
        # Detect if the first parameter expects an Iterator
        if i== 0 and annotation is Iterator:
            takes_iterator = True

    # Get return type
    ret_annotation = hints.get("return", Any)
    returns_iterator = ret_annotation is Iterator

    # Determine classification
    if returns_iterator and not takes_iterator:
        ftype = "source"
    elif returns_iterator and takes_iterator:
        ftype = "transform"
    elif not returns_iterator and takes_iterator:
        ftype = "sink"
    else:
        # No iterator involved - simple function
        ftype = "generic"

    return ftype

import importlib.util


def load_predefined_functions(filename="pipeline.py"):
    '''
    Load predefined functions from a given Python file.
    Functions must have been typed with the Iterator type hint
    either for the first argument (sinks) or the return type (sources), or both (transforms).
    '''
    functions = {}
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} not found.")

    spec = importlib.util.spec_from_file_location("pipeline", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and name[0].islower() and not name.startswith('_'):
            functions[name] = obj
    return functions

predefined_functions = load_predefined_functions("pipeline.py")


def load_custom_function(filename, func_name):
    '''Load a custom function from a given Python file'''
    if os.path.exists(filename):
        spec = importlib.util.spec_from_file_location("custom_module", filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, func_name):
            return getattr(module, func_name)
        else:
            raise ValueError(f'Function {func_name} not found in {filename}')
    else:
        raise FileNotFoundError(f"{filename} not found.")


def run_pipeline(func_list, params_dicts, preview=False, callback=None):
    '''Run a sequence of functions as a pipeline'''
    gen = None

    for func, params in zip(func_list, params_dicts):
        func_type = classify_function(func)
        print(f'Running step: {func.__name__} ({func_type})')
        sig = {k:v for k, v in inspect.signature(func).parameters.items()}
        if 'preview' in sig:
            params['preview'] = preview
            del sig['preview']

        if func_type == 'source' and gen is not None:
            raise ValueError(f"Source function {func.__name__} cannot follow another function in the pipeline.")
        elif func_type == 'transform' and gen is None:
            raise ValueError(f"Transform function {func.__name__} requires an input generator.")
        elif func_type == 'sink' and gen is None:
                raise ValueError(f"Sink function {func.__name__} requires an input generator.")

        if func_type == 'source':
            gen = func(**params)
        elif func_type == 'transform':
            gen = func(gen, **params)
        elif func_type == 'generic':
            f = wrap_as_generator(func)
            gen = f(gen, **params)
        elif func_type == 'sink':
            output = func(gen, **params)
            gen = None  # End of pipeline after sink
            if callback:
                callback({func: output})
            return output
        else:
            raise ValueError(f"Function {func.__name__} has an unsupported type: {func_type}.")

        if callback:
            gen, preview_gen = tee(gen)
            callback({func: list(islice(preview_gen, 1))[0] if func_type != 'source' else None})

    if gen is not None:
        print("Warning: Pipeline ended without a sink function. Consuming remaining generator.")
        # Consume final generator
        output = list(gen)
        print(output)
        return output


def wrap_as_generator(func):
    ''' Wrap a regular function to operate on each item of a generator'''
    def wrapper(gen, *args, **kwargs):
        for value in gen:
            result = func(value, *args, **kwargs)
            yield result
    return wrapper
