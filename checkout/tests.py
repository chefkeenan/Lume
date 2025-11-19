# checkout/tests.py
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from .forms import CartCheckoutForm
from .models import ProductOrder, ProductOrderItem

User = get_user_model()

class FakeProduct:
    def __init__(self, price=Decimal("50000.00"), stock=5, name="Prod A", product_name=None, pk=1):
        self.price = price
        self.stock = stock
        self.inStock = True
        self.name = name
        self.product_name = product_name
        self.pk = pk

    def refresh_from_db(self, fields=None):
        return


class FakeCartItem:
    def __init__(self, product, quantity=1, is_selected=True, product_id=1):
        self.product = product
        self.quantity = quantity
        self.is_selected = is_selected
        self.product_id = product_id


class FakeItemsQS:
    """Simulasi chaining: cart.items.select_related('product').filter(...).values_list(...).delete()"""
    def __init__(self, items):
        self._items = items

    def select_related(self, *_args, **_kwargs):
        return self

    def filter(self, **kwargs):
        if "is_selected" in kwargs:
            want = kwargs["is_selected"]
            return FakeItemsQS([i for i in self._items if i.is_selected == want])
        if "id__in" in kwargs:
            return self
        return self

    def exists(self):
        return bool(self._items)

    def __iter__(self):
        return iter(self._items)

    def values_list(self, field, flat=False):
        return [idx + 1 for idx, _ in enumerate(self._items)]

    def delete(self):
        return


class FakeCart:
    def __init__(self, items):
        self._items = items

    @property
    def items(self):
        return FakeItemsQS(self._items)

    def __init__(self, obj):
        self._obj = obj

    def select_for_update(self):
        return self

    def get(self, pk=None, **kwargs):
        return self._obj

    def filter(self, **kwargs):
        return self

    def update(self, **kwargs):
        # pretend updated
        return 1

class CheckoutViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="u1", password="pw", is_staff=False)

    def test_cart_checkout_page_requires_login(self):
        url = reverse("checkout:cart_checkout_page")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/user/login/", resp["Location"])

    @mock.patch("checkout.views.render")
    @mock.patch("checkout.views.get_object_or_404")
    def test_cart_checkout_page_renders_totals(self, m_get_obj, m_render):
        self.client.login(username="u1", password="pw")

        p1 = FakeProduct(price=Decimal("10000.00"), pk=1)
        p2 = FakeProduct(price=Decimal("20000.00"), pk=2)
        ci1 = FakeCartItem(product=p1, quantity=1, is_selected=True, product_id=1)
        ci2 = FakeCartItem(product=p2, quantity=2, is_selected=True, product_id=2)
        cart = FakeCart([ci1, ci2])

        m_get_obj.side_effect = lambda *a, **k: cart
        m_render.side_effect = lambda req, tpl, ctx: HttpResponse(f"OK {ctx['total']}")

        url = reverse("checkout:cart_checkout_page")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        ctx = m_render.call_args.args[2]
        self.assertEqual(ctx["subtotal"], Decimal("50000.00"))
        self.assertEqual(ctx["shipping"], Decimal("10000.00"))
        self.assertEqual(ctx["total"], Decimal("60000.00"))
        self.assertEqual(ctx["payment_method"], "Cash on Delivery")

    @mock.patch("checkout.views.get_object_or_404")
    @mock.patch("checkout.views.ProductOrderItem")
    @mock.patch("checkout.views.ProductOrder")
    def test_checkout_cart_create_happy_path_creates_order_and_clears_selected(
        self, m_order, m_item, m_get_obj
    ):
        self.client.login(username="u1", password="pw")

        p = FakeProduct(price=Decimal("15000.00"), stock=10, pk=11)
        FakeProduct.objects = _FakeProductManager(p)

        ci = FakeCartItem(product=p, quantity=3, is_selected=True, product_id=11)
        cart = FakeCart([ci])
        m_get_obj.side_effect = lambda *a, **k: cart

        fake_order = mock.Mock()
        fake_order.recalc_totals = mock.Mock()
        fake_order.save = mock.Mock()
        m_order.objects.create.return_value = fake_order

        url = reverse("checkout:checkout_cart_create")
        resp = self.client.post(url, data={
            "address_line1": "Jl. Mawar",
            "address_line2": "",
            "city": "Jakarta",
            "province": "DKI",
            "postal_code": "12345",
            "country": "Indonesia",
            "notes": "",
        })

        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("checkout:order_confirmed"), resp["Location"])

        self.assertTrue(m_order.objects.create.called)
        self.assertTrue(m_item.objects.create.called)
        fake_order.recalc_totals.assert_called_once()
        fake_order.save.assert_called_once()

    @mock.patch("checkout.views.get_object_or_404")
    def test_checkout_cart_create_no_selected_redirects(self, m_get_obj):
        self.client.login(username="u1", password="pw")

        p = FakeProduct(price=Decimal("15000.00"), stock=10, pk=11)
        ci = FakeCartItem(product=p, quantity=1, is_selected=False, product_id=11)
        cart = FakeCart([ci])
        m_get_obj.side_effect = lambda *a, **k: cart

        url = reverse("checkout:checkout_cart_create")
        resp = self.client.post(url, data={
            "address_line1": "Jl. Mawar",
            "city": "Jakarta",
            "province": "DKI",
            "postal_code": "12345",
            "country": "Indonesia",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("cart:page"), resp["Location"])

    def test_checkout_cart_create_invalid_form_redirects(self):
        self.client.login(username="u1", password="pw")
        url = reverse("checkout:checkout_cart_create")
        resp = self.client.post(url, data={"address_line1": ""})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("checkout:cart_checkout_page"), resp["Location"])

    @mock.patch("checkout.views.get_object_or_404")
    def test_cart_summary_json_ok(self, m_get_obj):
        self.client.login(username="u1", password="pw")

        p1 = FakeProduct(price=Decimal("12000.00"), pk=1)
        p2 = FakeProduct(price=Decimal("5000.00"), pk=2)
        sel = FakeCartItem(product=p1, quantity=2, is_selected=True, product_id=1)
        nos = FakeCartItem(product=p2, quantity=10, is_selected=False, product_id=2)
        cart = FakeCart([sel, nos])
        m_get_obj.side_effect = lambda *a, **k: cart

        url = reverse("checkout:cart_summary_json")
        resp = self.client.get(url, {"selected": "1"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(int(round(data["subtotal"])), 24000)
        self.assertEqual(int(round(data["shipping"])), 10000)
        self.assertEqual(int(round(data["total"])), 34000)
        self.assertEqual(data["count"], 2)

    def test_order_confirmed_ok(self):
        self.client.login(username="u1", password="pw")
        url = reverse("checkout:order_confirmed")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @mock.patch("checkout.views.BookingOrderItem")
    @mock.patch("checkout.views.BookingOrder")
    @mock.patch("checkout.views.ClassSessions")
    @mock.patch("checkout.views.get_object_or_404")
    def test_booking_checkout_post_ok(self, m_get_obj, m_class_sessions, m_b_order, m_b_item):
        self.client.login(username="u1", password="pw")

        fake_booking = mock.Mock()
        fake_booking.id = 7
        fake_booking.user_id = self.user.id
        fake_booking.is_cancelled = False
        fake_booking.session = mock.Mock()
        fake_booking.session.id = 77
        fake_booking.session.title = "Mat Pilates"
        fake_booking.price_at_booking = Decimal("80000.00")
        fake_booking.day_selected = "Mon"

        m_get_obj.return_value = fake_booking

        fake_session = mock.Mock()
        fake_session.capacity_max = 20
        fake_session.capacity_current = 0
        fake_session.bookings.filter.return_value.count.return_value = 0
        m_class_sessions.objects.select_for_update.return_value.get.return_value = fake_session

        m_b_item.objects.filter.return_value.exists.return_value = False

        m_b_order.objects.create.return_value = mock.Mock()

        url = reverse("checkout:booking_checkout", kwargs={"booking_id": 7})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("checkout:order_confirmed"), resp["Location"])
        self.assertTrue(m_b_order.objects.create.called)
        self.assertTrue(m_b_item.objects.create.called)
        self.assertTrue(fake_session.save.called)

    @mock.patch("checkout.views.BookingOrderItem")
    @mock.patch("checkout.views.get_object_or_404")
    def test_booking_checkout_already_checked_out_redirects(self, m_get_obj, m_b_item):
        self.client.login(username="u1", password="pw")

        fake_booking = mock.Mock()
        fake_booking.id = 8
        fake_booking.user_id = self.user.id
        fake_booking.is_cancelled = False
        fake_booking.session = mock.Mock()
        fake_booking.price_at_booking = Decimal("90000.00")
        m_get_obj.return_value = fake_booking

        m_b_item.objects.filter.return_value.exists.return_value = True

        url = reverse("checkout:booking_checkout", kwargs={"booking_id": 8})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("checkout:order_confirmed"), resp["Location"])


class CheckoutFormsModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u2", password="pw")

    def test_cart_checkout_form_attrs_and_placeholders(self):
        form = CartCheckoutForm()
        for name in ["address_line1", "address_line2", "city", "province", "postal_code", "country", "notes"]:
            w = form.fields[name].widget
            self.assertIn("class", w.attrs)
            self.assertIn("placeholder", w.attrs)

    def test_product_order_recalc_totals(self):
        order = ProductOrder.objects.create(
            user=self.user,
            cart=None,
            receiver_name="U2",
            receiver_phone="",
            address_line1="Jl. X",
            address_line2="",
            city="Jakarta",
            province="DKI",
            postal_code="12345",
            country="Indonesia",
            notes="",
        )
        ProductOrderItem.objects.create(order=order, product=None,
                                        product_name="A", unit_price=Decimal("10000.00"), quantity=2)
        ProductOrderItem.objects.create(order=order, product=None,
                                        product_name="B", unit_price=Decimal("5000.00"), quantity=1)

        order.recalc_totals()
        self.assertEqual(order.subtotal, Decimal("25000.00"))
        self.assertEqual(order.shipping_fee, Decimal("10000.00"))
        self.assertEqual(order.total, Decimal("35000.00"))
