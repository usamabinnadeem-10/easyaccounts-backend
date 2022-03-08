class RequestMiddleware:
    """Adding custom attributes to request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.branch = None
        request.role = None
        response = self.get_response(request)
        return response