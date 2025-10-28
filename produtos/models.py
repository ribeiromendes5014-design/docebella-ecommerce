from django.db import models
from django.templatetags.static import static
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from decimal import Decimal
import boto3
import os


# ======================
# CATEGORIA
# ======================
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    show_in_header = models.BooleanField(
        default=False,
        verbose_name="Mostrar no cabeçalho"
    )

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome
from django.db import models

# ======================
# Mensagem Topo
# ======================
class MensagemTopo(models.Model):
    texto = models.CharField(max_length=255, help_text="Texto que aparecerá rolando no topo do site.")
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=1, help_text="Define a ordem das mensagens.")
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['ordem']
        verbose_name = "Mensagem do Topo"
        verbose_name_plural = "Mensagens do Topo"

    def __str__(self):
        return self.texto[:50]

    def esta_ativa(self):
        from django.utils import timezone
        agora = timezone.now()
        if self.data_inicio and self.data_fim:
            return self.ativo and self.data_inicio <= agora <= self.data_fim
        return self.ativo

# ======================
# PRODUTO
# ======================
class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    usa_variacoes = models.BooleanField(default=False)
    estoque = models.IntegerField(default=0)
    
    # Campo existente para Upload no S3
    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)
    
    # 🚀 NOVO CAMPO: URL para imagem principal externa
    imagem_url_externa = models.URLField(
        max_length=2000, 
        null=True, 
        blank=True, 
        verbose_name="URL Imagem Externa Principal",
        help_text="Se preenchido, será usada esta URL em vez do arquivo local/S3."
    )
    
    disponivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sua lógica existente de renomeação/busca no S3 (mantida)
        if self.imagem and hasattr(self.imagem, "name"):
            ext = os.path.splitext(self.imagem.name)[1].lower()
            novo_nome = f"{self.slug}{ext}"
            caminho_final = f"produtos/{novo_nome}"

            if self.imagem.name != novo_nome:
                if default_storage.exists(caminho_final):
                    default_storage.delete(caminho_final)
                self.imagem.name = novo_nome
                print(f"🖼️ Imagem renomeada automaticamente para: {caminho_final}")

        elif not self.imagem:
            # Tenta buscar no S3 (mantida)
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

        super().save(*args, **kwargs)
        
    # 🎯 NOVO MÉTODO CENTRAL: Define qual URL de imagem principal usar
    def get_imagem_url(self):
        """
        Retorna a URL da imagem principal. Prioriza: 1. URL Externa, 2. Imagem S3, 3. Placeholder.
        """
        if self.imagem_url_externa:
            return self.imagem_url_externa
        if self.imagem:
            return self.imagem.url
        
        # Retorna o placeholder estático
        return static('img/placeholder.png')


    def valor_parcela_3x(self):
        """Retorna o valor da parcela em 3x com ajuste de 0.8872."""
        if not self.preco:
            return 0
        return (self.preco / 0.8872) / 3

    def __str__(self):
        return self.nome

    def get_preco_final(self):
        preco = Decimal(self.preco)
        promo_ativa = None
        for promo in self.promocoes.all():
            if promo.esta_vigente():
                promo_ativa = promo
                break
        if promo_ativa:
            preco = promo_ativa.aplicar_desconto(preco)
        return preco

    def get_display_price(self):
        preco_final = self.get_preco_final()
        return f"R$ {preco_final:.2f}".replace('.', ',')

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
# Banner
# ======================

class Banner(models.Model):
    titulo = models.CharField(max_length=100, blank=True, null=True)
    imagem = models.ImageField(upload_to='banners/', blank=True, null=True)
    imagem_mobile = models.ImageField(
        upload_to='banners/mobile/',
        blank=True,
        null=True,
        help_text="Versão otimizada para celular"
    )
    link = models.URLField(
        blank=True,
        null=True,
        help_text="Link opcional para o banner (versão desktop)"
    )
    link_mobile = models.URLField(
        blank=True,
        null=True,
        help_text="Link opcional apenas para o banner mobile"
    )
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=1)
    usar_em_carrossel = models.BooleanField(
        default=True,
        help_text="Se falso, exibe apenas um banner fixo."
    )

    class Meta:
        ordering = ['ordem']
        verbose_name = "Banner"
        verbose_name_plural = "Banners"

    def __str__(self):
        return self.titulo or f"Banner {self.id}"

    def clean(self):
        if not self.imagem and not self.link:
            raise ValidationError("Informe uma imagem ou um link para o banner.")





