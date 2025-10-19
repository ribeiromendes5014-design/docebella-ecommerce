from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from carrinho.models import ItemCarrinho
# Mantenha o frete_service, mas garantimos que ele retorne a Retirada na Loja
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
        return redirect('carrinho:ver_carrinho')
        
    subtotal_carrinho = sum(item.get_subtotal() for item in itens_carrinho)
    peso_total = calcular_peso_carrinho(itens_carrinho)
    frete_opcoes = {} 

    form = EnderecoForm(request.POST or None) # Inicializa o form para GET ou POST

    # --- Lógica de Frete Inicial (para GET ou para re-renderização) ---
    cep_para_calculo = request.POST.get('cep')
    if not cep_para_calculo and request.user.is_authenticated and hasattr(request.user, 'endereco_padrao') and request.user.endereco_padrao:
        cep_para_calculo = request.user.endereco_padrao.cep
    if not cep_para_calculo:
        cep_para_calculo = '83370000'
        
    frete_opcoes = calcular_frete_simulado(cep_para_calculo, peso_total, subtotal_carrinho)
    # ------------------------------------------------------------------

    if request.method == 'POST':
        
        acao = request.POST.get('acao', 'finalizar_pedido') # Assume finalizar se a acao nao for definida (para evitar bugs)

        # 1. TRATAMENTO PARA CÁLCULO DE FRETE (Onde você estava travado)
        if acao == 'calcular_frete':
            # Se a intenção é apenas calcular, recalculamos e a view renderiza no final.
            if form.is_valid():
                 cep_destino = form.cleaned_data.get('cep')
                 frete_opcoes = calcular_frete_simulado(cep_destino, peso_total, subtotal_carrinho)
                 messages.success(request, "Frete calculado! Selecione a opção e finalize o pedido.")
            else:
                 messages.error(request, "Corrija os erros do endereço antes de calcular o frete.")

        # 2. TRATAMENTO PARA FINALIZAR O PEDIDO
        elif acao == 'finalizar_pedido':
            
            # Recalcula o frete novamente (se o cep mudou) antes da finalização
            if form.is_valid():
                 cep_destino = form.cleaned_data.get('cep')
                 frete_opcoes = calcular_frete_simulado(cep_destino, peso_total, subtotal_carrinho)
            
            # --- LÓGICA DE CRIAÇÃO DO PEDIDO (Se o formulário e o frete forem válidos) ---
            if form.is_valid():
                metodo_frete_selecionado = request.POST.get('metodo_frete')
                
                # ... (Lógica de autoseleção de frete) ...
                if not metodo_frete_selecionado and len(frete_opcoes) == 1:
                    metodo_frete_selecionado = list(frete_opcoes.keys())[0]

                # 🚨 Validação de Frete CRÍTICA (Onde você estava falhando)
                if not metodo_frete_selecionado or metodo_frete_selecionado not in frete_opcoes:
                    messages.error(request, "Selecione um método de envio válido para finalizar.")
                    # Cai no return render final
                else:
                    # TUDO OK, CRIA O PEDIDO!
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
                                # ... (outros campos do pedido)
                            )
                            # ... (mover itens e abater estoque) ...
                            for item_carrinho in itens_carrinho:
                                # ... (Lógica de estoque e criação ItemPedido) ...
                                target = item_carrinho.variacao or item_carrinho.produto
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
                            return redirect('pedidos:detalhe_pedido', pedido_id=pedido.id) # SUCESSO!
                            
                    except Exception as e:
                        messages.error(request, f"Ocorreu um erro ao finalizar o pedido. Motivo: {e}")
                        return redirect('carrinho:ver_carrinho')
            # --- FIM: LÓGICA DE CRIAÇÃO DO PEDIDO ---
        
    # --- RENDERIZAÇÃO FINAL (Para GET ou para qualquer POST que falhe ou apenas recalcule) ---
    else:
        # GET Request: Inicializa o form
        form = EnderecoForm(initial={'nome': request.user.nome_completo, 'email': request.user.email})

    context = {
        'form': form,
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': subtotal_carrinho,
        'frete_opcoes': frete_opcoes,
        'titulo': "Checkout - Endereço e Frete"
    }
    return render(request, 'pedidos/checkout.html', context)


# ADICIONADA: View de Lista de Pedidos
@login_required 
def lista_pedidos(request):
    """
    Exibe uma lista de todos os pedidos feitos pelo usuário logado.
    """
    # 1. Busca os pedidos do cliente logado, ordenados do mais recente para o mais antigo.
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-data_criacao')
    
    context = {
        'titulo': 'Meus Pedidos',
        'pedidos': pedidos,
    }
    
    # 2. Renderiza o template 
    return render(request, 'pedidos/lista_pedidos.html', context)
