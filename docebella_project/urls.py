# docebella_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),

# ==========================================
# 🔐 PROTEÇÃO DO ADMIN (Honeypot + Caminho Secreto)
# ==========================================
# ⚠️ Antes de usar o Honeypot:
# Instale o pacote:
#   pip install django-admin-honeypot
# E adicione em settings.py:
#   INSTALLED_APPS += ['admin_honeypot']
# ==========================================

urlpatterns = [
    # 💖 Painel administrativo verdadeiro (tema Jazzmin)
    path('martins/', admin.site.urls),

    # 🪤 Honeypot (painel falso pra enganar bots que tentam /admin/)
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),

    # ==========================================
    # 🏠 ROTAS DO SITE
    # ==========================================

    # Página inicial e produtos
    path('', include('produtos.urls')),

    # Carrinho de compras
    path('carrinho/', include('carrinho.urls')),

    # Usuários (login, cadastro, painel, etc.)
    path('conta/', include('usuarios.urls')),

    # Pedidos e checkout
    path('pedido/', include('pedidos.urls', namespace='pedidos')),
]

# ==========================================
# 📁 CONFIGURAÇÃO DE MEDIA E STATIC
# ==========================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
