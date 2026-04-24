class CustomeHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # It makes the class to be a callable function
        response = self.get_response(request)
        if request.user.is_authenticated:
            response["X-Django-User"] = request.user.email
        return response
