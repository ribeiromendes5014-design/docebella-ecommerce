from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("produtos", "0004_alter_categoria_options_alter_variacao_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="variacao",
            name="parent",
            field=models.ForeignKey(
                to="produtos.variacao",
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                blank=True,
                related_name="child_variations",
            ),
        ),
    ]
