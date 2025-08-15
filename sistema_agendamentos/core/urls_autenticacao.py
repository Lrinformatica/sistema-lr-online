from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', LoginView.as_view(template_name='core/login.html'), name='login'),

    # ESTA É A MUDANÇA FINAL: AGORA USAMOS A NOSSA PRÓPRIA FUNÇÃO
    path('logout/', views.logout_view, name='logout'),
]