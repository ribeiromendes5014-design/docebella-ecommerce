from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('produto/<slug:slug>/', views.detalhe_produto, name='detalhe_produto'),
    path('categoria/<slug:categoria_slug>/', views.listar_por_categoria, name='listar_categoria'),
]
