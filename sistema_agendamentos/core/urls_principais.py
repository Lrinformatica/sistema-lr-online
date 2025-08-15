from django.urls import path
from . import views

urlpatterns = [
    # Rota para a página inicial (a vitrine de comerciantes)
    path('', views.home, name='home'),

    # Rota para a página onde o cliente vê seus agendamentos
    path('meus-agendamentos/', views.meus_agendamentos, name='meus_agendamentos'),

    # Rotas para o fluxo de agendamento do cliente
    path('servico/<int:servico_id>/agendar/', views.pagina_agendamento, name='pagina_agendamento'),
    path('agendamento/<int:agendamento_id>/confirmacao/', views.confirmacao_agendamento,
         name='confirmacao_agendamento'),

    # --- CORREÇÃO APLICADA AQUI ---
    # O nome da URL foi corrigido de 'listar_servicos' para 'lista_servicos' para bater com o template
    path('<slug:slug_do_comercio>/', views.listar_servicos, name='lista_servicos'),
]