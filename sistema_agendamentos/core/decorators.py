from django.shortcuts import redirect
from functools import wraps
from .models import Comercio

def comercio_ativo_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        comercio = Comercio.objects.filter(dono=request.user).first()
        if not comercio or comercio.acesso_bloqueado:
            return redirect('acesso_bloqueado')
        return view_func(request, comercio=comercio, *args, **kwargs)
    return _wrapped_view