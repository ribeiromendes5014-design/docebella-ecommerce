from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('carrinho', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemcarrinho',
            name='preco',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
    ]
