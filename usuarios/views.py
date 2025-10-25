# G:\projeto\usuarios\views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout # Renomeado login para auth_login
from django.contrib.auth.decorators import login_required 

# Importe os formulários customizados
from .forms import CadastroClienteForm, LoginForm 

# ====================================================================
# 1. VIEW DE CADASTRO (A view que estava faltando/com erro de grafia)
# ====================================================================
def cadastro_cliente(request):
    if request.method == 'POST':
        form = CadastroClienteForm(request.POST) 
        
        if form.is_valid():
            user = form.save() 
            
            # Não loga automaticamente, apenas redireciona para o login
            messages.success(request, 'Sua conta foi criada com sucesso! Você já pode fazer login.')
            return redirect('usuarios:login') 
            
        else:
            # DEBUG: Exibir erros no terminal (opcional)
            print("ERRO DE VALIDAÇÃO DO FORMULÁRIO DE CADASTRO:", form.errors)
            messages.error(request, 'Houve um erro no cadastro. Verifique os campos em vermelho.')
             
    else:
        form = CadastroClienteForm()
        
    context = {
        'form': form,
        'titulo': 'Criar Conta | Doce & Bella'
    }
    return render(request, 'usuarios/cadastro.html', context)


# ====================================================================
# 2. VIEW DE LOGIN (Baseada no seu código, usando authenticate pelo e-mail)
# ====================================================================
def login_cliente(request):
    # O urls.py do Django já usa a view padrão, mas se você tiver uma URL customizada:
    # if request.user.is_authenticated:
    #     return redirect('usuarios:painel_cliente') 

    # NOTA: Se você está usando path('login/', auth_views.LoginView.as_view(...)) no urls.py,
    # esta view customizada pode ser desnecessária ou causar conflito. 
    # Mantenha-a se a URL 'usuarios:login' aponta para ELA.

    if request.method == 'POST':
        form = LoginForm(request.POST) 

        if form.is_valid():
            # O LoginForm já mapeia o campo 'username' (que o authenticate espera) para 'email'.
            # O 'username' no form é o e-mail que o usuário digitou.
            email = form.cleaned_data.get('username') 
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=email, password=password)

            if user is not None:
                auth_login(request, user) 
                messages.success(request, 'Login realizado com sucesso! Bem-vindo(a).')
                return redirect('usuarios:painel_cliente')  
            else:
                messages.error(request, 'E-mail ou senha inválidos. Por favor, tente novamente.')
                
    else:
        form = LoginForm()
        
    context = {
        'form': form,
        'titulo': 'Login | Doce & Bella'
    }
    return render(request, 'usuarios/login.html', context)
    
# ====================================================================
# 3. VIEWS PROTEGIDAS (painel_cliente e detalhes_conta)
# ====================================================================

@login_required
def painel_cliente(request):
    """ View que exibe o painel do cliente. """
    context = {
        'titulo': 'Meu Painel',
        'usuario': request.user 
    }
    return render(request, 'usuarios/painel_cliente.html', context)


@login_required
def detalhes_conta(request):
    """ View para exibir e editar os detalhes da conta do cliente. """
    user = request.user

    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo')
        email = request.POST.get('email')
        senha = request.POST.get('password')

        # Atualiza o nome completo
        if nome_completo and nome_completo != user.nome_completo:
            user.nome_completo = nome_completo

        # Atualiza o e-mail
        if email and email != user.email:
            user.email = email

        # Atualiza a senha (opcional)
        if senha:
            user.set_password(senha)

        user.save()
        messages.success(request, 'Informações atualizadas com sucesso!')

        # Se a senha foi alterada, é necessário refazer login
        if senha:
            return redirect('usuarios:login')

        return redirect('usuarios:detalhes_conta')

    context = {
        'titulo': 'Detalhes da Conta',
        'usuario': user
    }
    return render(request, 'usuarios/detalhes_conta.html', context)

