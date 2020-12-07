from typing import Type

from dataclasses import dataclass

from winter.core import annotate


@dataclass
class GlobalExceptionAnnotation:
    exception_cls: Type[Exception]


def global_exception():
    def wrapper(exception_class):
        return register_global_exception(exception_class)
    return wrapper


def register_global_exception(exception_class):
    assert issubclass(exception_class, Exception), f'Class "{exception_class}" must be a subclass of Exception'
    annotation = GlobalExceptionAnnotation(exception_cls=exception_class)
    annotation_decorator = annotate(annotation, unique=True)
    annotation_decorator(exception_class)
    return exception_class
