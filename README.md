# Sistema de Control de Venta

Aplicación web desarrollada en Django para la digitalización y gestión de ventas de una pequeña tienda, implementando la arquitectura Modelo-Vista-Plantilla (MVT).

**Autor:** Yoshua Alberto Castillo Martínez  
**Carrera:** Analista Programador - INACAP Sede Renca  
**Asignatura:** Programación Back End (TI3041)  

## Funcionalidades Principales
* Registro de productos a vender con nombre, código, cantidad y precio.
* Actualización de stock y eliminación de productos.
* Visualización estructurada del listado de productos disponibles.
* Registro de ventas designadas a un RUT de cliente.
* Gestión de clientes con estructura de decisión: almacenamiento de datos para clientes habituales y registro de RUT exclusivo para clientes ocasionales (boleta).

## Tecnologías Utilizadas
* Backend: Python y Framework Django.
* Frontend: HTML/CSS mediante el motor de plantillas de Django.
* Base de datos: PostgreSQL (Supabase o cualquier proveedor compatible).
* Archivos estáticos: WhiteNoise y `collectstatic`.
* Despliegue: Vercel mediante `api/index.py`.
* Dependencias: `requirements.txt`.

## Configuración local

1. Clonar este repositorio.
2. Crear y activar el entorno virtual (`python -m venv .venv`).
3. Instalar las dependencias (`pip install -r requirements.txt`).
4. Crear un archivo `.env` (no se sube a Git) con una conexión PostgreSQL:

```env
DJANGO_SECRET_KEY=una-clave-secreta-larga
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://usuario:password@host:5432/base_de_datos
```

También se admiten `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_HOST` y `POSTGRES_PORT`.

5. Ejecutar las migraciones:

```powershell
python manage.py migrate
```

6. Crear el usuario del Admin:

```powershell
python manage.py createsuperuser
```

7. Preparar archivos estáticos:

```powershell
python manage.py collectstatic --noinput
```

8. Levantar el servidor:

```powershell
python manage.py runserver
```

## Funcionalidades evaluables

### CRUD y validaciones

* Productos: crear, listar, editar y eliminar.
* Validación de código/SKU, precio positivo y stock no negativo.
* Ventas asociadas a RUT de cliente.
* Cliente habitual: guarda nombre y teléfono.
* Cliente ocasional: guarda solo el RUT.
* Stock protegido mediante transacción y bloqueo de fila.
* Mensajes de éxito y error para cada operación.
* Listado público paginado.

### Django Admin

* Búsqueda por producto, SKU, cliente e ID de venta.
* Filtros por activo, stock, cliente habitual y ventas anuladas.
* Inline de `DetalleVenta` con subtotal de solo lectura.
* Validación de stock en el inline.
* Acciones masivas para anular y exportar CSV.
* Reporte de ventas por rango de fechas en `/admin/ventas/venta/reporte/`.
* Branding oscuro personalizado.

## Pruebas

```powershell
python manage.py check
python manage.py test ventas --keepdb
```

Las pruebas cubren el CRUD de productos, validaciones, clientes habituales y
ocasionales, actualización de stock, subtotal, validación del inline y CSV.

## Despliegue en Vercel

1. Importar el repositorio en Vercel.
2. Configurar las variables `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`,
   `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` y `DATABASE_URL`.
3. Configurar el dominio de Vercel en `DJANGO_ALLOWED_HOSTS`.
4. Configurar el dominio HTTPS completo en `DJANGO_CSRF_TRUSTED_ORIGINS`.
5. Vercel usará `api/index.py`; WhiteNoise servirá los archivos recolectados.
6. Ejecutar migraciones en la base PostgreSQL antes de usar la URL pública.

Los logs de Django se envían a la salida estándar, que queda disponible en los
logs operativos de Vercel.

## Presentación de resultados

Para demostrar el flujo completo:

1. Crear un producto activo.
2. Crear una venta desde el producto y comprobar la disminución del stock.
3. Repetir con un cliente habitual y verificar sus datos en Admin.
4. Repetir con un cliente ocasional y verificar que se conserve solo el RUT.
5. Abrir una venta en Admin y mostrar el subtotal del inline.
6. Intentar vender más stock y mostrar el error de validación.
7. Exportar ventas seleccionadas y abrir `ventas.csv`.
8. Abrir el reporte de ventas y consultar un rango de fechas.

## Autor

Yoshua Alberto Castillo Martínez
1. Clonar este repositorio.
2. Crear y activar el entorno virtual (`python -m venv venv`).
3. Instalar las dependencias (`pip install django`).
4. Aplicar las migraciones de la base de datos (`python manage.py migrate`).
5. Levantar el servidor de desarrollo (`python manage.py runserver`).
