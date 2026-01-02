from django import forms
from .models import Compra, Vehiculo, Repuesto
from software.models.cilindradaModel import Cilindrada
from software.models.cilindradaModel import Cilindrada

# Formulario para agregar una compra
class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['numero_compra', 'id_proveedor', 'fecha_compra']

# Formulario para agregar vehículos
class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['serie_motor', 'serie_chasis', 'estado_vehiculo', 'precio_compra', 'precio_venta', 'imperfecciones', 'cantidad']

# Formulario para agregar repuestos
class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = ['codigo_barras', 'precio_compra', 'precio_venta', 'cantidad']













