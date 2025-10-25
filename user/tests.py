from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class _BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.username = "keenan"
        self.password = "S3cret_pass!"
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def _attach_messages(self, request):
        setattr(request, "session", self.client.session)
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request


class UtilsTests(_BaseTestCase):
    def test_is_ajax_header(self):
        from user import views as v
        req = self.factory.post("/user/login/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertTrue(v._is_ajax(req))

    def test_is_ajax_post_field(self):
        from user import views as v
        req = self.factory.post("/user/login/", data={"ajax": "1"})
        self.assertTrue(v._is_ajax(req))

    def test_safe_next_valid_and_ignores_login_and_self(self):
        from user import views as v

        req1 = self.factory.get("/user/login/", {"next": "/protected/"})
        self.assertEqual(v._safe_next(req1), "/protected/")

        req2 = self.factory.get(reverse("user:login"), {"next": reverse("user:login")})
        self.assertEqual(v._safe_next(req2), reverse("main:landing"))

        path = "/user/login/"
        req3 = self.factory.get(path, {"next": path})
        self.assertEqual(v._safe_next(req3), reverse("main:landing"))

        req4 = self.factory.get("/user/login/")
        self.assertEqual(v._safe_next(req4), reverse("main:landing"))

class LoginViewTests(_BaseTestCase):
    def test_login_get_renders_form(self):
        resp = self.client.get(reverse("user:login"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)

    def test_login_success_html_redirect(self):
        resp = self.client.post(reverse("user:login"), {"username": self.username, "password": self.password})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("main:landing"))

    def test_login_success_ajax_json(self):
        resp = self.client.post(
            reverse("user:login"),
            {"username": self.username, "password": self.password, "ajax": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("redirect_url", data)

    def test_login_failure_ajax_returns_400_and_errors(self):
        resp = self.client.post(
            reverse("user:login"),
            {"username": self.username, "password": "wrong", "ajax": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data.get("ok"))
        self.assertIn("errors", data)

    def test_login_failure_html_rerenders_form(self):
        resp = self.client.post(
            reverse("user:login"),
            {"username": self.username, "password": "wrong"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)


class RegisterViewTests(_BaseTestCase):
    def test_register_get_renders_form(self):
        resp = self.client.get(reverse("user:register"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)

    def test_register_success_ajax_uses_mock_form(self):
        from user import views as v

        class FakeForm:
            def __init__(self, *args, **kwargs): pass
            def is_valid(self): return True
            def save(self): return User.objects.create_user(username="newuser", password="Abc12345!")

        with patch.object(v, "RegisterForm", FakeForm):
            resp = self.client.post(
                reverse("user:register"),
                {"username": "newuser", "password1": "Abc12345!", "password2": "Abc12345!", "ajax": "1"},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.json().get("ok"))
            self.assertEqual(resp.json().get("redirect_url"), reverse("main:landing"))

    def test_register_success_html_redirect(self):
        from user import views as v

        class FakeForm:
            def __init__(self, *args, **kwargs): pass
            def is_valid(self): return True
            def save(self): return User.objects.create_user(username="another", password="Abc12345!")

        with patch.object(v, "RegisterForm", FakeForm):
            resp = self.client.post(
                reverse("user:register"),
                {"username": "another", "password1": "Abc12345!", "password2": "Abc12345!"},
            )
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.url, reverse("main:landing"))

    def test_register_invalid_ajax_returns_400(self):
        from user import views as v

        class BadForm:
            errors = {"username": ["required"]}
            def __init__(self, *args, **kwargs): pass
            def is_valid(self): return False
            def non_field_errors(self): return []

        with patch.object(v, "RegisterForm", BadForm):
            resp = self.client.post(
                reverse("user:register"),
                {"username": "", "ajax": "1"},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(resp.status_code, 400)
            self.assertFalse(resp.json().get("ok"))
            self.assertIn("errors", resp.json())

    def test_register_invalid_html_rerenders_form(self):
        from user import views as v

        class BadForm:
            errors = {"username": ["required"]}
            def __init__(self, *args, **kwargs): pass
            def is_valid(self): return False
            def non_field_errors(self): return []

        with patch.object(v, "RegisterForm", BadForm):
            resp = self.client.post(reverse("user:register"), {"username": ""})
            self.assertEqual(resp.status_code, 200)
            self.assertIn("form", resp.context)


class LogoutViewTests(_BaseTestCase):
    def test_logout_redirects_to_landing(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(reverse("user:logout"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("main:landing"))


class MyProfileAuthTests(_BaseTestCase):
    @override_settings(LOGIN_URL="/user/login/")
    def test_my_profile_requires_login(self):
        resp = self.client.get(reverse("user:my_profile"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/user/login/", resp.url)


class MyProfileViewTests(_BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)

    def _mock_product_orders_minimal(self):
        order = MagicMock()
        order.id = 11
        order.created_at = self.user.date_joined
        order.total = 123456

        item = MagicMock()
        item.price = 10000
        item.quantity = 2
        item.line_total = None
        item.product_name = "Mat"
        item.product = None
        order.items.all.return_value = [item]
        return [order]

    def _mock_booking_items_minimal(self):
        boi = MagicMock()
        boi.session_title = "Yoga A"
        boi.booking = MagicMock()
        boi.booking.session = MagicMock()
        boi.booking.session.instructor = "Lume Coach"
        boi.order = MagicMock()
        boi.occurrence_date = None
        boi.occurrence_start_time = "09:00"
        return [boi]

    @patch("user.views.BookingOrderItem")
    @patch("user.views.ProductOrder")
    def test_my_profile_get_renders_context(self, PO, BOI):
        qs_po = MagicMock()
        qs_po.prefetch_related.return_value = qs_po
        qs_po.order_by.return_value = self._mock_product_orders_minimal()
        PO.objects.filter.return_value = qs_po

        qs_boi = MagicMock()
        qs_boi.select_related.return_value = qs_boi
        qs_boi.order_by.return_value = self._mock_booking_items_minimal()
        BOI.objects.filter.return_value = qs_boi

        resp = self.client.get(reverse("user:my_profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("member_since", resp.context)
        self.assertIn("orders", resp.context)
        self.assertIn("bookings", resp.context)
        self.assertTrue(isinstance(resp.context["orders"], list))
        self.assertTrue(isinstance(resp.context["bookings"], list))

    @patch("user.views.ProfileForm")
    def test_my_profile_post_updates_profile_and_redirects(self, ProfileForm):
        form = MagicMock()
        form.is_valid.return_value = True
        ProfileForm.return_value = form

        resp = self.client.post(reverse("user:my_profile"), {"username": "newname"})
        self.assertTrue(form.save.called)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("user:my_profile"))

    @patch("user.views.ProfileForm")
    def test_my_profile_post_invalid_rerenders(self, ProfileForm):
        form = MagicMock()
        form.is_valid.return_value = False
        ProfileForm.return_value = form

        resp = self.client.post(reverse("user:my_profile"), {"username": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)

    @patch("user.views.BookingOrderItem")
    @patch("user.views.ProductOrder")
    def test_my_profile_orders_edge_cases(self, PO, BOI):

        prod = MagicMock()
        prod.product_name = "Band"

        it1 = MagicMock()
        it1.price = None
        it1.unit_price = 15000
        it1.quantity = "3"
        it1.line_total = None
        it1.product_name = None
        it1.product = prod

        it2 = MagicMock()
        it2.price = 999999
        it2.quantity = 1
        it2.line_total = 12345
        it2.product_name = "Bottle"
        it2.product = None

        it3 = MagicMock()
        it3.price = 5000
        it3.quantity = None
        it3.line_total = None
        it3.product_name = None
        it3.product = None

        order = MagicMock()
        order.id = 77
        order.created_at = timezone.now()
        order.total = None
        order.items.all.return_value = [it1, it2, it3]

        qs_po = MagicMock()
        qs_po.prefetch_related.return_value = qs_po
        qs_po.order_by.return_value = [order]
        PO.objects.filter.return_value = qs_po

        qs_boi = MagicMock()
        qs_boi.select_related.return_value = qs_boi
        qs_boi.order_by.return_value = []
        BOI.objects.filter.return_value = qs_boi

        resp = self.client.get(reverse("user:my_profile"))
        self.assertEqual(resp.status_code, 200)
        orders = resp.context["orders"]
        self.assertEqual(len(orders), 1)
        o = orders[0]
        self.assertEqual(o["total"], 0)

        lines = o["line_items"]
        self.assertEqual(lines[0]["name"], "Band")
        self.assertEqual(lines[0]["price"], 15000)
        self.assertEqual(lines[0]["subtotal"], 45000)
        self.assertEqual(lines[1]["name"], "Bottle")
        self.assertEqual(lines[1]["subtotal"], 12345)
        self.assertEqual(lines[2]["name"], "-")
        self.assertEqual(lines[2]["qty"], 0)
        self.assertEqual(lines[2]["subtotal"], 0)

    @patch("user.views.BookingOrderItem")
    @patch("user.views.ProductOrder")
    def test_my_profile_bookings_edge_cases(self, PO, BOI):
        qs_po = MagicMock()
        qs_po.prefetch_related.return_value = qs_po
        qs_po.order_by.return_value = []
        PO.objects.filter.return_value = qs_po

        now = timezone.localdate()

        t1 = MagicMock()
        t1.session_title = "Yoga A"
        t1.booking = MagicMock()
        t1.booking.session = MagicMock()
        t1.booking.session.instructor = "Coach 1"
        t1.order = MagicMock()
        t1.occurrence_date = None
        t1.occurrence_start_time = "09:00"

        t2 = MagicMock()
        t2.session_title = "Yoga B"
        t2.booking = MagicMock()
        if hasattr(t2.booking, "session"):
            delattr(t2.booking, "session")
        t2.order = MagicMock()
        t2.occurrence_date = now - timedelta(days=3)
        t2.occurrence_start_time = "10:00"

        qs_boi = MagicMock()
        qs_boi.select_related.return_value = qs_boi
        qs_boi.order_by.return_value = [t1, t2]
        BOI.objects.filter.return_value = qs_boi

        resp = self.client.get(reverse("user:my_profile"))
        self.assertEqual(resp.status_code, 200)
        bookings = resp.context["bookings"]
        self.assertEqual(len(bookings), 2)

        b1 = bookings[0]
        b2 = bookings[1]

        self.assertEqual(b1["status"], "Upcoming")
        self.assertEqual(b1["instructor"], "Coach 1")

        self.assertEqual(b2["status"], "Completed")
        self.assertIsNone(b2["instructor"])
