from django.contrib import admin
from .models import ItemCarrinho

@admin.register(ItemCarrinho)
class ItemCarrinhoAdmin(admin.ModelAdmin):
    # CORREÇÃO: Usar o nome correto 'adicionado_em' para exibir e filtrar
    list_display = ('produto', 'quantidade', 'session_key', 'adicionado_em')
    
    # CORREÇÃO: Usar o nome correto 'adicionado_em' para os filtros
    list_filter = ('adicionado_em',)
    
    # Campos de pesquisa
    search_fields = ('produto__nome', 'session_key')
    
    # CORREÇÃO: Usar o nome correto 'adicionado_em' para campos somente leitura
    readonly_fields = ('adicionado_em',)