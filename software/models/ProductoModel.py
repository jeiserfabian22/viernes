
from django.db import models

from software.models.categoriaModel import Categoria
from software.models.UnidadesModel import Unidades
from software.models.marcaModel import Marca
from software.models.cilindradaModel import Cilindrada
from software.models.colorModel import Color

class Producto(models.Model):
    idproducto = models.AutoField(primary_key=True, db_column='idproducto')
    nomproducto = models.CharField(max_length=255, db_column='nomproducto')
    imagenprod = models.CharField(max_length=255, db_column='imagenprod')
    estado = models.IntegerField(db_column='estado')
    idcategoria = models.ForeignKey(Categoria, on_delete=models.DO_NOTHING, db_column='idcategoria', related_name='productos')
    idunidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, db_column='idunidad', related_name='productos')
    idmarca = models.ForeignKey(Marca, on_delete=models.DO_NOTHING, db_column='idmarca', related_name='productos')
    idcilindrada = models.ForeignKey(Cilindrada, on_delete=models.DO_NOTHING, db_column='idcilindrada', related_name='productos')
    idcolor = models.ForeignKey(Color, on_delete=models.DO_NOTHING, db_column='idcolor', related_name='productos')
    
    class Meta:
        managed = True
        db_table = 'producto'
        indexes = [models.Index(fields=['nomproducto'])]
