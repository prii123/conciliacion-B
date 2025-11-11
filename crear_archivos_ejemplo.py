import pandas as pd
from datetime import datetime, timedelta

# Crear datos de ejemplo para movimientos bancarios
movimientos_ejemplo = [
    {
        'fecha': '15-11-2024',
        'descripcion': 'Transferencia Electrónica - Cliente ABC',
        'valor': 150000,
        'es': 'E'
    },
    {
        'fecha': '15-11-2024',
        'descripcion': 'Pago Nomina Empleados',
        'valor': 2500000,
        'es': 'S'
    },
    {
        'fecha': '16-11-2024',
        'descripcion': 'Deposito Efectivo Sucursal',
        'valor': 450000,
        'es': 'E'
    },
    {
        'fecha': '16-11-2024',
        'descripcion': 'Comisión Bancaria Mensual',
        'valor': 25000,
        'es': 'S'
    },
    {
        'fecha': '17-11-2024',
        'descripcion': 'Pago Proveedor XYZ',
        'valor': 320000,
        'es': 'S'
    },
    {
        'fecha': '17-11-2024',
        'descripcion': 'Ingreso por Ventas',
        'valor': 780000,
        'es': 'E'
    },
    {
        'fecha': '18-11-2024',
        'descripcion': 'Transferencia a Cuenta Ahorros',
        'valor': 100000,
        'es': 'S'
    },
    {
        'fecha': '18-11-2024',
        'descripcion': 'Rendimientos CDT',
        'valor': 50000,
        'es': 'E'
    }
]

# Crear DataFrame
df = pd.DataFrame(movimientos_ejemplo)

# Guardar como Excel
df.to_excel('ejemplo_movimientos_banco.xlsx', index=False)

print("Archivo 'ejemplo_movimientos_banco.xlsx' creado exitosamente")
print("\nEstructura del archivo:")
print(f"Columnas: {list(df.columns)}")
print(f"Número de registros: {len(df)}")
print("\nPrimeras 3 filas:")
print(df.head(3))

# Crear también ejemplo para movimientos auxiliares
movimientos_auxiliar = [
    {
        'fecha': '15-11-2024',
        'descripcion': 'Venta de Contado - Factura 001',
        'valor': 180000,
        'es': 'E'
    },
    {
        'fecha': '15-11-2024',
        'descripcion': 'Compra Materia Prima',
        'valor': 95000,
        'es': 'S'
    },
    {
        'fecha': '16-11-2024',
        'descripcion': 'Pago Servicios Públicos',
        'valor': 85000,
        'es': 'S'
    },
    {
        'fecha': '16-11-2024',
        'descripcion': 'Ingreso Servicios Prestados',
        'valor': 220000,
        'es': 'E'
    },
    {
        'fecha': '17-11-2024',
        'descripcion': 'Gastos Administrativos',
        'valor': 45000,
        'es': 'S'
    },
    {
        'fecha': '17-11-2024',
        'descripcion': 'Recuperación Cartera',
        'valor': 150000,
        'es': 'E'
    }
]

df_auxiliar = pd.DataFrame(movimientos_auxiliar)
df_auxiliar.to_excel('ejemplo_movimientos_auxiliar.xlsx', index=False)

print("\nArchivo 'ejemplo_movimientos_auxiliar.xlsx' creado exitosamente")
print(f"Número de registros auxiliares: {len(df_auxiliar)}")

print("\n✓ Ambos archivos incluyen todas las columnas requeridas:")
print("  - fecha: Formato DD-MM-YYYY")
print("  - descripcion: Texto descriptivo")
print("  - valor: Valores numéricos")
print("  - es: 'E' para Entradas, 'S' para Salidas")
print("\nEstos archivos están listos para usar con la validación validar_excel()")