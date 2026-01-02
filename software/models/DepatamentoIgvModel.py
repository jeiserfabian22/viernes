from django.db import models

class Detalletipoigvxdepartamento(models.Model):
    iddetalletipoigvxdepartamento = models.AutoField(primary_key=True)
    id_tipo_igv = models.IntegerField()
    iddepartamentos = models.CharField(max_length=11, db_collation='latin1_swedish_ci', db_comment='\t')

    class Meta:
        managed = True
        db_table = 'detalletipoigvxdepartamento'