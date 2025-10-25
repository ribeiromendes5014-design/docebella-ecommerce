# carrinho/models.py

from django.db import models
# CORREÇÃO 1: Importamos VariacaoTamanho, que agora é o nosso SKU/Item de estoque
from produtos.models import Produto, VariacaoTamanho 
from django.utils import timezone
from decimal import Decimal

class ItemCarrinho(models.Model):
    # Vincula o item à sessão do usuário (para quem não está logado)
    session_key = models.CharField(max_length=40, db_index=True)

    # Produto e variação (ambos podem ser nulos em casos especiais)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True, blank=True)
    
    # CORREÇÃO 2: A ForeignKey agora aponta para o novo modelo de SKU
    variacao = models.ForeignKey(VariacaoTamanho, on_delete=models.CASCADE, null=True, blank=True) 

    # Quantidade e preço fixo no momento da adição
    quantidade = models.PositiveIntegerField(default=1)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0) 

    adicionado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item de Carrinho"
        verbose_name_plural = "Itens de Carrinho"
        # CORREÇÃO 3: unique_together usa VariacaoTamanho
        unique_together = ('produto', 'variacao', 'session_key') 

    def __str__(self):
        if self.variacao:
            # CORREÇÃO 4: O valor está na VariacaoTamanho, mas o nome do produto 
            # está na VariacaoTamanho.variacao_cor.produto.nome.
            # Vamos simplificar, acessando o nome do produto via FK
            if self.produto:
                # O valor é o tamanho. Para mostrar a cor, teríamos que acessar:
                # self.variacao.variacao_cor.cor
                return f'{self.produto.nome} ({self.variacao.tamanho}) - Qtd: {self.quantidade}'
            
            # Se o produto for nulo, mas a variação não for, pegamos o nome do produto via FK da variação
            if self.variacao.variacao_cor.produto:
                 nome_produto = self.variacao.variacao_cor.produto.nome
                 cor = self.variacao.variacao_cor.cor
                 return f'{nome_produto} ({cor}, {self.variacao.tamanho}) - Qtd: {self.quantidade}'

            return f'(Item de Variação) ({self.variacao.tamanho}) - Qtd: {self.quantidade}'

        if self.produto:
            return f'{self.produto.nome} - Qtd: {self.quantidade}'

        return f'Item de Carrinho Nulo - Qtd: {self.quantidade}'

    def get_preco_unitario(self):
        # Retorna o preço armazenado, se existir
        if self.preco and self.preco > 0:
            return self.preco

        # Caso contrário, busca o preço atual (fallback)
        if self.variacao:
            # CORREÇÃO 5: Usa o método de preço do novo modelo VariacaoTamanho
            return self.variacao.get_preco_final() 
        if self.produto:
            return self.produto.preco
        return Decimal('0.00') # Usar Decimal('0.00') para consistência

    def get_subtotal(self):
        return self.get_preco_unitario() * self.quantidade

# O restante do arquivo (CupomDesconto) permanece inalterado.
class CupomDesconto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    desconto_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Percentual de desconto, ex: 10 para 10%"
    )
    desconto_fixo = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Valor fixo de desconto em reais"
    )
    ativo = models.BooleanField(default=True)
    data_inicio = models.DateTimeField(default=timezone.now)
    data_fim = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.codigo

    def valido(self):
        agora = timezone.now()
        if not self.ativo:
            return False
        if self.data_fim and agora > self.data_fim:
            return False
        return True

    def aplicar_desconto(self, total):
        """Aplica o desconto (percentual ou fixo) e retorna o novo total."""
        total = Decimal(total)
        if self.desconto_percentual:
            total -= total * (self.desconto_percentual / Decimal('100'))
        elif self.desconto_fixo:
            total -= self.desconto_fixo
        return max(total, Decimal('0.00'))
