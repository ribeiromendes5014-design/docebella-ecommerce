from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('painel-loja/', admin.site.urls),

    # ✅ CORRETO: URLs do nested_admin
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

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('painel-loja/', admin.site.urls),
    path('_nested_admin/', include('nested_admin.urls')),
    path('', include('produtos.urls')),
    path('carrinho/', include('carrinho.urls')),
    path('conta/', include('usuarios.urls')),
    path('pedido/', include('pedidos.urls', namespace='pedidos')),
]

# -------------------------------------------------------------------------
# ✅ CORREÇÃO: ADICIONE A LINHA DE STATIC_URL (Arquivos Estáticos: CSS/JS)
# -------------------------------------------------------------------------
if settings.DEBUG:
    # Esta linha serve o 'nested-admin.css' e 'nested-admin.js'
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
    
    # Esta linha serve arquivos de Mídia (Imagens)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# -------------------------------------------------------------------------
