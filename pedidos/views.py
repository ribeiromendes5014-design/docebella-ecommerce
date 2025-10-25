from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from carrinho.models import ItemCarrinho
from .models import EnderecoEntrega, Pedido, ItemPedido
from django.db import transaction
from django import forms
from carrinho.views import _get_session_key
from produtos.models import Produto, Variacao 
from django.contrib import messages


# ---------------------- FORMULÁRIO ----------------------
class CheckoutFormSimplificado(forms.Form):
    nome = forms.CharField(max_length=255, label='Nome Completo')
    telefone = forms.CharField(
        max_length=20,
        label='Telefone (WhatsApp)',
        help_text="Para entrarmos em contato sobre seu pedido."
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CheckoutFormSimplificado, self).__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['nome'].initial = user.nome_completo


# ---------------------- CHECKOUT ----------------------
@login_required
def checkout(request):
    session_key = _get_session_key(request)
    itens_carrinho = ItemCarrinho.objects.filter(session_key=session_key)

    if not itens_carrinho.exists():
        messages.warning(request, "Seu carrinho está vazio.")
        return redirect('carrinho:ver_carrinho')

    # 💰 Garante que o subtotal use o preço salvo no carrinho
    subtotal_carrinho = sum(item.preco * item.quantidade for item in itens_carrinho)

    if request.method == 'POST':
        form = CheckoutFormSimplificado(request.POST, user=request.user)

        if form.is_valid():
            cleaned_data = form.cleaned_data

            try:
                with transaction.atomic():
                    # 1️⃣ Endereço fictício (retirada)
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

                    # 2️⃣ Cria o pedido
                    pedido = Pedido.objects.create(
                        cliente=request.user,
                        endereco=endereco_retirada,
                        valor_total=subtotal_carrinho,
                        valor_frete=0.00,
                        metodo_envio="Retirada na Loja"
                    )

                    # 3️⃣ Move os itens do carrinho
                    for item_carrinho in itens_carrinho:
                        target = item_carrinho.variacao or item_carrinho.produto

                        if not target:
                            raise Exception(f"Item inválido: Produto ou Variação não encontrados.")

                        if target.estoque < item_carrinho.quantidade:
                            raise Exception(f"Estoque insuficiente para {item_carrinho.produto.nome}.")

                        # ✅ Salva o preço exato que estava no carrinho
                        ItemPedido.objects.create(
                            pedido=pedido,
                            produto=item_carrinho.produto,
                            variacao=item_carrinho.variacao,
                            preco_unitario=item_carrinho.preco,
                            quantidade=item_carrinho.quantidade
                        )

                        # Atualiza o estoque
                        target.estoque -= item_carrinho.quantidade
                        target.save()

                    # Limpa o carrinho
                    itens_carrinho.delete()

                    messages.success(request, f"Pedido #{pedido.id} criado com sucesso! Aguardando pagamento.")
                    return redirect('pedidos:detalhe_pedido', pedido_id=pedido.id)

            except Exception as e:
                print("\n=== ERRO AO FINALIZAR PEDIDO ===")
                print("Motivo:", e)
                print("=================================\n")

                messages.error(request, f"Ocorreu um erro ao finalizar o pedido. Motivo: {e}")
                return redirect('carrinho:ver_carrinho')

        else:
            print("\n=== ERRO DE VALIDAÇÃO DO FORMULÁRIO ===")
            print(form.errors)
            print("======================================\n")
            messages.error(request, "Por favor, corrija os erros no formulário.")

    else:
        form = CheckoutFormSimplificado(user=request.user)

    context = {
        'form': form,
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': subtotal_carrinho,
        'frete_opcoes': {},
        'titulo': "Checkout - Finalizar Pedido"
    }
    return render(request, 'pedidos/checkout.html', context)


# ---------------------- CANCELAR PEDIDO ----------------------
@login_required
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)

    if pedido.status not in ["Pronto para Retirada", "Cancelado"]:
        pedido.status = "Cancelado"
        pedido.save()
        messages.success(request, f"O pedido #{pedido.id} foi cancelado com sucesso.")
    else:
        messages.warning(request, "Este pedido não pode mais ser cancelado.")

    return redirect('pedidos:meus_pedidos')


# ---------------------- DETALHE DO PEDIDO ----------------------
@login_required 
def detalhe_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    context = {
        'titulo': f'Detalhes do Pedido #{pedido.id}',
        'pedido': pedido,
    }
    return render(request, 'pedidos/detalhe_pedido.html', context)


# ---------------------- MEUS PEDIDOS ----------------------
@login_required 
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-data_criacao')
    context = {
        'titulo': 'Meus Pedidos',
        'pedidos': pedidos,
    }
    return render(request, 'pedidos/meus_pedidos.html', context)
