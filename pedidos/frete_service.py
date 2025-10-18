# pedidos/frete_service.py (Simulador de Cálculo de Frete)

def calcular_frete_simulado(cep_destino, peso_total_kg, valor_total):
    """
    Simula o cálculo de frete baseado no CEP e peso/valor do pedido,
    INCLUINDO a opção de Retirada na Loja.
    """
    
    # 1. Lógica de cálculo de frete padrão (PAC/SEDEX)
    if peso_total_kg < 0.5: 
        base = 15.00
    elif peso_total_kg < 2.0:
        base = 25.00
    else:
        base = 35.00
        
    # 2. Inicializa as opções de frete com a Retirada na Loja (R$ 0,00)
    # Sempre a Retirada na Loja deve estar disponível, por isso a incluímos aqui.
    opcoes = {
        'retirada': {'nome': 'Retirada na Loja', 'prazo': '1 dia útil', 'valor': 0.00},
    }
        
    # 3. Adiciona as opções de envio (PAC/SEDEX)
    if valor_total >= 200.00:
        # Frete grátis para PAC
        opcoes['pac'] = {'nome': 'PAC (GRÁTIS)', 'prazo': '10-15 dias', 'valor': 0.00}
        opcoes['sedex'] = {'nome': 'SEDEX', 'prazo': '5-8 dias', 'valor': base * 1.5}
        
    else:
        valor_pac = round(base * 1.0, 2)
        valor_sedex = round(base * 1.5, 2)
        
        opcoes['pac'] = {'nome': 'PAC', 'prazo': '10-15 dias', 'valor': valor_pac}
        opcoes['sedex'] = {'nome': 'SEDEX', 'prazo': '5-8 dias', 'valor': valor_sedex}
        
    return opcoes # Retorna todas as opções


def calcular_peso_carrinho(itens_carrinho):
    """
    Simula o cálculo do peso total do carrinho.
    """
    peso_por_unidade = 0.25 # 250g por item padrão
    peso_total = sum(item.quantidade * peso_por_unidade for item in itens_carrinho)
    return peso_total
