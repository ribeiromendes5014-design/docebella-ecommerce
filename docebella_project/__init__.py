import django
from django.utils.translation import gettext_lazy

# Corrige compatibilidade com pacotes antigos que usam ugettext_lazy
import django.utils.translation
django.utils.translation.ugettext_lazy = gettext_lazy
