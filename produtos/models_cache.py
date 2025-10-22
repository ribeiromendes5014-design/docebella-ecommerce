# produtos/models_cache.py
from django.db import models
from django.utils import timezone

class ProdutoCache(models.Model):
    produto_id = models.IntegerField(unique=True)
    nome = models.CharField(max_length=255)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    atualizado_em = models.DateTimeField(default=timezone.now)
    hash_conteudo = models.CharField(max_length=64)
    dados_json = models.JSONField()

    def __str__(self):
        return f"{self.nome} (Cache)"

    class Meta:
        verbose_name = "Produto em Cache"
        verbose_name_plural = "Produtos em Cache"
