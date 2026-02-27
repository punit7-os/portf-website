import csv
from django.core.management.base import BaseCommand
from shop.models import Category, Product
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Import products from CSV file safely"

    def handle(self, *args, **options):
        file_path = "shop/fixtures/products4.csv"

        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                category_name = row["Category"].strip()

                # ✅ SAFE CATEGORY HANDLING
                category = Category.objects.filter(name=category_name).first()
                if not category:
                    category = Category.objects.create(
                        name=category_name,
                        slug=slugify(category_name)
                    )

                # ✅ SAFE PRODUCT UPSERT
                Product.objects.update_or_create(
                    slug=row["Slug"].strip(),
                    defaults={
                        "category": category,
                        "name": row["Name"].strip(),
                        "description": row["Description"].strip(),
                        "price": row["Price"],
                        "image_url": row["Image_URLs"].strip(),
                        "is_active": row["Active"].strip().lower() == "yes",
                    }
                )

        self.stdout.write(self.style.SUCCESS("✅ Products imported successfully"))
