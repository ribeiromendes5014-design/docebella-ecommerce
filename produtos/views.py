# produtos/views.py
from django.shortcuts import render
from produtos.models import Produto
from django.core.paginator import Paginator

def home(request):
    query = request.GET.get('q', '')
    produtos_list = Produto.objects.filter(disponivel=True, estoque__gt=0)

    if query:
        produtos_list = produtos_list.filter(nome__icontains=query)

    produtos_list = produtos_list.order_by('-id')

    paginator = Paginator(produtos_list, 12)
    page = request.GET.get('page')
    produtos = paginator.get_page(page)

    return render(request, 'produtos/home.html', {
        'produtos': produtos,
        'query': query,
        'titulo': 'Doce & Bella E-commerce'
    })



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

    # 🔹 Cálculo da simulação de parcelamento
    preco = produto.preco or Decimal('0')
    valor_final = preco / Decimal('0.8872')  # Corrige o valor com base na sua fórmula
    valor_parcela = valor_final / Decimal('3')  # Divide em 3x

    # >> NOVO: Lógica para Produtos Relacionados <<
    produtos_relacionados = Produto.objects.filter(
        categoria=produto.categoria,  # Busca produtos da mesma categoria
        disponivel=True,
        estoque__gt=0                 # Com estoque
    ).exclude(
        id=produto.id                 # Exclui o produto atual
    ).order_by('?')[:4]               # Pega 4 produtos aleatórios
    
    # 🔹 Contexto enviado ao template
    context = {
        'produto': produto,
        'variacoes_por_tipo': variacoes_por_tipo,
        'produtos_relacionados': produtos_relacionados,
        'valor_parcela': valor_parcela,  # Adicionado aqui
        'titulo': f'{produto.nome} | Doce & Bella',
    }
    return render(request, 'produtos/detalhe_produto.html', context)
