# docebella_project/context_processors.py
from carrinho.models import ItemCarrinho
from carrinho.views import _get_session_key 
from django.db.models import Sum # <-- ESTA IMPORTAÇÃO ESTAVA FALTANDO!

def carrinho_contador(request):
    """
    Retorna o total de itens no carrinho da sessão atual para uso em todos os templates.
    """
    # Se a requisição não tiver sessão, use None ou o padrão
    if not hasattr(request, 'session'):
        return {'CARRINHO_TOTAL_ITENS': 0}
        
    session_key = _get_session_key(request)
    
    # Soma a quantidade de todos os itens no carrinho desta sessão
    total_itens = ItemCarrinho.objects.filter(session_key=session_key).aggregate(Sum('quantidade'))['quantidade__sum'] or 0
    
    return {'CARRINHO_TOTAL_ITENS': total_itens}