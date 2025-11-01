# G:\projeto\carrinho\views.py

from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, F
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from produtos.models import Produto, Variacao
from pedidos.models import Cupom  
from .models import ItemCarrinho  
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse



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


# ---------------------- ATUALIZAR CARRINHO ----------------------
@require_POST
def atualizar_carrinho(request):
    """Atualiza a quantidade de um item no carrinho"""
    session_key = _get_session_key(request)
    item_id = request.POST.get('item_id')
    nova_quantidade = int(request.POST.get('quantidade', 1))

    item = get_object_or_404(ItemCarrinho, id=item_id, session_key=session_key)

    if nova_quantidade <= 0:
        item.delete()
        messages.success(request, f"{item.produto.nome} foi removido do carrinho.")
    else:
        item.quantidade = nova_quantidade
        item.save()
        messages.success(request, f"Quantidade de {item.produto.nome} atualizada com sucesso.")

    return redirect('carrinho:ver_carrinho')



# ---------------------- REMOVER ITEM DO CARRINHO ----------------------
@require_POST
def remover_item(request, item_id):
    """Remove um item específico do carrinho"""
    session_key = _get_session_key(request)
    item = get_object_or_404(ItemCarrinho, id=item_id, session_key=session_key)
    item.delete()
    messages.success(request, "Item removido do carrinho.")
    return redirect('carrinho:ver_carrinho')


# ---------------------- ATUALIZAR QUANTIDADE ----------------------
@require_POST
def aplicar_cupom(request):
    """Aplica um cupom de desconto e salva na sessão do usuário"""
    codigo_cupom = request.POST.get('cupom_codigo', '').strip()
    session_key = _get_session_key(request)

    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    itens = ItemCarrinho.objects.filter(session_key=session_key)
    total = sum(item.get_subtotal() for item in itens)

    if not codigo_cupom:
        messages.error(request, "Por favor, insira um código de cupom.")
        return redirect('carrinho:ver_carrinho')

    try:
        cupom = Cupom.objects.get(codigo__iexact=codigo_cupom)
        agora = timezone.now()

        # 🚫 Validações
        if not cupom.ativo:
            messages.error(request, "Este cupom está inativo.")
            return redirect('carrinho:ver_carrinho')

        if cupom.data_fim and cupom.data_fim < agora:
            messages.error(request, "Este cupom expirou.")
            return redirect('carrinho:ver_carrinho')

        # 💰 Calcula o desconto
        desconto = Decimal('0.00')

        if getattr(cupom, 'desconto_percentual', None):
            percentual = Decimal(str(cupom.desconto_percentual))
            desconto = (total * percentual / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif getattr(cupom, 'desconto_fixo', None):
            desconto = Decimal(str(cupom.desconto_fixo))
        elif getattr(cupom, 'valor_desconto', None):
            desconto = Decimal(str(cupom.valor_desconto))

        # 🔒 Garante que o desconto não ultrapasse o total
        if desconto > total:
            desconto = total

        total_descontado = (total - desconto).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # ✅ SALVA NA SESSÃO (com valores limpos)
        request.session['cupom_codigo'] = str(cupom.codigo)
        request.session['desconto_valor'] = str(desconto)
        request.session['total_com_desconto'] = str(total_descontado)
        request.session.modified = True

        print("=== CUPOM SALVO NA SESSÃO ===")
        print("cupom_codigo:", request.session.get('cupom_codigo'))
        print("desconto_valor:", request.session.get('desconto_valor'))
        print("total_com_desconto:", request.session.get('total_com_desconto'))
        print("==============================")

        messages.success(
            request,
            f"Cupom '{cupom.codigo}' aplicado com sucesso! Desconto de R$ {desconto:.2f}."
        )

    except Cupom.DoesNotExist:
        messages.error(request, "Cupom inválido.")

    return redirect('carrinho:ver_carrinho')

# ---------------------- ADICIONAR AO CARRINHO (AJAX) ----------------------
@require_POST
@csrf_exempt
def adicionar_ao_carrinho_ajax(request):
    produto_slug = request.POST.get('produto_slug')
    produto = get_object_or_404(Produto, slug=produto_slug)
    session_key = _get_session_key(request)

    variacao_id = request.POST.get('variacao_id')
    quantidade = int(request.POST.get('quantidade', 1))

    variacao = None
    estoque_disponivel = produto.estoque

    if produto.usa_variacoes:
        if not variacao_id:
            return JsonResponse({'status': 'erro', 'mensagem': 'Selecione uma variação antes de adicionar.'})
        try:
            variacao = Variacao.objects.get(id=variacao_id, produto=produto)
            estoque_disponivel = variacao.estoque
        except Variacao.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': 'Variação inválida.'})

    if estoque_disponivel <= 0:
        return JsonResponse({'status': 'erro', 'mensagem': 'Produto esgotado.'})

    # Validação de estoque para a adição
    item_existente = ItemCarrinho.objects.filter(
        session_key=session_key,
        produto=produto,
        variacao=variacao
    ).first()
    
    quantidade_atual_no_carrinho = item_existente.quantidade if item_existente else 0
    nova_quantidade_total = quantidade_atual_no_carrinho + quantidade

    if nova_quantidade_total > estoque_disponivel:
        return JsonResponse({
            'status': 'erro', 
            'mensagem': f'Estoque insuficiente! Máximo permitido: {estoque_disponivel}.'
        })
    
    # 💰 Define o preço correto (promocional ou normal)
    preco_unitario = produto.get_preco_final()
    if variacao:
        preco_unitario += variacao.preco_adicional or 0

    item, criado = ItemCarrinho.objects.get_or_create(
        session_key=session_key,
        produto=produto,
        variacao=variacao,
        defaults={'quantidade': quantidade, 'preco': preco_unitario}
    )

    if not criado:
        item.quantidade = nova_quantidade_total
        item.preco = preco_unitario
        item.save()

    # 🚀 NOVO CÓDIGO: CALCULAR O NOVO TOTAL DE ITENS E RETORNAR 🚀
    total_itens = ItemCarrinho.objects.filter(session_key=session_key).aggregate(
        total=Sum('quantidade')
    )['total'] or 0

    return JsonResponse({
        'status': 'ok',
        'mensagem': f'{produto.nome} foi adicionado ao carrinho com sucesso!',
        'novo_total_itens': total_itens 
    })

# ---------------------- OBTER TOTAL DO CARRINHO (AJAX GLOBAL) ----------------------
def get_carrinho_total_ajax(request):
    """Retorna o número total de itens no carrinho da sessão atual."""
    
    session_key = request.session.session_key
    
    # Se não houver chave de sessão, garante que ela será criada se o Context Processor falhar
    if not request.session.session_key:
        request.session.create()
        session_key = request.session.session_key
        
    if not session_key:
        total_itens = 0
    else:
        # Usamos o F.objects.filter porque é mais eficiente
        total_itens = ItemCarrinho.objects.filter(session_key=session_key).aggregate(
            total=Sum('quantidade')
        )['total'] or 0
        
    return JsonResponse({
        'total_itens': total_itens
    })



