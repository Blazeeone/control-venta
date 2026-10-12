from django import forms
from django.core.exceptions import ValidationError
from .models import Producto

# Formulario para el modelo Producto para registrar y actualizar datos.
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto  
        fields = ['codigo', 'sku', 'nombre', 'precio', 'stock', 'activo']
        # Limita los campos en el HTML para evitar valores negativos
        widgets = {
            'precio': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        codigo = cleaned_data.get('codigo')
        sku = cleaned_data.get('sku')
        if not codigo and not sku:
            raise ValidationError("Debes ingresar al menos un Código o SKU para el producto.")
        return cleaned_data

    # Valida mediante estructuras de decisión que el precio sea mayor a 0
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio <= 0:
            raise ValidationError("El precio debe ser estrictamente mayor a 0.")
        return precio

    # Valida que el stock no sea negativo (permite 0 por si el producto se agota)
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise ValidationError("El stock no puede ser un valor negativo.")
        return stock


class RegistrarVentaForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad a vender",
        widget=forms.NumberInput(attrs={"min": 1}),
    )
    rut = forms.CharField(
        max_length=12,
        label="RUT del cliente",
        widget=forms.TextInput(attrs={"placeholder": "12.345.678-9"}),
    )
    es_habitual = forms.BooleanField(
        required=False,
        label="¿Es cliente habitual?",
    )
    nombre = forms.CharField(
        max_length=120,
        required=False,
        label="Nombre",
    )
    telefono = forms.CharField(
        max_length=15,
        required=False,
        label="Teléfono",
    )

    def __init__(self, *args, stock_disponible=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.stock_disponible = stock_disponible
        self.fields["cantidad"].widget.attrs["max"] = stock_disponible

    def clean_rut(self):
        rut = self.cleaned_data["rut"].strip()
        if len(rut) < 7:
            raise ValidationError("Ingresa un RUT válido.")
        return rut

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get("cantidad")
        es_habitual = cleaned_data.get("es_habitual")
        nombre = cleaned_data.get("nombre", "").strip()
        telefono = cleaned_data.get("telefono", "").strip()

        if cantidad is not None and cantidad > self.stock_disponible:
            self.add_error(
                "cantidad",
                f"No hay stock suficiente. Disponible: {self.stock_disponible}.",
            )

        if es_habitual:
            if not nombre:
                self.add_error(
                    "nombre",
                    "El nombre es obligatorio para un cliente habitual.",
                )
            if not telefono:
                self.add_error(
                    "telefono",
                    "El teléfono es obligatorio para un cliente habitual.",
                )

        cleaned_data["nombre"] = nombre
        cleaned_data["telefono"] = telefono
        return cleaned_data