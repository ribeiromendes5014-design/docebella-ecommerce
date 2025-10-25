# produtos/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Banner,
    MensagemTopo,
    Categoria,
    Produto,
    Promocao,
    ImagemProduto,
    VariacaoCor,
    VariacaoTamanho,
)
from . import models
from .models import Produto, VariacaoCor, VariacaoTamanho, ImagemProduto

# -----------------------------------------------------------------
# 1. Inlines (Imagens e Variações)
# -----------------------------------------------------------------
class ImagemProdutoInline(admin.TabularInline):
    """Permite adicionar várias fotos por produto na mesma página."""
    model = models.ImagemProduto
    extra = 1
    fields = ('imagem', 'imagem_url_externa', 'variacao', 'descricao', 'ordem', 'preview_imagem')
    readonly_fields = ('preview_imagem',)

    def preview_imagem(self, obj):
        """Mostra uma miniatura da imagem local ou externa."""
        if not obj.pk:
            return ""
        url = obj.get_imagem_url()
        if not url:
            return "—"
        return format_html('<img src="{}" style="max-height: 100px; border-radius: 6px;">', url)

    preview_imagem.short_description = "Pré-visualização"


class VariacaoCorInline(admin.StackedInline):
    """Permite adicionar cores do produto."""
    model = VariacaoCor
    extra = 1
    fields = ('cor', 'imagem', 'imagem_url_externa')
    verbose_name = 'Variação de Cor'
    verbose_name_plural = 'Variações de Cores'


class VariacaoTamanhoInline(admin.TabularInline):
    """Permite adicionar tamanhos/numerações por cor."""
    model = VariacaoTamanho
    extra = 1
    fields = ('variacao_cor', 'tamanho', 'preco_adicional', 'estoque')
    verbose_name = 'Numeração/Estoque'
    verbose_name_plural = 'Numerações/Estoques'


# -----------------------------------------------------------------
# 2. MensagemTopo
# -----------------------------------------------------------------
@admin.register(MensagemTopo)
class MensagemTopoAdmin(admin.ModelAdmin):
    list_display = ('texto', 'ativo', 'ordem', 'data_inicio', 'data_fim')
    list_editable = ('ativo', 'ordem')
    search_fields = ('texto',)
    ordering = ('ordem',)


# -----------------------------------------------------------------
# 3. Banner
# -----------------------------------------------------------------
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ativo', 'ordem', 'usar_em_carrossel')
    list_editable = ('ativo', 'ordem', 'usar_em_carrossel')
    search_fields = ('titulo',)
    ordering = ('ordem',)


# -----------------------------------------------------------------
# 4. Categoria
# -----------------------------------------------------------------
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}


# -----------------------------------------------------------------
# 5. Produto
# -----------------------------------------------------------------
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'estoque', 'disponivel', 'usa_variacoes')
    list_filter = ('disponivel', 'categoria', 'usa_variacoes')
    search_fields = ('nome', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    list_editable = ('preco', 'estoque', 'disponivel')

    # Exibe tudo junto na tela do produto
    inlines = [VariacaoCorInline, VariacaoTamanhoInline, ImagemProdutoInline]

    fieldsets = (
        (None, {
            'fields': (
                'categoria',
                'nome',
                'slug',
                'descricao',
                'preco',
                'imagem',
                'imagem_url_externa',
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
# 6. Promoção
# -----------------------------------------------------------------
@admin.register(Promocao)
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
        return "✅ Vigente" if obj.esta_vigente() else "⛔ Expirada"
    esta_vigente.short_description = "Status"
