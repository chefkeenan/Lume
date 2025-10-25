from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock


class MainBase(TestCase):
    def setUp(self):
        self.client = Client()



class FakeItem:
    def __init__(self, id_hex, name, desc, price):
        self.id = f"{id_hex[0:8]}-{id_hex[8:12]}-{id_hex[12:16]}-{id_hex[16:20]}-{id_hex[20:32]}"
        self.product_name = name
        self.description = desc
        self.price = price


class FakeQS:
    def __init__(self, items):
        self._items = list(items)

    def _clone(self, items):
        return FakeQS(items)

    def all(self):
        return self

    def filter(self, *args, **kwargs):
        items = self._items
        if "price__gte" in kwargs:
            lo = kwargs["price__gte"]
            items = [x for x in items if x.price >= lo]
        if "price__lt" in kwargs:
            hi = kwargs["price__lt"]
            items = [x for x in items if x.price < hi]
        term = None
        for k, v in kwargs.items():
            if k.endswith("__icontains"):
                term = str(v).lower()
        if not term and args:
            q = args[0]
            children = getattr(q, "children", None)
            if children:
                for (k, v) in children:
                    if k.endswith("__icontains"):
                        term = str(v).lower()
                        break
        if term:
            items = [x for x in items if term in x.product_name.lower() or term in x.description.lower()]
        return self._clone(items)

    def order_by(self, *fields):
        items = self._items
        for field in reversed(fields):
            rev = field.startswith("-")
            key = field[1:] if rev else field
            if key == "price":
                items = sorted(items, key=lambda x: x.price, reverse=rev)
            elif key == "id":
                items = sorted(items, key=lambda x: x.id, reverse=rev)
        return self._clone(items)

    def count(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, sl):
        return self._items[sl]


class ShowMainTests(MainBase):
    @patch("main.views.Product")
    def test_show_main_basic_pagination_and_total(self, Product):
        items = [FakeItem(f"{i:032x}", f"Prod {i}", "desc", price=1000 * i) for i in range(1, 21)]
        qs = FakeQS(items)
        Product.objects.all.return_value = qs
        resp = self.client.get(reverse("main:show_main"), {"page": 1})
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertIn("page_obj", ctx)
        self.assertEqual(ctx["total_found"], 20)
        self.assertEqual(len(ctx["page_obj"].object_list), 12)

    @patch("main.views.Product")
    def test_show_main_search_q(self, Product):
        items = [
            FakeItem(f"{1:032x}", "Yoga Mat", "Good mat", 150000),
            FakeItem(f"{2:032x}", "Bottle", "Water bottle", 80000),
        ]
        qs = FakeQS(items)
        Product.objects.all.return_value = qs
        resp = self.client.get(reverse("main:show_main"), {"q": "yoga"})
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertEqual(ctx["total_found"], 1)
        self.assertEqual(ctx["page_obj"].object_list[0].product_name, "Yoga Mat")

    @patch("main.views.Product")
    def test_show_main_price_filter_and_order(self, Product):
        items = [
            FakeItem(f"{1:032x}", "A", "x", 150_000),
            FakeItem(f"{2:032x}", "B", "x", 300_000),
            FakeItem(f"{3:032x}", "C", "x", 700_000),
            FakeItem(f"{4:032x}", "D", "x", 1_500_000),
            FakeItem(f"{5:032x}", "E", "x", 6_000_000),
        ]
        qs = FakeQS(items)
        Product.objects.all.return_value = qs
        resp = self.client.get(reverse("main:show_main"), {"price": "200k-500k", "order": "-price"})
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertEqual(ctx["total_found"], 1)
        objs = ctx["page_obj"].object_list
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0].price, 300_000)
        resp2 = self.client.get(reverse("main:show_main"), {"price": "5m+"})
        self.assertEqual(resp2.context["total_found"], 1)
        self.assertEqual(resp2.context["page_obj"].object_list[0].price, 6_000_000)


class LandingHighlightsTests(MainBase):
    @patch("main.views.render_to_string")
    @patch("main.views.Product")
    def test_landing_highlights_respects_exclude_and_count(self, Product, render_to_string):
        p1 = MagicMock()
        p1.id = 101
        p2 = MagicMock()
        p2.id = 102
        qs = MagicMock()
        Product.objects.filter.return_value = qs
        qs.exclude.return_value = qs
        qs.order_by.return_value = [p1, p2]
        render_to_string.side_effect = [
            "<div>card101</div>",
            "<div>card102</div>",
        ]
        resp = self.client.get(
            reverse("main:landing_highlights"),
            {"exclude": "10,101", "count": "2"},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["count"], 2)
        self.assertIn("wrap-101", payload["cards"][0])
        self.assertIn("card101", payload["cards"][0])
        self.assertIn("wrap-102", payload["cards"][1])
        self.assertIn("card102", payload["cards"][1])
