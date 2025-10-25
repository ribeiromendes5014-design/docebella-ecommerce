# G:\projeto\carrinho\views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, F
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

from produtos.models import Produto, Variacao
from pedidos.models import Cupom  # ✅ usa o modelo do admin (pedidos)
from .models import ItemCarrinho  # mantém apenas o ItemCarrinho



# ---------------------- FUNÇÃO AUXILIAR ----------------------
def _get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


# ---------------------- ADICIONAR AO CARRINHO ----------------------
@require_POST
def adicionar_ao_carrinho(request, produto_slug):
    produto = get_object_or_404(Produto, slug=produto_slug)
    session_key = _get_session_key(request)

    variacao_id = request.POST.get('variacao_id')
    quantidade = int(request.POST.get('quantidade', 1))

    variacao = None
    estoque_disponivel = produto.estoque  # estoque padrão (sem variação)

    # --- Se o produto tiver variações ---
    if produto.usa_variacoes:
        if not variacao_id:
            messages.error(request, "Selecione uma variação antes de adicionar ao carrinho.")
            return redirect('detalhe_produto', slug=produto_slug)

        try:
            variacao = Variacao.objects.get(id=variacao_id, produto=produto)
            estoque_disponivel = variacao.estoque
        except Variacao.DoesNotExist:
            messages.error(request, 'Variação inválida ou não encontrada.')
            return redirect('detalhe_produto', slug=produto_slug)

    # --- Validações de estoque ---
    if estoque_disponivel <= 0:
        messages.error(request, "Produto esgotado.")
        return redirect('detalhe_produto', slug=produto_slug)

    if quantidade <= 0:
        messages.error(request, "A quantidade deve ser maior que zero.")
        return redirect('detalhe_produto', slug=produto_slug)

    # 🔒 Impede adicionar acima do estoque
    if quantidade > estoque_disponivel:
        messages.error(
            request,
            f"Quantidade solicitada ({quantidade}) excede o estoque disponível ({estoque_disponivel})."
        )
        return redirect('detalhe_produto', slug=produto_slug)

    # 💰 Define o preço correto (promocional ou normal)
    preco_base = produto.get_preco_final()
    preco_unitario = preco_base
    if variacao:
        preco_unitario += variacao.preco_adicional or 0

    # --- Buscar item existente no carrinho ---
    item_query = ItemCarrinho.objects.filter(
        session_key=session_key,
        produto=produto,
        variacao=variacao
    )

    if item_query.exists():
        item = item_query.first()
        nova_quantidade = item.quantidade + quantidade

        # 🔒 Travar se exceder estoque
        if nova_quantidade > estoque_disponivel:
            messages.error(
                request,
                f"Estoque insuficiente! Você já possui {item.quantidade} no carrinho. "
                f"Máximo permitido: {estoque_disponivel}."
            )
            return redirect('detalhe_produto', slug=produto_slug)

        item.quantidade = nova_quantidade
        item.preco = preco_unitario  # 🔄 Atualiza preço se produto entrou em promoção
        item.save()
        messages.success(request, f"Quantidade de {produto.nome} atualizada no carrinho.")
    else:
        ItemCarrinho.objects.create(
            session_key=session_key,
            produto=produto,
            variacao=variacao,
            quantidade=quantidade,
            preco=preco_unitario  # ✅ Salva o preço certo no momento da adição
        )
        messages.success(request, f"{produto.nome} adicionado ao carrinho!")

    return redirect('carrinho:ver_carrinho')


