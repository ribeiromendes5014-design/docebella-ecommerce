# docebella_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('painel-loja/', admin.site.urls),
    
    # 1. Rotas do App PRODUTOS (Home Page)
    path('', include('produtos.urls')), 
    
    # 2. Rotas do App CARRINHO
    path('carrinho/', include('carrinho.urls')),
    
    # 3. Rotas do App USUÁRIOS/CONTA (Contém as rotas customizadas de login/logout/cadastro/painel)
    path('conta/', include('usuarios.urls')), 
    
    # 4. Rotas do App PEDIDOS/CHECKOUT
    # CORREÇÃO AQUI: Adicionamos o argumento namespace='pedidos'
    path('pedido/', include('pedidos.urls', namespace='pedidos')),
    
    # LINHA REMOVIDA/COMENTADA: 
    # Removemos a inclusão padrão do Django para evitar conflitos,
    # já que as URLs de login e logout foram definidas no app 'usuarios'.
    # path('accounts/', include('django.contrib.auth.urls')), 
]

# ... restante do código para MEDIA
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
