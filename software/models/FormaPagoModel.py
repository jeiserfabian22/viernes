from django.db import models


class FormaPago(models.Model):
    id_forma_pago = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    estado = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'formaspago'


        