from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Ciudad(models.Model):
    nombre = models.TextField(max_length=255)

    def __str__(self):
        return self.nombre

class ListaNegra(models.Model):
    patente = models.TextField(max_length=6)
    motivo = models.TextField(max_length=255)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    ciudad = models.TextField(max_length=255)

    def __str__(self):
        return self.patente

class Infraccion(models.Model):
    nombre = models.TextField(max_length=255)
    descripcion = models.TextField(max_length=255)

class Carpeta(models.Model):
    nombre = models.TextField(max_length=255)
    ubicacion = models.TextField(max_length=255)
    ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

class CarpetaUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE)

    def __str__(self):
        return self.usuario

class Alerta(models.Model):
    ciudad_envia = models.ForeignKey(Ciudad, related_name='alertas_enviadas', on_delete=models.CASCADE)
    ciudad_recibe = models.ForeignKey(Ciudad, related_name='alertas_recibidas', on_delete=models.CASCADE)
    fecha= models.DateTimeField()
    patente = models.TextField()
    comentario = models.TextField()
    visto = models.IntegerField() #1 es visto - 2 es no visto
    imagen = models.TextField()

    def __str__(self):
        return self.estado

class Registro(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    patente = models.TextField(max_length=6)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    imagen = models.TextField()
    infraccion = models.ForeignKey(Infraccion, on_delete=models.CASCADE)
    observacion = models.TextField(max_length=255)

    def __str__(self):
        return self.patente
    
    def formato_fecha_hora(self):
        return self.fecha_hora.strftime('%d/%m/%Y %H:%M:%S')
    

class CiudadVecina(models.Model):
    origen = models.ForeignKey(Ciudad, on_delete=models.CASCADE, related_name='origen')
    destino = models.ForeignKey(Ciudad, on_delete=models.CASCADE, related_name='destino')


    def __str__(self):
        return self.origen

class Fallo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE)

    def formato_fh_fallo(self):
        return self.fecha_hora.strftime('%d/%m/%Y %H:%M:%S')