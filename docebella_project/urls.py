from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('painel-loja/', admin.site.urls),

    # 👇 ADICIONE ESTA LINHA
    path('_nested_admin/', include('nested_admin.urls')),

    # 1. Rotas do App PRODUTOS (Home Page)
    path('', include('produtos.urls')),

    # 2. Rotas do App CARRINHO
    path('carrinho/', include('carrinho.urls')),

    # 3. Rotas do App USUÁRIOS/CONTA
    path('conta/', include('usuarios.urls')),

    # 4. Rotas do App PEDIDOS/CHECKOUT
    path('pedido/', include('pedidos.urls', namespace='pedidos')),
]

# Servir arquivos de mídia em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
