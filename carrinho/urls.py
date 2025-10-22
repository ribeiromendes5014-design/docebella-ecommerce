# G:\projeto\carrinho\urls.py
from . import views
from django.urls import path

# 👇 ADICIONE ESTA LINHA PARA CORRIGIR O ERRO
app_name = 'carrinho' 

urlpatterns = [
    # Rota para adicionar um produto
    path('adicionar/<slug:produto_slug>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    
    # Rota para visualizar o carrinho
    path('', views.ver_carrinho, name='ver_carrinho'),
    
    # Rota para remover um item
    path('remover/<int:item_id>/', views.remover_item, name='remover_item'),
    
    # Rota para atualizar a quantidade
    path('atualizar/', views.atualizar_carrinho, name='atualizar_carrinho'),
    
    # Adicione também a rota do cupom que o template vai precisar
    path('aplicar-cupom/', views.aplicar_cupom, name='aplicar_cupom'),
]