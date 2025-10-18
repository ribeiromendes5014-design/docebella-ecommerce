# pedidos/views.py - CORRIGIDO E COMPLETO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from carrinho.models import ItemCarrinho 
from pedidos.frete_service import calcular_frete_simulado, calcular_peso_carrinho
from .models import EnderecoEntrega, Pedido, ItemPedido 
from django.db import transaction
from django import forms
from carrinho.views import _get_session_key 
from produtos.models import Produto 
from django.contrib import messages
from produtos.models import Variacao # Importar Variacao para checagem de estoque


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
        # Corrigido para a URL correta do carrinho (assumindo 'carrinho:ver_carrinho')
        return redirect('carrinho:ver_carrinho') 
        
    subtotal_carrinho = sum(item.get_subtotal() for item in itens_carrinho)
    peso_total = calcular_peso_carrinho(itens_carrinho)
    frete_opcoes = {} 

    if request.method == 'POST':
        form = EnderecoForm(request.POST)
        cep_destino = request.POST.get('cep', '')

        # 1. Recalcular Frete (sempre que o formulário é enviado)
        if cep_destino:
            frete_opcoes = calcular_frete_simulado(cep_destino, peso_total, subtotal_carrinho)
        
        # 2. Se o formulário for válido (dados de endereço OK)
        if form.is_valid():
            metodo_frete_selecionado = request.POST.get('metodo_frete')
            
            # Recalcular frete aqui novamente se o POST não for a verificação inicial
            # Para o contexto, manter a lógica original:
            if not metodo_frete_selecionado or metodo_frete_selecionado not in frete_opcoes:
                messages.error(request, "Selecione um método de envio válido.")
            else:
                valor_frete = frete_opcoes[metodo_frete_selecionado]['valor']
                valor_total_final = subtotal_carrinho + valor_frete

                try:
                    with transaction.atomic():
                        # A. Salvar Endereço
                        endereco = EnderecoEntrega.objects.create(**form.cleaned_data)
                        
                        # B. Criar o Pedido
                        pedido = Pedido.objects.create(
                            cliente=request.user,
                            endereco=endereco,
                            valor_total=valor_total_final,
                            valor_frete=valor_frete,
                        )

                        # C. Mover Itens e Abater Estoque
                        for item_carrinho in itens_carrinho:
                            
                            # 🚨 CORREÇÃO CRÍTICA 1: Checa se o produto ou variação existe 🚨
                            if not item_carrinho.produto:
                                # Lança exceção para reverter a transação
                                raise Exception(f"Item no carrinho inválido: Produto deletado.")
                                
                            target = item_carrinho.variacao or item_carrinho.produto
                            
                            # 🚨 CORREÇÃO CRÍTICA 2: Checa se há estoque suficiente 🚨
                            if target.estoque < item_carrinho.quantidade:
                                # Lança exceção com mensagem específica
                                raise Exception(f"Estoque insuficiente para {item_carrinho.produto.nome}.")
                                
                            # Cria o item do pedido
                            ItemPedido.objects.create(
                                pedido=pedido,
                                produto=item_carrinho.produto,
                                variacao=item_carrinho.variacao,
                                preco_unitario=item_carrinho.get_preco_unitario(),
                                quantidade=item_carrinho.quantidade
                            )
                            
                            # Abater Estoque
                            target.estoque -= item_carrinho.quantidade
                            target.save()
                        
                        # D. Limpar o Carrinho
                        itens_carrinho.delete()
                        
                        messages.success(request, f"Pedido #{pedido.id} criado. Prossiga para o pagamento.")
                        return redirect('pedidos:detalhe_pedido', pedido_id=pedido.id) 

                except Exception as e:
                    # Captura o erro (incluindo o novo erro de estoque) e exibe mensagem amigável
                    messages.error(request, f"Ocorreu um erro ao finalizar o pedido. Motivo: {e}")
                    # Redireciona para o carrinho, permitindo que o usuário ajuste
                    return redirect('carrinho:ver_carrinho') 
        
    else:
        # GET Request: Inicializa o form com dados do usuário logado
        form = EnderecoForm(initial={'nome': request.user.first_name, 'email': request.user.email})

    context = {
        'form': form,
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': subtotal_carrinho,
        'frete_opcoes': frete_opcoes,
        'titulo': "Checkout - Endereço e Frete"
    }
    return render(request, 'pedidos/checkout.html', context)


# View de Detalhe do Pedido (Após finalização/Pagamento)
@login_required
def detalhe_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    
    if request.method == 'POST':
        # Simula a aprovação do pagamento
        pedido.status = 'Pagamento Aprovado'
        pedido.save()
        messages.success(request, f"Pagamento do Pedido #{pedido_id} APROVADO! Seu pedido será processado.")
        # ATENÇÃO: Verifique se 'painel_cliente' tem um namespace, ex: 'usuarios:painel_cliente'
        return redirect('painel_cliente') 
    
    context = {
        'pedido': pedido,
        'titulo': f'Pedido #{pedido_id} - Pagamento'
    }
    return render(request, 'pedidos/detalhe_pedido.html', context)


# ADICIONADA: View de Lista de Pedidos (Estava faltando e causou o erro!)
@login_required 
def lista_pedidos(request):
    """
    Exibe uma lista de todos os pedidos feitos pelo usuário logado.
    Esta função foi adicionada para resolver o AttributeError.
    """
    # 1. Busca os pedidos do cliente logado, ordenados do mais recente para o mais antigo.
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-data_criacao')
    
    context = {
        'titulo': 'Meus Pedidos',
        'pedidos': pedidos,
    }
    
    # 2. Renderiza o template 
    return render(request, 'pedidos/lista_pedidos.html', context)
