# produtos/admin.py

from django.contrib import admin
# Importa todos os modelos necessários diretamente
from .models import (
    Banner, 
    MensagemTopo, 
    Categoria, 
    Produto, 
    Promocao, 
    ImagemProduto,
    # ATENÇÃO: Os novos modelos devem estar aqui!
    VariacaoCor, 
    VariacaoTamanho 
) 
from . import models  # Importa o módulo completo — seguro contra ImportError
from django.utils.html import format_html


# -----------------------------------------------------------------
# 1. Inlines (Imagens e Variações)
# -----------------------------------------------------------------
class ImagemProdutoInline(admin.TabularInline):
    """Permite adicionar várias fotos por produto na mesma página."""
    model = models.ImagemProduto
    extra = 1

    # Campos que aparecem no admin
    fields = (
        'imagem',
        'imagem_url_externa',
        'variacao',
        'descricao',
        'ordem',
        'preview_imagem',  # mostra a miniatura
    )

    readonly_fields = ('preview_imagem',)

    def preview_imagem(self, obj):
        """Mostra uma miniatura da imagem local ou externa"""
        if not obj.pk:
            return ""
        url = obj.get_imagem_url()
        if not url:
            return "—"
        return format_html('<img src="{}" style="max-height: 100px; border-radius: 6px;">', url)

    preview_imagem.short_description = "Pré-visualização"


# NOVO INLINE 1: Variações de Tamanho (nível mais interno)
class VariacaoTamanhoInline(admin.TabularInline):
    """Permite adicionar vários tamanhos/estoques por cor."""
    model = VariacaoTamanho # Aponta para o novo modelo de Tamanho
    extra = 1
    # Note que o preço é o preço adicional da variação de tamanho/SKU
    fields = ('tamanho', 'preco_adicional', 'estoque') 
    verbose_name = 'Numeração/Estoque'
    verbose_name_plural = 'Numerações/Estoques'

# NOVO INLINE 2: Variações de Cor (nível intermediário, aninha os tamanhos)
class VariacaoCorInline(admin.StackedInline): # StackedInline é melhor para aninhar
    """Permite agrupar variações de tamanho por cor no admin do produto."""
    model = VariacaoCor # Aponta para o novo modelo de Cor
    extra = 1
    fields = ('cor', 'imagem', 'imagem_url_externa')
    
    # ANINHAMENTO: A Cor contém a lista de Tamanhos
    inlines = [VariacaoTamanhoInline] 
    
    verbose_name = 'Variação de Cor'
    verbose_name_plural = 'Variações de Cores'



# -----------------------------------------------------------------
#Texto admin
# -----------------------------------------------------------------

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
