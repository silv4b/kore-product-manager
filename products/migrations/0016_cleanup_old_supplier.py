from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0015_migrate_suppliers"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="old_supplier",
        ),
        migrations.DeleteModel(
            name="Supplier",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="new_supplier",
            new_name="supplier",
        ),
    ]
