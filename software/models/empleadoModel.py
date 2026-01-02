from django.db import models
class Empleado(models.Model):
    empleado = models.OneToOneField('Empresa', models.DO_NOTHING, primary_key=True)
    idempresa = models.IntegerField(blank=True, null=True)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=75, blank=True, null=True)
    telefono = models.CharField(max_length=9, blank=True, null=True)
    direccion = models.CharField(max_length=75, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'empleado'