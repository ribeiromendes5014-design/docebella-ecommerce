# G:\projeto\carrinho\views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
# Importações de agregação corrigidas:
from django.db.models import Sum, F, Value, DecimalField 
from django.db.models.functions import Coalesce # Importação crucial para tratar NULL
from django.contrib import messages 

from produtos.models import Produto, Variacao 
from .models import ItemCarrinho


# Função auxiliar para obter a chave de sessão (session_key)
def _get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

@require_POST
def adicionar_ao_carrinho(request, produto_slug):
    produto = get_object_or_404(Produto, slug=produto_slug)
    session_key = _get_session_key(request)
    
    # 1. Obter Variação e Quantidade
    variacao_id = request.POST.get('variacao_id')
    quantidade = int(request.POST.get('quantidade', 1))
    
    variacao = None
    if produto.usa_variacoes and variacao_id:
        variacao = get_object_or_404(Variacao, id=variacao_id, produto=produto)
    elif produto.usa_variacoes and not variacao_id:
        messages.error(request, "Selecione uma opção de produto (variação).")
        # Este redirect está correto sem namespace, pois o app 'produtos' não tem um
        return redirect('detalhe_produto', slug=produto_slug) 

    # 2. Verificação de Estoque (Simplificada)
    estoque_disponivel = variacao.estoque if variacao else produto.estoque
    
    if quantidade <= 0:
        messages.error(request, "A quantidade deve ser maior que zero.")
        return redirect('detalhe_produto', slug=produto_slug) 
    
    # 3. Adicionar/Atualizar Item no Carrinho
    item, criado = ItemCarrinho.objects.get_or_create(
        session_key=session_key,
        produto=produto,
        variacao=variacao, 
        defaults={'quantidade': quantidade}
    )
    
    if not criado:
        # Se o item já existe, apenas incrementa a quantidade
        nova_quantidade = item.quantidade + quantidade
        
        if nova_quantidade > estoque_disponivel:
             messages.error(request, f"Estoque insuficiente! Máximo: {estoque_disponivel}.")
             return redirect('detalhe_produto', slug=produto_slug) 
        
        item.quantidade = nova_quantidade
        item.save()

    messages.success(request, f"{item.produto.nome} adicionado ao carrinho!")
    return redirect('detalhe_produto', slug=produto_slug)


# View para listar e calcular o carrinho (Página Completa)
def ver_carrinho(request):
    session_key = _get_session_key(request)
    
    itens_carrinho = ItemCarrinho.objects.filter(session_key=session_key)
    
    # 🚨 CORREÇÃO CRUCIAL APLICADA AQUI: Tratar NULL como 0 para o cálculo
    carrinho_data = itens_carrinho.annotate(
        # Coalesce trata variacao__preco_adicional (que é NULL se não houver variação) como 0.00
        preco_unitario_final=F('produto__preco') + Coalesce(F('variacao__preco_adicional'), Value(0, output_field=DecimalField()))
    ).aggregate(
        subtotal=Sum(F('quantidade') * F('preco_unitario_final')),
        total_itens=Sum('quantidade')
    )
    
    context = {
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': carrinho_data.get('subtotal') or 0.00, 
        'total_itens': carrinho_data.get('total_itens') or 0,
        'titulo': "Seu Carrinho de Compras"
    }
    return render(request, 'carrinho/carrinho.html', context)


# >> VIEW ATUALIZAR QUANTIDADE <<
@require_POST
def atualizar_carrinho(request):
    item_id = request.POST.get('item_id')
    nova_quantidade = int(request.POST.get('quantidade', 0))
    session_key = _get_session_key(request)
    
    item = get_object_or_404(ItemCarrinho, id=item_id, session_key=session_key)
    
    if nova_quantidade > 0:
        # Lógica de estoque (simplificada)
        estoque_disponivel = item.variacao.estoque if item.variacao else item.produto.estoque
        
        if nova_quantidade <= estoque_disponivel:
            item.quantidade = nova_quantidade
            item.save()
            messages.success(request, f"Quantidade de {item.produto.nome} atualizada.")
        else:
            messages.error(request, f"Quantidade excede o estoque disponível: {estoque_disponivel}.")
    else:
        # Se a quantidade for 0, remove o item
        item.delete()
        messages.success(request, f"{item.produto.nome} removido do carrinho.")
        
    # <--- CORREÇÃO: Adicionado namespace 'carrinho:' ao redirect
    return redirect('carrinho:ver_carrinho') 


def remover_item(request, item_id):
    item = get_object_or_404(ItemCarrinho, id=item_id, session_key=_get_session_key(request))
    item.delete()
    messages.success(request, f"{item.produto.nome} removido do carrinho.")
    
    # <--- CORREÇÃO: Adicionado namespace 'carrinho:' ao redirect
    return redirect('carrinho:ver_carrinho')


# <--- CORREÇÃO: Adicionada a função 'aplicar_cupom' que estava faltando ---
@require_POST
def aplicar_cupom(request):
    if request.method == 'POST':
        codigo_cupom = request.POST.get('cupom_codigo')
        
        # ---
        # AQUI VAI A LÓGICA
        # 1. Verificar se o cupom existe e é válido
        # 2. Se for, aplicar o desconto (talvez salvando na sessão)
        # 3. Adicionar uma mensagem de sucesso ou erro com 'messages.success(...)'
        # ---
        
        # Por enquanto, apenas exibimos o código no console e adicionamos uma mensagem
        print(f"Usuário tentou aplicar o cupom: {codigo_cupom}")
        messages.info(request, f"Lógica para o cupom '{codigo_cupom}' ainda não implementada.")

    # Redireciona de volta para a página do carrinho
    return redirect('carrinho:ver_carrinho')