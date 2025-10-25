from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

User = get_user_model()

@override_settings(LOGIN_URL="/user/login/")
class CatalogAndJsonTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", password="pass")
        self.client.login(username="user", password="pass")

    def test_utils_weekday_map_and_base_title(self):
        from bookingkelas import views as v
        m = v._weekday_map()
        self.assertEqual(m["0"], "Monday")
        self.assertEqual(m["6"], "Sunday")
        self.assertEqual(v._base_title("Yoga Flow - Monday"), "Yoga Flow")

    @patch("bookingkelas.views.AdminSessionsForm")
    @patch("bookingkelas.views.ClassSessions")
    def test_catalog_groups_sessions(self, ClassSessions, AdminSessionsForm):
        s1 = MagicMock()
        s1.id = 1
        s1.title = "Yoga Flow - Monday"
        s1.category = "yoga"
        s1.instructor = "Coach A"
        s1.time = "09:00"
        s1.room = "R1"
        s1.price = 50000
        s1.capacity_max = 20
        s1.capacity_current = 5
        s1.days = ["0"]

        s2 = MagicMock()
        s2.id = 2
        s2.title = "Yoga Flow - Wednesday"
        s2.category = "yoga"
        s2.instructor = "Coach A"
        s2.time = "09:00"
        s2.room = "R1"
        s2.price = 50000
        s2.capacity_max = 20
        s2.capacity_current = 7
        s2.days = ["2"]

        qs = MagicMock()
        qs.all.return_value = qs
        qs.order_by.return_value = [s1, s2]
        ClassSessions.objects.all.return_value = qs

        resp = self.client.get(reverse("bookingkelas:catalog"))
        self.assertEqual(resp.status_code, 200)
        sessions = resp.context["sessions"]
        self.assertEqual(len(sessions), 1)
        card = sessions[0]
        self.assertEqual(card["base_title"], "Yoga Flow")
        self.assertIn("Monday", card["days_names"])
        self.assertIn("Wednesday", card["days_names"])
        self.assertEqual(card["category"], "yoga")

    @patch("bookingkelas.views.AdminSessionsForm")
    @patch("bookingkelas.views.ClassSessions")
    def test_catalog_with_category_filter(self, ClassSessions, AdminSessionsForm):
        s = MagicMock()
        s.id = 3
        s.title = "Pilates Core - Friday"
        s.category = "pilates"
        s.instructor = "Coach B"
        s.time = "10:00"
        s.room = "R2"
        s.price = 60000
        s.capacity_max = 15
        s.capacity_current = 3
        s.days = ["4"]

        qs = MagicMock()
        qs.all.return_value = qs
        qs.order_by.return_value = qs
        qs.filter.return_value = [s]
        ClassSessions.objects.all.return_value = qs

        resp = self.client.get(reverse("bookingkelas:catalog") + "?category=pilates")
        self.assertEqual(resp.status_code, 200)
        sessions = resp.context["sessions"]
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["category"], "pilates")

    @patch("bookingkelas.views.AdminSessionsForm")
    @patch("bookingkelas.views.ClassSessions")
    def test_catalog_empty(self, ClassSessions, AdminSessionsForm):
        qs = MagicMock()
        qs.all.return_value = qs
        qs.order_by.return_value = []
        ClassSessions.objects.all.return_value = qs

        resp = self.client.get(reverse("bookingkelas:catalog"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["sessions"], [])

    @patch("bookingkelas.views.ClassSessions")
    def test_sessions_json_ok(self, ClassSessions):
        s = MagicMock()
        s.id = 10
        s.title = "Pilates Core - Friday"
        s.category = "pilates"
        s.instructor = "Coach B"
        s.capacity_current = 3
        s.capacity_max = 12
        s.description = "Core strength"
        s.price = 60000
        s.room = "R2"
        s.days = ["4"]
        s.time = "10:00"
        s.is_full = False

        qs = MagicMock()
        qs.all.return_value = qs
        qs.order_by.return_value = [s]
        ClassSessions.objects.all.return_value = qs

        resp = self.client.get(reverse("bookingkelas:sessions_json"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("sessions", data)
        # Dengan CATEGORY_CHOICES di-patch ke [], category_display jatuh ke default (nilai category)
        self.assertEqual(data["sessions"][0]["category_display"], "pilates")
        self.assertIn("Friday", data["sessions"][0]["days_names"])

    def test_sessions_json_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("bookingkelas:sessions_json"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/user/login/", resp.url)

    @patch("bookingkelas.views.ClassSessions")
    def test_get_session_details_json_404(self, ClassSessions):
        qs = MagicMock()
        qs.exists.return_value = False
        ClassSessions.objects.filter.return_value = qs

        resp = self.client.get(reverse("bookingkelas:get_session_details_json", args=["NotExists"]))
        self.assertEqual(resp.status_code, 404)

    @patch("bookingkelas.views.ClassSessions")
    def test_get_session_details_json_ok(self, ClassSessions):
        s_general = MagicMock()
        s_general.id = 1
        s_general.title = "Zumba Party - Tuesday"
        s_general.instructor = "Coach Z"
        s_general.time = "18:00"
        s_general.room = "R3"
        s_general.price = 45000
        s_general.description = "Fun cardio"

        s_day1 = MagicMock()
        s_day1.id = 11
        s_day1.days = ["1"]
        s_day1.is_full = False
        s_day1.capacity_current = 8
        s_day1.capacity_max = 15

        s_day2 = MagicMock()
        s_day2.id = 12
        s_day2.days = ["3"]
        s_day2.is_full = True
        s_day2.capacity_current = 15
        s_day2.capacity_max = 15

        s_day3 = MagicMock()
        s_day3.id = 13
        s_day3.days = []
        s_day3.is_full = False
        s_day3.capacity_current = 0
        s_day3.capacity_max = 10

        qs = MagicMock()
        qs.filter.return_value = qs
        qs.exists.return_value = True
        qs.first.return_value = s_general
        qs.__iter__.return_value = iter([s_day1, s_day2, s_day3])
        ClassSessions.objects.filter.return_value = qs

        resp = self.client.get(reverse("bookingkelas:get_session_details_json", args=["Zumba Party"]))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["base_title_cleaned"], "Zumba Party")
        labels = {o["label"] for o in payload["day_options"]}
        self.assertTrue({"Tuesday", "Thursday"}.issubset(labels))
        self.assertEqual(len(payload["day_options"]), 2)

@override_settings(LOGIN_URL="/user/login/")
class BookingActionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", password="pass")
        self.client.login(username="user", password="pass")

    @patch("bookingkelas.views.get_object_or_404")
    @patch("bookingkelas.views.ClassSessions")
    def test_book_class_full(self, ClassSessions, get_object):
        s = MagicMock()
        s.is_full = True
        ClassSessions.objects.select_for_update.return_value = MagicMock()
        get_object.return_value = s

        resp = self.client.get(reverse("bookingkelas:book_class", args=[1]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

    @patch("bookingkelas.views.Booking")
    @patch("bookingkelas.views.get_object_or_404")
    @patch("bookingkelas.views.ClassSessions")
    def test_book_class_already_booked(self, ClassSessions, get_object, Booking):
        s = MagicMock()
        s.is_full = False
        s.price = 50000
        ClassSessions.objects.select_for_update.return_value = MagicMock()
        get_object.return_value = s
        Booking.objects.filter.return_value.exists.return_value = True

        resp = self.client.get(reverse("bookingkelas:book_class", args=[2]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

    @patch("bookingkelas.views.Booking")
    @patch("bookingkelas.views.get_object_or_404")
    @patch("bookingkelas.views.ClassSessions")
    def test_book_class_success(self, ClassSessions, get_object, Booking):
        s = MagicMock()
        s.is_full = False
        s.price = 70000
        ClassSessions.objects.select_for_update.return_value = MagicMock()
        get_object.return_value = s
        Booking.objects.filter.return_value.exists.return_value = False

        new_b = MagicMock()
        new_b.id = 123
        Booking.objects.create.return_value = new_b

        self.client.get(reverse("checkout:booking_checkout", args=[123]))

        resp2 = self.client.get(reverse("bookingkelas:book_class", args=[3]))
        self.assertEqual(resp2.status_code, 302)
        self.assertIn("checkout", resp2.url)
        self.assertIn("booking", resp2.url)

    @patch("bookingkelas.views.Booking")
    @patch("bookingkelas.views.get_object_or_404")
    def test_book_daily_session_post_missing_id(self, get_object, Booking):
        resp = self.client.post(reverse("bookingkelas:book_daily_session"), {})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

    def test_book_daily_session_get_redirects(self):
        resp = self.client.get(reverse("bookingkelas:book_daily_session"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

    @patch("bookingkelas.views.Booking")
    @patch("bookingkelas.views.get_object_or_404")
    def test_book_daily_session_already_confirmed(self, get_object, Booking):
        s = MagicMock()
        s.id = 77
        get_object.return_value = s
        Booking.objects.filter.return_value.exists.return_value = True

        resp = self.client.post(reverse("bookingkelas:book_daily_session"), {"session_id": 77})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

    @patch("bookingkelas.views.Booking")
    @patch("bookingkelas.views.get_object_or_404")
    def test_book_daily_session_pending_exists(self, get_object, Booking):
        s = MagicMock()
        s.id = 88
        s.bookings = MagicMock()
        s.capacity_max = 10
        get_object.return_value = s

        Booking.objects.filter.return_value.exists.return_value = False
        pending = MagicMock()
        pending.id = 999
        Booking.objects.filter.return_value.first.return_value = pending

        resp = self.client.post(reverse("bookingkelas:book_daily_session"), {"session_id": 88})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("checkout", resp.url)

    @patch("bookingkelas.views.Booking")
    @patch("bookingkelas.views.get_object_or_404")
    def test_book_daily_session_full(self, get_object, Booking):
        s = MagicMock()
        s.id = 89
        s.capacity_max = 2
        s.bookings = MagicMock()
        s.bookings.filter.return_value.count.return_value = 2
        get_object.return_value = s

        Booking.objects.filter.return_value.exists.return_value = False
        Booking.objects.filter.return_value.first.return_value = None

        resp = self.client.post(reverse("bookingkelas:book_daily_session"), {"session_id": 89})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

    @patch("bookingkelas.views.Booking")
    @patch("bookingkelas.views.get_object_or_404")
    def test_book_daily_session_success(self, get_object, Booking):
        s = MagicMock()
        s.id = 90
        s.capacity_max = 5
        s.bookings = MagicMock()
        s.bookings.filter.return_value.count.return_value = 1
        s.days = ["1"]
        s.price = 55000
        get_object.return_value = s

        Booking.objects.filter.return_value.exists.return_value = False
        Booking.objects.filter.return_value.first.return_value = None

        new_b = MagicMock()
        new_b.id = 321
        Booking.objects.create.return_value = new_b

        resp = self.client.post(reverse("bookingkelas:book_daily_session"), {"session_id": 90})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("checkout", resp.url)

    @patch("bookingkelas.views.get_object_or_404")
    def test_book_daily_session_generic_exception_caught(self, get_object):
        get_object.side_effect = Exception("boom")
        resp = self.client.post(reverse("bookingkelas:book_daily_session"), {"session_id": 123})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

@override_settings(LOGIN_URL="/user/login/")
class AdminViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", password="pass", is_staff=False)
        self.admin = User.objects.create_user(username="admin", password="pass", is_staff=True)

    def test_class_list_requires_staff(self):
        self.client.login(username="user", password="pass")
        resp = self.client.get(reverse("bookingkelas:class_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/user/login/", resp.url)

    @patch("bookingkelas.views.ClassSessions")
    def test_class_list_ok(self, ClassSessions):
        self.client.login(username="admin", password="pass")
        qs = MagicMock()
        qs.all.return_value = qs
        qs.order_by.return_value = []
        ClassSessions.objects.all.return_value = qs
        resp = self.client.get(reverse("bookingkelas:class_list"))
        self.assertEqual(resp.status_code, 200)

    @patch("bookingkelas.views.get_object_or_404")
    @patch("bookingkelas.views.AdminSessionEditForm")
    def test_class_edit_get(self, AdminSessionEditForm, get_object):
        self.client.login(username="admin", password="pass")
        get_object.return_value = MagicMock()
        form = MagicMock()
        form.is_valid.return_value = False
        AdminSessionEditForm.return_value = form

        resp = self.client.get(reverse("bookingkelas:class_edit", args=[1]))
        self.assertEqual(resp.status_code, 200)

    @patch("bookingkelas.views.get_object_or_404")
    @patch("bookingkelas.views.AdminSessionEditForm")
    def test_class_edit_post_valid(self, AdminSessionEditForm, get_object):
        self.client.login(username="admin", password="pass")
        get_object.return_value = MagicMock()
        form = MagicMock()
        form.is_valid.return_value = True
        AdminSessionEditForm.return_value = form

        resp = self.client.post(reverse("bookingkelas:class_edit", args=[1]), {"title": "X"})
        self.assertTrue(form.save.called)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:class_list"), resp.url)

    @patch("bookingkelas.views.get_object_or_404")
    @patch("bookingkelas.views.AdminSessionEditForm")
    def test_class_edit_post_invalid_rerenders(self, AdminSessionEditForm, get_object):
        self.client.login(username="admin", password="pass")
        get_object.return_value = MagicMock()
        form = MagicMock()
        form.is_valid.return_value = False
        AdminSessionEditForm.return_value = form

        resp = self.client.post(reverse("bookingkelas:class_edit", args=[2]), {"title": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("Location", resp.headers)

    @patch("bookingkelas.views.get_object_or_404")
    def test_class_delete_get_rejected(self, get_object):
        self.client.login(username="admin", password="pass")
        get_object.return_value = MagicMock()
        resp = self.client.get(reverse("bookingkelas:class_delete", args=[1]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:class_list"), resp.url)

    @patch("bookingkelas.views.get_object_or_404")
    def test_class_delete_post_ok(self, get_object):
        self.client.login(username="admin", password="pass")
        obj = MagicMock()
        get_object.return_value = obj
        resp = self.client.post(reverse("bookingkelas:class_delete", args=[1]))
        self.assertTrue(obj.delete.called)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:class_list"), resp.url)

    @patch("bookingkelas.views.get_object_or_404")
    @patch("bookingkelas.views.AdminSessionEditForm")
    def test_get_edit_form_ok(self, AdminSessionEditForm, get_object):
        self.client.login(username="admin", password="pass")
        get_object.return_value = MagicMock()
        AdminSessionEditForm.return_value = MagicMock()
        resp = self.client.get(reverse("bookingkelas:get_edit_form", args=[1]))
        self.assertEqual(resp.status_code, 200)

    @patch("bookingkelas.views.AdminSessionsForm")
    def test_add_session_get_redirect(self, AdminSessionsForm):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(reverse("bookingkelas:add_session"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

    @patch("bookingkelas.views.AdminSessionsForm")
    def test_add_session_post_valid(self, AdminSessionsForm):
        self.client.login(username="admin", password="pass")
        form = MagicMock()
        form.is_valid.return_value = True
        inst = MagicMock()
        inst.title = "New Sesi"
        form.save.return_value = inst
        AdminSessionsForm.return_value = form

        resp = self.client.post(reverse("bookingkelas:add_session"), {"title": "New Sesi"})
        self.assertTrue(form.save.called)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)

    @patch("bookingkelas.views.AdminSessionsForm")
    def test_add_session_post_invalid(self, AdminSessionsForm):
        self.client.login(username="admin", password="pass")
        form = MagicMock()
        form.is_valid.return_value = False
        form.errors = {"title": ["This field is required."]}
        AdminSessionsForm.return_value = form

        resp = self.client.post(reverse("bookingkelas:add_session"), {"title": ""})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("bookingkelas:catalog"), resp.url)