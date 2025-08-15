from django import forms
from django.contrib.auth.models import User
from .models import Produto, Comercio, Servico, Funcionario, EntradaEstoque, MovimentacaoCaixa

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'codigo_barras', 'preco_custo', 'preco_venda', 'quantidade_estoque']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'preco_custo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_venda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantidade_estoque': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# --- NOVO FORMULÁRIO ADICIONADO AQUI ---
class ComercioConfigForm(forms.ModelForm):
    class Meta:
        model = Comercio
        fields = ['nome', 'whatsapp', 'endereco', 'horario_funcionamento', 'logo_personalizada']
        labels = {
            'nome': 'Nome do Estabelecimento',
            'logo_personalizada': 'Logo (para o painel)',
            'horario_funcionamento': 'Horários de Atendimento',
        }
        help_texts = {
            'horario_funcionamento': 'Ex: Seg-Sex: 8h às 18h, Sab: 8h às 12h',
            'logo_personalizada': 'Esta logo aparecerá no topo do seu painel. Deixe em branco para usar a padrão.',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 79999998888'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'horario_funcionamento': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo_personalizada': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['nome', 'duracao_minutos', 'valor']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'duracao_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'servicos_que_realiza']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'servicos_que_realiza': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

class EntradaEstoqueForm(forms.ModelForm):
    class Meta:
        model = EntradaEstoque
        fields = ['produto', 'quantidade', 'preco_custo_unitario']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'preco_custo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class MovimentacaoCaixaForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoCaixa
        fields = ['valor', 'descricao']
        widgets = {
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'username', 'email']
        labels = {
            'first_name': 'Nome Completo',
            'username': 'Identificador (CPF/Telefone, apenas números)',
            'email': 'E-mail (Opcional)',
        }
        help_texts = {
            'username': 'Use um identificador único, como CPF ou telefone, sem pontos ou traços.',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = False