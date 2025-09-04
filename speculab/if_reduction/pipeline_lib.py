
from itertools import islice, tee
from functools import partial
import pathos.multiprocessing as mp
from functools import wraps

import inspect
from typing import Iterator, Iterable, get_type_hints, Any, Literal


class StartPipe:
    pass


class Pipe:

    def __init__(self, func):
        self.func = func

    def __ror__(self, other):
        # "other" is the input from the left side of the pipe
        if other is not StartPipe:
            return self.func(other)
        else:
            return self.func()

    def __call__(self, *args, **kwargs):
        # Allow calling the function as usual
        return self.func(*args, **kwargs)


def parallel_yield(processes=8, chunksize=1):
    """
    Decorator to run a function in parallel inside a pipeline.
    Can be used without arguments, or with the processes and chunksize arguments
    """
    if callable(processes):
        return parallel_yield()(processes)
    else:
        def decorator(func):
            @wraps(func)
            def wrapper(stream, **kwargs):
                partial_func = partial(func, **kwargs)
                with mp.Pool(processes=processes or mp.cpu_count()) as pool:
                    for result in pool.imap(partial_func, stream, chunksize=chunksize):
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
        # Detect if the first parameter expects an Iterator or Iterable
        if i== 0 and annotation in [Iterator, Iterable]:
            takes_iterator = True

    # Get return type
    ret_annotation = hints.get("return", Any)
    returns_iterator = ret_annotation in [Iterator, Iterable]

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


def run_pipeline(func_list, params_dicts, flag_list, preview=False,
                 callback=None, check_interrupt_callback=None,
                 progress_callback=None):
    '''Run a sequence of functions as a pipeline

    Functions are classified as either sources, sink, or transforms/generic. If they
    aren't generators, they are wrapped with "wrap_as_generator()".

    Pipelines must begin with a source function and may end with a sink, although the latter
    is not enforced. Intermediate generators are added for regular callbacks.

    Parameters:
    func_list: list of functions to run in sequence
    params_dicts: list of dicts with parameters for each function
    flag_list: list of dicts with flags for each function (e.g. {'mp_enabled': True})
    preview: if True, pass preview=True to functions that support it
    callback: function to call after each step with the current output (e.g. for UI updates)
    check_interrupt_callback: function to call to check if the pipeline should be interrupted
    progress_callback: function to call at regular intervals to report progress
    '''
    gen = None

    for func, params, flags in zip(func_list, params_dicts, flag_list):
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

        # Apply multiprocesing if enabled, which makes the function a generator as a side-effect
        mp_number = flags.get("mp_enabled", False)
        if mp_number:
            f = parallel_yield(processes=mp_number)(func)
        elif func_type == 'generic':
            f = wrap_as_generator(func)
        else:
            f = func

        if func_type == 'source':
            gen = f(**params)          # Sources are the initial generator
        elif func_type == 'transform':
            gen = f(gen, **params)
        elif func_type == 'generic':
            gen = f(gen, **params)
        elif func_type == 'sink':
            output = f(gen, **params)  # Sinks will consume the generator
            # Call callbacks manually since the pipeline ends here
            if progress_callback:
                progress_callback({func: 1})
            if callback:
                callback({func: output})
            return output
        else:
            raise ValueError(f"Function {func.__name__} has an unsupported type: {func_type}.")

        if callback:
            # Callback at each single iteration to display all intermediate results
            # def call_the_callback(stream, this_func):
            #     for item in stream:
            #         callback({this_func: item if func_type != 'source' else None})
            #         yield item
            # gen = call_the_callback(gen, func)

            # Preview callback only on the first item of each step
            gen, preview_gen = tee(gen)
            callback({func: list(islice(preview_gen, 1))[0] if func_type != 'source' else None})

        if check_interrupt_callback:
            def check_callback(stream):
                for item in stream:
                    if check_interrupt_callback():
                        print("Pipeline interrupted by user.")
                        break
                    yield item
            gen = check_callback(gen)

        if progress_callback:
            def call_progress_callback(stream, fobj):
                counter = 0
                for item in stream:
                    counter += 1
                    progress_callback({fobj: counter})
                    yield item
            gen = call_progress_callback(gen, func)

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
