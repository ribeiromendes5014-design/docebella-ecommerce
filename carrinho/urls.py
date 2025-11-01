# app/urls.py (carrinho)

from . import views
from django.urls import path

app_name = 'carrinho'

urlpatterns = [
    # 1. Rota AJAX de Adição (Corrigida e Prioritária)
    path('adicionar/ajax/', views.adicionar_ao_carrinho_ajax, name='adicionar_ao_carrinho_ajax'),

    # 🚀 ROTA NOVA: Para o JavaScript buscar o total do carrinho
    path('get-total/', views.get_carrinho_total_ajax, name='get_carrinho_total_ajax'), # <-- ADICIONE ESTA LINHA

    # 2. Rota de Adição Normal
    path('adicionar/<slug:produto_slug>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),

    # ... as outras rotas
    path('', views.ver_carrinho, name='ver_carrinho'),
    path('remover/<int:item_id>/', views.remover_item, name='remover_item'),
    path('atualizar/', views.atualizar_carrinho, name='atualizar_carrinho'),
    path('aplicar-cupom/', views.aplicar_cupom, name='aplicar_cupom'),
]
