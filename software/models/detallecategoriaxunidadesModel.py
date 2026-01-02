from django.db import models

from software.models.categoriaModel import Categoria
class Detallecategoriaxunidades(models.Model):
    iddetallecategoriaxunidades = models.AutoField(primary_key=True)
    idcategoria = models.ForeignKey(Categoria, models.DO_NOTHING, db_column='idcategoria')
    idunidad = models.ForeignKey('Unidades', models.DO_NOTHING, db_column='idunidad')

    class Meta:
        managed = True
        db_table = 'detallecategoriaxunidades'