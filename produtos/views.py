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

def home(request):
    query = request.GET.get('q', '')

    produtos_list = Produto.objects.filter(
        disponivel=True
    ).filter(
        Q(estoque__gt=0) | Exists(
            Variacao.objects.filter(produto=OuterRef('pk'), estoque__gt=0)
        )
    )

    if query:
        produtos_list = produtos_list.filter(nome__icontains=query)

    produtos_list = produtos_list.order_by('-id')
    paginator = Paginator(produtos_list, 12)
    page = request.GET.get('page')
    produtos = paginator.get_page(page)

    # 🔹 Novo: adiciona flag "tem_promocao" para destacar no template
    agora = timezone.now()
    for p in produtos:
        p.tem_promocao = any(
            promo.esta_vigente() for promo in p.promocoes.all()
        )

    # 🆕 Adicione estas duas linhas:
    mensagens_topo = MensagemTopo.objects.filter(ativo=True)
    banners = Banner.objects.filter(ativo=True)

    return render(request, 'produtos/home.html', {
        'produtos': produtos,
        'query': query,
        'titulo': 'Doce & Bella E-commerce',
        # 🆕 envia os dados para o template:
        'mensagens_topo': mensagens_topo,
        'banners': banners,
    })

def listar_por_categoria(request, categoria_slug):
    categoria = get_object_or_404(Categoria, slug=categoria_slug)
    produtos = Produto.objects.filter(categoria=categoria, disponivel=True).order_by('-id')
    
    return render(request, 'produtos/listar_categoria.html', {
        'categoria': categoria,
        'produtos': produtos,
        'titulo': f'{categoria.nome} | Doce & Bella'
    })


# NOVA VIEW: Detalhe do Produto (Com Produtos Relacionados)
def detalhe_produto(request, slug):
    # Busca o produto ou retorna 404
    produto = get_object_or_404(Produto, slug=slug, disponivel=True)

    # 🔹 Busca TODAS as variações ativas do produto
    variacoes = Variacao.objects.filter(produto=produto)

    # 🔹 Agrupar variações por cor (para não repetir cores iguais)
    variacoes_por_cor = defaultdict(list)
    for v in variacoes:
        if v.cor:  # evita None
            variacoes_por_cor[v.cor].append({
                "id": v.id,
                "tamanho": v.valor,
                "estoque": v.estoque,
                "imagem": v.imagem.url if v.imagem else (v.produto.imagem.url if v.produto.imagem else "")
            })

    # 🔹 Listas únicas de cores e tamanhos
    cores = sorted(set([v.cor for v in variacoes if v.cor]))
    tamanhos = sorted(set([v.valor for v in variacoes if v.valor]))

    # 🔹 Serializa os dados para o JS no template
    variacoes_json = [
        {
            "id": v.id,
            "cor": v.cor,
            "tamanho": v.valor,
            "estoque": v.estoque,
            "imagem": v.imagem.url if v.imagem else (v.produto.imagem.url if v.produto.imagem else "")
        }
        for v in variacoes
    ]

    # 🔹 Cálculo da simulação de parcelamento
    preco = produto.get_preco_final() or Decimal('0')
    valor_final = preco / Decimal('0.8872')
    valor_parcela = valor_final / Decimal('3')

    # 🔹 Promoção ativa (para o cronômetro)
    promo_ativa = None
    for promo in produto.promocoes.all():
        if promo.esta_vigente():
            promo_ativa = promo
            break

    # 🔹 Produtos relacionados
    produtos_relacionados = Produto.objects.filter(
        categoria=produto.categoria,
        disponivel=True,
        estoque__gt=0
    ).exclude(id=produto.id).order_by('?')[:4]

    # 🔹 Envia tudo ao template
    context = {
        "produto": produto,
        "cores": cores,
        "tamanhos": tamanhos,
        "variacoes_por_cor": dict(variacoes_por_cor),
        "variacoes_json": json.dumps(variacoes_json, ensure_ascii=False),
        "produtos_relacionados": produtos_relacionados,
        "valor_parcela": valor_parcela,
        "promo_ativa": promo_ativa,
        "titulo": f"{produto.nome} | Doce & Bella",
    }

    return render(request, "produtos/detalhe_produto.html", context)
