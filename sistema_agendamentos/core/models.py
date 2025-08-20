from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from decimal import Decimal  # Adicionei esta importação que estava faltando para o Decimal funcionar


# --- NOVO MODELO PARA GERENCIAR A EQUIPE ---
class MembroComercio(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),  # Pode gerenciar tudo, incluindo a equipe
        ('vendedor', 'Vendedor'),  # Pode apenas acessar o PDV e fazer vendas
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='membro_de')
    comercio = models.ForeignKey('Comercio', on_delete=models.CASCADE)
    role = models.CharField('Função', max_length=20, choices=ROLE_CHOICES, default='vendedor')

    class Meta:
        # Garante que um usuário só pode ter uma função em um comércio
        unique_together = ('usuario', 'comercio')

    def __str__(self):
        return f'{self.usuario.username} - {self.comercio.nome} ({self.get_role_display()})'


class Comercio(models.Model):
    dono = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    cnpj = models.CharField('CNPJ', max_length=18, blank=True, null=True)
    email_contato = models.EmailField('E-mail de Contato', blank=True, null=True)
    cpf_responsavel = models.CharField('CPF do Responsável', max_length=14, blank=True, null=True)
    acesso_bloqueado = models.BooleanField('Bloquear Acesso', default=False)
    whatsapp = models.CharField('WhatsApp', max_length=20, blank=True, null=True)
    endereco = models.CharField('Endereço', max_length=255, blank=True, null=True)
    horario_funcionamento = models.TextField('Horário de Funcionamento', blank=True, null=True)
    logo_personalizada = models.ImageField('Logo Personalizada (Painel)', upload_to='logos_personalizadas/', null=True,
                                           blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

# --- O RESTO DOS SEUS MODELOS (INTACTOS) ---

class Servico(models.Model):
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    duracao_minutos = models.IntegerField(default=60)
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nome


class Funcionario(models.Model):
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    servicos_que_realiza = models.ManyToManyField(Servico, blank=True)

    def __str__(self):
        return self.nome


class HorarioTrabalho(models.Model):
    DIAS_DA_SEMANA = (
        (1, 'Segunda-feira'), (2, 'Terça-feira'), (3, 'Quarta-feira'),
        (4, 'Quinta-feira'), (5, 'Sexta-feira'), (6, 'Sábado'), (7, 'Domingo')
    )
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    dia_da_semana = models.IntegerField(choices=DIAS_DA_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    def __str__(self):
        return f"{self.get_dia_da_semana_display()} de {self.hora_inicio} às {self.hora_fim}"


class Agendamento(models.Model):
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    data_hora = models.DateTimeField()

    def __str__(self):
        return f"Agendamento para {self.cliente.username} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class Produto(models.Model):
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    codigo_barras = models.CharField(max_length=100, blank=True, null=True, unique=True)
    nome = models.CharField(max_length=100)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_estoque = models.IntegerField(default=0)

    def __str__(self):
        return self.nome


class Venda(models.Model):
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    data_hora = models.DateTimeField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    forma_pagamento = models.CharField(max_length=50)
    cliente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    cliente_info_texto = models.CharField(max_length=100, blank=True, null=True,
                                          verbose_name="Informação do Cliente no Cupom")

    def __str__(self):
        return f"Venda #{self.id} - {self.data_hora.strftime('%d/%m/%Y')}"


class ItemVendido(models.Model):
    venda = models.ForeignKey(Venda, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True, blank=True)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, null=True, blank=True)
    quantidade = models.IntegerField()
    preco_unitario_na_venda = models.DecimalField(max_digits=10, decimal_places=2)
    preco_custo_unitario_na_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def get_lucro_item(self):
        return (self.preco_unitario_na_venda - self.preco_custo_unitario_na_venda) * self.quantidade - self.desconto


class EntradaEstoque(models.Model):
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco_custo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateTimeField(auto_now_add=True)


class Caixa(models.Model):
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    operador = models.ForeignKey(User, on_delete=models.CASCADE)
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_fechamento = models.DateTimeField(null=True, blank=True)
    valor_abertura = models.DecimalField(max_digits=10, decimal_places=2)
    valor_fechamento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    aberto = models.BooleanField(default=True)


class MovimentacaoCaixa(models.Model):
    TIPO_CHOICES = (('sangria', 'Sangria'), ('suplemento', 'Suplemento'))
    caixa = models.ForeignKey(Caixa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    data = models.DateTimeField(auto_now_add=True)


class ClienteProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente_profile')
    comercio_associado = models.ForeignKey(Comercio, on_delete=models.CASCADE)

    def __str__(self):
            return f"Perfil de {self.user.username} para {self.comercio_associado.nome}"