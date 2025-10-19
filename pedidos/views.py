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


# NOVO FORMULÁRIO SIMPLIFICADO PARA RETIRADA
class CheckoutFormSimplificado(forms.Form):
    nome = forms.CharField(max_length=255, label='Nome Completo')
    email = forms.EmailField(label='E-mail')
    telefone = forms.CharField(max_length=20, label='Telefone (WhatsApp)', 
                                help_text="Para entrarmos em contato sobre seu pedido.")

    # Sobrescreve o __init__ para preencher os dados do usuário logado
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Pega o usuário que passamos da view
        super(CheckoutFormSimplificado, self).__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            # Tenta preencher os campos com dados do usuário
            nome_completo = user.get_full_name()
            if not nome_completo and hasattr(user, 'nome_completo'):
                 nome_completo = user.nome_completo
            
            self.fields['nome'].initial = nome_completo or user.username
            self.fields['email'].initial = user.email
            # Se você tiver um campo 'telefone' no seu User, pode preencher aqui
            # if hasattr(user.profile, 'telefone'):
            #    self.fields['telefone'].initial = user.profile.telefone


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
            
            # --- O "PULO DO GATO" ESTÁ AQUI ---
            # Como seu modelo Pedido EXIGE um EnderecoEntrega,
            # vamos criar um "Endereço Falso" apenas com os dados de retirada.
            
            cleaned_data = form.cleaned_data
            
            try:
                with transaction.atomic():
                    
                    # 1. Crie o Endereço Falso (Dummy)
                    # Usamos os dados do form para nome/email e o telefone no 'complemento'
                    # Os outros campos são "chumbados" (hard-coded)
                    endereco_retirada = EnderecoEntrega.objects.create(
                        nome=cleaned_data['nome'],
                        sobrenome="(Retirada na Loja)",
                        email=cleaned_data['email'],
                        cep="00000-000",
                        rua="Retirada na Loja",
                        numero="S/N",
                        complemento=f"Telefone: {cleaned_data['telefone']}",
                        bairro="Loja",
                        cidade="Doce&Bella", # Ou o nome da sua cidade
                        estado="PR" # Ou o seu estado
                    )
                    
                    # 2. Crie o Pedido, agora com R$ 0 de frete
                    pedido = Pedido.objects.create(
                        cliente=request.user,
                        endereco=endereco_retirada, # Usamos o endereço falso
                        valor_total=subtotal_carrinho, # Total é SÓ o subtotal
                        valor_frete=0.00,
                        metodo_envio="Retirada na Loja"
                    )
                    
                    # 3. Mova os itens do carrinho para o pedido
                    # (Esta parte do seu código já estava correta)
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
                    
                    # FINALMENTE, o REDIRECT que faltava!
                    return redirect('pedidos:detalhe_pedido', pedido_id=pedido.id)
                
            except Exception as e:
                messages.error(request, f"Ocorreu um erro ao finalizar o pedido. Motivo: {e}")
                return redirect('carrinho:ver_carrinho')
        
        else:
            # Se o formulário for inválido, recarrega a página mostrando os erros
            messages.error(request, "Por favor, corrija os erros no formulário.")

    else:
        # GET Request: Inicializa o form simplificado passando o usuário
        form = CheckoutFormSimplificado(user=request.user)

    context = {
        'form': form,
        'itens_carrinho': itens_carrinho,
        'subtotal_carrinho': subtotal_carrinho,
        'frete_opcoes': {}, # Deixamos vazio, pois não há opções
        'titulo': "Checkout - Finalizar Pedido"
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
