from rest_framework import routers, viewsets

from .models import Producto, Cliente, Venta, DetalleVenta
from .serializers import ProductoSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ProductoSerializer

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = ProductoSerializer

class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.all()
    serializer_class = ProductoSerializer

router = routers.DefaultRouter()
router.register(r'productos',ProductoViewSet)

router = routers.DefaultRouter()
router.register(r'Cliente',ClienteViewSet)

router = routers.DefaultRouter()
router.register(r'Venta',VentaViewSet)

router = routers.DefaultRouter()
router.register(r'DetalleVenta',DetalleVentaViewSet)