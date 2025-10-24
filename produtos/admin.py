# produtos/admin.py

from django.contrib import admin
from . import models  # Importa o módulo completo — seguro contra ImportError


# -----------------------------------------------------------------
# 1. Inlines (Imagens e Variações)
# -----------------------------------------------------------------
class ImagemProdutoInline(admin.TabularInline):
    """Permite adicionar várias fotos por produto na mesma página."""
    model = models.ImagemProduto
    extra = 1
    fields = ('imagem', 'variacao', 'descricao', 'ordem')


class VariacaoInline(admin.TabularInline):
    """Permite editar as variações dentro da página do Produto."""
    model = models.Variacao
    extra = 1
    fields = (
        'tipo',
        'valor',
        'preco_adicional',
        'estoque',
        'imagem',
        'imagem_url_externa',  # 👈 adiciona aqui
    )



# -----------------------------------------------------------------
#Texto admin
# -----------------------------------------------------------------
from django.contrib import admin
from .models import Banner, MensagemTopo

@admin.register(MensagemTopo)
class MensagemTopoAdmin(admin.ModelAdmin):
    list_display = ('texto', 'ativo', 'ordem', 'data_inicio', 'data_fim')
    list_editable = ('ativo', 'ordem')
    search_fields = ('texto',)
    ordering = ('ordem',)

# -----------------------------------------------------------------
# Banner admin
# -----------------------------------------------------------------
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ativo', 'ordem', 'usar_em_carrossel')
    list_editable = ('ativo', 'ordem', 'usar_em_carrossel')
    search_fields = ('titulo',)
    ordering = ('ordem',)


# -----------------------------------------------------------------
# 2. Categoria
# -----------------------------------------------------------------
@admin.register(models.Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}


# -----------------------------------------------------------------
# 3. Produto
# -----------------------------------------------------------------
@admin.register(models.Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'estoque', 'disponivel', 'usa_variacoes')
    list_filter = ('disponivel', 'categoria', 'usa_variacoes')
    search_fields = ('nome', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    list_editable = ('preco', 'estoque', 'disponivel')

    inlines = [VariacaoInline, ImagemProdutoInline]

    fieldsets = (
    (None, {
        'fields': (
            'categoria',
            'nome',
            'slug',
            'descricao',
            'preco',
            'imagem',
            'imagem_url_externa',  # 👈 adiciona aqui
        ),
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
# 4. Promoção
# -----------------------------------------------------------------
@admin.register(models.Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "produto", "desconto_percentual", "valor_desconto", "ativo", "data_inicio", "data_fim")
    list_filter = ("ativo", "data_inicio", "data_fim")
    search_fields = ("titulo", "produto__nome")

    fieldsets = (
        (None, {
            "fields": ("titulo", "produto", "desconto_percentual", "valor_desconto", "ativo"),
        }),
        ("Período da promoção", {
            "fields": ("data_inicio", "data_fim"),
        }),
    )

    def esta_vigente(self, obj):
        """Exibe um ícone ou texto para status de validade."""
        return "✅ Vigente" if obj.esta_vigente() else "⛔ Expirada"

    esta_vigente.short_description = "Status"
