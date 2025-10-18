# produtos/admin.py (CORRIGIDO)
from django.contrib import admin
from .models import Categoria, Produto, Variacao # Importar Variacao

# 1. Inline para Variações
class VariacaoInline(admin.TabularInline):
    """Permite editar as variações dentro da página do Produto."""
    model = Variacao
    extra = 1 # Mostra uma linha vazia extra para adicionar
    # Exibe todos os campos relevantes
    fields = ('tipo', 'valor', 'preco_adicional', 'estoque') 

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
    
    # 🚨 ESTA PROPRIEDADE DEVE SER COMENTADA OU REMOVIDA 🚨
    # inlines = [VariacaoInline]  
    
    # Adicionando o fieldsets de volta (que é onde o inlines estava)
    fieldsets = (
        (None, {
            'fields': ('categoria', 'nome', 'slug', 'descricao', 'preco', 'imagem'),
        }),
        ('Controle de Estoque/Variação', {
            'fields': ('usa_variacoes', 'estoque', 'disponivel'),
            'description': 'O campo Estoque só é relevante se "usa variações" estiver DESMARCADO.',
        }),
    )
