# pedidos/urls.py
from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    # ✅ NOVO: Página de "Meus Pedidos"
    path('', views.meus_pedidos, name='meus_pedidos'),
    
    # ✅ Checkout
    path('checkout/', views.checkout, name='checkout'),

    # ✅ Detalhe do Pedido
    path('<int:pedido_id>/', views.detalhe_pedido, name='detalhe_pedido'),
    path('<int:pedido_id>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),
]
