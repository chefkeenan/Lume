# catalog/management/commands/import_catalog_csv.py
import csv
import re
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import Product

def _clean_price(v):
    """
    Normalisasi harga:
    - Terima '1000000', '1.000.000', 'Rp 1.000.000', ' Rp1,000,000 ' -> int rupiah
    - Kosong -> None
    """
    if v is None:
        return None
    s = str(v).strip()
    # buang semua char non-digit
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else None

def _strip_keys(row: dict):
    # rapikan nama kolom (CSV lo punya " price" dengan spasi di depan)
    return {(k.strip() if isinstance(k, str) else k): v for k, v in row.items()}

def _coalesce_description(row: dict) -> str:
    """
    Susun description dari kolom CSV yang relevan:
    - key_specs kalau ada
    - plus ringkasan brand/category/variant/marketplace/source_url
    """
    parts = []
    ks = (row.get("key_specs") or "").strip()
    if ks:
        parts.append(ks)

    # ringkas metadata jadi paragraf kedua
    meta = []
    if row.get("brand"):
        meta.append(f"Brand: {row.get('brand')}")
    if row.get("category"):
        meta.append(f"Kategori: {row.get('category')}")
    if row.get("variant"):
        meta.append(f"Varian: {row.get('variant')}")
    if row.get("marketplace"):
        meta.append(f"Marketplace: {row.get('marketplace')}")
    if row.get("source_url"):
        meta.append(f"Sumber: {row.get('source_url')}")
    if meta:
        parts.append(" | ".join(meta))

    desc = "\n\n".join([p for p in parts if p])
    return desc or (row.get("product_name") or "").strip()

class Command(BaseCommand):
    help = "Import produk ke catalog.Product dari file CSV (pilates_products_100.csv)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path ke file CSV.")
        # strategi dedupe default: kombinasi product_name+price
        parser.add_argument(
            "--dedupe-by",
            default="product_name,price",
            help="Field untuk pencocokan update_or_create, koma-separate. Default: product_name,price",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Jalankan tanpa commit (untuk cek hasil dulu).",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        csv_path = Path(opts["csv_path"])
        if not csv_path.exists():
            raise CommandError(f"CSV tidak ditemukan: {csv_path}")

        dedupe_fields = [f.strip() for f in str(opts["dedupe_by"]).split(",") if f.strip()]
        dry_run = opts["dry_run"]

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        created, updated, skipped = 0, 0, 0

        for raw in rows:
            row = _strip_keys(raw)
            # alias " price" -> "price" bila perlu
            if "price" not in row and " price" in row:
                row["price"] = row[" price"]

            # mapping kolom CSV -> field model
            product_name = (row.get("product_name") or "").strip()
            thumbnail = (row.get("image_url") or row.get("thumbnail") or "").strip() or None
            price = _clean_price(row.get("price"))
            # stock gak ada di CSV lo -> default 1
            stock = 1
            in_stock = True if stock and stock > 0 else False
            description = _coalesce_description(row)

            if not product_name:
                skipped += 1
                continue

            # siapkan lookup untuk upsert (update_or_create)
            lookup = {}
            for f in dedupe_fields:
                if f == "product_name":
                    lookup["product_name"] = product_name
                elif f == "price":
                    lookup["price"] = price
                elif f == "thumbnail":
                    lookup["thumbnail"] = thumbnail
                else:
                    # kalau field dedupe gak dikenali, di-skip
                    pass

            defaults = {
                "stock": stock,
                "inStock": in_stock,
                "thumbnail": thumbnail,
                "description": description,
                "price": price,
            }

            if not lookup:
                # fallback: minimal product_name
                lookup = {"product_name": product_name}

            obj, was_created = Product.objects.update_or_create(defaults=defaults, **lookup)
            if was_created:
                created += 1
            else:
                updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run aktif: semua perubahan dibatalkan."))
            raise CommandError(f"Preview selesai. created={created}, updated={updated}, skipped={skipped}")

        self.stdout.write(self.style.SUCCESS(
            f"Import selesai. created={created}, updated={updated}, skipped={skipped}"
        ))
