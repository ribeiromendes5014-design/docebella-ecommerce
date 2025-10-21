# docebella_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseNotFound

# =============================
# 🔐 FAKE ADMIN (Honeypot opcional)
# =============================
# Se quiser enganar bots que tentarem /admin/, instale antes:
# pip install django-admin-honeypot
# e adicione 'admin_honeypot' em INSTALLED_APPS (settings.py)

urlpatterns = [
    # 🩷 Painel secreto real
    path('martins/', admin.site.urls),

    # 🪤 Honeypot (opcional, fake admin pra despistar bots)
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),

    # =============================
    # 🏠 Rotas principais do site
    # =============================

    # 1. Página inicial / produtos
    path('', include('produtos.urls')), 

    # 2. Carrinho de compras
    path('carrinho/', include('carrinho.urls')),

    # 3. Usuários (login, cadastro, painel)
    path('conta/', include('usuarios.urls')), 

    # 4. Pedidos / checkout
    path('pedido/', include('pedidos.urls', namespace='pedidos')),
]

# =============================
# 📁 Configuração de arquivos estáticos/media
# =============================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
