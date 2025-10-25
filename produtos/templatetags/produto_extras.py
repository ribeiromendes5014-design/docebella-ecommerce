from django import template

register = template.Library()

@register.filter
def get_estoque_por_tamanho(variacoes, tamanho):
    """
    Retorna o estoque total das variações que correspondem ao tamanho informado.
    """
    if not variacoes:
        return 0
    total = 0
    for v in variacoes:
        if v.get('tamanho') == tamanho:
            total += v.get('estoque', 0)
    return total
