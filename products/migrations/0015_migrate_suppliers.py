from django.db import migrations


def migrate_suppliers(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    OldSupplier = apps.get_model("products", "Supplier")
    NewSupplier = apps.get_model("partners", "Supplier")

    for product in Product.objects.select_related("old_supplier").iterator():
        old_sup = product.old_supplier
        if old_sup is None:
            continue

        defaults = {
            "email": old_sup.contact if "@" in old_sup.contact else "",
            "phone": old_sup.contact if "@" not in old_sup.contact else "",
            "observations": old_sup.observations,
        }
        new_sup, _ = NewSupplier.objects.get_or_create(
            user=old_sup.user,
            name=old_sup.name,
            defaults=defaults,
        )
        product.new_supplier = new_sup
        product.save(update_fields=["new_supplier"])


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0014_add_partner_supplier_fk"),
    ]

    operations = [
        migrations.RunPython(migrate_suppliers, reverse_code=migrations.RunPython.noop),
    ]
