from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone # Importar timezone para as datas de validade
from produtos.models import Produto, Variacao


class OpcaoFrete(models.Model):
    # 🚨 Adicione temporariamente 'blank=True' 🚨
    nome = models.CharField(max_length=100, unique=True, blank=True)
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome
        
class EnderecoEntrega(models.Model):
    nome = models.CharField(max_length=255)
    sobrenome = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField()
    
    # Tornar OPCIONAL:
    cep = models.CharField(max_length=9, blank=True, null=True)
    rua = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    complemento = models.CharField(max_length=255, blank=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)

    def __str__(self):
        return f'{self.rua}, {self.numero} - {self.cidade}/{self.estado}'
    
    class Meta:
        verbose_name_plural = "Endereços de Entrega"


class Pedido(models.Model):
    STATUS_CHOICES = (
        ('Aguardando Pagamento', 'Aguardando Pagamento'),
        ('Pagamento Aprovado', 'Pagamento Aprovado'),
        ('Em Separação', 'Em Separação'),
        ('Enviado', 'Enviado'),
        ('Entregue', 'Entregue'),
        ('Cancelado', 'Cancelado'),
    )

    # Cliente
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    
    # Endereço e Cupom
    endereco = models.OneToOneField(EnderecoEntrega, on_delete=models.CASCADE, null=True)
    cupom = models.ForeignKey('Cupom', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Informações financeiras
    # 🚨 CORREÇÃO CRÍTICA AQUI: O status padrão agora é 'Em Separação' 🚨
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Em Separação')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Adicionado 'metodo_envio' (Corrigido o erro anterior da view)
    metodo_envio = models.CharField(max_length=100, default='Retirada na Loja')
    
    # Rastreamento
    codigo_rastreio = models.CharField(max_length=100, blank=True, null=True)

    data_criacao = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Pedido #{self.id}'


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    # 🚨 CORRIGIDO AQUI: Permite que produtos simples sejam criados com VARIAÇÃO NULA 🚨
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=True, blank=True)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField()

    def __str__(self):
        # Proteção contra erro se produto/variação forem deletados
        if self.variacao and self.variacao.valor:
            nome_produto = self.produto.nome if self.produto else "Deletado"
            nome_display = f"{nome_produto} ({self.variacao.valor})"
        elif self.produto:
            nome_display = self.produto.nome
        else:
            nome_display = "Produto Deletado/Inválido"

        return f'{self.quantidade}x {nome_display} (Pedido {self.pedido.id})'



# >> NOVO MODELO: CUPOM DE DESCONTO <<
from produtos.models import Produto, Categoria  # ✅ Adicione este import junto com os outros

class Cupom(models.Model):
    TIPO_DESCONTO = (
        ('percentagem', 'Percentagem'),  # Ex: 10% de desconto
        ('fixo', 'Valor Fixo'),          # Ex: R$ 20,00 de desconto
    )

    codigo = models.CharField(max_length=50, unique=True)

    # Detalhes do Desconto
    tipo = models.CharField(max_length=15, choices=TIPO_DESCONTO, default='percentagem')
    valor_desconto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Regras de Uso
    valor_minimo_pedido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Valor mínimo do pedido para aplicar o cupom."
    )
    limite_usos = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Número máximo de vezes que este cupom pode ser usado por todos os clientes."
    )
    usos_atuais = models.IntegerField(default=0)

    # Validade
    data_inicio = models.DateTimeField(default=timezone.now)
    data_fim = models.DateTimeField()

    # Status
    ativo = models.BooleanField(default=True)

    # 🔹 NOVOS CAMPOS (restrições opcionais)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="(Opcional) Limite o cupom a uma categoria específica de produtos."
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="(Opcional) Limite o cupom a um produto específico."
    )

    class Meta:
        verbose_name = "Cupom de Desconto"
        verbose_name_plural = "Cupons de Desconto"

    def __str__(self):
        return self.codigo

    # ===============================
    # ✅ Validações e lógica de uso
    # ===============================
    def is_valid(self):
        """Verifica se o cupom está ativo e dentro do limite de datas/usos."""
        now = timezone.now()
        return (
            self.ativo and
            self.data_inicio <= now <= self.data_fim and
            self.usos_atuais < self.limite_usos
        )

    def aplica_em_produto(self, produto):
        """Verifica se o cupom pode ser aplicado ao produto informado."""
        if self.produto and produto != self.produto:
            return False
        if self.categoria and produto.categoria != self.categoria:
            return False
        return True

    def clean(self):
        """Valida regras básicas antes de salvar."""
        from django.core.exceptions import ValidationError
        if self.data_fim <= self.data_inicio:
            raise ValidationError("A data de fim deve ser posterior à data de início.")
