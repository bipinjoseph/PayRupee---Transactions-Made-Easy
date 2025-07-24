# decorators.py
from django.shortcuts import redirect

def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('/loginpage/')
        return view_func(request, *args, **kwargs)
    return wrapper
