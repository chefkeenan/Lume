from django.test import TestCase, Client, override_settings, RequestFactory
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from catalog import views as catalog_views

User = get_user_model()

UID = "00000000-0000-0000-0000-000000000001"


def url_or(path_name, *args, **kwargs):
    try:
        return reverse(path_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        if path_name.endswith("product_edit_modal"):
            pk = kwargs.get("pk") or (args[0] if args else "")
            return f"/catalog/products/{pk}/edit-modal/"
        if path_name.endswith("product_delete"):
            pk = kwargs.get("pk") or (args[0] if args else "")
            return f"/catalog/products/{pk}/delete/"
        if path_name.endswith("detail"):
            pid = kwargs.get("id") or (args[0] if args else "")
            return f"/catalog/products/{pid}/"
        if path_name.endswith("product_list"):
            return "/catalog/products/"
        if path_name.endswith("product_add_modal"):
            return "/catalog/products/add-modal/"
        if path_name.endswith("product_create"):
            return "/catalog/products/add/"
        raise


@override_settings(LOGIN_URL="/user/login/")
class CatalogAdminModalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.user = User.objects.create_user(username="user", password="pass", is_staff=False)

    def test_requires_login_and_staff_for_modals(self):
        resp = self.client.get(url_or("catalog:product_add_modal"))
        self.assertEqual(resp.status_code, 302)
        self.client.login(username="user", password="pass")
        resp = self.client.get(url_or("catalog:product_add_modal"))
        self.assertEqual(resp.status_code, 302)

    @patch("catalog.views.render_to_string")
    @patch("catalog.views.ProductForm")
    def test_product_add_modal_ok(self, ProductForm, render_to_string):
        self.client.login(username="admin", password="pass")
        render_to_string.return_value = "<form>...</form>"
        resp = self.client.get(url_or("catalog:product_add_modal"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertIn("form_html", data)

    @patch("catalog.views.get_object_or_404")
    @patch("catalog.views.render_to_string")
    @patch("catalog.views.ProductForm")
    def test_product_edit_modal_ok(self, ProductForm, render_to_string, get_object):
        self.client.login(username="admin", password="pass")
        obj = MagicMock()
        get_object.return_value = obj
        render_to_string.return_value = "<form>EDIT</form>"
        resp = self.client.get(url_or("catalog:product_edit_modal", UID))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        self.assertIn("form_html", resp.json())


@override_settings(LOGIN_URL="/user/login/")
class CatalogListDetailTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.client.login(username="admin", password="pass")

    @patch("catalog.views.Product")
    def test_product_list_renders(self, Product):
        qs = MagicMock()
        qs.all.return_value = qs
        qs.order_by.return_value = []
        Product.objects.all.return_value = qs
        resp = self.client.get(url_or("catalog:product_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("products", resp.context)

    @patch("catalog.views.get_object_or_404")
    def test_product_detail_ok(self, get_object):
        obj = MagicMock()
        get_object.return_value = obj
        resp = self.client.get(url_or("catalog:detail", UID))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("p", resp.context)


@override_settings(LOGIN_URL="/user/login/")
class CatalogUpdateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)



    @patch("catalog.views.get_object_or_404")
    @patch("catalog.views.ProductForm")
    def test_product_update_nonajax_valid_redirects(self, ProductForm, get_object):
        obj = MagicMock()
        obj.pk = UID
        get_object.return_value = obj
        form = MagicMock()
        form.is_valid.return_value = True
        ProductForm.return_value = form
        req = self.factory.post("/catalog/products/update/", {"product_name": "X"})
        req.user = self.staff
        resp = catalog_views.product_update(req, pk=UID)
        self.assertEqual(resp.status_code, 302)



class CatalogDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("catalog.views.Product")
    def test_product_delete_requires_post(self, Product):
        resp = self.client.get(url_or("catalog:product_delete", UID))
        self.assertEqual(resp.status_code, 405)

    @patch("catalog.views.Product")
    def test_product_delete_ajax_204(self, Product):
        Product.objects.filter.return_value.delete.return_value = (1, {})
        resp = self.client.post(
            url_or("catalog:product_delete", UID),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 204)

    @patch("catalog.views.Product")
    def test_product_delete_nonajax_redirect_home(self, Product):
        Product.objects.filter.return_value.delete.return_value = (1, {})
        resp = self.client.post(url_or("catalog:product_delete", UID))
        self.assertEqual(resp.status_code, 302)
        from django.urls import reverse as r
        try:
            home = r("main:show_main")
        except NoReverseMatch:
            home = "/"
        self.assertIn(home, resp.url)


@override_settings(LOGIN_URL="/user/login/")
class CatalogCreateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.client.login(username="admin", password="pass")

    @patch("catalog.views.ProductForm")
    def test_product_create_post_valid_nonajax_redirects(self, ProductForm):
        form = MagicMock()
        form.is_valid.return_value = True
        obj = MagicMock()
        obj.pk = UID
        form.save.return_value = obj
        ProductForm.return_value = form
        resp = self.client.post(url_or("catalog:product_create"), {"product_name": "New"})
        self.assertEqual(resp.status_code, 302)

    @patch("catalog.views.ProductForm")
    def test_product_create_post_invalid_rerender(self, ProductForm):
        form = MagicMock()
        form.is_valid.return_value = False
        ProductForm.return_value = form
        resp = self.client.post(url_or("catalog:product_create"), {"product_name": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)
