from django.core.validators import MinValueValidator
from django.db import models


class Producto(models.Model):
    nombre = models.CharField(max_length=120, db_index=True)
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="SKU / Código")
    codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código alternativo")
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.01)],
    )
    stock = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Sincroniza sku y codigo para compatibilidad bidireccional
        if not self.sku and self.codigo:
            self.sku = self.codigo
        elif not self.codigo and self.sku:
            self.codigo = self.sku
        super().save(*args, **kwargs)

    def __str__(self):
        identificador = self.sku or self.codigo or f"ID {self.pk}"
        return f"{self.nombre} ({identificador})"


class Cliente(models.Model):
    nombre = models.CharField(max_length=120, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    rut = models.CharField(max_length=12, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    habitual = models.BooleanField(default=False)

    def __str__(self):
        if self.nombre:
            return self.nombre
        if self.rut:
            return f"Cliente {self.rut}"
        return f"Cliente #{self.pk}"


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    anulada = models.BooleanField(default=False)

    @property
    def total(self):
        return sum(d.subtotal for d in self.detalles.all())

    def __str__(self):
        return f"Venta #{self.pk} — {self.cliente}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    