# ---------------------- VER CARRINHO ----------------------
def ver_carrinho(request):
    session_key = _get_session_key(request)
    itens_carrinho = ItemCarrinho.objects.filter(session_key=session_key)

    # 💰 Calcula subtotal e quantidade total
    carrinho_data = itens_carrinho.aggregate(
        subtotal=Sum(F('quantidade') * F('preco')),
        total_itens=Sum('quantidade')
    )

    subtotal = carrinho_data.get('subtotal') or Decimal('0.00')
    total_itens = carrinho_data.get('total_itens') or 0

    # 🧾 Lê valores salvos na sessão (cupom e desconto)
    desconto = Decimal(str(request.session.get('desconto_valor', 0.00)))
    cupom_codigo = request.session.get('cupom_codigo', '')
    total_com_desconto = subtotal - desconto

    if total_com_desconto < 0:
        total_com_desconto = Decimal('0.00')

    context = {
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': subtotal,
        'total_itens': total_itens,
        'desconto': desconto,
        'total_com_desconto': total_com_desconto,
        'cupom_codigo': cupom_codigo,
        'titulo': "Seu Carrinho de Compras"
    }

    return render(request, 'carrinho/carrinho.html', context)



# ---------------------- ATUALIZAR QUANTIDADE ----------------------
@require_POST
def atualizar_carrinho(request):
    item_id = request.POST.get('item_id')
    nova_quantidade = int(request.POST.get('quantidade', 0))
    session_key = _get_session_key(request)

    item = get_object_or_404(ItemCarrinho, id=item_id, session_key=session_key)

    if nova_quantidade > 0:
        estoque_disponivel = item.variacao.estoque if item.variacao else item.produto.estoque

        if nova_quantidade <= estoque_disponivel:
            item.quantidade = nova_quantidade
            item.save()
            messages.success(request, f"Quantidade de {item.produto.nome} atualizada.")
        else:
            messages.error(request, f"Quantidade excede o estoque disponível ({estoque_disponivel}).")
    else:
        item.delete()
        messages.success(request, f"{item.produto.nome} removido do carrinho.")

    return redirect('carrinho:ver_carrinho')


# ---------------------- REMOVER ITEM ----------------------
def remover_item(request, item_id):
    item = get_object_or_404(ItemCarrinho, id=item_id, session_key=_get_session_key(request))
    item.delete()
    messages.success(request, f"{item.produto.nome} removido do carrinho.")
    return redirect('carrinho:ver_carrinho')


# ---------------------- CUPOM ----------------------
# ---------------------- CUPOM ----------------------
@require_POST
def aplicar_cupom(request):
    codigo_cupom = request.POST.get('cupom_codigo', '').strip()
    session_key = request.session.session_key

    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # Busca os itens do carrinho
    itens = ItemCarrinho.objects.filter(session_key=session_key)
    total = sum(item.get_subtotal() for item in itens)
    total_descontado = total

    if not codigo_cupom:
        messages.error(request, "Por favor, insira um código de cupom.")
        return redirect('carrinho:ver_carrinho')

    try:
        cupom = Cupom.objects.get(codigo__iexact=codigo_cupom)
        agora = timezone.now()

        # Verifica validade
        if not cupom.ativo:
            messages.error(request, "Este cupom está inativo.")
        elif cupom.data_fim and cupom.data_fim < agora:
            messages.error(request, "Este cupom expirou.")
        else:
            # Calcula o desconto
            desconto = Decimal('0.00')
            if hasattr(cupom, 'desconto_percentual') and cupom.desconto_percentual:
                desconto = total * (cupom.desconto_percentual / Decimal('100'))
            elif hasattr(cupom, 'desconto_fixo') and cupom.desconto_fixo:
                desconto = cupom.desconto_fixo
            elif hasattr(cupom, 'valor_desconto') and cupom.valor_desconto:
                desconto = cupom.valor_desconto

            total_descontado = total - desconto
            if total_descontado < 0:
                total_descontado = Decimal('0.00')

            # Guarda os dados na sessão
            request.session['cupom_codigo'] = cupom.codigo
            request.session['desconto_valor'] = float(desconto)
            request.session['total_com_desconto'] = float(total_descontado)

            messages.success(
                request,
                f"Cupom '{cupom.codigo}' aplicado com sucesso! Desconto de R$ {desconto:.2f}."
            )

    except Cupom.DoesNotExist:
        messages.error(request, "Cupom inválido.")

    return redirect('carrinho:ver_carrinho')



