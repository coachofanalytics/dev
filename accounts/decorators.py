from django.shortcuts import redirect


def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('main:layout')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func
'''
def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):

            group = None
            if request.users.groups.exists():
                group= request.users.groups.all()[0].name

            if group in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                HttpResponse("You are not authorized to view this Page")
        return wrapper_func
    return decorator
    '''