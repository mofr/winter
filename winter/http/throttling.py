import time
import typing

import dataclasses
from django.core.cache import cache as default_cache
from rest_framework.throttling import BaseThrottle

from ..core import Component
from ..core import annotate

if typing.TYPE_CHECKING:  # pragma: no cover
    from ..routing import Route


@dataclasses.dataclass
class ThrottlingAnnotation:
    rate: typing.Optional[str]
    scope: typing.Optional[str]


@dataclasses.dataclass
class Throttling:
    num_requests: int
    duration: int
    scope: str


def throttling(rate: typing.Optional[str], scope: typing.Optional[str] = None):
    return annotate(ThrottlingAnnotation(rate, scope), single=True)


class BaseRateThrottle(BaseThrottle):
    throttling_by_http_method: typing.Dict[str, Throttling] = {}
    cache = default_cache
    cache_format = 'throttle_{scope}_{ident}'

    def allow_request(self, request, view):
        throttling = self._get_throttling(request)

        if throttling is None:
            return True

        self.key = self._get_cache_key(request, view, throttling.scope)

        history = self.cache.get(self.key, [])
        self.now = time.time()

        while history and history[-1] <= self.now - throttling.duration:
            history.pop()

        if len(history) >= throttling.num_requests:
            return False

        history.insert(0, self.now)
        self.cache.set(self.key, history, throttling.duration)
        return True

    def _get_cache_key(self, request, view, scope: str):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format.format(scope=scope, ident=ident)

    def _get_throttling(self, request) -> typing.Optional[Throttling]:
        return self.throttling_by_http_method.get(request.method.lower())


def _parse_rate(rate):
    """
    Given the request rate string, return a two tuple of:
    <allowed number of requests>, <period of time in seconds>
    """
    num, period = rate.split('/')
    num_requests = int(num)
    duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
    return (num_requests, duration)


def create_throttle_classes(
        component: Component,
        routes: typing.List['Route'],
) -> typing.Tuple[typing.Type[BaseRateThrottle], ...]:
    base_throttling_annotation = component.annotations.get_one_or_none(ThrottlingAnnotation)
    throttling_by_http_method_: typing.Dict[str, typing.Optional[Throttling]] = {}

    for route in routes:

        throttling_annotation = route.method.annotations.get_one_or_none(ThrottlingAnnotation)

        if throttling_annotation is None:
            throttling_annotation = base_throttling_annotation

        if throttling_annotation is not None and throttling_annotation.rate is not None:
            num_requests, duration = _parse_rate(throttling_annotation.rate)
            throttling = Throttling(num_requests, duration, throttling_annotation.scope)
            throttling_by_http_method_[route.http_method.lower()] = throttling

    if not throttling_by_http_method_:
        return ()

    class RateThrottle(BaseRateThrottle):
        throttling_by_http_method = throttling_by_http_method_

    return (RateThrottle,)
