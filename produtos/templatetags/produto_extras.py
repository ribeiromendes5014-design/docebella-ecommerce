from django import template

register = template.Library()

@register.filter
def get_estoque_por_tamanho(variacoes, tamanho):
    """
    Retorna o estoque total das variações que correspondem ao tamanho informado.
    Compatível com objetos Django (QuerySet) e dicionários.
    """
    if not variacoes:
        return 0

    total = 0
    for v in variacoes:
        # se for um objeto Django (como no seu caso)
        if hasattr(v, 'tamanho') and hasattr(v, 'estoque'):
            if v.tamanho == tamanho:
                total += v.estoque or 0
        # se for um dicionário (fallback futuro, não obrigatório)
        elif isinstance(v, dict):
            if v.get('tamanho') == tamanho:
                total += v.get('estoque', 0)
    return total
