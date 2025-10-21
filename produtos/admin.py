# produtos/admin.py (VERSÃO FINAL COM IMAGENS E GALERIA)

from django.contrib import admin
# 🚨 1. Importar todos os novos modelos (incluindo ImagemProduto) 🚨
from .models import Categoria, Produto, Variacao, ImagemProduto 
from .models import Promocao


# -----------------------------------------------------------------
# 1. Inlines (Seções que aparecem abaixo do formulário principal)
# -----------------------------------------------------------------

# 1.1. Inline para a Galeria de Imagens
class ImagemProdutoInline(admin.TabularInline):
    """Permite adicionar várias fotos por produto na mesma página."""
    model = ImagemProduto
    extra = 1 # Mostra um campo de upload vazio por padrão
    # Permite linkar a imagem à variação específica
    fields = ('imagem', 'variacao', 'descricao', 'ordem') 


# 1.2. Inline para Variações (com campo de imagem)
class VariacaoInline(admin.TabularInline):
    """Permite editar as variações dentro da página do Produto."""
    model = Variacao
    extra = 1 
    # 🚨 Incluir o novo campo 'imagem' aqui 🚨
    fields = ('tipo', 'valor', 'preco_adicional', 'estoque', 'imagem')


# -----------------------------------------------------------------
# 2. Classes de Registro no Admin
# -----------------------------------------------------------------

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'estoque', 'disponivel', 'usa_variacoes')
    list_filter = ('disponivel', 'categoria', 'usa_variacoes')
    search_fields = ('nome', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    list_editable = ('preco', 'estoque', 'disponivel')
    
    # 🚨 3. Ligar os Inlines ao ProdutoAdmin 🚨
    inlines = [VariacaoInline, ImagemProdutoInline] 
    
    # Definição dos campos para o formulário principal
    fieldsets = (
        (None, {
            'fields': ('categoria', 'nome', 'slug', 'descricao', 'preco', 'imagem'),
        }),
        ('Controle de Estoque/Variação', {
            'fields': ('usa_variacoes', 'estoque', 'disponivel'),
            'description': 'O campo Estoque só é relevante se "usa variações" estiver DESMARCADO.',
        }),
    )

    # --------------------------------------------------------------------------------
    # 4. Função para Manipular a Exibição do Campo ESTOQUE
    # --------------------------------------------------------------------------------
    def get_fieldsets(self, request, obj=None):
        """Alterna a exibição do campo 'estoque' se o objeto usa variações."""
        fieldsets = list(self.fieldsets)
        
        # Encontra o fieldset de Controle de Estoque (é sempre o segundo item)
        controle_fieldset = list(fieldsets[1][1]['fields'])
        
        # O Django só chama esta lógica se estiver editando um objeto (obj is not None)
        if obj and obj.usa_variacoes:
            if 'estoque' in controle_fieldset:
                controle_fieldset.remove('estoque')
        
        # Atualiza o fieldset com a lista de campos ajustada
        fieldsets[1][1]['fields'] = tuple(controle_fieldset)
        
        return fieldsets
    


@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "desconto_percentual", "ativa", "data_inicio", "data_fim")
    list_filter = ("ativa", "data_inicio", "data_fim")
    search_fields = ("nome", "descricao")
    filter_horizontal = ("produtos",)
    fieldsets = (
        (None, {"fields": ("nome", "descricao", "desconto_percentual", "ativa")}),
        ("Período da promoção", {"fields": ("data_inicio", "data_fim")}),
        ("Produtos incluídos", {"fields": ("produtos",)}),
    )

