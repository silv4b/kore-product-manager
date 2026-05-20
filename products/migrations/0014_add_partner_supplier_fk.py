import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("partners", "0002_supplier_observations"),
        ("products", "0013_alter_supplier_contact_alter_supplier_observations"),
    ]

    operations = [
        migrations.RenameField(
            model_name="product",
            old_name="supplier",
            new_name="old_supplier",
        ),
        migrations.AddField(
            model_name="product",
            name="new_supplier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to="partners.supplier",
            ),
        ),
    ]
