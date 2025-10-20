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
    estoque_disponivel = produto.estoque # Assume estoque do produto pai por padrão
    
    # --- 1.1. Lógica de Variação (Validação e Busca) ---
    if produto.usa_variacoes:
        if not variacao_id:
            messages.error(request, "Selecione uma opção de produto (variação).")
            # O nome da view é 'detalhe_produto' sem namespace, o redirect está correto.
            return redirect('detalhe_produto', slug=produto_slug)
        
        try:
            # Busca a variação única (a combinação) pelo ID
            variacao = Variacao.objects.get(id=variacao_id, produto=produto)
            # 🚨 CRÍTICO: Usa o estoque da variação, não do produto pai.
            estoque_disponivel = variacao.estoque 
            
        except Variacao.DoesNotExist:
            messages.error(request, 'Variação selecionada é inválida.')
            return redirect('detalhe_produto', slug=produto_slug)
    
    # --- 2. Verificação de Estoque FINAL (Antes de Adicionar/Atualizar) ---
    
    # Valida se a quantidade é válida
    if quantidade <= 0:
        messages.error(request, "A quantidade deve ser maior que zero.")
        return redirect('detalhe_produto', slug=produto_slug)
    
    # Valida se o item está em estoque (para o caso de ser o primeiro item)
    if estoque_disponivel <= 0:
        messages.error(request, "Produto esgotado.")
        return redirect('detalhe_produto', slug=produto_slug)


    # 3. Adicionar/Atualizar Item no Carrinho
    
    # Tenta encontrar o item existente (usa a variação como parte da chave de busca)
    item_query = ItemCarrinho.objects.filter(
        session_key=session_key,
        produto=produto,
        variacao=variacao # Se variacao for None, busca itens sem variação
    )
    
    if item_query.exists():
        item = item_query.first()
        # Se o item já existe, apenas incrementa a quantidade
        nova_quantidade = item.quantidade + quantidade
        
        # 🚨 CORREÇÃO DE ESTOQUE: Aqui você estava usando estoque_disponivel, mas se a
        # variação for nula, precisa usar o estoque do produto. A lógica acima já resolveu isso.
        if nova_quantidade > estoque_disponivel:
              messages.error(request, f"Estoque insuficiente! Máximo disponível: {estoque_disponivel}.")
              return redirect('detalhe_produto', slug=produto_slug)
        
        item.quantidade = nova_quantidade
        item.save()
        criado = False # Marca como não criado para a mensagem de sucesso
        
    else:
        # Se não existe, cria um novo item
        ItemCarrinho.objects.create(
            session_key=session_key,
            produto=produto,
            variacao=variacao,
            quantidade=quantidade
        )
        criado = True # Marca como criado para a mensagem de sucesso

    messages.success(request, f"{produto.nome} adicionado ao carrinho!")
    # É melhor redirecionar para a página do carrinho após adicionar o item
    return redirect('carrinho:ver_carrinho')


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
