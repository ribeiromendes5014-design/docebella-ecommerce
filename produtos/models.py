from django.db import models
from django.utils import timezone
from decimal import Decimal

# ======================
# CATEGORIA
# ======================
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome


# ======================
# PRODUTO
# ======================
class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='produtos')
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
    import boto3
from django.conf import settings
import os

class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    usa_variacoes = models.BooleanField(default=False)
    estoque = models.IntegerField(default=0)
    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)
    disponivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
    import os
    import boto3
    from django.conf import settings
    from django.core.files.storage import default_storage

    # --- CASO 1: Enviou imagem manualmente ---
    if self.imagem and hasattr(self.imagem, "name"):
        ext = os.path.splitext(self.imagem.name)[1].lower()  # ex: .jpg, .png
        novo_nome = f"produtos/{self.slug}{ext}"

        if self.imagem.name != novo_nome:
            # Evita duplicação se já existir uma imagem antiga
            if default_storage.exists(novo_nome):
                default_storage.delete(novo_nome)
            self.imagem.name = novo_nome
            print(f"🖼️ Imagem renomeada automaticamente para: {novo_nome}")

    # --- CASO 2: Nenhuma imagem enviada → tenta buscar no S3 ---
    elif not self.imagem:
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        bucket = settings.AWS_STORAGE_BUCKET_NAME
        possible_keys = [
            f"media/produtos/{self.slug}.jpg",
            f"media/produtos/{self.slug}.png",
            f"media/produtos/{self.slug}.jpeg",
        ]

        for key in possible_keys:
            try:
                s3.head_object(Bucket=bucket, Key=key)
                self.imagem.name = key.replace("media/", "")
                print(f"📸 Imagem encontrada e vinculada automaticamente: {key}")
                break
            except s3.exceptions.ClientError:
                continue

    # Salva normalmente
    super().save(*args, **kwargs)



    def valor_parcela_3x(self):
        """Retorna o valor da parcela em 3x com ajuste de 0.8872."""
        if not self.preco:
            return 0
        return (self.preco / 0.8872) / 3

    def __str__(self):
        return self.nome

    # ======================
    # 🔹 PREÇO (cálculo com promoção)
    # ======================
    def get_preco_final(self):
        """
        Retorna o preço numérico considerando promoção vigente, se houver.
        """
        preco = Decimal(self.preco)
        promo_ativa = None

        # Busca uma promoção ativa e vigente
        for promo in self.promocoes.all():
            if promo.esta_vigente():
                promo_ativa = promo
                break

        # Aplica desconto, se houver
        if promo_ativa:
            preco = promo_ativa.aplicar_desconto(preco)

        return preco

    def get_display_price(self):
        """Retorna o preço formatado (string) considerando promoção vigente."""
        preco_final = self.get_preco_final()
        return f"R$ {preco_final:.2f}".replace('.', ',')

    # ======================
    # 🔹 ESTOQUE
    # ======================
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
        unique_together = (('produto', 'tipo', 'valor'),)

    def __str__(self):
        nome_produto = self.produto.nome if self.produto else f"ID {self.id} (Produto Sem Nome)"
        return f'{nome_produto} - {self.tipo}: {self.valor}'

    def get_preco_final(self):
        preco_base = self.produto.get_preco_final() if self.produto else Decimal('0.00')
        return preco_base + self.preco_adicional

    def get_display_preco_final(self):
        return f"R$ {self.get_preco_final():.2f}".replace('.', ',')

    def save(self, *args, **kwargs):
        import os
        import boto3
        from django.conf import settings
        from django.core.files.storage import default_storage

        # Nome base para o arquivo (ex: vestido-floral-verde)
        base_name = f"{self.produto.slug}-{self.valor.lower().replace(' ', '-')}"

        # --- CASO 1: imagem foi enviada manualmente ---
        if self.imagem and hasattr(self.imagem, "name"):
            ext = os.path.splitext(self.imagem.name)[1].lower()  # ex: .jpg, .png
            novo_nome = f"produtos/variacoes/{base_name}{ext}"

            if self.imagem.name != novo_nome:
                # Evita duplicação se o nome já existir
                if default_storage.exists(novo_nome):
                    default_storage.delete(novo_nome)
                self.imagem.name = novo_nome
                print(f"🎨 Imagem de variação renomeada automaticamente: {novo_nome}")

        # --- CASO 2: imagem não enviada → tenta achar no S3 ---
        elif not self.imagem:
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            bucket = settings.AWS_STORAGE_BUCKET_NAME
            possible_keys = [
                f"media/produtos/variacoes/{base_name}.jpg",
                f"media/produtos/variacoes/{base_name}.png",
                f"media/produtos/variacoes/{base_name}.jpeg",
            ]

            for key in possible_keys:
                try:
                    s3.head_object(Bucket=bucket, Key=key)
                    self.imagem.name = key.replace("media/", "")
                    print(f"🖼️ Imagem de variação encontrada e vinculada automaticamente: {key}")
                    break
                except s3.exceptions.ClientError:
                    continue

        super().save(*args, **kwargs)



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
# PROMOÇÃO
# ======================
class Promocao(models.Model):
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.CASCADE,
        related_name='promocoes'
    )
    titulo = models.CharField(max_length=150)
    desconto_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentual de desconto (ex: 10 para 10%)",
        null=True,
        blank=True
    )
    valor_desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Desconto fixo em reais (opcional)",
        null=True,
        blank=True
    )
    data_inicio = models.DateTimeField(default=timezone.now)
    data_fim = models.DateTimeField(null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Promoção"
        verbose_name_plural = "Promoções"
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.titulo} ({self.produto.nome})"

    def esta_vigente(self):
        """Retorna True se a promoção está ativa e dentro do período de validade."""
        agora = timezone.now()
        if not self.ativo:
            return False
        if self.data_fim:
            return self.data_inicio <= agora <= self.data_fim
        return self.data_inicio <= agora

    def aplicar_desconto(self, preco_original):
        """Retorna o preço com desconto aplicado."""
        preco = Decimal(preco_original)
        if self.desconto_percentual:
            desconto = preco * (self.desconto_percentual / Decimal('100'))
            preco -= desconto
        elif self.valor_desconto:
            preco -= self.valor_desconto
        return max(preco, Decimal('0.00'))

    def tempo_restante(self):
        """Retorna o tempo restante em segundos (ou None se não houver data_fim)."""
        if not self.data_fim:
            return None
        agora = timezone.now()
        diff = self.data_fim - agora
        return max(int(diff.total_seconds()), 0)
