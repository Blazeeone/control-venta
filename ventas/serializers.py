from rest_framework import serializers

from .models import Producto, Cliente, Venta, DetalleVenta

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        frields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        frields = '__all__'

class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        frields = '__all__'

class DetalleVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleVenta
        frields = '__all__'
        