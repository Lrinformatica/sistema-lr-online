from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from datetime import date, datetime, timedelta
from django.http import HttpResponseNotFound, JsonResponse
import json
from django.db import transaction
from django.db.models import Sum, F, Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
# --- NOVA IMPORTAÇÃO PARA LER XML ---
import xml.etree.ElementTree as ET
from .models import (
    Comercio, Servico, HorarioTrabalho, Agendamento,
    Funcionario, Produto, Venda, ItemVendido, EntradaEstoque,
    Caixa, MovimentacaoCaixa, ClienteProfile
)
from .forms import (
    ProdutoForm, ServicoForm, FuncionarioForm, EntradaEstoqueForm,
    MovimentacaoCaixaForm, ClienteForm, ComercioConfigForm
)
from .decorators import comercio_ativo_required


# ### VIEWS PÚBLICAS ###

def home(request):
    todos_os_comercios = Comercio.objects.all()
    contexto = {'comercios': todos_os_comercios}
    return render(request, 'core/home.html', contexto)


def listar_servicos(request, slug_do_comercio):
    try:
        comercio = Comercio.objects.get(slug=slug_do_comercio)
        servicos_cadastrados = Servico.objects.filter(comercio=comercio)
        contexto = {'comercio': comercio, 'servicos': servicos_cadastrados}
        return render(request, 'core/lista_servicos.html', contexto)
    except Comercio.DoesNotExist:
        return HttpResponseNotFound('<h1>Comércio não encontrado</h1>')


def cadastro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    contexto = {'form': form}
    return render(request, 'core/cadastro.html', contexto)


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def meus_agendamentos(request):
    agendamentos = Agendamento.objects.filter(cliente=request.user).order_by('-data_hora')
    contexto = {'agendamentos': agendamentos}
    return render(request, 'core/meus_agendamentos.html', contexto)


@login_required
def confirmacao_agendamento(request, agendamento_id):
    agendamento = Agendamento.objects.get(id=agendamento_id)
    contexto = {'agendamento': agendamento}
    return render(request, 'core/confirmacao_agendamento.html', contexto)


@login_required
def pagina_agendamento(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id)
    funcionarios_aptos = Funcionario.objects.filter(servicos_que_realiza=servico)
    contexto = {'servico': servico, 'funcionarios_aptos': funcionarios_aptos, }
    if request.method == 'POST':
        acao = request.POST.get('acao', '')
        data_selecionada_str = request.POST.get('data_selecionada') or request.POST.get('data_agendamento')
        funcionario_id_str = request.POST.get('funcionario')
        contexto['data_selecionada_str'] = data_selecionada_str
        if funcionario_id_str:
            contexto['funcionario_selecionado_id'] = int(funcionario_id_str)
        if acao.startswith('agendar:'):
            partes_acao = acao.split(':')
            horario_selecionado_str = f"{partes_acao[1]}:{partes_acao[2]}"
            data_hora_agendamento = datetime.strptime(f'{data_selecionada_str} {horario_selecionado_str}',
                                                      '%Y-%m-%d %H:%M')
            funcionario_selecionado = get_object_or_404(Funcionario, id=funcionario_id_str)
            novo_agendamento = Agendamento.objects.create(
                comercio=servico.comercio,
                cliente=request.user,
                funcionario=funcionario_selecionado,
                servico=servico,
                data_hora=data_hora_agendamento
            )
            return redirect('confirmacao_agendamento', agendamento_id=novo_agendamento.id)
        elif acao == 'ver_horarios':
            if data_selecionada_str and funcionario_id_str:
                horarios_disponiveis = []
                data_selecionada = datetime.strptime(data_selecionada_str, '%Y-%m-%d').date()
                dia_da_semana = data_selecionada.weekday() + 1
                funcionario_selecionado = get_object_or_404(Funcionario, id=funcionario_id_str)
                try:
                    horario_trabalho = HorarioTrabalho.objects.get(dia_da_semana=dia_da_semana,
                                                                   comercio=servico.comercio)
                    agendamentos_do_dia = Agendamento.objects.filter(data_hora__date=data_selecionada,
                                                                     funcionario=funcionario_selecionado)
                    horarios_ocupados = [ag.data_hora.time() for ag in agendamentos_do_dia]
                    hora_inicio = datetime.combine(data_selecionada, horario_trabalho.hora_inicio)
                    hora_fim = datetime.combine(data_selecionada, horario_trabalho.hora_fim)
                    duracao_servico = timedelta(minutes=servico.duracao_minutos)
                    slot_atual = hora_inicio
                    while slot_atual + duracao_servico <= hora_fim:
                        if slot_atual.time() not in horarios_ocupados:
                            horarios_disponiveis.append(slot_atual.strftime('%H:%M'))
                        slot_atual += timedelta(minutes=15)
                except HorarioTrabalho.DoesNotExist:
                    pass
                contexto['horarios_disponiveis'] = horarios_disponiveis
    return render(request, 'core/pagina_agendamento.html', contexto)


