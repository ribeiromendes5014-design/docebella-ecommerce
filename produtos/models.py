# produtos/models.py (CORRIGIDO)
from django.db import models
from django.utils.text import slugify # Importar para slugs (útil no admin)

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True) 

    class Meta:
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome

class Produto(models.Model):
    # Relação com Categoria
    # 🚨 TROCAR POR models.CASCADE 🚨
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    
    # Informações básicas
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2) 
    
    # NOVO CAMPO: Indica se o produto usa estoque de Variacao
    usa_variacoes = models.BooleanField(default=False, help_text="Marque se este produto tiver variações (tamanho, cor) com estoque próprio.") 
    
    # Estoque mantido apenas para produtos SEM variação
    estoque = models.IntegerField(default=0) 
    
    # Imagem
    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)
    
    # Status
    disponivel = models.BooleanField(default=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome
        
    def get_display_price(self):
        # Proteção contra preco ser None, embora seja improvável no seu setup
        preco = self.preco if self.preco is not None else 0.00
        return f"R$ {preco:.2f}".replace('.', ',')
        
    def get_estoque_total(self):
        # Se usar variações, soma o estoque de todas as variações
        if self.usa_variacoes:
            return sum(v.estoque for v in self.variacoes.all())
        return self.estoque

    def get_status_estoque(self):
        estoque_total = self.get_estoque_total()
        if estoque_total == 0:
            return "Esgotado"
        elif estoque_total <= 5:
            return f"Últimas {estoque_total} unidades!"
        return "Disponível"


# NOVO MODELO: Variação de Produto
class Variacao(models.Model):
    TIPO_VARIACOES = (
        ('Tamanho', 'Tamanho'),
        ('Cor', 'Cor'),
        ('Outro', 'Outro'),
    )
    
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='variacoes')
    tipo = models.CharField(max_length=50, choices=TIPO_VARIACOES, default='Tamanho')
    valor = models.CharField(max_length=100)
    preco_adicional = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estoque = models.IntegerField(default=0)
    
    # 🚨 NOVO CAMPO: Imagem de capa para esta variação 🚨
    imagem = models.ImageField(
        upload_to='produtos/variacoes/', 
        null=True, 
        blank=True,
        help_text="Opcional. Se preenchido, esta imagem será exibida quando esta variação for selecionada na loja."
    )
    
    class Meta:
        verbose_name = "Variação"
        verbose_name_plural = "Variações"
        unique_together = (('produto', 'tipo', 'valor'))  # Garante unicidade

    def __str__(self):
        nome_produto = self.produto.nome if self.produto else f"ID {self.id} (Produto Sem Nome)"
        return f'{nome_produto} - {self.tipo}: {self.valor}'
        
    def get_preco_final(self):
        preco_base = self.produto.preco if self.produto else 0.00
        return preco_base + self.preco_adicional

    def get_display_preco_final(self):
        return f"R$ {self.get_preco_final():.2f}".replace('.', ',')

class ImagemProduto(models.Model):
    produto = models.ForeignKey(
        Produto, 
        related_name='galeria_imagens', # Usaremos este nome na view
        on_delete=models.CASCADE,
        verbose_name='Produto Principal'
    )
    # 🚨 Link para a variação (para fotos específicas, ex: Cor Azul) 🚨
    variacao = models.ForeignKey(
        'Variacao',
        related_name='imagens',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Variação (Opcional)'
    )
    imagem = models.ImageField(upload_to='produtos/galeria/')
    descricao = models.CharField(max_length=255, blank=True)
    ordem = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Imagem da Galeria'
        verbose_name_plural = 'Imagens da Galeria'

    def __str__(self):
        return f"Imagem de {self.produto.nome} - Ordem {self.ordem}"
