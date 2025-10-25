from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('carrinho', '0002_auto_20251022_1411'),  # ajuste se sua última migração tiver outro nome
    ]

    operations = [
        migrations.AddField(
            model_name='itemcarrinho',
            name='preco',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
    ]
