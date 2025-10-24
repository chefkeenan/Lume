from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse
from django.http import Http404
from unittest.mock import patch, MagicMock
import bookingkelas.views as views
from decimal import Decimal
import json

class ViewsUnitTest(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        # normal user
        self.user = User.objects.create_user(username="user1", password="pass")
        # staff user
        self.staff = User.objects.create_user(username="staff1", password="pass")
        self.staff.is_staff = True
        self.staff.save()

    @patch('bookingkelas.views.ClassSessions')
    def test_catalog_groups_sessions_and_renders(self, mock_ClassSessions):
        """
        Test catalog view groups sessions by base title/time/category and renders context.
        We patch ClassSessions.objects.all().order_by(...) to return fake sessions.
        """
        # create fake session objects
        s1 = MagicMock()
        s1.title = "Yoga - Beginner"
        s1.time = "09:00"
        s1.category = "fitness"
        s1.instructor = "Alice"
        s1.room = "Room A"
        s1.price = Decimal("10.00")
        s1.capacity_max = 10
        s1.capacity_current = 3
        s1.days = [0, 2]
        s1.id = 101

        s2 = MagicMock()
        s2.title = "Yoga - Beginner"
        s2.time = "09:00"
        s2.category = "fitness"
        s2.instructor = "Alice"
        s2.room = "Room A"
        s2.price = Decimal("10.00")
        s2.capacity_max = 10
        s2.capacity_current = 4
        s2.days = [4]
        s2.id = 102

        # chain .objects.all().order_by("title")
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = [s1, s2]
        mock_ClassSessions.objects.all.return_value = mock_qs

        request = self.rf.get("/catalog")
        request.user = AnonymousUser()

        resp = views.catalog(request)
        # render returns HttpResponse; status 200
        self.assertEqual(resp.status_code, 200)
        # context should include grouped sessions; we can inspect rendered context_data
        # Django test client not used, but template rendering via view returns HttpResponse
        # Ensure the view built 'sessions' in context by calling view function's context via response.content check
        # More robust: call sessions_json flow separately. At minimum assert response is 200.

    @patch('bookingkelas.views.ClassSessions')
    def test_sessions_json_returns_expected_structure(self, mock_ClassSessions):
        """
        sessions_json should build JSON with sessions and weekday names mapping.
        """
        s = MagicMock()
        s.id = 1
        s.title = "Pilates - Intro"
        s.category = "wellness"
        s.instructor = "Bob"
        s.capacity_current = 2
        s.capacity_max = 12
        s.description = "desc"
        s.price = Decimal("12.50")
        s.room = "Room B"
        s.days = [1, 3]
        s.time = "18:30"
        s.is_full = False

        mock_qs = MagicMock()
        mock_qs.order_by.return_value = [s]
        mock_ClassSessions.objects.all.return_value = mock_qs

        request = self.rf.get("/sessions_json")
        request.user = self.user  # sessions_json requires login
        resp = views.sessions_json(request)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn("sessions", data)
        self.assertEqual(len(data["sessions"]), 1)
        sess = data["sessions"][0]
        self.assertEqual(sess["title"], "Pilates - Intro")
        self.assertEqual(sess["days"], [1, 3])
        # days_names should be filled with weekday mapping (Tuesday, Thursday) -> check length
        self.assertEqual(len(sess["days_names"]), 2)

    @patch('bookingkelas.views.ClassSessions')
    def test_get_session_details_json_found_and_404(self, mock_ClassSessions):
        """
        get_session_details_json should return details when sessions found; 404 when not.
        """
        # Case: not found -> return 404 JSON
        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        mock_ClassSessions.objects.filter.return_value = mock_qs

        request = self.rf.get("/details/SomeTitle")
        resp = views.get_session_details_json(request, base_title="SomeTitle")
        self.assertEqual(resp.status_code, 404)
        data = json.loads(resp.content)
        self.assertIn("error", data)

        # Case: found -> returns expected fields
        s_item = MagicMock()
        s_item.title = "Meditation - 1"
        s_item.instructor = "Carl"
        s_item.time = "07:00"
        s_item.room = "Room Z"
        s_item.price = Decimal("5.00")
        s_item.description = "desc"
        # days stored maybe list of strings; view expects s_item.days and uses lower().strip() on first
        s_item.days = ["0"]
        s_item.id = 201
        s_item.is_full = False
        s_item.capacity_current = 1
        s_item.capacity_max = 10

        mock_qs2 = MagicMock()
        mock_qs2.exists.return_value = True
        mock_qs2.first.return_value = s_item
        # filter should be iterable; set __iter__ to yield s_item
        mock_qs2.__iter__.return_value = iter([s_item])
        mock_ClassSessions.objects.filter.return_value = mock_qs2

        resp2 = views.get_session_details_json(request, base_title="Meditation")
        self.assertEqual(resp2.status_code, 200)
        data2 = json.loads(resp2.content)
        self.assertIn("base_title_cleaned", data2)
        self.assertIn("day_options", data2)
        self.assertGreaterEqual(len(data2["day_options"]), 1)

    @patch('bookingkelas.views.get_object_or_404')
    @patch('bookingkelas.views.Booking')
    def test_book_class_success_and_full(self, mock_BookingModel, mock_get_object):
        """
        Test book_class view when session available and when full.
        We'll patch get_object_or_404 to return a fake session object.
        """
        # Successful booking path
        fake_session = MagicMock()
        fake_session.is_full = False
        fake_session.id = 333
        fake_session.price = Decimal("20.00")
        mock_get_object.return_value = fake_session

        # Simulate Booking.objects.filter(...).exists() returns False
        booking_qs = MagicMock()
        booking_qs.filter.return_value.exists.return_value = False
        mock_BookingModel.objects = booking_qs

        # Patch Booking.objects.create to return a booking with id
        created_booking = MagicMock()
        created_booking.id = 999
        booking_qs.create.return_value = created_booking

        request = self.rf.get("/book/333")
        request.user = self.user

        resp = views.book_class(request, session_id=333)
        # Expect redirect to checkout:booking_checkout with new booking id
        self.assertEqual(resp.status_code, 302)
        # Ensure create called with expected args (user, session, price_at_booking)
        booking_qs.create.assert_called_once()
        called_kwargs = booking_qs.create.call_args.kwargs
        self.assertIn('user', called_kwargs)
        self.assertIn('session', called_kwargs)
        self.assertIn('price_at_booking', called_kwargs)

        # Now test when session is full
        fake_session_full = MagicMock()
        fake_session_full.is_full = True
        mock_get_object.return_value = fake_session_full

        # calling view should redirect back to catalog (messages added)
        resp2 = views.book_class(request, session_id=444)
        self.assertEqual(resp2.status_code, 302)

    @patch('bookingkelas.views.get_object_or_404')
    @patch('bookingkelas.views.Booking')
    def test_book_daily_session_various_paths(self, mock_BookingModel, mock_get_object):
        """
        Test book_daily_session POST behavior for:
         - missing session_id
         - already confirmed booking (order_items present)
         - pending booking (order_items null) -> redirect to checkout existing
         - capacity full
         - successful creation
        We'll mock Booking queries to simulate these cases.
        """
        # Prepare fake session to be returned by get_object_or_404
        s = MagicMock()
        s.id = 777
        s.days = ["1"]
        s.price = Decimal("15.00")
        s.capacity_max = 2
        s.bookings = MagicMock()
        # for confirmed_count use s.bookings.filter(...).count()
        s.bookings.filter.return_value.count.return_value = 0
        mock_get_object.return_value = s

        request = self.rf.post("/book_daily", data={})
        request.user = self.user

        # Case: no session_id in POST -> redirect with message (redirect)
        resp = views.book_daily_session(request)
        self.assertEqual(resp.status_code, 302)

        # Case: provided session_id but user already has confirmed booking -> messages.info & redirect
        # Simulate Booking.objects.filter(... order_items__isnull=False).exists() returns True
        qb = MagicMock()
        qb.filter.return_value.exists.return_value = True
        mock_BookingModel.objects = qb

        request2 = self.rf.post("/book_daily", data={"session_id": "777"})
        request2.user = self.user
        resp2 = views.book_daily_session(request2)
        self.assertEqual(resp2.status_code, 302)

        # Case: pending booking exists (order_items__isnull=True) -> should redirect to checkout with existing id
        # Now filter(... order_items__isnull=False).exists() -> False
        qb.filter.return_value.exists.return_value = False
        # pending_booking: first() returns an object with id
        pending = MagicMock()
        pending.id = 555
        qb.filter.return_value.first.return_value = pending

        request3 = self.rf.post("/book_daily", data={"session_id": "777"})
        request3.user = self.user
        resp3 = views.book_daily_session(request3)
        # Should redirect to checkout
        self.assertEqual(resp3.status_code, 302)

        # Case: no pending booking, but confirmed_count >= capacity_max -> class full
        qb.filter.return_value.first.return_value = None
        # set s.bookings.filter(...).count() to simulate full
        s.bookings.filter.return_value.count.return_value = 2  # equal to capacity_max
        resp4 = views.book_daily_session(request3)
        self.assertEqual(resp4.status_code, 302)

        # Case: successful new booking creation
        s.bookings.filter.return_value.count.return_value = 0
        created = MagicMock()
        created.id = 4242
        qb.create.return_value = created

        # Ensure Booking.objects.create will be called in view
        qb.filter.return_value.first.return_value = None
        qb.create.return_value = created

        request4 = self.rf.post("/book_daily", data={"session_id": "777"})
        request4.user = self.user
        resp5 = views.book_daily_session(request4)
        self.assertEqual(resp5.status_code, 302)
        qb.create.assert_called()  # called to create new Booking

    @patch('bookingkelas.views.ClassSessions')
    def test_admin_views_require_staff_and_render(self, mock_ClassSessions):
        """
        Test class_list and class_edit/get_edit_form/class_delete minimal behaviors for staff user.
        We will not test form saving logic deeply here, just that staff access returns something.
        """
        # Mock ClassSessions.objects.all().order_by(...)
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = []
        mock_ClassSessions.objects.all.return_value = mock_qs

        # class_list with staff user
        request = self.rf.get("/admin/classes")
        request.user = self.staff
        resp = views.class_list(request)
        self.assertEqual(resp.status_code, 200)

        # get_edit_form - ensure it returns 200 for existing pk
        # patch get_object_or_404 to return an instance
        with patch('bookingkelas.views.get_object_or_404') as mock_get:
            fake_kelas = MagicMock()
            mock_get.return_value = fake_kelas
            req2 = self.rf.get("/admin/edit/1")
            req2.user = self.staff
            resp2 = views.get_edit_form(req2, pk=1)
            self.assertEqual(resp2.status_code, 200)

        # class_delete: GET should redirect with error (as view does)
        with patch('bookingkelas.views.get_object_or_404') as mock_get2:
            fake_kelas = MagicMock()
            mock_get2.return_value = fake_kelas
            req3 = self.rf.get("/admin/delete/1")
            req3.user = self.staff
            resp3 = views.class_delete(req3, pk=1)
            # view redirects (messages.error + redirect)
            self.assertEqual(resp3.status_code, 302)

        # class_delete: POST should delete and redirect
        with patch('bookingkelas.views.get_object_or_404') as mock_get3:
            fake_kelas = MagicMock()
            mock_get3.return_value = fake_kelas
            req4 = self.rf.post("/admin/delete/1")
            req4.user = self.staff
            resp4 = views.class_delete(req4, pk=1)
            # delete called on object
            fake_kelas.delete.assert_called_once()
            self.assertEqual(resp4.status_code, 302)
