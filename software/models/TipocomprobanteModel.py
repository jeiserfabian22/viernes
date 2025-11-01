from django.db import models

class Tipocomprobante(models.Model):
    idtipocomprobante = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=255)
    abreviatura = models.CharField(max_length=255)
    estado = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'tipocomprobante'

    def __str__(self):
        return self.nombre
    

    