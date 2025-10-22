from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL("-- Recriada manualmente para restaurar dependência perdida."),
    ]
