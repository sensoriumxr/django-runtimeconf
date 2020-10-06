from django.http import HttpResponseNotAllowed

from .interface import get_runtime_client


class UrlToggleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        runtimeconf = get_runtime_client()
        path = request.path.split('?')[0]
        possible_key_name = '|'.join([path, request.method])
        second_possible_key_name = '|'.join([
            '/'.join(path.split('/')[:-1]),
            request.method
        ])
        if possible_key_name in runtimeconf.keys():
            if runtimeconf.keys()[possible_key_name] is False:
                return HttpResponseNotAllowed([request.method])
        elif second_possible_key_name in runtimeconf.keys():
            if runtimeconf.keys()[second_possible_key_name] is False:
                return HttpResponseNotAllowed([request.method])
        response = self.get_response(request)
        return response
