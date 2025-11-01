from django.db import models


class Empresa(models.Model):
    idempresa = models.AutoField(primary_key=True)
    ruc = models.CharField(max_length=11)
    razonsocial = models.CharField(max_length=255)
    nombrecomercial = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    mododev = models.IntegerField()
    logo = models.CharField(max_length=255)
    telefono = models.CharField(max_length=25)
    usersec = models.CharField(max_length=255)
    passwordsec = models.CharField(max_length=255)
    ubigueo = models.CharField(max_length=10, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'empresa'