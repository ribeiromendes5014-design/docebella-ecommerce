# pedidos/frete_service.py (Simulador de Cálculo de Frete)

def calcular_frete_simulado(cep_destino, peso_total_kg, valor_total):
    """
    Simula o cálculo de frete baseado no CEP e peso/valor do pedido.
    """
    if peso_total_kg < 0.5: 
        base = 15.00
    elif peso_total_kg < 2.0:
        base = 25.00
    else:
        base = 35.00
        
    if valor_total >= 200.00:
        return {
            'pac': {'nome': 'PAC (GRÁTIS)', 'prazo': '10-15 dias', 'valor': 0.00},
            'sedex': {'nome': 'SEDEX', 'prazo': '5-8 dias', 'valor': base * 1.5}
        }
        
    valor_pac = round(base * 1.0, 2)
    valor_sedex = round(base * 1.5, 2)
    
    return {
        'pac': {'nome': 'PAC', 'prazo': '10-15 dias', 'valor': valor_pac},
        'sedex': {'nome': 'SEDEX', 'prazo': '5-8 dias', 'valor': valor_sedex}
    }

def calcular_peso_carrinho(itens_carrinho):
    """
    Simula o cálculo do peso total do carrinho.
    """
    peso_por_unidade = 0.25 # 250g por item padrão
    peso_total = sum(item.quantidade * peso_por_unidade for item in itens_carrinho)
    return peso_total