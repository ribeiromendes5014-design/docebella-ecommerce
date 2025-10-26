from .models import Categoria

def categorias_header(request):
    return {
        'categorias_header': Categoria.objects.filter(show_in_header=True)
    }
