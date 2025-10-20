from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from carrinho.models import ItemCarrinho
# from pedidos.frete_service import calcular_frete_simulado, calcular_peso_carrinho # Não precisamos mais disso
from .models import EnderecoEntrega, Pedido, ItemPedido
from django.db import transaction
from django import forms
from carrinho.views import _get_session_key
from produtos.models import Produto, Variacao 
from django.contrib import messages


# NOVO FORMULÁRIO SIMPLIFICADO PARA RETIRADA
class CheckoutFormSimplificado(forms.Form):
    
    # CAMPO 1: NOME (Obrigatório)
    nome = forms.CharField(max_length=255, label='Nome Completo')
    
    # O CAMPO E-MAIL FOI REMOVIDO CONFORME SUA SOLICITAÇÃO.
    
    # CAMPO 2: TELEFONE (Para contato)
    telefone = forms.CharField(
        max_length=20, 
        label='Telefone (WhatsApp)', 
        help_text="Para entrarmos em contato sobre seu pedido."
    )

    # Sobrescreve o __init__ para preencher os dados do usuário logado
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CheckoutFormSimplificado, self).__init__(*args, **kwargs)
        
        # Pré-preenche o campo 'nome' com o nome do usuário logado
        if user and user.is_authenticated:
            self.fields['nome'].initial = user.nome_completo


# View Principal do Checkout (MODIFICADA)
@login_required
def checkout(request):
    session_key = _get_session_key(request)
    itens_carrinho = ItemCarrinho.objects.filter(session_key=session_key)

    if not itens_carrinho.exists():
        messages.warning(request, "Seu carrinho está vazio.")
        return redirect('carrinho:ver_carrinho')
        
    subtotal_carrinho = sum(item.get_subtotal() for item in itens_carrinho)

    if request.method == 'POST':
        # Usamos o novo formulário
        form = CheckoutFormSimplificado(request.POST, user=request.user)
        
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            try:
                with transaction.atomic():
                    
                    # 1. Crie o Endereço Falso (Dummy)
                    endereco_retirada = EnderecoEntrega.objects.create(
                        nome=cleaned_data['nome'],
                        sobrenome="",
                        email=request.user.email,
                        cep="00000-000",
                        rua="Retirada na Loja",
                        numero="S/N",
                        complemento=f"Telefone: {cleaned_data['telefone']}",
                        bairro="Loja",
                        cidade="Doce&Bella",
                        estado="PR"
                    )
                    
                    # 2. Crie o Pedido
                    pedido = Pedido.objects.create(
                        cliente=request.user,
                        endereco=endereco_retirada,
                        valor_total=subtotal_carrinho,
                        valor_frete=0.00,
                        metodo_envio="Retirada na Loja"
                    )
                    
                    # 3. Mova os itens do carrinho e atualize o estoque
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
                    messages.success(request, f"Pedido #{pedido.id} criado com sucesso! Aguardando pagamento.")
                    
                    return redirect('pedidos:detalhe_pedido', pedido_id=pedido.id)
                
            except Exception as e:
                # 🚨 ESTE BLOCO ESTAVA MAL INDENTADO 🚨
                print("\n=======================================================")
                print("FALHA NA CRIAÇÃO DO PEDIDO (EXCEPTION DISPARADA):")
                print("MOTIVO:", e)
                print("=======================================================\n")
                
                messages.error(request, f"Ocorreu um erro ao finalizar o pedido. Motivo: {e}")
                return redirect('carrinho:ver_carrinho')
        
        else:
            # 🚨 ESTE BLOCO ESTAVA MAL INDENTADO 🚨
            # Se o formulário for inválido, recarrega a página mostrando os erros
            print("\n=======================================================")
            print("ERRO DE VALIDAÇÃO DO FORMULÁRIO (IS_VALID() = False):")
            print(form.errors)
            print("=======================================================\n")
            
            messages.error(request, "Por favor, corrija os erros no formulário.")

    else:
        # GET Request: Inicializa o form simplificado passando o usuário
        form = CheckoutFormSimplificado(user=request.user)

    context = {
        'form': form,
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': subtotal_carrinho,
        'frete_opcoes': {},
        'titulo': "Checkout - Finalizar Pedido"
    }
    return render(request, 'pedidos/checkout.html', context)


# -------------------------------------------------------------
## Detalhe do Pedido (MANTIDO)
# -------------------------------------------------------------

@login_required 
def detalhe_pedido(request, pedido_id):
    pedido = get_object_or_404(
        Pedido, 
        id=pedido_id, 
        cliente=request.user
    )
    
    context = {
        'titulo': f'Detalhes do Pedido #{pedido.id}',
        'pedido': pedido,
    }
    
    # 🚨 CORREÇÃO CRÍTICA 2: Renderizar o template 'pedidos/detalhe_pedido.html'
    return render(request, 'pedidos/detalhe_pedido.html', context)


# -------------------------------------------------------------
## Lista de Pedidos (MANTIDO)
# -------------------------------------------------------------

@login_required 
def lista_pedidos(request):
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-data_criacao')
    
    context = {
        'titulo': 'Meus Pedidos',
        'pedidos': pedidos,
    }
    
    # 🚨 CORREÇÃO CRÍTICA 3: Renderizar o template 'pedidos/lista_pedidos.html'
    return render(request, 'pedidos/lista_pedidos.html', context)