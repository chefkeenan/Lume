# bookingkelas/management/commands/load_kelas.py
import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from bookingkelas.models import ClassSessions

WEEKDAY_MAP = {
    "mon": "Monday",
    "tue": "Tuesday",
    "wed": "Wednesday",
    "thur": "Thursday",
    "fri": "Friday",
    "sat": "Saturday",
}

class Command(BaseCommand):
    help = "Load kelas dataset expanded (daily per-day rows) dari CSV ke ClassSessions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            dest="csv_path",
            help="Path ke CSV (default: bookingkelas/management/data/data_kelas.csv)",
            default=os.path.join(settings.BASE_DIR, "bookingkelas", "management", "data", "data_kelas.csv")
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"CSV file not found at {csv_path}"))
            return

        created = 0
        skipped = 0

        with open(csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.reader(fh, delimiter=',', quotechar='"')
            headers = next(reader)
          
            headers = [h.strip() for h in headers]

            for row in reader:
                if not any(cell.strip() for cell in row):
                    continue

                row_map = dict(zip(headers, [c.strip() for c in row]))

                title = row_map.get("title")
                category = row_map.get("category", "daily").lower()
                instructor = row_map.get("instructor", "")
                try:
                    capacity_max = int(row_map.get("capacity_max") or 20)
                except ValueError:
                    self.stdout.write(self.style.WARNING(f"⚠️  Invalid capacity for {title}, defaulting to 20"))
                    capacity_max = 20

                description = row_map.get("description", "")
                price = int(float(row_map.get("price") or 0))  
                room = row_map.get("room", "")
                time = row_map.get("time", "")

                day_key_raw = (row_map.get("day_key") or "").strip()
                days = []

                if day_key_raw:
                    
                    if ";" in day_key_raw:
                        parts = [p.strip() for p in day_key_raw.split(";") if p.strip()]
                    elif "," in day_key_raw:
                        parts = [p.strip() for p in day_key_raw.split(",") if p.strip()]
                    else:
                        parts = [day_key_raw]

                    
                    days = [WEEKDAY_MAP.get(p.lower(), p.lower()) for p in parts]
                else:
                    days = []


                
                instance_data = {
                    "category": category,
                    "instructor": instructor,
                    "capacity_max": capacity_max,
                    "description": description,
                    "price": price,
                    "room": room,
                    "time": time,
                    "days": days,
                }


                qs_kwargs = {"title": title, "time": time}
                if category == "daily" and days:
                    qs_kwargs["days"] = days

                obj, was_created = ClassSessions.objects.get_or_create(
                    **qs_kwargs,
                    defaults=instance_data
                )
                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"Created: {title} (days={days})"))
                else:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"Skipped (exists): {title} (days={days})"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created={created} Skipped={skipped}"))
