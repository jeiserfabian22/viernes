from django.db import models
from software.models.almacenesModel import Almacenes
from software.models.VehiculosModel import Vehiculo
from software.models.RespuestoCompModel import RepuestoComp
from software.models.compradetalleModel import CompraDetalle


class Stock(models.Model):
    id_stock = models.AutoField(primary_key=True)
    id_almacen = models.ForeignKey(Almacenes, on_delete=models.CASCADE, db_column='id_almacen', related_name='stocks')
    idcompradetalle = models.ForeignKey(CompraDetalle, on_delete=models.CASCADE, db_column='idcompradetalle', related_name='stocks', null=True, blank=True)
    # Producto puede ser vehículo o repuesto
    id_vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, db_column='id_vehiculo', related_name='stocks', null=True, blank=True)
    id_repuesto_comprado = models.ForeignKey(RepuestoComp, on_delete=models.CASCADE, db_column='id_repuesto_comprado', related_name='stocks', null=True, blank=True)
    cantidad_disponible = models.IntegerField(default=0, db_column='cantidad_disponible')
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True, db_column='fecha_ultima_actualizacion')
    estado = models.IntegerField(default=1, db_column='estado')
    
    class Meta:
        managed = True
        db_table = 'stock'
        
    
    def __str__(self):
        if self.id_vehiculo:
            return f"Stock: {self.id_vehiculo.idproducto.nomproducto} - {self.id_almacen.nombre_almacen} ({self.cantidad_disponible})"
        elif self.id_repuesto_comprado:
            return f"Stock: {self.id_repuesto_comprado.id_repuesto.nombre} - {self.id_almacen.nombre_almacen} ({self.cantidad_disponible})"
        return f"Stock #{self.id_stock}"
    
    def agregar_stock(self, cantidad):
        """Incrementa el stock"""
        self.cantidad_disponible += cantidad
        self.save()
    
    def descontar_stock(self, cantidad):
        """Decrementa el stock (con validación)"""
        if self.cantidad_disponible >= cantidad:
            self.cantidad_disponible -= cantidad
            self.save()
            return True
        return False
    
    @property
    def tiene_stock(self):
        """Verifica si hay stock disponible"""
        return self.cantidad_disponible > 0