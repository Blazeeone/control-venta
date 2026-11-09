from rest_framework import routers, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Cliente, DetalleVenta, Producto, Venta
from .serializers import (
    ClienteSerializer,
    DetalleVentaSerializer,
    ProductoSerializer,
    VentaSerializer,
)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by("nombre")
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by("rut")
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.select_related("cliente").prefetch_related(
        "detalles__producto"
    ).order_by("-fecha", "-pk")
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]


class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.select_related("venta", "producto").all()
    serializer_class = DetalleVentaSerializer
    permission_classes = [IsAuthenticated]


router = routers.DefaultRouter()
router.register(r"productos", ProductoViewSet, basename="producto-api")
router.register(r"clientes", ClienteViewSet, basename="cliente-api")
router.register(r"ventas", VentaViewSet, basename="venta-api")
router.register(r"detalles-venta", DetalleVentaViewSet, basename="detalle-venta-api")
