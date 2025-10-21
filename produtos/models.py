from django.db import models
from django.utils import timezone
from django.utils.text import slugify  # Para slugs (útil no admin)

# ======================
# CATEGORIA
# ======================
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome


# ======================
# PRODUTO
# ======================
class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)

    usa_variacoes = models.BooleanField(
        default=False,
        help_text="Marque se este produto tiver variações (tamanho, cor) com estoque próprio."
    )
    estoque = models.IntegerField(default=0)

    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)
    disponivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    def valor_parcela_3x(self):
        """Retorna o valor da parcela em 3x com ajuste de 0.8872."""
        if not self.preco:
            return 0
        return (self.preco / 0.8872) / 3

    def __str__(self):
        return self.nome

    # ======================
    # 🔹 PREÇO (com promoção)
    # ======================
    def get_display_price(self):
        """
        Retorna o preço considerando promoções ativas.
        Se houver uma promoção vigente, aplica o desconto automaticamente.
        """
        preco = self.preco or 0.00

        promo = self.promocoes.filter(
            ativa=True,
            data_inicio__lte=timezone.now()
        ).filter(
            models.Q(data_fim__gte=timezone.now()) | models.Q(data_fim__isnull=True)
        ).first()

        if promo:
            preco_final = promo.preco_promocional
            return f"R$ {preco_final:.2f}".replace('.', ',') + " 🔥"

        return f"R$ {preco:.2f}".replace('.', ',')

    def get_estoque_total(self):
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


# ======================
# VARIAÇÃO
# ======================
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

    imagem = models.ImageField(
        upload_to='produtos/variacoes/',
        null=True,
        blank=True,
        help_text="Opcional. Se preenchido, esta imagem será exibida quando esta variação for selecionada na loja."
    )

    class Meta:
        verbose_name = "Variação"
        verbose_name_plural = "Variações"
        unique_together = (('produto', 'tipo', 'valor'))

    def __str__(self):
        nome_produto = self.produto.nome if self.produto else f"ID {self.id} (Produto Sem Nome)"
        return f'{nome_produto} - {self.tipo}: {self.valor}'

    def get_preco_final(self):
        preco_base = self.produto.preco if self.produto else 0.00
        return preco_base + self.preco_adicional

    def get_display_preco_final(self):
        return f"R$ {self.get_preco_final():.2f}".replace('.', ',')


# ======================
# GALERIA DE IMAGENS
# ======================
class ImagemProduto(models.Model):
    produto = models.ForeignKey(
        Produto,
        related_name='galeria_imagens',
        on_delete=models.CASCADE,
        verbose_name='Produto Principal'
    )
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


# ======================
# PROMOÇÃO (CORRIGIDO)
# ======================
class Promocao(models.Model):
    nome = models.CharField("Nome da promoção", max_length=100)
    descricao = models.TextField(blank=True, null=True)
    desconto_percentual = models.DecimalField(
        "Desconto (%)", max_digits=5, decimal_places=2,
        help_text="Ex: 10.00 = 10%"
    )
    produtos = models.ManyToManyField('Produto', related_name='promocoes', blank=True)
    data_inicio = models.DateTimeField("Início da promoção", default=timezone.now)
    data_fim = models.DateTimeField("Fim da promoção", blank=True, null=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Promoção"
        verbose_name_plural = "Promoções"
        ordering = ["-data_inicio"]

    def __str__(self):
        return f"{self.nome} ({self.desconto_percentual}% off)"

    def esta_vigente(self):
        agora = timezone.now()
        return (
            self.ativa
            and self.data_inicio <= agora
            and (self.data_fim is None or self.data_fim >= agora)
        )