# ======================
# VARIAÇÃO
# ======================
class Variacao(models.Model):
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.CASCADE,
        related_name='variacoes'
    )
    cor = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Cor"
    )
    tamanho = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Tamanho"
    )
    outro = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Outra variação"
    )
    estoque = models.PositiveIntegerField(
        default=0,
        verbose_name="Estoque"
    )
    imagem = models.ImageField(
        upload_to='produtos/variacoes/',
        blank=True,
        null=True,
        verbose_name="Imagem"
    )
    imagem_url_externa = models.URLField(
        max_length=2000,
        blank=True,
        null=True,
        verbose_name="URL da Imagem Externa",
        help_text="Se preenchido, substitui a imagem local."
    )
    preco_adicional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Preço adicional"
    )

    class Meta:
        verbose_name = "Variação"
        verbose_name_plural = "Variações"
        ordering = ['produto', 'cor', 'tamanho', 'outro']

    def __str__(self):
        variacoes = []
        if self.cor:
            variacoes.append(self.cor)
        if self.tamanho:
            variacoes.append(self.tamanho)
        if self.outro:
            variacoes.append(self.outro)
        return f"{self.produto.nome} - {' / '.join(variacoes) or 'Única'}"

    def get_imagem_url(self):
        """
        Retorna a URL da imagem da variação, priorizando a URL externa.
        Ordem de prioridade:
        1. URL externa (imagem_url_externa)
        2. Imagem local da variação
        3. Imagem do produto principal
        4. Placeholder padrão
        """
        # 1️⃣ URL externa definida manualmente
        if self.imagem_url_externa:
            return self.imagem_url_externa

        # 2️⃣ Imagem local
        if self.imagem and hasattr(self.imagem, "url"):
            return self.imagem.url

        # 3️⃣ Imagem do produto (fallback)
        if hasattr(self.produto, "imagem") and self.produto.imagem:
            return self.produto.imagem.url

        # 4️⃣ Imagem placeholder
        return static("img/placeholder.png")

    def save(self, *args, **kwargs):
        """
        Renomeia automaticamente a imagem local e mantém compatibilidade com URLs externas.
        Gera o nome com base nas variações atuais (cor, tamanho, outro).
        """
        variacoes = []
        if self.cor:
            variacoes.append(self.cor)
        if self.tamanho:
            variacoes.append(self.tamanho)
        if self.outro:
            variacoes.append(self.outro)

        base_name = (
            f"{self.produto.slug}-{'-'.join(v.lower().replace(' ', '-') for v in variacoes)}"
            if self.produto else f"variacao-{self.pk}"
        )

        # CASO 1: imagem local enviada manualmente
        if self.imagem and hasattr(self.imagem, "name"):
            ext = os.path.splitext(self.imagem.name)[1].lower()
            novo_nome = f"media/produtos/variacoes/{base_name}{ext}"

            if self.imagem.name != novo_nome:
                if default_storage.exists(novo_nome):
                    default_storage.delete(novo_nome)
                self.imagem.name = novo_nome
                print(f"🎨 Imagem de variação renomeada automaticamente: {novo_nome}")

        # CASO 2: sem imagem e sem URL externa
        elif not self.imagem and not getattr(self, "imagem_url_externa", None):
            pass  # Pode adicionar lógica extra aqui, se quiser

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
    imagem = models.ImageField(upload_to='produtos/galeria/', blank=True, null=True)
    imagem_url_externa = models.URLField(
        "URL da Imagem Externa (opcional)",
        blank=True,
        null=True,
        help_text="Cole aqui o link direto da imagem se quiser usar uma hospedada externamente."
    )
    descricao = models.CharField(max_length=255, blank=True)
    ordem = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Imagem da Galeria'
        verbose_name_plural = 'Imagens da Galeria'

    def __str__(self):
        return f"Imagem de {self.produto.nome} - Ordem {self.ordem}"

    def get_imagem_url(self):
        """
        Retorna a URL da imagem, priorizando externa > local > placeholder.
        Evita erro se não houver arquivo associado.
        """
        if self.imagem_url_externa:
            return self.imagem_url_externa

        if self.imagem and getattr(self.imagem, 'name', None):
            try:
                return self.imagem.url
            except ValueError:
                pass

        return static('img/placeholder.png')




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
        agora = timezone.now()
        if not self.ativo:
            return False
        if self.data_fim:
            return self.data_inicio <= agora <= self.data_fim
        return self.data_inicio <= agora

    def aplicar_desconto(self, preco_original):
        preco = Decimal(preco_original)
        if self.desconto_percentual:
            desconto = preco * (self.desconto_percentual / Decimal('100'))
            preco -= desconto
        elif self.valor_desconto:
            preco -= self.valor_desconto
        return max(preco, Decimal('0.00'))

    def tempo_restante(self):
        if not self.data_fim:
            return None
        agora = timezone.now()
        diff = self.data_fim - agora
        return max(int(diff.total_seconds()), 0)
