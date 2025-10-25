# produtos/admin.py

from django.contrib import admin
from . import models  # Importa o módulo completo — seguro contra ImportError
from django.utils.html import format_html
import nested_admin


# -----------------------------------------------------------------
# 1. Inlines (Imagens e Variações)
# -----------------------------------------------------------------
class ImagemProdutoInline(nested_admin.NestedTabularInline):
    """Permite adicionar várias fotos por produto na mesma página."""
    model = models.ImagemProduto
    extra = 1
    sortable_field_name = "ordem"  # <- 👈 ESSENCIAL para o nested_admin funcionar!

    # Campos que aparecem no admin
    fields = (
        'imagem',
        'imagem_url_externa',
        'variacao',
        'descricao',
        'ordem',
        'preview_imagem',
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
#   variação
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# 2.1 Variações e Subvariações com Nested Admin
# -----------------------------------------------------------------
import nested_admin

class SubVariacaoInline(nested_admin.NestedTabularInline):
    """Subvariações dentro de uma variação principal (ex: Tamanhos dentro de Cor)."""
    model = models.Variacao
    fk_name = 'parent'
    extra = 1
    fields = ('tipo', 'valor', 'estoque', 'imagem', 'imagem_url_externa')
    verbose_name = "Subvariação"
    verbose_name_plural = "Subvariações"


class VariacaoInline(nested_admin.NestedTabularInline):
    """Variações principais (ex: Cores), que podem conter subvariações."""
    model = models.Variacao
    fk_name = 'produto'
    extra = 1
    fields = (
        'tipo',
        'valor',
        'estoque',
        'imagem',
        'imagem_url_externa',
        'parent',  # 👈 Adicionado
    )
    verbose_name = "Variação"
    verbose_name_plural = "Variações"

# -----------------------------------------------------------------
# 2.1 Variações e Subvariações
# -----------------------------------------------------------------



@admin.register(models.Variacao)
class VariacaoAdmin(admin.ModelAdmin):
    """Admin para gerenciar variações de forma hierárquica."""
    list_display = ('produto', 'tipo', 'valor', 'estoque', 'parent')
    list_filter = ('produto', 'tipo')
    search_fields = ('valor', 'produto__nome')
    exclude = ('parent',)






@admin.register(models.Produto)
class ProdutoAdmin(nested_admin.NestedModelAdmin):
    """Admin completo do produto com variações aninhadas e imagens."""
    inlines = [VariacaoInline, ImagemProdutoInline]
    list_display = ('nome', 'categoria', 'preco', 'estoque', 'disponivel', 'usa_variacoes')
    list_filter = ('disponivel', 'categoria', 'usa_variacoes')
    search_fields = ('nome', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    list_editable = ('preco', 'estoque', 'disponivel')

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
