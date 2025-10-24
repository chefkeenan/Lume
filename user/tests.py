from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch, MagicMock

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


class RegisterViewTests(_BaseTestCase):
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


class LogoutViewTests(_BaseTestCase):
    def test_logout_redirects_to_landing(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(reverse("user:logout"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("main:landing"))


class MyProfileViewTests(_BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)

    def _mock_product_orders(self):
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

    def _mock_booking_items(self):
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
        qs_po.order_by.return_value = self._mock_product_orders()
        PO.objects.filter.return_value = qs_po

        qs_boi = MagicMock()
        qs_boi.select_related.return_value = qs_boi
        qs_boi.order_by.return_value = self._mock_booking_items()
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