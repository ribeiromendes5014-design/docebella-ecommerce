# carrinho/models.py
from django.db import models
from produtos.models import Produto, Variacao

class ItemCarrinho(models.Model):
    # Vincula o item à sessão do usuário (para quem não está logado)
    session_key = models.CharField(max_length=40, db_index=True)

    # Produto e variação (ambos podem ser nulos em casos especiais)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True, blank=True)
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=True, blank=True)

    # Quantidade e preço fixo no momento da adição
    quantidade = models.PositiveIntegerField(default=1)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ CAMPO ADICIONADO AQUI

    adicionado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item de Carrinho"
        verbose_name_plural = "Itens de Carrinho"
        unique_together = ('produto', 'variacao', 'session_key')

    def __str__(self):
        if self.variacao:
            if self.produto:
                return f'{self.produto.nome} ({self.variacao.valor}) - Qtd: {self.quantidade}'
            return f'(Produto Nulo) ({self.variacao.valor}) - Qtd: {self.quantidade}'

        if self.produto:
            return f'{self.produto.nome} - Qtd: {self.quantidade}'

        return f'Item de Carrinho Nulo - Qtd: {self.quantidade}'

    def get_preco_unitario(self):
        # Retorna o preço armazenado, se existir
        if self.preco and self.preco > 0:
            return self.preco

        # Caso contrário, busca o preço atual (fallback)
        if self.variacao and self.variacao.produto:
            return self.variacao.get_preco_final()
        if self.produto:
            return self.produto.preco
        return 0.00

    def get_subtotal(self):
        return self.get_preco_unitario() * self.quantidade
