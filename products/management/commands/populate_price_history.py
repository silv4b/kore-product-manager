from django.core.management.base import BaseCommand

from products.models import PriceHistory, Product


class Command(BaseCommand):
    help = "Popula o histórico de preços para produtos existentes"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING("Iniciando migração de histórico de preços...")
        )

        created_count = 0
        skipped_count = 0

        for product in Product.objects.all():
            if not product.price_history.exists():
                PriceHistory.objects.create(product=product, price=product.price)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Histórico criado para: {product.name} - R$ {product.price}"
                    )
                )
                created_count += 1
            else:
                self.stdout.write(f"- {product.name} já possui histórico")
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Migração concluída! {created_count} registros criados, {skipped_count} ignorados."
            )
        )
