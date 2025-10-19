from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from carrinho.models import ItemCarrinho
from pedidos.frete_service import calcular_frete_simulado, calcular_peso_carrinho
from .models import EnderecoEntrega, Pedido, ItemPedido
from django.db import transaction
from django import forms
from carrinho.views import _get_session_key
from produtos.models import Produto, Variacao 
from django.contrib import messages


# Formulário de Endereço Básico (para o MVP)
class EnderecoForm(forms.Form):
    nome = forms.CharField(max_length=255, label='Nome')
    sobrenome = forms.CharField(max_length=255, label='Sobrenome')
    email = forms.EmailField(label='E-mail')
    cep = forms.CharField(max_length=9, label='CEP')
    rua = forms.CharField(max_length=255, label='Rua/Avenida')
    numero = forms.CharField(max_length=10, label='Número')
    complemento = forms.CharField(max_length=255, required=False, label='Complemento')
    bairro = forms.CharField(max_length=100, label='Bairro')
    cidade = forms.CharField(max_length=100, label='Cidade')
    estado = forms.CharField(max_length=2, label='Estado (UF)')


# View Principal do Checkout
@login_required
def checkout(request):
    session_key = _get_session_key(request)
    itens_carrinho = ItemCarrinho.objects.filter(session_key=session_key)

    if not itens_carrinho.exists():
        messages.warning(request, "Seu carrinho está vazio.")
        return redirect('carrinho:ver_carrinho')
        
    subtotal_carrinho = sum(item.get_subtotal() for item in itens_carrinho)
    peso_total = calcular_peso_carrinho(itens_carrinho)
    frete_opcoes = {} 

    form = EnderecoForm(request.POST or None)

    if request.method == 'POST':
        
        acao = request.POST.get('acao', 'finalizar_pedido')

        if form.is_valid():
            cep_destino = form.cleaned_data.get('cep')
            frete_opcoes = calcular_frete_simulado(cep_destino, peso_total, subtotal_carrinho)

        if acao == 'calcular_frete':
            if form.is_valid():
                messages.success(request, "Frete calculado! Selecione a opção e finalize o pedido.")
            else:
                messages.error(request, "Corrija os erros do endereço antes de calcular o frete.")

        elif acao == 'finalizar_pedido':
            
            if form.is_valid():
                metodo_frete_selecionado = request.POST.get('metodo_frete')
                
                if not metodo_frete_selecionado and len(frete_opcoes) == 1:
                    metodo_frete_selecionado = list(frete_opcoes.keys())[0]

                if not metodo_frete_selecionado or metodo_frete_selecionado not in frete_opcoes:
                    messages.error(request, "Selecione um método de envio válido para finalizar.")
                else:
                    valor_frete = frete_opcoes[metodo_frete_selecionado]['valor']
                    valor_total_final = subtotal_carrinho + valor_frete

                    try:
                        with transaction.atomic():
                            endereco = EnderecoEntrega.objects.create(**form.cleaned_data)
                            
                            pedido = Pedido.objects.create(
                                cliente=request.user,
                                endereco=endereco,
                                valor_total=valor_total_final,
                                valor_frete=valor_frete,
                                metodo_envio=metodo_frete_selecionado # Adicionado: Salvar o método de envio
                            )
                            
                            for item_carrinho in itens_carrinho:
                                
                                target = item_carrinho.variacao or item_carrinho.produto
                                
                                if not target:
                                    raise Exception(f"Item do carrinho inválido: Produto ou Variação não encontrados.")
                                    
                                if target.estoque < item_carrinho.quantidade:
                                    raise Exception(f"Estoque insuficiente para {item_carrinho.produto.nome}.")
                                    
                                ItemPedido.objects.create(
                                    pedido=pedido,
                                    produto=item_carrinho.produto,
                                    variacao=item_carrinho.variacao,
                                    preco_unitario=item_carrinho.get_preco_unitario(),
                                    quantidade=item_carrinho.quantidade
                                )
                                target.estoque -= item_carrinho.quantidade
                                target.save()
                                
                            itens_carrinho.delete()
                            messages.success(request, f"Pedido #{pedido.id} criado. Prossiga para o pagamento.")
                            return redirect('pedidos:detalhe_pedido', pedido_id=pedido.id)
                            
                    except Exception as e:
                        messages.error(request, f"Ocorreu um erro ao finalizar o pedido. Motivo: {e}")
                        return redirect('carrinho:ver_carrinho')
            
            elif not form.is_valid():
                messages.error(request, "Corrija os erros do endereço para finalizar o pedido.")
        
    else:
        # GET Request: Inicializa o form com dados do usuário logado (assumindo que você tem 'nome_completo')
        initial_data = {}
        if hasattr(request.user, 'nome_completo'):
            initial_data['nome'] = request.user.nome_completo.split(' ')[0] if request.user.nome_completo else ''
            initial_data['sobrenome'] = ' '.join(request.user.nome_completo.split(' ')[1:]) if request.user.nome_completo and len(request.user.nome_completo.split(' ')) > 1 else ''
        if hasattr(request.user, 'email'):
            initial_data['email'] = request.user.email
            
        form = EnderecoForm(initial=initial_data)


    context = {
        'form': form,
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': subtotal_carrinho,
        'frete_opcoes': frete_opcoes,
        'titulo': "Checkout - Endereço e Frete"
    }
    return render(request, 'pedidos/checkout.html', context)


# -------------------------------------------------------------
## NOVO: Detalhe do Pedido (Adicionado para corrigir o Erro 500)
# -------------------------------------------------------------

@login_required 
def detalhe_pedido(request, pedido_id):
    """
    Exibe os detalhes de um pedido específico.
    """
    # Tenta buscar o pedido. Se não existir (404) ou se não pertencer ao usuário logado, retorna 404.
    pedido = get_object_or_404(
        Pedido, 
        id=pedido_id, 
        cliente=request.user
    )
    
    # Os itens do pedido serão acessados via relação reversa: pedido.itens.all()
    
    context = {
        'titulo': f'Detalhes do Pedido #{pedido.id}',
        'pedido': pedido,
    }
    
    return render(request, 'pedidos/detalhe_pedido.html', context)


# -------------------------------------------------------------
## Lista de Pedidos
# -------------------------------------------------------------

@login_required 
def lista_pedidos(request):
    """
    Exibe uma lista de todos os pedidos feitos pelo usuário logado.
    """
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-data_criacao')
    
    context = {
        'titulo': 'Meus Pedidos',
        'pedidos': pedidos,
    }
    
    return render(request, 'pedidos/lista_pedidos.html', context)
