# produtos/views.py
from django.shortcuts import render, get_object_or_404
from .models import Produto, Categoria, Variacao 


# View da Home Page
def home_page(request):
    """
    View da página inicial.
    Exibe uma lista de produtos disponíveis.
    """
    # Filtra apenas os produtos que estão disponíveis e têm estoque > 0
    # Usamos get_estoque_total para suportar produtos com ou sem variação
    produtos_destaque = [
        p for p in Produto.objects.filter(disponivel=True).order_by('-criado_em')
        if p.get_estoque_total() > 0
    ][:8]
    
    context = {
        'produtos': produtos_destaque,
        'titulo': "Doce & Bella - Sua loja de perfumaria e acessórios"
    }
    return render(request, 'produtos/home.html', context)


# NOVA VIEW: Detalhe do Produto (Com Produtos Relacionados)
def detalhe_produto(request, slug):
    # Busca o produto ou retorna 404
    produto = get_object_or_404(Produto, slug=slug, disponivel=True)
    
    # Separa as variações por tipo (ex: 'Tamanho', 'Cor') para exibição
    variacoes_por_tipo = {}
    if produto.usa_variacoes:
        tipos_disponiveis = produto.variacoes.values('tipo').distinct()
        for tipo in tipos_disponiveis:
            nome_tipo = tipo['tipo']
            variacoes_por_tipo[nome_tipo] = produto.variacoes.filter(tipo=nome_tipo).order_by('valor')

    # >> NOVO: Lógica para Produtos Relacionados <<
    produtos_relacionados = Produto.objects.filter(
        categoria=produto.categoria, # Busca produtos da mesma categoria
        disponivel=True,
        estoque__gt=0                # Com estoque
    ).exclude(
        id=produto.id                # Exclui o produto que estamos vendo
    ).order_by('?')[:4]              # Pega 4 produtos aleatórios
    
    context = {
        'produto': produto,
        'variacoes_por_tipo': variacoes_por_tipo,
        'produtos_relacionados': produtos_relacionados, # Adiciona ao contexto
        'titulo': f'{produto.nome} | Doce & Bella'
    }
    return render(request, 'produtos/detalhe_produto.html', context)