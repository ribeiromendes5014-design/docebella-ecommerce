# produtos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # A rota da página inicial
    path('', views.home, name='home'),
    # A rota de detalhe do produto
    path('produto/<slug:slug>/', views.detalhe_produto, name='detalhe_produto'), 
    # NENHUMA OUTRA LINHA DEVE ESTAR AQUI.
]
