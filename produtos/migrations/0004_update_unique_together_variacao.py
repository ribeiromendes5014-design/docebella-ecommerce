from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0005_add_cor_field_fix'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='variacao',
            unique_together={('produto', 'tipo', 'valor', 'cor')},
        ),
    ]