# ### VIEWS DO PAINEL ###

@login_required
@comercio_ativo_required
def painel_home(request, comercio):
    tz_local = timezone.get_current_timezone()
    hoje_local = timezone.now().astimezone(tz_local).date()
    inicio_dia_local = timezone.make_aware(datetime.combine(hoje_local, datetime.min.time()))
    fim_dia_local = timezone.make_aware(datetime.combine(hoje_local, datetime.max.time()))
    agendamentos_de_hoje = Agendamento.objects.filter(comercio=comercio,
                                                      data_hora__range=(inicio_dia_local, fim_dia_local)).order_by(
        'data_hora')
    contexto = {'comercio': comercio, 'agendamentos': agendamentos_de_hoje}
    return render(request, 'core/painel/painel_home.html', contexto)


@login_required
@comercio_ativo_required
def gerenciar_clientes(request, comercio):
    lista_clientes = User.objects.filter(cliente_profile__comercio_associado=comercio)
    contexto = {
        'comercio': comercio,
        'clientes': lista_clientes,
    }
    return render(request, 'core/painel/gerenciar_clientes.html', contexto)


@login_required
@comercio_ativo_required
def adicionar_editar_cliente(request, comercio, cliente_id=None):
    if cliente_id:
        cliente = get_object_or_404(User, id=cliente_id, cliente_profile__comercio_associado=comercio)
        titulo_pagina = "Editar Cliente"
    else:
        cliente = None
        titulo_pagina = "Adicionar Novo Cliente"

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            novo_cliente = form.save(commit=False)
            if not cliente_id:
                senha_aleatoria = get_random_string(length=10)
                novo_cliente.set_password(senha_aleatoria)

            novo_cliente.save()

            if not cliente_id:
                ClienteProfile.objects.create(user=novo_cliente, comercio_associado=comercio)

            messages.success(request, 'Cliente salvo com sucesso!')
            return redirect('gerenciar_clientes')
    else:
        form = ClienteForm(instance=cliente)

    contexto = {
        'form': form,
        'titulo_pagina': titulo_pagina,
        'comercio': comercio,
    }
    return render(request, 'core/painel/adicionar_editar_form.html', contexto)


@login_required
@comercio_ativo_required
def gerenciar_produtos(request, comercio):
    lista_produtos = Produto.objects.filter(comercio=comercio)
    contexto = {'comercio': comercio, 'produtos': lista_produtos, }
    return render(request, 'core/painel/gerenciar_produtos.html', contexto)


@login_required
@comercio_ativo_required
def adicionar_editar_produto(request, comercio, produto_id=None):
    if produto_id:
        produto = get_object_or_404(Produto, id=produto_id, comercio=comercio)
        titulo_pagina = "Editar Produto"
    else:
        produto = None
        titulo_pagina = "Adicionar Novo Produto"
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            produto_salvo = form.save(commit=False)
            produto_salvo.comercio = comercio
            produto_salvo.save()
            return redirect('gerenciar_produtos')
    else:
        form = ProdutoForm(instance=produto)
    contexto = {'form': form, 'titulo_pagina': titulo_pagina, 'comercio': comercio}
    return render(request, 'core/painel/adicionar_editar_form.html', contexto)


