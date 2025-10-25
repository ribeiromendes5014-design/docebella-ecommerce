from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage

# Personalização do painel administrativo
admin.site.site_header = "Painel Administrativo - Doce & Bella 💖"
admin.site.site_title = "Doce & Bella | Admin"
admin.site.index_title = "Bem-vinda ao Painel de Controle ✨"

# Adiciona CSS personalizado
def custom_admin_css():
    return [staticfiles_storage.url('css/admin_custom.css')]

def custom_each_context(request):
    context = admin.site.each_context(request)
    context["admin_css"] = custom_admin_css()
    return context

admin.site.each_context = custom_each_context
