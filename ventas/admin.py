import csv
import logging
from datetime import date
from decimal import Decimal

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path
from django.utils.dateparse import parse_date

from .models import Producto, Cliente, Venta, DetalleVenta

logger = logging.getLogger(__name__)

admin.site.site_header = "Panel Interno - Control de Ventas"
admin.site.site_title = "Admin Control de Ventas"
admin.site.index_title = "Operaciones"


class StockBajoFilter(SimpleListFilter):
    title = "stock"
    parameter_name = "stock"

    def lookups(self, request, model_admin):
        return (
            ("bajo", "Menos de 10"),
            ("sin", "Sin stock"),
        )

    def queryset(self, request, queryset):
        if self.value() == "bajo":
            return queryset.filter(stock__lt=10)
        if self.value() == "sin":
            return queryset.filter(stock=0)
        return queryset


@admin.action(description="Anular ventas seleccionadas")
def marcar_anuladas(modeladmin, request, queryset):
    updated = queryset.update(anulada=True)
    modeladmin.message_user(request, f"{updated} ventas anuladas.")


@admin.action(description="Exportar ventas a CSV")
def exportar_ventas_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ventas.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Cliente", "Fecha", "Anulada", "Total"])

    ventas = queryset.select_related("cliente").prefetch_related("detalles__producto")
    for venta in ventas:
        writer.writerow(
            [
                venta.id,
                venta.cliente.nombre,
                venta.fecha,
                venta.anulada,
                venta.total,
            ]
        )

    return response


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sku", "codigo", "precio", "stock", "activo")
    search_fields = ("nombre", "sku", "codigo")
    list_filter = ("activo", StockBajoFilter)
    ordering = ("nombre",)
    list_per_page = 25
    autocomplete_fields = ()
    fieldsets = (
        ("Datos básicos", {"fields": ("nombre", "sku", "codigo", "precio")}),
        ("Inventario", {"fields": ("stock", "activo")}),
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "email", "telefono", "habitual")
    search_fields = ("nombre", "rut", "email")
    list_filter = ("habitual",)
    fieldsets = (
        ("Datos personales", {"fields": ("nombre", "rut", "email", "telefono")}),
        ("Cliente habitual", {"fields": ("habitual",)}),
    )
    list_per_page = 25


class DetalleVentaInlineFormSet(BaseInlineFormSet):
    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        cantidades_por_producto = {}
        productos = {}

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            producto = form.cleaned_data.get("producto")
            cantidad = form.cleaned_data.get("cantidad")
            if producto is None or cantidad is None:
                continue

            cantidades_por_producto[producto.pk] = (
                cantidades_por_producto.get(producto.pk, 0) + cantidad
            )
            productos[producto.pk] = producto

        for producto_id, cantidad_total in cantidades_por_producto.items():
            producto = productos[producto_id]
            if cantidad_total > producto.stock:
                raise ValidationError(
                    f"Stock insuficiente para {producto} "
                    f"(disponible: {producto.stock})."
                )


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    formset = DetalleVentaInlineFormSet
    extra = 1
    autocomplete_fields = ("producto",)
    readonly_fields = ("subtotal",)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    change_list_template = "admin/ventas/venta/change_list.html"
    date_hierarchy = "fecha"
    list_display = ("id", "cliente", "fecha", "anulada", "total_display")
    search_fields = ("cliente__nombre", "id")
    list_filter = ("anulada",)
    inlines = [DetalleVentaInline]
    actions = [marcar_anuladas, exportar_ventas_csv]
    list_per_page = 25
    readonly_fields = ("fecha", "total_display")
    fieldsets = (
        ("Datos de la venta", {"fields": ("cliente", "fecha", "anulada")}),
        ("Resumen", {"fields": ("total_display",)}),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("cliente").prefetch_related(
            "detalles__producto"
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "reporte/",
                self.admin_site.admin_view(self.reporte_view),
                name="ventas_venta_reporte",
            ),
        ]
        return custom_urls + urls

    def reporte_view(self, request):
        fecha_desde = parse_date(request.GET.get("desde", ""))
        fecha_hasta = parse_date(request.GET.get("hasta", ""))
        errores = []
        if request.GET.get("desde") and fecha_desde is None:
            errores.append("La fecha inicial no es válida.")
        if request.GET.get("hasta") and fecha_hasta is None:
            errores.append("La fecha final no es válida.")
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            errores.append("La fecha inicial no puede ser posterior a la fecha final.")

        ventas = self.get_queryset(request)
        if not errores:
            if fecha_desde:
                ventas = ventas.filter(fecha__date__gte=fecha_desde)
            if fecha_hasta:
                ventas = ventas.filter(fecha__date__lte=fecha_hasta)

        total = sum((venta.total for venta in ventas), Decimal("0.00"))
        context = {
            **self.admin_site.each_context(request),
            "title": "Reporte de ventas",
            "opts": self.model._meta,
            "ventas": ventas,
            "total_ventas": total,
            "cantidad_ventas": ventas.count() if not errores else 0,
            "fecha_desde": request.GET.get("desde", ""),
            "fecha_hasta": request.GET.get("hasta", ""),
            "errores": errores,
        }
        return render(request, "admin/ventas/venta/report.html", context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        action = "actualizada" if change else "creada"
        logger.info(
            "Venta %s %s desde Admin por %s.",
            obj.pk,
            action,
            request.user.get_username(),
        )

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(description="Total", ordering="id")
    def total_display(self, obj):
        return f"${obj.total:,.0f}"


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ("venta", "producto", "cantidad", "precio_unitario", "subtotal")
    readonly_fields = ("subtotal",)
    fieldsets = (
        ("Detalle", {"fields": ("venta", "producto", "cantidad", "precio_unitario")}),
        ("Calculado", {"fields": ("subtotal",)}),
    )