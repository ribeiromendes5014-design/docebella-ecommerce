# Generated manually because original migration was missing

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='metodo_envio',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('Entrega Padrão', 'Entrega Padrão'),
                    ('Retirada na Loja', 'Retirada na Loja'),
                ],
                default='Entrega Padrão',
            ),
        ),
        migrations.AlterField(
            model_name='enderecoentrega',
            name='bairro',
            field=models.CharField(max_length=120, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='enderecoentrega',
            name='numero',
            field=models.CharField(max_length=10, blank=True, null=True),
        ),
    ]
