from django.urls import path
from django.shortcuts import render  # <-- AQUI ESTÁ A IMPORTAÇÃO CORRETA
from . import views

urlpatterns = [
    # URLs Principais do Painel
    path('', views.painel_home, name='painel_home'),
    path('configuracoes/', views.configuracoes_loja, name='painel_configuracoes'),
    path('relatorios/', views.relatorios_financeiros, name='painel_relatorios'),

    # URLs de Produtos
    path('produtos/', views.gerenciar_produtos, name='gerenciar_produtos'),
    path('produtos/adicionar/', views.adicionar_editar_produto, name='adicionar_produto'),
    path('produtos/editar/<int:produto_id>/', views.adicionar_editar_produto, name='editar_produto'),
    path('produtos/estoque/entrada/', views.entrada_estoque, name='entrada_estoque'),
    path('produtos/importar_xml/', views.importar_produtos_xml, name='importar_produtos_xml'),

    # URLs de Serviços
    path('servicos/', views.gerenciar_servicos, name='gerenciar_servicos'),
    path('servicos/adicionar/', views.adicionar_editar_servico, name='adicionar_servico'),
    path('servicos/editar/<int:servico_id>/', views.adicionar_editar_servico, name='editar_servico'),

    # URLs de Funcionários
    path('funcionarios/', views.gerenciar_funcionarios, name='gerenciar_funcionarios'),
    path('funcionarios/adicionar/', views.adicionar_editar_funcionario, name='adicionar_funcionario'),
    path('funcionarios/editar/<int:funcionario_id>/', views.adicionar_editar_funcionario, name='editar_funcionario'),

    # URLs de Clientes
    path('clientes/', views.gerenciar_clientes, name='gerenciar_clientes'),
    path('clientes/adicionar/', views.adicionar_editar_cliente, name='adicionar_cliente'),
    path('clientes/editar/<int:cliente_id>/', views.adicionar_editar_cliente, name='editar_cliente'),

    # URLs do PDV e Caixa
    path('pdv/', views.pdv, name='painel_pdv'),
    path('pdv/buscar-itens/', views.buscar_itens_pdv, name='buscar_itens_pdv'),
    path('pdv/finalizar/', views.finalizar_venda, name='finalizar_venda'),
    path('venda/<int:venda_id>/recibo/', views.recibo_venda, name='recibo_venda'),
    path('venda/<int:venda_id>/cupom/', views.cupom_venda, name='cupom_venda'),
    path('caixa/abrir/', views.abrir_caixa, name='abrir_caixa'),
    path('caixa/abrir/', views.abrir_caixa, name='abrir_caixa'),
    path('caixa/fechar/', views.fechar_caixa, name='fechar_caixa'),
    path('caixa/suplemento/', views.movimentacao_caixa, {'tipo': 'suplemento'}, name='caixa_suplemento'),
    path('caixa/sangria/', views.movimentacao_caixa, {'tipo': 'sangria'}, name='caixa_sangria'),

    # URL Genérica de Exclusão
    path('excluir/<str:tipo_item>/<int:item_id>/', views.excluir_item, name='excluir_item'),
    path('acesso-bloqueado/', lambda request: render(request, 'core/painel/acesso_bloqueado.html'), name='acesso_bloqueado'),
]