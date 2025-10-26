# produtos/admin.py

from django.contrib import admin
from . import models  # Importa o módulo completo — seguro contra ImportError
from django.utils.html import format_html
from django import forms
from django.core.exceptions import ValidationError

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


class VariacaoForm(forms.ModelForm):
    class Meta:
        model = models.Variacao
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        tipo = cleaned_data.get('tipo')
        valor = cleaned_data.get('valor')
        color = cleaned_data.get('cor')  # 👈 Adiciona aqui

        # Só valida se os dados principais existirem
        if produto and tipo and valor:
            existe = models.Variacao.objects.filter(
                produto=produto,
                tipo=tipo,
                valor=valor,
                cor=color  # 👈 usa aqui também
            )

            # Ignora a própria instância se estiver editando
            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():
                raise ValidationError(
                    f"Já existe uma variação '{valor}' ({color}) para o tipo '{tipo}' neste produto."
                )

        return cleaned_data

        
# -----------------------------------------------------------------
#   variação
# -----------------------------------------------------------------

class VariacaoInline(admin.TabularInline):
    model = models.Variacao
    extra = 1
    fields = ('cor', 'tamanho', 'outro', 'estoque', 'imagem', 'imagem_url_externa', 'preco_adicional')




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
