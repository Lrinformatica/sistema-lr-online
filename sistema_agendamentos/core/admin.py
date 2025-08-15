from django.contrib import admin
from .models import (
    Comercio, Servico, Funcionario, HorarioTrabalho, Agendamento,
    Produto, Venda, ItemVendido, EntradaEstoque, Caixa, MovimentacaoCaixa
)

class ComercioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'dono', 'acesso_bloqueado')
    list_filter = ('acesso_bloqueado',)
    search_fields = ('nome', 'dono__username')

admin.site.register(Comercio, ComercioAdmin)
admin.site.register(Venda)
admin.site.register(Caixa)
admin.site.register(Produto)
admin.site.register(Servico)
admin.site.register(Funcionario)
admin.site.register(Agendamento)
admin.site.register(MovimentacaoCaixa)
admin.site.register(EntradaEstoque)
admin.site.register(HorarioTrabalho)