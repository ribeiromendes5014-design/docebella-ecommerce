# produtos/admin.py (VERSÃO AJUSTADA E CORRIGIDA)

from django.contrib import admin
from .models import Categoria, Produto, Variacao, ImagemProduto, Promocao


# -----------------------------------------------------------------
# 1. Inlines (Imagens e Variações)
# -----------------------------------------------------------------

class ImagemProdutoInline(admin.TabularInline):
    """Permite adicionar várias fotos por produto na mesma página."""
    model = ImagemProduto
    extra = 1
    fields = ('imagem', 'variacao', 'descricao', 'ordem')


class VariacaoInline(admin.TabularInline):
    """Permite editar as variações dentro da página do Produto."""
    model = Variacao
    extra = 1
    fields = ('tipo', 'valor', 'preco_adicional', 'estoque', 'imagem')


# -----------------------------------------------------------------
# 2. Categoria
# -----------------------------------------------------------------

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}


# -----------------------------------------------------------------
# 3. Produto
# -----------------------------------------------------------------

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'estoque', 'disponivel', 'usa_variacoes')
    list_filter = ('disponivel', 'categoria', 'usa_variacoes')
    search_fields = ('nome', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    list_editable = ('preco', 'estoque', 'disponivel')

    inlines = [VariacaoInline, ImagemProdutoInline]

    fieldsets = (
        (None, {
            'fields': ('categoria', 'nome', 'slug', 'descricao', 'preco', 'imagem'),
        }),
        ('Controle de Estoque/Variação', {
            'fields': ('usa_variacoes', 'estoque', 'disponivel'),
            'description': 'O campo Estoque só é relevante se "usa variações" estiver DESMARCADO.',
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """Remove o campo 'estoque' se o produto usa variações."""
        fieldsets = list(self.fieldsets)
        controle_fieldset = list(fieldsets[1][1]['fields'])
        if obj and obj.usa_variacoes and 'estoque' in controle_fieldset:
            controle_fieldset.remove('estoque')
        fieldsets[1][1]['fields'] = tuple(controle_fieldset)
        return fieldsets


# -----------------------------------------------------------------
# 4. Promoção (CORRIGIDO)
# -----------------------------------------------------------------

@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "desconto_percentual", "ativa", "data_inicio", "data_fim")
    list_filter = ("ativa", "data_inicio", "data_fim")
    search_fields = ("nome", "descricao", "produtos__nome")
    filter_horizontal = ("produtos",)

    fieldsets = (
        (None, {
            "fields": ("nome", "descricao", "desconto_percentual", "ativa")
        }),
        ("Período da promoção", {
            "fields": ("data_inicio", "data_fim")
        }),
        ("Produtos incluídos", {
            "fields": ("produtos",),
            "description": "Selecione um ou mais produtos para aplicar esta promoção."
        }),
    )

    def get_queryset(self, request):
        """Retorna o queryset padrão sem usar select_related (pois é ManyToMany)."""
        return super().get_queryset(request)

    def esta_vigente(self, obj):
        """Exibe um ícone ou texto para status de validade."""
        return "✅ Vigente" if obj.esta_vigente() else "⛔ Expirada"
    esta_vigente.short_description = "Status"
    from django.contrib import admin

# 🌸 Personalização visual do painel
admin.site.site_header = "Doce & Bella - Painel Administrativo 💅"
admin.site.site_title = "Administração Doce & Bella"
admin.site.index_title = "Bem-vinda ao Painel de Gestão, Bella!"

