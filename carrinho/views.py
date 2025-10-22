# G:\projeto\carrinho\views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, F, Value, DecimalField 
from django.db.models.functions import Coalesce
from django.contrib import messages

from produtos.models import Produto, Variacao 
from .models import ItemCarrinho


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
        messages.error(request, f"Quantidade solicitada ({quantidade}) excede o estoque disponível ({estoque_disponivel}).")
        return redirect('detalhe_produto', slug=produto_slug)

    # 💰 Define o preço correto (promocional ou normal)
    preco_base = produto.preco_promocional or produto.preco
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
                f"Estoque insuficiente! Você já possui {item.quantidade} no carrinho. Máximo permitido: {estoque_disponivel}."
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

    # 💰 Agora o subtotal é calculado com base no campo preco do carrinho (fixo)
    carrinho_data = itens_carrinho.aggregate(
        subtotal=Sum(F('quantidade') * F('preco')),
        total_itens=Sum('quantidade')
    )

    context = {
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': carrinho_data.get('subtotal') or 0.00,
        'total_itens': carrinho_data.get('total_itens') or 0,
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
@require_POST
def aplicar_cupom(request):
    codigo_cupom = request.POST.get('cupom_codigo')
    print(f"Usuário tentou aplicar o cupom: {codigo_cupom}")
    messages.info(request, f"Lógica para o cupom '{codigo_cupom}' ainda não implementada.")
    return redirect('carrinho:ver_carrinho')
from django.db import models
from produtos.models import Produto, Variacao

class ItemCarrinho(models.Model):
    session_key = models.CharField(max_length=40)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    variacao = models.ForeignKey(Variacao, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ Adicione isto!
    adicionado_em = models.DateTimeField(auto_now_add=True)

    def subtotal(self):
        return self.quantidade * self.preco

    def __str__(self):
        return f"{self.produto.nome} ({self.quantidade}x)"
