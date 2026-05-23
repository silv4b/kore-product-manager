import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0018_alter_product_status_alter_product_unidade_medida"),
    ]

    operations = [
        migrations.CreateModel(
            name="Stock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantidade_atual", models.IntegerField(default=0, verbose_name="Quantidade Atual")),
                ("quantidade_reservada", models.IntegerField(default=0, verbose_name="Quantidade Reservada")),
                ("estoque_minimo", models.IntegerField(default=0, verbose_name="Estoque Mínimo")),
                ("estoque_maximo", models.IntegerField(blank=True, null=True, verbose_name="Estoque Máximo")),
                ("lote", models.CharField(blank=True, default="", max_length=50, verbose_name="Lote")),
                ("data_validade", models.DateField(blank=True, null=True, verbose_name="Data de Validade")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("local", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stocks", to="products.storagelocation")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stocks", to="products.product")),
            ],
            options={
                "verbose_name": "Estoque",
                "verbose_name_plural": "Estoques",
                "unique_together": {("product", "local")},
            },
        ),
    ]
