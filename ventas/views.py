from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Producto, Cliente, Venta, DetalleVenta
from .forms import ProductoForm, RegistrarVentaForm


def api_client(request):
    return render(request, "ventas/api_client.html")


def ventas_list(request):
    """Muestra el historial de ventas registradas."""
    ventas = (
        Venta.objects.select_related("cliente")
        .prefetch_related("detalles__producto")
        .order_by("-fecha", "-pk")
    )
    consulta = request.GET.get("q", "").strip()
    if consulta:
        ventas = ventas.filter(
            Q(cliente__rut__icontains=consulta)
            | Q(cliente__nombre__icontains=consulta)
            | Q(detalles__producto__nombre__icontains=consulta)
            | Q(pk__icontains=consulta)
        ).distinct()

    paginator = Paginator(ventas, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    total_periodo = sum((venta.total for venta in page_obj.object_list), 0)
    return render(
        request,
        "ventas/venta_list.html",
        {
            "object_list": page_obj.object_list,
            "page_obj": page_obj,
            "consulta": consulta,
            "total_periodo": total_periodo,
        },
    )


def venta_detail(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related("cliente").prefetch_related(
            "detalles__producto"
        ),
        pk=pk,
    )
    return render(request, "ventas/venta_detail.html", {"venta": venta})

# READ (list): Mostrar listado de productos disponibles
def producto_list(request):
    productos = Producto.objects.filter(activo=True).order_by("nombre")
    paginator = Paginator(productos, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "ventas/producto_list.html",
        {"object_list": page_obj.object_list, "page_obj": page_obj},
    )

# READ (detail): Ver detalle de un producto
def producto_detail(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'ventas/producto_detail.html', {'object': producto})

# CREATE: Registrar el producto a vender con nombre, código, cantidad y precio
@csrf_protect
def producto_create(request):
    """Vista protegida con CSRF"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente')
            return redirect('producto_list')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = ProductoForm()
    
    return render(request, 'ventas/producto_form.html', {'form': form})

# UPDATE: Permitir actualizar stock y otros datos del producto
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente.')
            return redirect('producto_list')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'ventas/producto_form.html', {'form': form})

# DELETE: Permitir eliminar productos
def producto_delete(request, pk):
    producto = Producto.objects.filter(pk=pk).first()

    if producto is None:
        if request.method == "POST":
            messages.warning(
                request,
                "El producto ya no existe o ya fue eliminado.",
            )
            return redirect("producto_list")
        raise Http404("No existe el producto solicitado.")

    if request.method == "POST":
        try:
            producto.delete()
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar este producto porque tiene ventas asociadas. "
                "Puedes marcarlo como inactivo.",
            )
            return redirect("producto_list")

        messages.success(
            request,
            f'Producto "{producto.nombre}" eliminado correctamente.',
        )
        return redirect("producto_list")

    return render(
        request,
        "ventas/producto_confirm_delete.html",
        {"object": producto},
    )

# VENTA (Caso 2): Registrar venta, actualizar stock y manejar cliente
@csrf_protect
def registrar_venta(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)

    if request.method == 'POST':
        form = RegistrarVentaForm(
            request.POST,
            stock_disponible=producto.stock,
        )
        if form.is_valid():
            with transaction.atomic():
                producto = Producto.objects.select_for_update().get(
                    pk=producto.pk,
                    activo=True,
                )
                cantidad = form.cleaned_data["cantidad"]
                if cantidad > producto.stock:
                    form.add_error(
                        "cantidad",
                        f"No hay stock suficiente. Disponible: {producto.stock}.",
                    )
                else:
                    cliente, _ = Cliente.objects.get_or_create(
                        rut=form.cleaned_data["rut"],
                    )
                    cliente.habitual = form.cleaned_data["es_habitual"]
                    if cliente.habitual:
                        cliente.nombre = form.cleaned_data["nombre"]
                        cliente.telefono = form.cleaned_data["telefono"]
                    else:
                        cliente.nombre = None
                        cliente.telefono = None
                    cliente.save()

                    producto.stock -= cantidad
                    producto.save(update_fields=["stock"])

                    venta = Venta.objects.create(cliente=cliente)
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio,
                    )

                    messages.success(
                        request,
                        f"Venta #{venta.pk} registrada con éxito. Stock actualizado.",
                    )
                    return redirect("producto_list")
    else:
        form = RegistrarVentaForm(
            initial={"cantidad": 1},
            stock_disponible=producto.stock,
        )

    return render(
        request,
        "ventas/registrar_venta.html",
        {"producto": producto, "form": form},
    )