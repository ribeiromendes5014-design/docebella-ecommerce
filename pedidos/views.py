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
    frete_opcoes = {}  # Inicia vazio no GET

    form = EnderecoForm(request.POST or None)

    if request.method == 'POST':
        
        # Ação padrão é 'finalizar_pedido' se o botão não tiver 'name="acao"'
        acao = request.POST.get('acao', 'finalizar_pedido')

        if form.is_valid():
            cep_destino = form.cleaned_data.get('cep')
            # Sempre recalculamos o frete se o formulário for válido, 
            # independentemente da ação, para ter as opções no contexto.
            frete_opcoes = calcular_frete_simulado(cep_destino, peso_total, subtotal_carrinho)

        # 1. TRATAMENTO PARA CÁLCULO DE FRETE (Botão 1)
        if acao == 'calcular_frete':
            if form.is_valid():
                messages.success(request, "Frete calculado! Selecione a opção e finalize o pedido.")
            else:
                messages.error(request, "Corrija os erros do endereço antes de calcular o frete.")
            # O código continua para o return render final.

        # 2. TRATAMENTO PARA FINALIZAR O PEDIDO (Botão 2)
        elif acao == 'finalizar_pedido':
            
            if form.is_valid():
                metodo_frete_selecionado = request.POST.get('metodo_frete')
                
                # Tenta autoselecionar se só houver 1 opção
                if not metodo_frete_selecionado and len(frete_opcoes) == 1:
                    metodo_frete_selecionado = list(frete_opcoes.keys())[0]

                # Validação de Frete
                if not metodo_frete_selecionado or metodo_frete_selecionado not in frete_opcoes:
                    # Adiciona a mensagem e renderiza novamente com as opções calculadas
                    messages.error(request, "Selecione um método de envio válido para finalizar.")
                else:
                    # TUDO OK, CRIA O PEDIDO!
                    valor_frete = frete_opcoes[metodo_frete_selecionado]['valor']
                    valor_total_final = subtotal_carrinho + valor_frete

                    try:
                        with transaction.atomic():
                            # Cria o endereço
                            endereco = EnderecoEntrega.objects.create(**form.cleaned_data)
                            
                            # Cria o pedido
                            pedido = Pedido.objects.create(
                                cliente=request.user,
                                endereco=endereco,
                                valor_total=valor_total_final,
                                valor_frete=valor_frete,
                                # ... (outros campos do pedido)
                            )
                            
                            # Mover itens e abater estoque
                            for item_carrinho in itens_carrinho:
                                
                                # 🚨 CORREÇÃO DE SEGURANÇA AQUI 🚨
                                # Garante que 'target' seja um objeto de modelo válido
                                target = item_carrinho.variacao or item_carrinho.produto
                                
                                # Verifica se o target realmente existe antes de acessar o estoque
                                if not target:
                                    raise Exception(f"Item do carrinho inválido: Produto ou Variação não encontrados para o item de ID {item_carrinho.id}.")
                                    
                                # Verificação de Estoque
                                if target.estoque < item_carrinho.quantidade:
                                    raise Exception(f"Estoque insuficiente para {item_carrinho.produto.nome}.")
                                    
                                # Cria o item do pedido
                                ItemPedido.objects.create(
                                    pedido=pedido,
                                    produto=item_carrinho.produto,
                                    variacao=item_carrinho.variacao,
                                    preco_unitario=item_carrinho.get_preco_unitario(),
                                    quantidade=item_carrinho.quantidade
                                )
                                # Abate Estoque
                                target.estoque -= item_carrinho.quantidade
                                target.save()
                                
                            itens_carrinho.delete()
                            messages.success(request, f"Pedido #{pedido.id} criado. Prossiga para o pagamento.")
                            return redirect('pedidos:detalhe_pedido', pedido_id=pedido.id) # SUCESSO!
                            
                    except Exception as e:
                        # Este bloco captura erros de transação ou de lógica de estoque (como estoque insuficiente)
                        messages.error(request, f"Ocorreu um erro ao finalizar o pedido. Motivo: {e}")
                        # Após um erro grave, é mais seguro redirecionar para uma tela neutra
                        return redirect('carrinho:ver_carrinho')
            
            # Se o form não for válido no finalizar_pedido
            elif not form.is_valid():
                messages.error(request, "Corrija os erros do endereço para finalizar o pedido.")
            # --- FIM: LÓGICA DE CRIAÇÃO DO PEDIDO ---
        
    # --- RENDERIZAÇÃO FINAL ---
    else:
        # GET Request: Inicializa o form com dados do usuário logado
        form = EnderecoForm(initial={'nome': request.user.nome_completo, 'email': request.user.email})
        
        # 🚨 Removido: A lógica de frete para o GET inicial foi removida
        # para evitar cálculos desnecessários e dependências iniciais.
        # As opções de frete só aparecerão após o primeiro POST (calcular_frete).


    context = {
        'form': form,
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': subtotal_carrinho,
        'frete_opcoes': frete_opcoes, # Isso estará vazio no GET e preenchido após o POST
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
