# usuarios/urls.py - CORRIGIDO E COMPLETO

from django.urls import path, include  # ⬅️ 1. Adicionar 'include' aqui
from django.contrib.auth import views as auth_views
from . import views

# CORREÇÃO 1: Definir o app_name para suportar o namespace 'usuarios:'
app_name = 'usuarios'

urlpatterns = [
    # 1. Registro de Novo Usuário (Customizada)
    path('cadastro/', views.cadastro_cliente, name='cadastro'),
    
    # 2. Login (Usando a view padrão do Django)
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    
    # 3. Logout (Usando a view padrão do Django)
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # 4. Painel do Cliente (Customizada)
    path('painel/', views.painel_cliente, name='painel_cliente'),
    
    # 5. Detalhes da Conta (Customizada)
    path('detalhes/', views.detalhes_conta, name='detalhes_conta'),

    # ⚠️ CORREÇÃO CRUCIAL (Password Reset URLs)
    # 6. URLs de Redefinição de Senha do Django.
    # Elas herdam o namespace 'usuarios', tornando 'password_reset' acessível via 
    # {% url 'usuarios:password_reset' %}
    path('', include('django.contrib.auth.urls')), 
]