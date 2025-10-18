# carrinho/models.py
from django.db import models
from produtos.models import Produto, Variacao # Importa os modelos do nosso outro app

class ItemCarrinho(models.Model):
    # Usaremos um ID de sessão para vincular o item ao carrinho de um usuário anônimo
    session_key = models.CharField(max_length=40, db_index=True)
    
    # O produto base e a variação exata (se houver)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=True, blank=True) 
    
    # Quantidade
    quantidade = models.PositiveIntegerField(default=1)
    
    adicionado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item de Carrinho"
        verbose_name_plural = "Itens de Carrinho"
        unique_together = ('produto', 'variacao', 'session_key') 

    def __str__(self):
        if self.variacao:
            return f'{self.produto.nome} ({self.variacao.valor}) - Qtd: {self.quantidade}'
        return f'{self.produto.nome} - Qtd: {self.quantidade}'
        
    def get_preco_unitario(self):
        if self.variacao:
            return self.variacao.get_preco_final()
        return self.produto.preco
        
    def get_subtotal(self):
        return self.get_preco_unitario() * self.quantidade