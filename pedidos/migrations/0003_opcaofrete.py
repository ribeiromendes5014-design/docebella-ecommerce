from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # O último arquivo de migração do app 'pedidos' que o Django usou
        ('pedidos', '0002_initial'), 
    ]

    operations = [
        migrations.CreateModel(
            name='OpcaoFrete',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True, blank=True)),
                ('custo', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('ativo', models.BooleanField(default=True)),
            ],
        ),
