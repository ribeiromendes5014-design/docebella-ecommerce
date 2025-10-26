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
    paginator = Paginator(produtos_list, 200)
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
    produto = get_object_or_404(Produto, slug=slug, disponivel=True)

    # Calcula o estoque total
    if produto.usa_variacoes:
        estoque_total = sum(v.estoque for v in produto.variacoes.all())
    else:
        estoque_total = produto.estoque

    # Separa variações
    variacoes = produto.variacoes.all()
    cores = sorted(set(v.cor for v in variacoes if v.cor))
    tamanhos = sorted(set(v.tamanho for v in variacoes if v.tamanho))
    outros = sorted(set(v.outro for v in variacoes if v.outro))  # opcional

    # Monta o JSON das variações
    from django.core.serializers.json import DjangoJSONEncoder
    import json
    variacoes_json = json.dumps([
        {
            "id": v.id,
            "cor": v.cor or "",
            "tamanho": v.tamanho or "",
            "outro": v.outro or "",
            "estoque": v.estoque,
            "imagem": v.get_imagem_url(),  # ✅ usa o método da model
        }
        for v in variacoes
    ], cls=DjangoJSONEncoder)

    # Cálculo de parcelamento
    from decimal import Decimal
    preco = produto.get_preco_final() or Decimal('0')
    valor_final = preco / Decimal('0.8872')
    valor_parcela = valor_final / Decimal('3')

    # Promoção ativa
    promo_ativa = None
    for promo in produto.promocoes.all():
        if promo.esta_vigente():
            promo_ativa = promo
            break

    # Produtos relacionados
    produtos_relacionados = Produto.objects.filter(
        categoria=produto.categoria,
        disponivel=True,
        estoque__gt=0
    ).exclude(
        id=produto.id
    ).order_by('?')[:4]

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
        'titulo': f'{produto.nome} | Doce & Bella',
    }

    return render(request, 'produtos/detalhe_produto.html', context)



