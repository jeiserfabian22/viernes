from datetime import datetime
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from software.models.comprasModel import Compras
from software.models.ProveedoresModel import Proveedores
from software.models.TipoclienteModel import Tipocliente
from software.models.ProductoModel import Producto
from software.models.categoriaModel import Categoria
from software.models.compradetalleModel import CompraDetalle
from software.models.VentasModel import Ventas
from software.models.VentaDetalleModel import VentaDetalle
from software.models.UsuarioModel import Usuario
from software.models.UnidadesModel import Unidades
from software.models.TipousuarioModel import Tipousuario
from software.models.TipodocumentoModel import Tipodocumento
from software.models.TipoclienteModel import Tipocliente
from software.models.ProveedoresModel import Proveedores
from software.models.NumserieModel import Numserie
from software.models.ModulosModel import Modulos
from software.models.empresaModel import Empresa
from software.models.empleadoModel import Empleado

from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.detallecategoriaxunidadesModel import Detallecategoriaxunidades
from software.models.departamentosModel import Departamentos
from software.models.codigocorreoModel import CodigoCorreo
from django.db import connection
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

# Importar las utilidades de cifrado
from software.utils.encryption_utils import EncryptionManager, PasswordManager


def usuarios(request):
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        usuarios_db = Usuario.objects.filter(estado=1)
        
        # Descifrar correos para mostrarlos en la vista
        usuarios = []
        for usuario in usuarios_db:
            usuario.correo_descifrado = EncryptionManager.decrypt_email(usuario.correo)
            usuarios.append(usuario)
        
        tipoUsuarios = Tipousuario.objects.filter(estado=1)
        data = {
            'usuarios': usuarios,
            'tipoUsuarios': tipoUsuarios,
            'permisos': permisos
        }
        return render(request, 'usuarios/usuarios.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")


def agregar(request):
    if request.method == "POST":
        try:
            nombreUsuario = request.POST.get('nombreUsuario2')
            correoUsuario = request.POST.get('correoUsuario2')
            contrasenaUsuario = request.POST.get('contrasenaUsuario2')
            tipoUsuario = request.POST.get('tipoUsuario2')
            celularUsuario = request.POST.get('celularUsuario2')
            dniUsuario = request.POST.get('dniUsuario2')

            # Validaciones básicas
            if not all([nombreUsuario, correoUsuario, contrasenaUsuario, tipoUsuario, celularUsuario, dniUsuario]):
                return JsonResponse({"error": "Todos los campos son requeridos"}, status=400)

            # Cifrar el correo electrónico
            correo_cifrado = EncryptionManager.encrypt_email(correoUsuario)
            if not correo_cifrado:
                return JsonResponse({"error": "Error al cifrar el correo electrónico"}, status=400)
            
            # Hashear la contraseña
            contrasena_hasheada = PasswordManager.hash_password(contrasenaUsuario)
            if not contrasena_hasheada:
                return JsonResponse({"error": "Error al procesar la contraseña"}, status=400)

            # Traer la instancia de tipo usuario
            getTipoUsuario = get_object_or_404(Tipousuario, idtipousuario=tipoUsuario)

            # Crear el usuario con datos cifrados
            usuario = Usuario.objects.create(
                nombrecompleto=nombreUsuario,
                correo=correo_cifrado,  # Correo cifrado
                contrasena=contrasena_hasheada,  # Contraseña hasheada
                idtipousuario=getTipoUsuario,
                celular=celularUsuario,
                dni=dniUsuario,
                estado=1
            )
            usuario.save()
            
            return JsonResponse({
                "message": "Usuario agregado exitosamente",
                "id": usuario.idusuario
            }, status=201)
            
        except Exception as e:
            return JsonResponse({"error": f"Error al crear usuario: {str(e)}"}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)


def editar(request):
    if request.method == "POST":
        try:
            idUsuario = request.POST.get('idusuario')
            nombreUsuario = request.POST.get('nombreUsuario')
            correoUsuario = request.POST.get('correoUsuario')
            contrasenaUsuario = request.POST.get('contrasenaUsuario')
            tipoUsuario = request.POST.get('tipoUsuario')
            celularUsuario = request.POST.get('celularUsuario')
            dniUsuario = request.POST.get('dniUsuario')

            # Validaciones básicas
            if not all([idUsuario, nombreUsuario, correoUsuario, tipoUsuario, celularUsuario, dniUsuario]):
                return JsonResponse({"error": "Todos los campos son requeridos"}, status=400)

            # Obtener el usuario existente
            usuario = get_object_or_404(Usuario, idusuario=idUsuario)
            
            # Traer la instancia de tipo usuario
            getTipoUsuario = get_object_or_404(Tipousuario, idtipousuario=tipoUsuario)

            # Actualizar campos básicos
            usuario.nombrecompleto = nombreUsuario
            usuario.idtipousuario = getTipoUsuario
            usuario.celular = celularUsuario
            usuario.dni = dniUsuario
            
            # Verificar si el correo cambió
            correo_actual_descifrado = EncryptionManager.decrypt_email(usuario.correo)
            if correo_actual_descifrado != correoUsuario:
                # Cifrar el nuevo correo
                correo_cifrado = EncryptionManager.encrypt_email(correoUsuario)
                if not correo_cifrado:
                    return JsonResponse({"error": "Error al cifrar el correo electrónico"}, status=400)
                usuario.correo = correo_cifrado
            
            # Verificar si la contraseña cambió
            # Si la contraseña recibida no está hasheada (no empieza con pbkdf2_), hashearla
            if contrasenaUsuario and not contrasenaUsuario.startswith('pbkdf2_'):
                contrasena_hasheada = PasswordManager.hash_password(contrasenaUsuario)
                if not contrasena_hasheada:
                    return JsonResponse({"error": "Error al procesar la contraseña"}, status=400)
                usuario.contrasena = contrasena_hasheada
            
            usuario.save()
            
            return JsonResponse({
                "message": "Usuario editado exitosamente",
                "id": usuario.idusuario
            }, status=200)
            
        except Exception as e:
            return JsonResponse({"error": f"Error al editar usuario: {str(e)}"}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)


def eliminar(request, id):
    if request.method == "GET":
        try:
            usuario = get_object_or_404(Usuario, idusuario=id)
            usuario.estado = 0
            usuario.save()
            return JsonResponse({"message": "Usuario eliminado exitosamente"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)


def login_usuario(correo_plano, contrasena_plana):
    """
    Función auxiliar para validar el login de un usuario
    Args:
        correo_plano (str): Correo en texto plano
        contrasena_plana (str): Contraseña en texto plano
    Returns:
        Usuario o None
    """
    try:
        # Buscar todos los usuarios activos
        usuarios = Usuario.objects.filter(estado=1)
        
        for usuario in usuarios:
            # Descifrar el correo de cada usuario
            correo_descifrado = EncryptionManager.decrypt_email(usuario.correo)
            
            # Si el correo coincide, verificar la contraseña
            if correo_descifrado == correo_plano:
                if PasswordManager.verify_password(contrasena_plana, usuario.contrasena):
                    return usuario
        
        return None
    except Exception as e:
        print(f"Error en login: {e}")
        return None