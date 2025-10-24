from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from cart.models import Cart, CartItem
from catalog.models import Product

User = get_user_model()

class CartViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="pass12345",
            is_staff=False,
        )
        self.staff = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass12345",
            is_staff=True,
        )

        # Produk utama
        self.prod_ok = Product.objects.create(
            product_name="Pilates Ring",
            price=150000,
            stock=5,
            inStock=True,
        )

        # Produk kedua biar bisa buat 2 CartItem berbeda tanpa nabrak constraint
        self.prod_ok_2 = Product.objects.create(
            product_name="Foam Roller",
            price=200000,
            stock=3,
            inStock=True,
        )

        # Produk out of stock
        self.prod_oos = Product.objects.create(
            product_name="Yoga Strap",
            price=50000,
            stock=0,
            inStock=False,
        )

    #  cart_page 
    def test_cart_page_redirects_if_not_logged_in(self):
        url = reverse("cart:page")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp["Location"])
        self.assertIn("next=", resp["Location"])

    def test_cart_page_renders_if_logged_in(self):
        self.client.login(username="buyer", password="pass12345")
        url = reverse("cart:page")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("cart", resp.context)
        self.assertIn("items", resp.context)
        self.assertIn("total_items", resp.context)

    # cart_json 
    def test_cart_json_returns_items_and_metadata(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(
            cart=cart, product=self.prod_ok, quantity=2, is_selected=True
        )

        url = reverse("cart:json")
        resp = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["product_name"], "Pilates Ring")

    # add_to_cart
    def test_add_to_cart_creates_item_first_time(self):
        self.client.login(username="buyer", password="pass12345")
        url = reverse("cart:add", args=[self.prod_ok.pk])
        resp = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["added"])
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(
            CartItem.objects.filter(cart=cart, product=self.prod_ok).exists()
        )

    def test_add_to_cart_increments_quantity_until_stock(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.prod_ok, quantity=2)
        url = reverse("cart:add", args=[self.prod_ok.pk])
        resp = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        item = CartItem.objects.get(cart=cart, product=self.prod_ok)
        self.assertEqual(item.quantity, 3)

    def test_add_to_cart_block_when_stock_reached(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(
            cart=cart, product=self.prod_ok, quantity=self.prod_ok.stock
        )
        url = reverse("cart:add", args=[self.prod_ok.pk])
        resp = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertTrue(data["warn"])
        self.assertIn("last available stock", data["message"])

    def test_add_to_cart_out_of_stock_product(self):
        self.client.login(username="buyer", password="pass12345")
        url = reverse("cart:add", args=[self.prod_oos.pk])
        resp = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertIn("out of stock", data["message"])

    def test_add_to_cart_staff_blocked(self):
        self.client.login(username="admin", password="pass12345")
        url = reverse("cart:add", args=[self.prod_ok.pk])
        resp = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotEqual(resp.status_code, 200)

    # set_quantity_ajax 
    def test_set_quantity_updates_quantity_normally(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.prod_ok, quantity=1)
        url = reverse("cart:set_qty", args=[item.pk])
        resp = self.client.post(
            url, {"quantity": "3"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        data = resp.json()
        self.assertTrue(data["ok"])
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

    def test_set_quantity_more_than_stock_gets_blocked(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.prod_ok, quantity=1)
        url = reverse("cart:set_qty", args=[item.pk])
        resp = self.client.post(
            url, {"quantity": "99"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        data = resp.json()
        self.assertFalse(data["ok"])
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_set_quantity_zero_deletes_item(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.prod_ok, quantity=2)
        url = reverse("cart:set_qty", args=[item.pk])
        resp = self.client.post(
            url, {"quantity": "0"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    # remove_item_ajax
    def test_remove_item_ajax_deletes_item(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.prod_ok, quantity=1)
        url = reverse("cart:remove_ajax", args=[item.pk])
        resp = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    # select_all / unselect_all
    def test_select_all_sets_all_items_selected_true(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        i1 = CartItem.objects.create(
            cart=cart, product=self.prod_ok, quantity=1, is_selected=False
        )
        i2 = CartItem.objects.create(
            cart=cart, product=self.prod_ok_2, quantity=2, is_selected=False
        )
        url = reverse("cart:select_all")
        resp = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        data = resp.json()
        self.assertTrue(data["ok"])
        i1.refresh_from_db()
        i2.refresh_from_db()
        self.assertTrue(i1.is_selected)
        self.assertTrue(i2.is_selected)

    def test_unselect_all_sets_all_items_selected_false(self):
        self.client.login(username="buyer", password="pass12345")
        cart, _ = Cart.objects.get_or_create(user=self.user)
        i1 = CartItem.objects.create(
            cart=cart, product=self.prod_ok, quantity=1, is_selected=True
        )
        i2 = CartItem.objects.create(
            cart=cart, product=self.prod_ok_2, quantity=2, is_selected=True
        )
        url = reverse("cart:unselect_all")
        resp = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        data = resp.json()
        self.assertTrue(data["ok"])
        i1.refresh_from_db()
        i2.refresh_from_db()
        self.assertFalse(i1.is_selected)
        self.assertFalse(i2.is_selected)
