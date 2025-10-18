# pedidos/models.py - CORRIGIDO
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone # Importar timezone para as datas de validade

from produtos.models import Produto, Variacao


class EnderecoEntrega(models.Model):
    nome = models.CharField(max_length=255)
    sobrenome = models.CharField(max_length=255)
    email = models.EmailField()
    cep = models.CharField(max_length=9)
    rua = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=255, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)

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
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Aguardando Pagamento')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Rastreamento
    codigo_rastreio = models.CharField(max_length=100, blank=True, null=True)

    data_criacao = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Pedido #{self.id}'


class ItemPedido(models.Model):
    # Use a string completa 'pedidos.Pedido'
    pedido = models.ForeignKey(
        'pedidos.Pedido', 
        on_delete=models.CASCADE, 
        related_name='itens'
    )
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, related_name='itens_pedido')
    variacao = models.ForeignKey(Variacao, on_delete=models.SET_NULL, null=True, blank=True)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=1)

    def get_subtotal(self):
        return self.preco_unitario * self.quantidade

    def __str__(self):
        # Proteção contra Server Error (500) por Produto/Variação deletados
        
        # 1. Tenta obter o nome do produto ou variação
        if self.variacao and self.variacao.valor:
            # Garante que o produto também existe para evitar erro
            nome_produto = self.produto.nome if self.produto else "Deletado"
            nome_display = f"{nome_produto} ({self.variacao.valor})"
        elif self.produto:
            nome_display = self.produto.nome
        else:
            nome_display = "Produto Deletado/Inválido"
            
        return f'{self.quantidade}x {nome_display} (Pedido {self.pedido.id})'


# >> NOVO MODELO: CUPOM DE DESCONTO <<
class Cupom(models.Model):
    TIPO_DESCONTO = (
        ('percentagem', 'Percentagem'), # Ex: 10% de desconto
        ('fixo', 'Valor Fixo'),        # Ex: R$ 20,00 de desconto
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
    
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cupom de Desconto"
        verbose_name_plural = "Cupons de Desconto"

    def __str__(self):
        return self.codigo

    def is_valid(self):
        """Verifica se o cupom está ativo e dentro do limite de datas/usos."""
        now = timezone.now()
        return (self.ativo and 
                self.data_inicio <= now and 
                self.data_fim >= now and
                self.usos_atuais < self.limite_usos)
