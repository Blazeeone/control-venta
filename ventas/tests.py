from decimal import Decimal

from django.forms.models import inlineformset_factory
from django.test import TestCase
from django.urls import reverse
from django.test import RequestFactory

from .admin import DetalleVentaInlineFormSet, exportar_ventas_csv
from .models import Cliente, DetalleVenta, Producto, Venta


class ControlVentaTests(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(
            nombre="Teclado",
            sku="TEC-001",
            precio=Decimal("10000.00"),
            stock=5,
            activo=True,
        )
        self.cliente = Cliente.objects.create(
            rut="12.345.678-9",
            nombre="Ana Pérez",
            habitual=True,
        )

    def test_producto_formulario_publico_valida_precio_y_codigo(self):
        response = self.client.post(
            reverse("producto_create"),
            {
                "nombre": "Mouse",
                "sku": "",
                "codigo": "",
                "precio": "0",
                "stock": "2",
                "activo": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Debes ingresar al menos un Código o SKU")
        self.assertContains(response, "El precio debe ser estrictamente mayor a 0")

    def test_registrar_venta_actualiza_stock_y_guarda_cliente_habitual(self):
        response = self.client.post(
            reverse("registrar_venta", args=[self.producto.pk]),
            {
                "cantidad": "2",
                "rut": "12.345.678-9",
                "es_habitual": "on",
                "nombre": "Ana Pérez",
                "telefono": "987654321",
            },
        )

        self.assertRedirects(response, reverse("producto_list"))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)
        self.assertEqual(Venta.objects.count(), 1)
        self.assertEqual(DetalleVenta.objects.get().subtotal, Decimal("20000.00"))

    def test_registrar_venta_rechaza_stock_insuficiente(self):
        response = self.client.post(
            reverse("registrar_venta", args=[self.producto.pk]),
            {
                "cantidad": "6",
                "rut": "12.345.678-9",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No hay stock suficiente")
        self.assertEqual(Venta.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

    def test_cliente_no_habitual_solo_conserva_rut(self):
        response = self.client.post(
            reverse("registrar_venta", args=[self.producto.pk]),
            {
                "cantidad": "1",
                "rut": "98.765.432-1",
            },
        )

        self.assertRedirects(response, reverse("producto_list"))
        cliente = Cliente.objects.get(rut="98.765.432-1")
        self.assertFalse(cliente.habitual)
        self.assertIsNone(cliente.nombre)
        self.assertIsNone(cliente.telefono)

    def test_listado_publico_muestra_solo_productos_activos(self):
        Producto.objects.create(
            nombre="Producto inactivo",
            sku="INACT-001",
            precio=Decimal("5000.00"),
            stock=2,
            activo=False,
        )

        response = self.client.get(reverse("producto_list"))

        self.assertContains(response, "Teclado")
        self.assertNotContains(response, "Producto inactivo")

    def test_listado_publico_pagina_productos(self):
        for index in range(11):
            Producto.objects.create(
                nombre=f"Producto adicional {index}",
                sku=f"AD-{index}",
                precio=Decimal("1000.00"),
                stock=5,
                activo=True,
            )

        response = self.client.get(reverse("producto_list"), {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertTrue(response.context["page_obj"].has_previous())

    def test_eliminar_producto_sin_ventas(self):
        response = self.client.post(
            reverse("producto_delete", args=[self.producto.pk]),
        )

        self.assertRedirects(response, reverse("producto_list"))
        self.assertFalse(Producto.objects.filter(pk=self.producto.pk).exists())

    def test_eliminar_producto_con_ventas_muestra_mensaje(self):
        venta = Venta.objects.create(cliente=self.cliente)
        DetalleVenta.objects.create(
            venta=venta,
            producto=self.producto,
            cantidad=1,
            precio_unitario=self.producto.precio,
        )

        response = self.client.post(
            reverse("producto_delete", args=[self.producto.pk]),
            follow=True,
        )

        self.assertContains(response, "tiene ventas asociadas")
        self.assertTrue(Producto.objects.filter(pk=self.producto.pk).exists())

    def test_eliminar_producto_ya_eliminado_redirige_con_mensaje(self):
        producto_id = self.producto.pk
        self.producto.delete()

        response = self.client.post(
            reverse("producto_delete", args=[producto_id]),
            follow=True,
        )

        self.assertContains(response, "ya no existe o ya fue eliminado")

    def test_inline_calcula_y_rechaza_stock_insuficiente(self):
        venta = Venta.objects.create(cliente=self.cliente)
        formset_class = inlineformset_factory(
            Venta,
            DetalleVenta,
            formset=DetalleVentaInlineFormSet,
            fields=("producto", "cantidad", "precio_unitario"),
            extra=1,
        )
        formset = formset_class(
            {
                "detalles-TOTAL_FORMS": "1",
                "detalles-INITIAL_FORMS": "0",
                "detalles-MIN_NUM_FORMS": "0",
                "detalles-MAX_NUM_FORMS": "1000",
                "detalles-0-producto": str(self.producto.pk),
                "detalles-0-cantidad": "6",
                "detalles-0-precio_unitario": "10000.00",
            },
            instance=venta,
            prefix="detalles",
        )

        self.assertFalse(formset.is_valid())
        self.assertIn("Stock insuficiente", str(formset.non_form_errors()))

    def test_exportar_ventas_csv_contiene_columnas_y_total(self):
        venta = Venta.objects.create(cliente=self.cliente)
        DetalleVenta.objects.create(
            venta=venta,
            producto=self.producto,
            cantidad=2,
            precio_unitario=Decimal("10000.00"),
        )
        request = RequestFactory().get("/admin/ventas/venta/")
        response = exportar_ventas_csv(
            None,
            request,
            Venta.objects.filter(pk=venta.pk),
        )

        content = response.content.decode("utf-8")
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("ID,Cliente,Fecha,Anulada,Total", content)
        self.assertIn("Ana Pérez", content)
        self.assertIn("20000.00", content)
