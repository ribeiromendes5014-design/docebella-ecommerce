from django.contrib import admin
# Imports de todos os modelos
from .models import EnderecoEntrega, Pedido, ItemPedido, Cupom, OpcaoFrete 


# ------------------------------------
# 1. ADMIN PARA ITENS DE PEDIDO (INLINE)
# ------------------------------------

class ItemPedidoInline(admin.TabularInline):
    """Exibe os itens do pedido dentro da página de edição do Pedido."""
    model = ItemPedido
    extra = 0
    can_delete = False
    readonly_fields = ('produto', 'variacao', 'preco_unitario', 'quantidade')
    fields = ('produto', 'variacao', 'preco_unitario', 'quantidade')


# ------------------------------------
# 2. ADMIN PARA PEDIDOS (CONSOLIDADO)
# ------------------------------------

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    
    # --- MÉTODOS PARA EXIBIR INFORMAÇÕES DE CONTATO ---
    def cliente_email(self, obj):
        # Puxa o email do objeto 'Cliente' (usuário)
        return obj.cliente.email if obj.cliente else 'N/A'
    cliente_email.short_description = 'Email do Cliente'

    def telefone_contato(self, obj):
        """Lê o telefone que foi salvo no campo 'complemento' do endereço dummy."""
        if obj.endereco and obj.endereco.complemento:
            # Retorna o complemento (que é a string "Telefone: XXXX")
            return obj.endereco.complemento
        return 'N/A'
    telefone_contato.short_description = 'Telefone de Contato'
    # --------------------------------------------------

    # 🚨 ATUALIZAÇÃO 1: Adiciona EMAIL do cliente na LISTA 🚨
    list_display = (
        'id', 
        'cliente', 
        'cliente_email', # NOVO: Email na lista
        'data_criacao', 
        'status',
        'valor_total',
        'valor_frete',
        'valor_desconto',
        'codigo_rastreio',
    )
    list_filter = ('status', 'data_criacao')
    
    # Busca por email do cliente
    search_fields = ('cliente__email', 'endereco__cep', 'id')
    
    # 🚨 ATUALIZAÇÃO 2: Reorganiza os fieldsets para incluir Contato 🚨
    fieldsets = (
        ('Informações de Contato e Pedido', {
            'fields': (
                'cliente', 
                'cliente_email', # NOVO: Email na página de edição
                'telefone_contato', # NOVO: Telefone na página de edição
                'data_criacao', 
                'status', 
                'metodo_envio', # Adicionado manualmente o campo que estava faltando
                'cupom'
            ),
        }),
        ('Detalhes Financeiros', {
            'fields': ('valor_total', 'valor_frete', 'valor_desconto'),
        }),
        ('Entrega e Rastreio', {
            # O campo 'endereco' contém o telefone no complemento do endereço dummy
            'fields': ('endereco', 'codigo_rastreio'), 
        }),
    )
    
    # Inclui a lista de itens dentro da página de edição do pedido
    inlines = [ItemPedidoInline]
    
    # 🚨 ATUALIZAÇÃO 3: Adiciona os novos campos à lista de SOMENTE LEITURA 🚨
    readonly_fields = (
        'cliente', 'cliente_email', 'telefone_contato', 'data_criacao', 
        'valor_total', 'valor_frete', 'valor_desconto', 'endereco', 'cupom', 
        'metodo_envio' # Adicionado
    )
    
    # Ações de Admin (Mantidas) 
    actions = ['marcar_como_em_separacao', 'marcar_como_pronto_para_retirada']

    def marcar_como_em_separacao(self, request, queryset):
        queryset.update(status='Em Separação')
        self.message_user(request, f"{queryset.count()} pedido(s) marcados como Em Separação.")
    marcar_como_em_separacao.short_description = "Marcar como Em Separação"
    
    def marcar_como_pronto_para_retirada(self, request, queryset):
        queryset.update(status='Enviado') 
        self.message_user(request, f"{queryset.count()} pedido(s) marcados como Pronto para Retirada.")
    marcar_como_pronto_para_retirada.short_description = "Marcar como Pronto para Retirada"


# ------------------------------------
# 3. ADMIN PARA OPÇÕES DE FRETE
# ------------------------------------

@admin.register(OpcaoFrete)
class OpcaoFreteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'custo', 'ativo')


# ------------------------------------
# 4. ADMIN PARA ENDEREÇOS (Opcional, para visualização)
# ------------------------------------

@admin.register(EnderecoEntrega)
class EnderecoEntregaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sobrenome', 'cep', 'cidade', 'estado')
    search_fields = ('nome', 'sobrenome', 'cep')
    readonly_fields = (
        'nome', 'sobrenome', 'email',
        'cep', 'rua',
        'complemento', 'bairro', 'cidade', 'estado'
    )
    list_per_page = 25


# ------------------------------------
# 5. ADMIN PARA CUPONS DE DESCONTO
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
        'categoria',    # ✅ novo campo
        'produto',      # ✅ novo campo
        'is_valid'
    )
    list_filter = ('ativo', 'tipo', 'categoria', 'data_inicio', 'data_fim')
    search_fields = ('codigo',)
    readonly_fields = ('usos_atuais',)

    fieldsets = (
        ('Informações do Cupom', {
            'fields': (
                'codigo',
                'tipo',
                'valor_desconto',
                'valor_minimo_pedido',
                'limite_usos',
                'usos_atuais',
                'ativo'
            )
        }),
        ('Período de Validade', {
            'fields': ('data_inicio', 'data_fim'),
        }),
        ('Restrições (opcionais)', {
            'fields': ('categoria', 'produto'),
            'description': 'Limite este cupom a uma categoria ou produto específico, se desejar.'
        }),
    )

    # Exibe "Válido" ou "Inválido" na listagem
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = "Válido?"
