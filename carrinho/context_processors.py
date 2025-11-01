# docebella_project/context_processors.py

from carrinho.models import ItemCarrinho
from django.db.models import Sum

def carrinho_contador(request):
    """Calcula e retorna o número total de itens no carrinho para exibição global."""
    
    # Garante que a sessão existe antes de tentar ler a chave
    if not request.session.session_key:
        request.session.create()
        
    session_key = request.session.session_key
        
    if not session_key:
        total_itens = 0
    else:
        total_itens = ItemCarrinho.objects.filter(session_key=session_key).aggregate(
            total=Sum('quantidade')
        )['total'] or 0
    
    return {'CARRINHO_TOTAL_ITENS': total_itens}
