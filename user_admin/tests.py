from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal

User = get_user_model()


@override_settings(LOGIN_URL="/user/login/")
class AdminViewsAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", password="pass")
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)

    # ---- dashboard ----
    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("useradmin:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/user/login/", resp.url)

    def test_dashboard_requires_staff(self):
        self.client.login(username="user", password="pass")
        resp = self.client.get(reverse("useradmin:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/user/login/", resp.url)

    def test_dashboard_ok_for_staff(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(reverse("useradmin:dashboard"))
        self.assertEqual(resp.status_code, 200)

    # ---- api endpoints require staff ----
    def test_api_requires_staff(self):
        # logout
        self.client.logout()
        for name in ["useradmin:api_stats", "useradmin:api_users", "useradmin:api_orders",
                     "useradmin:api_bookings", "useradmin:api_activity"]:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/user/login/", resp.url)

        # login as non-staff
        self.client.login(username="user", password="pass")
        for name in ["useradmin:api_stats", "useradmin:api_users", "useradmin:api_orders",
                     "useradmin:api_bookings", "useradmin:api_activity"]:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/user/login/", resp.url)


@override_settings(LOGIN_URL="/user/login/")
class AdminApiStatsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.client.login(username="admin", password="pass")

    @patch("user_admin.views.BookingOrder")
    @patch("user_admin.views.ProductOrder")
    @patch("user_admin.views.User")
    @patch("user_admin.views.Booking")
    def test_api_stats_json(self, BookingModel, UserModel, ProductOrder, BookingOrder):
        ProductOrder.objects.aggregate.return_value = {"s": Decimal("125000")}
        BookingOrder.objects.aggregate.return_value = {"s": Decimal("75000")}
        ProductOrder.objects.count.return_value = 9
        UserModel.objects.count.return_value = 12
        BookingModel.objects.count.return_value = 8

        resp = self.client.get(reverse("useradmin:api_stats"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["total_income"], "200000.00")
        self.assertEqual(payload["data"]["total_orders"], 9)
        self.assertEqual(payload["data"]["total_users"], 12)
        self.assertEqual(payload["data"]["total_bookings"], 8)

    @patch("user_admin.views.BookingOrder")
    @patch("user_admin.views.ProductOrder")
    @patch("user_admin.views.User")
    @patch("user_admin.views.Booking")
    def test_api_stats_handles_none_aggregates(self, BookingModel, UserModel, ProductOrder, BookingOrder):
        ProductOrder.objects.aggregate.return_value = {"s": None}
        BookingOrder.objects.aggregate.return_value = {"s": None}
        ProductOrder.objects.count.return_value = 0
        UserModel.objects.count.return_value = 0
        BookingModel.objects.count.return_value = 0

        resp = self.client.get(reverse("useradmin:api_stats"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["total_income"], "0.00")


@override_settings(LOGIN_URL="/user/login/")
class AdminApiUsersTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.client.login(username="admin", password="pass")

    @patch("user_admin.views.User")
    def test_api_users_list(self, UserModel):
        u1 = MagicMock()
        u1.id = 1
        u1.username = "keenan"
        u1.email = "k@example.com"
        u1.phone = "0812"
        u1.date_joined = self.staff.date_joined
        u1.total_orders = 3
        u1.total_bookings = 2
        u1.is_active = True

        u2 = MagicMock()
        u2.id = 2
        u2.username = "adi"
        u2.email = ""
        u2.phone = ""
        u2.date_joined = self.staff.date_joined
        u2.total_orders = 0
        u2.total_bookings = 0
        u2.is_active = False

        qs = MagicMock()
        qs.filter.return_value = qs
        qs.annotate.return_value = qs
        qs.order_by.return_value = [u1, u2]
        UserModel.objects.all.return_value = qs

        resp = self.client.get(reverse("useradmin:api_users"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["users"]), 2)
        self.assertEqual(payload["users"][0]["username"], "keenan")
        self.assertEqual(payload["users"][1]["status"], "inactive")
        # format date
        self.assertIn("join_date", payload["users"][0])
        self.assertRegex(payload["users"][0]["join_date"], r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")

    @patch("user_admin.views.User")
    def test_api_users_search_filters(self, UserModel):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.annotate.return_value = qs
        qs.order_by.return_value = []
        UserModel.objects.all.return_value = qs

        resp = self.client.get(reverse("useradmin:api_users"), {"q": "keen"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(qs.filter.called)
        _, kwargs = qs.filter.call_args
        self.assertIn("username__icontains", kwargs)

    @patch("user_admin.views.User")
    def test_api_users_empty(self, UserModel):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.annotate.return_value = qs
        qs.order_by.return_value = []
        UserModel.objects.all.return_value = qs

        resp = self.client.get(reverse("useradmin:api_users"), {"q": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["users"], [])


@override_settings(LOGIN_URL="/user/login/")
class AdminApiOrdersTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.client.login(username="admin", password="pass")

    @patch("user_admin.views.ProductOrder")
    def test_api_orders_shapes_line_items(self, ProductOrder):
        user = MagicMock()
        user.id = 10
        user.username = "keenan"
        user.email = "k@example.com"

        item = MagicMock()
        item.price = 10000
        item.quantity = 2
        item.line_total = None
        item.product_name = "Mat"
        item.product = None

        order = MagicMock()
        order.id = 55
        order.user_id = 10
        order.user = user
        order.total = Decimal("30000")
        order.created_at = self.staff.date_joined
        order.items.all.return_value = [item]

        qs = MagicMock()
        qs.select_related.return_value = qs
        qs.prefetch_related.return_value = qs
        qs.order_by.return_value = [order]
        ProductOrder.objects.select_related.return_value = qs

        resp = self.client.get(reverse("useradmin:api_orders"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["orders"]), 1)
        o = data["orders"][0]
        self.assertEqual(o["user_name"], "keenan")
        self.assertEqual(o["amount"], 30000)
        self.assertEqual(o["line_items"][0]["subtotal"], 20000)

    @patch("user_admin.views.ProductOrder")
    def test_api_orders_edge_cases_names_prices(self, ProductOrder):
        user = MagicMock()
        user.username = "adi"
        # Item 1: price None -> use unit_price, qty str, name from related product
        prod = MagicMock()
        prod.product_name = "Band"
        it1 = MagicMock()
        it1.price = None
        it1.unit_price = 15000
        it1.quantity = "3"
        it1.line_total = None
        it1.product_name = None
        it1.product = prod
        # Item 2: line_total already computed -> use that
        it2 = MagicMock()
        it2.price = 999999  # ignored by line_total
        it2.quantity = 1
        it2.line_total = 12345
        it2.product_name = "Bottle"
        it2.product = None
        # Item 3: malformed price -> except path -> subtotal 0, amount 0 handling
        it3 = MagicMock()
        it3.price = "abc"
        it3.quantity = None
        it3.line_total = None
        it3.product_name = None
        it3.product = None

        order = MagicMock()
        order.id = 77
        order.user_id = 2
        order.user = user
        order.total = None  # amount fallback to 0
        order.created_at = self.staff.date_joined
        order.items.all.return_value = [it1, it2, it3]

        qs = MagicMock()
        qs.select_related.return_value = qs
        qs.prefetch_related.return_value = qs
        qs.order_by.return_value = [order]
        ProductOrder.objects.select_related.return_value = qs

        resp = self.client.get(reverse("useradmin:api_orders"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        o = payload["orders"][0]
        self.assertEqual(o["amount"], 0)  # total None -> 0
        lines = o["line_items"]
        # it1: unit_price*qty
        self.assertEqual(lines[0]["name"], "Band")
        self.assertEqual(lines[0]["price"], 15000)
        self.assertEqual(lines[0]["subtotal"], 45000)
        # it2: line_total respected
        self.assertEqual(lines[1]["name"], "Bottle")
        self.assertEqual(lines[1]["subtotal"], 12345)
        # it3: malformed -> subtotal 0, name "-"
        self.assertEqual(lines[2]["name"], "-")
        self.assertEqual(lines[2]["subtotal"], 0)

    @patch("user_admin.views.ProductOrder")
    def test_api_orders_empty(self, ProductOrder):
        qs = MagicMock()
        qs.select_related.return_value = qs
        qs.prefetch_related.return_value = qs
        qs.order_by.return_value = []
        ProductOrder.objects.select_related.return_value = qs

        resp = self.client.get(reverse("useradmin:api_orders"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["orders"], [])


@override_settings(LOGIN_URL="/user/login/")
class AdminApiBookingsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.client.login(username="admin", password="pass")

    @patch("user_admin.views.Booking")
    def test_api_bookings_json(self, BookingModel):
        user = MagicMock()
        user.id = 7
        user.username = "keenan"

        session = MagicMock()
        session.title = "Yoga Flow"
        session.instructor = "Coach A"

        b = MagicMock()
        b.id = 101
        b.user = user
        b.user_id = 7
        b.session = session
        b.created_at = self.staff.date_joined
        b.is_cancelled = False

        qs = MagicMock()
        qs.select_related.return_value = qs
        qs.order_by.return_value = [b]
        BookingModel.objects.select_related.return_value = qs

        resp = self.client.get(reverse("useradmin:api_bookings"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["bookings"][0]["class_name"], "Yoga Flow")
        self.assertEqual(payload["bookings"][0]["status"], "completed")

    @patch("user_admin.views.Booking")
    def test_api_bookings_instructor_fallback_and_cancelled(self, BookingModel):
        user = MagicMock()
        user.username = "adi"

        session = MagicMock()
        session.title = "Pilates"
        session.instructor = ""  # fallback ke ""

        b = MagicMock()
        b.id = 202
        b.user = user
        b.user_id = 9
        b.session = session
        b.created_at = self.staff.date_joined
        b.is_cancelled = True

        qs = MagicMock()
        qs.select_related.return_value = qs
        qs.order_by.return_value = [b]
        BookingModel.objects.select_related.return_value = qs

        resp = self.client.get(reverse("useradmin:api_bookings"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        row = payload["bookings"][0]
        self.assertEqual(row["instructor"], "")
        self.assertEqual(row["status"], "cancelled")

    @patch("user_admin.views.Booking")
    def test_api_bookings_empty(self, BookingModel):
        qs = MagicMock()
        qs.select_related.return_value = qs
        qs.order_by.return_value = []
        BookingModel.objects.select_related.return_value = qs

        resp = self.client.get(reverse("useradmin:api_bookings"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["bookings"], [])


@override_settings(LOGIN_URL="/user/login/")
class AdminApiActivityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.client.login(username="admin", password="pass")

    @patch("user_admin.views.Booking")
    @patch("user_admin.views.ProductOrder")
    def test_api_activity_merged_and_sorted(self, ProductOrder, BookingModel):
        u1 = MagicMock()
        u1.username = "keenan"
        o1 = MagicMock()
        o1.user = u1
        o1.total = Decimal("50000")
        o1.created_at = self.staff.date_joined

        u2 = MagicMock()
        u2.username = "adi"
        s = MagicMock()
        s.title = "Pilates"
        b1 = MagicMock()
        b1.user = u2
        b1.session = s
        b1.created_at = self.staff.date_joined
        b1.is_cancelled = True

        po_qs = MagicMock()
        po_qs.select_related.return_value = po_qs
        po_qs.order_by.return_value = [o1]
        ProductOrder.objects.select_related.return_value = po_qs

        bk_qs = MagicMock()
        bk_qs.select_related.return_value = bk_qs
        bk_qs.order_by.return_value = [b1]
        BookingModel.objects.select_related.return_value = bk_qs

        resp = self.client.get(reverse("useradmin:api_activity"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertGreaterEqual(len(payload["activity"]), 1)
        types = {a["type"] for a in payload["activity"]}
        self.assertTrue({"order", "booking"}.issubset(types))
        order_row = next(a for a in payload["activity"] if a["type"] == "order")
        self.assertIn("Rp", order_row["subtitle"])
        self.assertIn(".", order_row["subtitle"])

    @patch("user_admin.views.Booking")
    @patch("user_admin.views.ProductOrder")
    def test_api_activity_empty(self, ProductOrder, BookingModel):
        po_qs = MagicMock()
        po_qs.select_related.return_value = po_qs
        po_qs.order_by.return_value = []
        ProductOrder.objects.select_related.return_value = po_qs

        bk_qs = MagicMock()
        bk_qs.select_related.return_value = bk_qs
        bk_qs.order_by.return_value = []
        BookingModel.objects.select_related.return_value = bk_qs

        resp = self.client.get(reverse("useradmin:api_activity"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["activity"], [])
