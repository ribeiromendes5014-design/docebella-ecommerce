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
    
    # 🔴 ESSA LINHA DEVE ESTAR ATIVA PARA O PAINEL APARECER
    inlines = [VariacaoInline] 
    
    fieldsets = (
        (None, {
            'fields': ('categoria', 'nome', 'slug', 'descricao', 'preco', 'imagem'),
        }),
        ('Controle de Estoque/Variação', {
            # O campo 'estoque' é o estoque geral do produto, que deve ser escondido 
            # se 'usa_variacoes' for True. A variação é que terá seu próprio estoque.
            'fields': ('usa_variacoes', 'estoque', 'disponivel'),
            'description': 'O campo Estoque só é relevante se "usa variações" estiver DESMARCADO.',
        }),
    )

    # --------------------------------------------------------------------------------
    # 🚨 Adicione esta função para manipular a exibição do campo ESTOQUE no Admin 🚨
    # --------------------------------------------------------------------------------
    def get_fieldsets(self, request, obj=None):
        """Alterna a exibição do campo 'estoque' se o objeto usa variações."""
        fieldsets = list(self.fieldsets)
        
        # Encontra o fieldset de Controle de Estoque
        controle_fieldset = list(fieldsets[1][1]['fields'])
        
        if obj and obj.usa_variacoes:
            # Se usa variações, esconde o campo 'estoque' do produto pai, 
            # pois o estoque está nos inlines (variações).
            if 'estoque' in controle_fieldset:
                controle_fieldset.remove('estoque')
        
        # Atualiza o fieldset
        fieldsets[1][1]['fields'] = tuple(controle_fieldset)
        
        return fieldsets
