# pedidos/urls.py - CORRIGIDO

from django.urls import path
from . import views

# CORREÇÃO AQUI: Esta linha deve estar ativa (descomentada)
app_name = 'pedidos' 

urlpatterns = [
    # Rota para a lista de pedidos. O nome DEVE ser 'lista'
    path('lista/', views.lista_pedidos, name='lista'), 
    
    # 1. Página de Checkout (Endereço e Frete)
    path('checkout/', views.checkout, name='checkout'),
    
    # 2. Página de Detalhe/Resumo e Pagamento
    path('<int:pedido_id>/', views.detalhe_pedido, name='detalhe_pedido'),
]