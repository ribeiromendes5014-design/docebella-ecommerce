from django.contrib import admin
from .models import EnderecoEntrega, Pedido, ItemPedido, Cupom

# ------------------------------------
# 1. ADMIN PARA ITENS DE PEDIDO (INLINE)
# ------------------------------------

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = ('produto', 'variacao', 'preco_unitario', 'quantidade')
    can_delete = False


# ------------------------------------
# 2. ADMIN PARA PEDIDOS
# ------------------------------------

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'cliente', 
        'data_criacao', 
        'status',
        'valor_total',
        'valor_frete',
        'valor_desconto',
        'codigo_rastreio',
    )
    list_filter = ('status', 'data_criacao')
    
    # 🚨 CORREÇÃO FINAL: Altera 'cliente__username' (que não existe) para 'cliente__email' 🚨
    search_fields = ('cliente__email', 'endereco__cep', 'id')
    
    # Detalhes que aparecem na página de edição
    fieldsets = (
        ('Informações do Pedido', {
            'fields': ('cliente', 'status', 'data_criacao', 'cupom'),
        }),
        ('Detalhes Financeiros', {
            'fields': ('valor_total', 'valor_frete', 'valor_desconto'),
        }),
        ('Entrega', {
            'fields': ('endereco', 'codigo_rastreio'),
        }),
    )
    
    # Inclui a lista de itens dentro da página de edição do pedido
    inlines = [ItemPedidoInline]
    
    # Campos que não podem ser alterados após o pedido ser feito
    readonly_fields = ('cliente', 'data_criacao', 'valor_total', 'valor_frete', 'valor_desconto', 'endereco', 'cupom')


# ------------------------------------
# 3. ADMIN PARA ENDEREÇOS (Opcional, para visualização)
# ------------------------------------

@admin.register(EnderecoEntrega)
class EnderecoEntregaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sobrenome', 'cep', 'cidade', 'estado')
    search_fields = ('nome', 'sobrenome', 'cep')
    readonly_fields = ('nome', 'sobrenome', 'email', 'cep', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado')
    list_per_page = 25


# ------------------------------------
# 4. ADMIN PARA CUPONS DE DESCONTO
# ------------------------------------

@admin.register(Cupom)
class CupomAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 
        'tipo', 
        'valor_desconto', 
        'valor_minimo_pedido', 
        'limite_usos', 
        'usos_atuais',
        'data_inicio',
        'data_fim',
        'ativo',
        'is_valid' 
    )
    list_filter = ('ativo', 'tipo', 'data_inicio', 'data_fim')
    search_fields = ('codigo',)
    readonly_fields = ('usos_atuais',)
