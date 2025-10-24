from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0002_banner_mensagemtopo_alter_categoria_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=100, blank=True, null=True)),
                ('imagem', models.ImageField(upload_to='banners/')),
                ('link', models.URLField(blank=True, null=True, help_text="Link opcional para o banner.")),
                ('ativo', models.BooleanField(default=True)),
                ('ordem', models.PositiveIntegerField(default=1)),
                ('usar_em_carrossel', models.BooleanField(default=True, help_text="Se falso, exibe apenas um banner fixo.")),
            ],
            options={
                'ordering': ['ordem'],
                'verbose_name': 'Banner',
                'verbose_name_plural': 'Banners',
            },
        ),
        migrations.CreateModel(
            name='MensagemTopo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.CharField(max_length=255, help_text="Texto que aparecerá rolando no topo do site.")),
                ('ativo', models.BooleanField(default=True)),
                ('ordem', models.PositiveIntegerField(default=1, help_text="Define a ordem das mensagens.")),
                ('data_inicio', models.DateTimeField(blank=True, null=True)),
                ('data_fim', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['ordem'],
                'verbose_name': 'Mensagem do Topo',
                'verbose_name_plural': 'Mensagens do Topo',
            },
        ),
    ]
