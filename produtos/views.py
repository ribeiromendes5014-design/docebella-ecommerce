# produtos/views.py
from produtos.models import Produto, Variacao, Banner, MensagemTopo
from django.shortcuts import render
from produtos.models import Produto
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Exists, OuterRef
from produtos.models import Produto, Variacao
from decimal import Decimal
from produtos.models import Produto, Categoria
from django.utils import timezone
import json
from collections import defaultdict
from django.views.decorators.cache import cache_page

@cache_page(600)
def home(request):
    query = request.GET.get('q', '')

    # 🛑 OTIMIZAÇÃO CRÍTICA (N+1 Solution)
    # prefetch_related carrega promoções e variações em poucas consultas eficientes,
    # em vez de uma consulta separada para CADA produto no loop.
    produtos_list = Produto.objects.filter(
        disponivel=True
    ).filter(
        Q(estoque__gt=0) | Exists(
            Variacao.objects.filter(produto=OuterRef('pk'), estoque__gt=0)
        )
    ).prefetch_related('promocoes', 'variacoes') # <-- 2. A CHAVE DA VELOCIDADE

    if query:
        produtos_list = produtos_list.filter(nome__icontains=query)

    produtos_list = produtos_list.order_by('-id')
    paginator = Paginator(produtos_list, 200)
    page = request.GET.get('page')
    produtos = paginator.get_page(page)

    # O loop abaixo agora é RÁPIDO porque as promoções já foram pré-carregadas
    agora = timezone.now()
    for p in produtos:
        # Acessar p.promocoes.all() é rápido aqui
        p.tem_promocao = any(
            promo.esta_vigente() for promo in p.promocoes.all()
        )

    # 💡 Otimização Adicional: Use .only() para Banners/Mensagens, carregando apenas campos essenciais
    mensagens_topo = MensagemTopo.objects.filter(ativo=True).only('texto', 'ordem')
    banners = Banner.objects.filter(ativo=True).only('titulo', 'imagem', 'imagem_mobile', 'link', 'link_mobile')


    return render(request, 'produtos/home.html', {
        'produtos': produtos,
        'query': query,
        'titulo': 'Doce & Bella E-commerce',
        # envia os dados para o template:
        'mensagens_topo': mensagens_topo,
        'banners': banners,
    })

# --------------------------------------------------------------------------------------
# 🎯 OTIMIZAÇÃO 1: Listar por Categoria (N+1 Resolvido + Cache)
# --------------------------------------------------------------------------------------
@cache_page(600) # Cacheia a página de categoria por 10 minutos
def listar_por_categoria(request, categoria_slug):
    # select_related para a categoria é RÁPIDO porque só há uma
    categoria = get_object_or_404(Categoria, slug=categoria_slug)
    
    # 🛑 OTIMIZAÇÃO CRÍTICA AQUI: Adicionar prefetch_related para resolver N+1
    produtos_list = Produto.objects.filter(
        categoria=categoria, 
        disponivel=True
    ).prefetch_related('promocoes', 'variacoes').order_by('-id')

    # Mantendo a paginação para listas grandes
    paginator = Paginator(produtos_list, 20) # 20 itens por página é um bom padrão
    page = request.GET.get('page')
    produtos = paginator.get_page(page)

    # O loop de promoção também é rápido agora
    agora = timezone.now()
    for p in produtos:
        p.tem_promocao = any(
            promo.esta_vigente() for promo in p.promocoes.all()
        )
    
    return render(request, 'produtos/listar_categoria.html', {
        'categoria': categoria,
        'produtos': produtos,
        'titulo': f'{categoria.nome} | Doce & Bella'
    })


# --------------------------------------------------------------------------------------
# 🎯 OTIMIZAÇÃO 2: Detalhe do Produto (N+1 Resolvido + Cache)
# --------------------------------------------------------------------------------------
@cache_page(300) # Cacheia a página de detalhes por 5 minutos
def detalhe_produto(request, slug):
    # 🛑 OTIMIZAÇÃO PRINCIPAL: select_related para Categoria e prefetch_related para Variações e Promoções
    produto = get_object_or_404(
        Produto.objects.select_related('categoria').prefetch_related('variacoes', 'promocoes', 'galeria_imagens'), 
        slug=slug, 
        disponivel=True
    )

    # O código abaixo é RÁPIDO porque as variações, promoções e galeria já foram carregadas
    
    # 1. ESTOQUE TOTAL E VARIAÇÕES
    variacoes = produto.variacoes.all() # RÁPIDO!
    
    if produto.usa_variacoes:
        estoque_total = sum(v.estoque for v in variacoes)
    else:
        estoque_total = produto.estoque

    cores = sorted(set(v.cor for v in variacoes if v.cor))
    tamanhos = sorted(set(v.tamanho for v in variacoes if v.tamanho))
    outros = sorted(set(v.outro for v in variacoes if v.outro))

    # 2. MONTA O JSON DE VARIAÇÕES (RÁPIDO)
    variacoes_json = json.dumps([
        {
            "id": v.id,
            "cor": v.cor or "",
            "tamanho": v.tamanho or "",
            "outro": v.outro or "",
            "estoque": v.estoque,
            "imagem": v.get_imagem_url(),
        }
        for v in variacoes
    ], cls=DjangoJSONEncoder)

    # 3. CÁLCULO DE PARCELAMENTO (Lógica Python)
    # OBS: Recomenda-se usar p.get_preco_final, que deve estar otimizado com @cached_property na Model.
    preco = produto.get_preco_final or Decimal('0') # Se usar @cached_property, é acessado como atributo
    valor_final = preco / Decimal('0.8872')
    valor_parcela = valor_final / Decimal('3')

    # 4. PROMOÇÃO ATIVA (RÁPIDO)
    promo_ativa = None
    for promo in produto.promocoes.all(): # RÁPIDO!
        if promo.esta_vigente():
            promo_ativa = promo
            break

    # 5. PRODUTOS RELACIONADOS (OTIMIZADOS)
    # Adicionando prefetch_related para carregar promoções e variações dos relacionados também.
    produtos_relacionados = Produto.objects.filter(
        categoria=produto.categoria,
        disponivel=True,
        # Filtro de estoque removido aqui se o filtro de produtos_list (acima) já é suficiente, 
        # mas mantido para garantir só relacionados disponíveis.
        Q(estoque__gt=0) | Exists(
             Variacao.objects.filter(produto=OuterRef('pk'), estoque__gt=0)
        )
    ).exclude(
        id=produto.id
    ).order_by('?')[:4].prefetch_related('promocoes', 'variacoes') # <-- OTIMIZAÇÃO

    # Contexto
    context = {
        'produto': produto,
        'cores': cores,
        'tamanhos': tamanhos,
        'outros': outros,
        'variacoes': variacoes,
        'produtos_relacionados': produtos_relacionados,
        'valor_parcela': valor_parcela,
        'promo_ativa': promo_ativa,
        'variacoes_json': variacoes_json,
        'estoque_total': estoque_total,
        'galeria_imagens': produto.galeria_imagens.all(), # RÁPIDO!
        'titulo': f'{produto.nome} | Doce & Bella',
    }

    return render(request, 'produtos/detalhe_produto.html', context)



