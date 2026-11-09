from decimal import Decimal

from django.core.management.base import BaseCommand

from ventas.models import Cliente, Producto


PRODUCTOS = (
    ("Notebook Lenovo IdeaPad 3", "NB-LEN-001", Decimal("549990.00"), 8),
    ("Notebook HP 15", "NB-HP-002", Decimal("479990.00"), 6),
    ("Monitor LG 24 pulgadas", "MON-LG-003", Decimal("129990.00"), 12),
    ("Teclado mecánico Redragon", "TEC-RED-004", Decimal("45990.00"), 18),
    ("Mouse Logitech inalámbrico", "MOU-LOG-005", Decimal("24990.00"), 24),
    ("Audífonos Sony Bluetooth", "AUD-SON-006", Decimal("69990.00"), 15),
    ("Webcam Full HD", "WEB-FHD-007", Decimal("34990.00"), 10),
    ("Disco SSD 1 TB", "SSD-1TB-008", Decimal("89990.00"), 9),
    ("Memoria USB 128 GB", "USB-128-009", Decimal("12990.00"), 30),
    ("Cable HDMI 2 metros", "CAB-HDMI-010", Decimal("8990.00"), 35),
    ("Hub USB-C multipuerto", "HUB-USC-011", Decimal("29990.00"), 14),
    ("Silla ergonómica de oficina", "SIL-ERG-012", Decimal("159990.00"), 5),
)

CLIENTES = (
    ("Camila González", "camila.gonzalez@example.com", "11.111.111-1", "+56911111111", True),
    ("Matías Rojas", "matias.rojas@example.com", "12.222.222-2", "+56922222222", True),
    ("Sofía Martínez", "sofia.martinez@example.com", "13.333.333-3", "+56933333333", True),
    ("Diego Pérez", "diego.perez@example.com", "14.444.444-4", "+56944444444", False),
    ("Valentina Silva", "valentina.silva@example.com", "15.555.555-5", "+56955555555", True),
    ("Joaquín Torres", "joaquin.torres@example.com", "16.666.666-6", "+56966666666", False),
)


class Command(BaseCommand):
    help = "Carga productos y clientes de demostración sin duplicar registros."

    def handle(self, *args, **options):
        productos_creados = 0
        productos_actualizados = 0
        for nombre, sku, precio, stock in PRODUCTOS:
            _, creado = Producto.objects.update_or_create(
                sku=sku,
                defaults={
                    "nombre": nombre,
                    "codigo": sku,
                    "precio": precio,
                    "stock": stock,
                    "activo": True,
                },
            )
            if creado:
                productos_creados += 1
            else:
                productos_actualizados += 1

        clientes_creados = 0
        clientes_actualizados = 0
        for nombre, email, rut, telefono, habitual in CLIENTES:
            _, creado = Cliente.objects.update_or_create(
                rut=rut,
                defaults={
                    "nombre": nombre,
                    "email": email,
                    "telefono": telefono,
                    "habitual": habitual,
                },
            )
            if creado:
                clientes_creados += 1
            else:
                clientes_actualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos demo listos: {productos_creados} productos creados, "
                f"{productos_actualizados} actualizados; "
                f"{clientes_creados} clientes creados, "
                f"{clientes_actualizados} actualizados."
            )
        )
