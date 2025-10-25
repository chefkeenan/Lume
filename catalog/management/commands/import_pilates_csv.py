import csv
import re
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import Product
from django.conf import settings

def _clean_price(v):
    if v is None:
        return None
    s = str(v).strip()
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else None

def _strip_keys(row: dict):
    return {(k.strip() if isinstance(k, str) else k): v for k, v in row.items()}

def _coalesce_description(row: dict) -> str:
    parts = []
    ks = (row.get("key_specs") or "").strip()
    if ks:
        parts.append(ks)
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
    help = "Import produk ke catalog.Product dari file CSV."

    def add_arguments(self, parser):
        default_csv = Path(settings.BASE_DIR) / "catalog" / "management" / "data" / "dataset_pilates.csv"
        parser.add_argument(
            "csv_path",
            nargs="?",
            default=str(default_csv),
            type=str,
            help=f"Path ke file CSV. (optional) Default: {default_csv}",
        )
        parser.add_argument(
            "--dedupe-by",
            default="external_id",
            help="Field untuk pencocokan update_or_create. Contoh: external_id ATAU product_name,thumbnail,price",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Jalankan tanpa commit (cek hasil dulu).",
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
            external_id = (row.get("id") or "").strip() or None
            product_name = (row.get("product_name") or "").strip()
            thumbnail = (row.get("image_url") or row.get("thumbnail") or "").strip() or None
            price = _clean_price(row.get("price"))
            stock = 1
            in_stock = True if stock and stock > 0 else False
            description = _coalesce_description(row)

            if not product_name:
                skipped += 1
                continue

            lookup = {}
            for f in dedupe_fields:
                if f == "external_id":
                    lookup["external_id"] = external_id
                elif f == "product_name":
                    lookup["product_name"] = product_name
                elif f == "price":
                    lookup["price"] = price
                elif f == "thumbnail":
                    lookup["thumbnail"] = thumbnail
                else:
                    pass

            if not lookup:
                lookup = {"external_id": external_id} if external_id else {"product_name": product_name}

            defaults = {
                "product_name": product_name,
                "stock": stock,
                "inStock": in_stock,
                "thumbnail": thumbnail,
                "description": description,
                "price": price,
                "external_id": external_id,  
            }

            obj, was_created = Product.objects.update_or_create(defaults=defaults, **lookup)
            if was_created:
                created += 1
            else:
                updated += 1

        if dry_run:
            transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING("Dry-run aktif: semua perubahan akan dibatalkan (rollback)."))
            self.stdout.write(self.style.SUCCESS(f"Preview selesai. created={created}, updated={updated}, skipped={skipped}"))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Import selesai. created={created}, updated={updated}, skipped={skipped}"
        ))