@login_required
@comercio_ativo_required
def configuracoes_loja(request, comercio):
    if request.method == 'POST':
        form = ComercioConfigForm(request.POST, request.FILES, instance=comercio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Suas informações foram salvas com sucesso!')
            return redirect('painel_configuracoes')
    else:
        form = ComercioConfigForm(instance=comercio)
    contexto = {'comercio': comercio, 'form': form}
    return render(request, 'core/painel/configuracoes_loja.html', contexto)


# --- NOVA VIEW PARA IMPORTAÇÃO DE PRODUTOS VIA XML ---
@login_required
@comercio_ativo_required
def importar_produtos_xml(request, comercio):
    if request.method == 'POST' and request.FILES.get('arquivo_xml'):
        arquivo_xml = request.FILES['arquivo_xml']

        if not arquivo_xml.name.endswith('.xml'):
            messages.error(request, "Formato de arquivo inválido. Por favor, envie um arquivo .xml")
            return redirect('gerenciar_produtos')

        try:
            tree = ET.parse(arquivo_xml)
            root = tree.getroot()

            produtos_importados = 0
            # Namespace padrão para NFe (Nota Fiscal Eletrônica)
            namespace = '{http://www.portalfiscal.inf.br/nfe}'

            # Procura por todos os itens detalhados na nota
            for det_node in root.findall(f'.//{namespace}det'):
                prod_node = det_node.find(f'{namespace}prod')
                if prod_node is not None:
                    nome_produto = prod_node.find(f'{namespace}xProd').text
                    preco_venda_str = prod_node.find(f'{namespace}vUnCom').text
                    quantidade_str = prod_node.find(f'{namespace}qCom').text

                    # Cria o produto no banco de dados
                    Produto.objects.create(
                        comercio=comercio,
                        nome=nome_produto,
                        preco_venda=Decimal(preco_venda_str),
                        quantidade_estoque=int(float(quantidade_str)),
                        # Você pode adicionar mais campos aqui se precisar (ex: preco_custo, codigo_barras)
                    )
                    produtos_importados += 1

            if produtos_importados > 0:
                messages.success(request, f"{produtos_importados} produtos foram importados com sucesso!")
            else:
                messages.warning(request, "Nenhum produto encontrado no arquivo XML. Verifique se é uma NFe válida.")

        except ET.ParseError:
            messages.error(request, "Erro ao processar o arquivo XML. O arquivo pode estar corrompido.")
        except Exception as e:
            messages.error(request, f"Ocorreu um erro inesperado: {e}")

        return redirect('gerenciar_produtos')

    return redirect('gerenciar_produtos')


# ... (O resto do seu arquivo views.py continua daqui para baixo) ...
@login_required
@comercio_ativo_required
def gerenciar_servicos(request, comercio):
    lista_servicos = Servico.objects.filter(comercio=comercio)
    contexto = {'comercio': comercio, 'servicos': lista_servicos, }
    return render(request, 'core/painel/gerenciar_servicos.html', contexto)


@login_required
@comercio_ativo_required
def adicionar_editar_servico(request, comercio, servico_id=None):
    if servico_id:
        servico = get_object_or_404(Servico, id=servico_id, comercio=comercio)
        titulo_pagina = "Editar Serviço"
    else:
        servico = None
        titulo_pagina = "Adicionar Novo Serviço"
    if request.method == 'POST':
        form = ServicoForm(request.POST, instance=servico)
        if form.is_valid():
            servico_salvo = form.save(commit=False)
            servico_salvo.comercio = comercio
            servico_salvo.save()
            return redirect('gerenciar_servicos')
    else:
        form = ServicoForm(instance=servico)
    contexto = {'form': form, 'titulo_pagina': titulo_pagina, 'comercio': comercio}
    return render(request, 'core/painel/adicionar_editar_form.html', contexto)


@login_required
@comercio_ativo_required
def gerenciar_funcionarios(request, comercio):
    lista_funcionarios = Funcionario.objects.filter(comercio=comercio)
    contexto = {'comercio': comercio, 'funcionarios': lista_funcionarios, }
    return render(request, 'core/painel/gerenciar_funcionarios.html', contexto)


@login_required
@comercio_ativo_required
def adicionar_editar_funcionario(request, comercio, funcionario_id=None):
    if funcionario_id:
        funcionario = get_object_or_404(Funcionario, id=funcionario_id, comercio=comercio)
        titulo_pagina = "Editar Funcionário"
    else:
        funcionario = None
        titulo_pagina = "Adicionar Novo Funcionário"
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        form.fields['servicos_que_realiza'].queryset = Servico.objects.filter(comercio=comercio)
        if form.is_valid():
            funcionario_salvo = form.save(commit=False)
            funcionario_salvo.comercio = comercio
            funcionario_salvo.save()
            form.save_m2m()
            return redirect('gerenciar_funcionarios')
    else:
        form = FuncionarioForm(instance=funcionario)
        form.fields['servicos_que_realiza'].queryset = Servico.objects.filter(comercio=comercio)
    contexto = {'form': form, 'titulo_pagina': titulo_pagina, 'comercio': comercio}
    return render(request, 'core/painel/adicionar_editar_form.html', contexto)


@login_required
@comercio_ativo_required
def relatorios_financeiros(request, comercio):
    tz_local = timezone.get_current_timezone()
    hoje_local = timezone.now().astimezone(tz_local).date()
    inicio_dia_local = timezone.make_aware(datetime.combine(hoje_local, datetime.min.time()))
    fim_dia_local = timezone.make_aware(datetime.combine(hoje_local, datetime.max.time()))
    inicio_semana_local = hoje_local - timedelta(days=hoje_local.weekday())
    inicio_mes_local = hoje_local.replace(day=1)
    inicio_semana_aware = timezone.make_aware(datetime.combine(inicio_semana_local, datetime.min.time()))
    inicio_mes_aware = timezone.make_aware(datetime.combine(inicio_mes_local, datetime.min.time()))

    vendas_hoje = Venda.objects.filter(comercio=comercio, data_hora__range=(inicio_dia_local, fim_dia_local))
    vendas_semana = Venda.objects.filter(comercio=comercio, data_hora__gte=inicio_semana_aware)
    vendas_mes = Venda.objects.filter(comercio=comercio, data_hora__gte=inicio_mes_aware)
    movimentacoes_hoje = MovimentacaoCaixa.objects.filter(caixa__comercio=comercio,
                                                          data__range=(inicio_dia_local, fim_dia_local))
    movimentacoes_semana = MovimentacaoCaixa.objects.filter(caixa__comercio=comercio, data__gte=inicio_semana_aware)
    movimentacoes_mes = MovimentacaoCaixa.objects.filter(caixa__comercio=comercio, data__gte=inicio_mes_aware)

    faturamento_hoje = vendas_hoje.aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00')
    faturamento_semana = vendas_semana.aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00')
    faturamento_mes = vendas_mes.aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0.00')
    lucro_hoje = sum(item.get_lucro_item() for venda in vendas_hoje for item in venda.itens.all())
    lucro_semana = sum(item.get_lucro_item() for venda in vendas_semana for item in venda.itens.all())
    lucro_mes = sum(item.get_lucro_item() for venda in vendas_mes for item in venda.itens.all())
    total_sangrias_hoje = movimentacoes_hoje.filter(tipo='sangria').aggregate(Sum('valor'))['valor__sum'] or Decimal(
        '0.00')
    total_sangrias_semana = movimentacoes_semana.filter(tipo='sangria').aggregate(Sum('valor'))[
                                'valor__sum'] or Decimal('0.00')
    total_sangrias_mes = movimentacoes_mes.filter(tipo='sangria').aggregate(Sum('valor'))['valor__sum'] or Decimal(
        '0.00')
    total_suplementos_hoje = movimentacoes_hoje.filter(tipo='suplemento').aggregate(Sum('valor'))[
                                 'valor__sum'] or Decimal('0.00')
    total_suplementos_semana = movimentacoes_semana.filter(tipo='suplemento').aggregate(Sum('valor'))[
                                   'valor__sum'] or Decimal('0.00')
    total_suplementos_mes = movimentacoes_mes.filter(tipo='suplemento').aggregate(Sum('valor'))[
                                'valor__sum'] or Decimal('0.00')

    contexto = {
        'comercio': comercio,
        'faturamento_hoje': faturamento_hoje,
        'faturamento_semana': faturamento_semana,
        'faturamento_mes': faturamento_mes,
        'lucro_hoje': lucro_hoje,
        'lucro_semana': lucro_semana,
        'lucro_mes': lucro_mes,
        'total_sangrias_hoje': total_sangrias_hoje,
        'total_sangrias_semana': total_sangrias_semana,
        'total_sangrias_mes': total_sangrias_mes,
        'total_suplementos_hoje': total_suplementos_hoje,
        'total_suplementos_semana': total_suplementos_semana,
        'total_suplementos_mes': total_suplementos_mes,
        'movimentacoes_hoje': movimentacoes_hoje,
        'hoje': hoje_local,
    }
    return render(request, 'core/painel/relatorios.html', contexto)


@login_required
@comercio_ativo_required
def entrada_estoque(request, comercio):
    if request.method == 'POST':
        form = EntradaEstoqueForm(request.POST)
        form.fields['produto'].queryset = Produto.objects.filter(comercio=comercio)
        if form.is_valid():
            nova_entrada = form.save(commit=False)
            nova_entrada.comercio = comercio
            nova_entrada.save()
            produto = nova_entrada.produto
            produto.quantidade_estoque = F('quantidade_estoque') + nova_entrada.quantidade
            produto.preco_custo = nova_entrada.preco_custo_unitario
            produto.save(update_fields=['quantidade_estoque', 'preco_custo'])
            return redirect('gerenciar_produtos')
    else:
        form = EntradaEstoqueForm()
        form.fields['produto'].queryset = Produto.objects.filter(comercio=comercio)
    contexto = {'comercio': comercio, 'form': form, }
    return render(request, 'core/painel/entrada_estoque.html', contexto)


@login_required
@comercio_ativo_required
def excluir_item(request, comercio, tipo_item, item_id):
    modelos = {
        'produto': (Produto, 'gerenciar_produtos'),
        'servico': (Servico, 'gerenciar_servicos'),
        'funcionario': (Funcionario, 'gerenciar_funcionarios'),
    }
    Model, url_redirecionamento = modelos.get(tipo_item)
    if not Model:
        return HttpResponseNotFound("Tipo de item inválido")
    item_para_excluir = get_object_or_404(Model, id=item_id, comercio=comercio)
    if request.method == 'POST':
        item_para_excluir.delete()
        messages.success(request, f'{tipo_item.capitalize()} excluído com sucesso.')
        return redirect(url_redirecionamento)
    contexto = {
        'item': item_para_excluir,
        'tipo_item': tipo_item,
        'comercio': comercio,
    }
    return render(request, 'core/painel/excluir_item_confirmacao.html', contexto)


@login_required
@comercio_ativo_required
def pdv(request, comercio):
    caixa_aberto = Caixa.objects.filter(comercio=comercio, aberto=True).first()
    if not caixa_aberto:
        return redirect('abrir_caixa')
    contexto = {
        'comercio': comercio,
        'caixa': caixa_aberto
    }
    return render(request, 'core/painel/pdv.html', contexto)


@login_required
@comercio_ativo_required
def abrir_caixa(request, comercio):
    if Caixa.objects.filter(comercio=comercio, aberto=True).exists():
        messages.warning(request, "Já existe um caixa aberto. Finalize a venda ou feche o caixa atual.")
        return redirect('painel_pdv')
    if request.method == 'POST':
        valor_abertura_str = request.POST.get('valor_abertura')
        if valor_abertura_str:
            try:
                valor_formatado = valor_abertura_str.replace(',', '.')
                valor_decimal = Decimal(valor_formatado)
                Caixa.objects.create(
                    comercio=comercio,
                    operador=request.user,
                    valor_abertura=valor_decimal
                )
                messages.success(request, f"Caixa aberto com sucesso com o valor inicial de R$ {valor_decimal:.2f}.")
                return redirect('painel_pdv')
            except Exception:
                messages.error(request, "Valor de abertura inválido. Por favor, insira um número.")
    contexto = {'comercio': comercio}
    return render(request, 'core/painel/abrir_caixa.html', contexto)


@login_required
@comercio_ativo_required
def fechar_caixa(request, comercio):
    caixa_aberto = Caixa.objects.filter(comercio=comercio, aberto=True).first()
    if not caixa_aberto:
        messages.error(request, "Nenhum caixa aberto para fechar.")
        return redirect('painel_home')
    vendas_do_caixa = Venda.objects.filter(
        comercio=comercio,
        data_hora__gte=caixa_aberto.data_abertura,
    )
    total_vendas_dinheiro = vendas_do_caixa.filter(forma_pagamento='dinheiro').aggregate(Sum('valor_total'))[
                                'valor_total__sum'] or Decimal('0.00')
    total_suplementos = MovimentacaoCaixa.objects.filter(caixa=caixa_aberto, tipo='suplemento').aggregate(Sum('valor'))[
                            'valor__sum'] or Decimal('0.00')
    total_sangrias = MovimentacaoCaixa.objects.filter(caixa=caixa_aberto, tipo='sangria').aggregate(Sum('valor'))[
                         'valor__sum'] or Decimal('0.00')
    valor_esperado = (caixa_aberto.valor_abertura + total_vendas_dinheiro + total_suplementos) - total_sangrias
    if request.method == 'POST':
        caixa_aberto.valor_fechamento = valor_esperado
        caixa_aberto.data_fechamento = timezone.now()
        caixa_aberto.aberto = False
        caixa_aberto.save()
        messages.success(request, f"Caixa fechado com sucesso com o valor de R$ {valor_esperado}.")
        return redirect('painel_home')
    contexto = {
        'caixa': caixa_aberto,
        'total_vendas_dinheiro': total_vendas_dinheiro,
        'total_suplementos': total_suplementos,
        'total_sangrias': total_sangrias,
        'valor_esperado': valor_esperado,
        'comercio': comercio,
    }
    return render(request, 'core/painel/fechar_caixa.html', contexto)


@login_required
@comercio_ativo_required
def movimentacao_caixa(request, comercio, tipo):
    caixa_aberto = Caixa.objects.filter(comercio=comercio, aberto=True).first()
    if not caixa_aberto:
        messages.error(request, "Nenhum caixa aberto para fazer a movimentação.")
        return redirect('painel_home')
    if request.method == 'POST':
        form = MovimentacaoCaixaForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.caixa = caixa_aberto
            movimentacao.tipo = tipo
            movimentacao.save()
            return redirect('painel_pdv')
    else:
        form = MovimentacaoCaixaForm()
    contexto = {
        'form': form,
        'tipo': tipo.capitalize(),
        'comercio': comercio,
    }
    return render(request, 'core/painel/movimentacao_caixa.html', contexto)


@login_required
@comercio_ativo_required
def buscar_itens_pdv(request, comercio):
    termo_busca = request.GET.get('termo', '')
    produtos = Produto.objects.filter(
        Q(nome__icontains=termo_busca) | Q(codigo_barras=termo_busca),
        comercio=comercio
    )
    servicos = Servico.objects.filter(nome__icontains=termo_busca, comercio=comercio)
    resultados = []
    for produto in produtos:
        resultados.append(
            {'id': f'produto_{produto.id}', 'nome': produto.nome, 'preco': str(produto.preco_venda), 'tipo': 'Produto'})
    for servico in servicos:
        resultados.append(
            {'id': f'servico_{servico.id}', 'nome': servico.nome, 'preco': str(servico.valor), 'tipo': 'Serviço'})
    return JsonResponse({'itens': resultados})


@login_required
@comercio_ativo_required
def finalizar_venda(request, comercio):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            carrinho = dados.get('carrinho', [])
            forma_pagamento = dados.get('forma_pagamento')
            valor_total = dados.get('total')
            desconto = dados.get('desconto', 0)
            cliente_info_texto = dados.get('cliente_info_texto')
            with transaction.atomic():
                nova_venda = Venda.objects.create(
                    comercio=comercio,
                    valor_total=valor_total,
                    desconto=desconto,
                    forma_pagamento=forma_pagamento,
                    cliente_info_texto=cliente_info_texto
                )
                for item_carrinho in carrinho:
                    item_id_str = item_carrinho.get('id', '')
                    quantidade = item_carrinho.get('quantidade', 0)
                    desconto_item = item_carrinho.get('desconto', 0)
                    if item_id_str.startswith('produto_'):
                        produto_id = int(item_id_str.split('_')[1])
                        produto = Produto.objects.get(id=produto_id)
                        ItemVendido.objects.create(
                            venda=nova_venda,
                            produto=produto,
                            quantidade=quantidade,
                            preco_unitario_na_venda=produto.preco_venda,
                            preco_custo_unitario_na_venda=produto.preco_custo,
                            desconto=desconto_item
                        )
                        produto.quantidade_estoque = F('quantidade_estoque') - quantidade
                        produto.save()
                    elif item_id_str.startswith('servico_'):
                        servico_id = int(item_id_str.split('_')[1])
                        servico = Servico.objects.get(id=servico_id)
                        ItemVendido.objects.create(
                            venda=nova_venda,
                            servico=servico,
                            quantidade=quantidade,
                            preco_unitario_na_venda=servico.valor,
                            preco_custo_unitario_na_venda=0,
                            desconto=desconto_item
                        )
            return JsonResponse({'success': True, 'venda_id': nova_venda.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método não permitido'}, status=405)


@login_required
@comercio_ativo_required
def recibo_venda(request, comercio, venda_id):
    try:
        venda = Venda.objects.get(id=venda_id, comercio=comercio)
    except Venda.DoesNotExist:
        return HttpResponseNotFound("Venda não encontrada")
    contexto = {'venda': venda, 'comercio': comercio}
    return render(request, 'core/painel/recibo_venda.html', contexto)


@login_required
@comercio_ativo_required
def cupom_venda(request, comercio, venda_id):
    try:
        venda = Venda.objects.get(id=venda_id, comercio=comercio)
    except Venda.DoesNotExist:
        return HttpResponseNotFound("Venda não encontrada")

    contexto = {'venda': venda, 'comercio': comercio}
    # Esta função irá renderizar um novo ficheiro HTML que vamos criar a seguir
    return render(request, 'core/painel/cupom_termico.html', contexto)