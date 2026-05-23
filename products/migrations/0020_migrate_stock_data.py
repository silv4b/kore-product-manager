from django.db import migrations


def migrate_stock_data(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Stock = apps.get_model("products", "Stock")
    StorageLocation = apps.get_model("products", "StorageLocation")
    db_alias = schema_editor.connection.alias

    for product in Product.objects.using(db_alias).iterator():
        # Fields still exist at this migration stage
        if product.stock > 0 or product.min_stock_level > 0:
            default_local = StorageLocation.objects.using(db_alias).filter(
                user=product.user, is_active=True
            ).first()

            if default_local:
                Stock.objects.using(db_alias).create(
                    product=product,
                    local=default_local,
                    quantidade_atual=product.stock or 0,
                    estoque_minimo=product.min_stock_level or 0,
                )


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0019_create_stock_model"),
    ]

    operations = [
        migrations.RunPython(migrate_stock_data, reverse_code=migrations.RunPython.noop),
    ]
