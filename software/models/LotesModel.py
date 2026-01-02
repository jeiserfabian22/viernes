from django.db import models
from software.models.Tipo_entidadModel import TipoEntidad

class Lotes(models.Model):
    idLote = models.AutoField(primary_key=True)
    idcompradetalle = models.ForeignKey('CompraDetalle', models.DO_NOTHING, db_column='idcompradetalle')
    idproducto = models.ForeignKey('Producto', models.DO_NOTHING, db_column='idproducto')
    identificador = models.CharField(max_length=50)
    fecha_produccion = models.DateField()
    fecha_vencimiento = models.DateField()
    cantidad = models.IntegerField()
    
    class Meta:
        managed = True
        db_table = 'lotes'