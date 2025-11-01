from django.db import models
from software.models.Tipo_entidadModel import TipoEntidad
from software.models.TipoclienteModel import Tipocliente

class Cliente(models.Model):
    idcliente = models.AutoField(primary_key=True)
    idtipocliente = models.ForeignKey(Tipocliente, on_delete=models.DO_NOTHING, db_column='idtipocliente', related_name='clientes')
    numdoc = models.CharField(max_length=25)
    razonsocial = models.CharField(max_length=255)
    telefono = models.CharField(max_length=10)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    estado = models.IntegerField()
    id_tipo_entidad = models.ForeignKey(TipoEntidad, on_delete=models.DO_NOTHING, db_column='id_tipo_entidad', related_name='clientes')
    
    class Meta:
        managed = False
        db_table = 'clientes'

    def __str__(self):
        return self.razonsocial