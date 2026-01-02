# software/urls.py - VERSIÓN OFUSCADA CON IDS ENCRIPTADOS

from django.urls import path

from .views import login
from .views import categorias
from .views import marcas
from .views import colores
from .views import cilindradas
from .views import estadoproductos
from .views import configuracion
from .views import compras
from .views import productos
from .views import repuestos
from .views import unidades
from .views import usuarios
from .views import ventas
from .views import permisos
from .views import cpanel
from .views import tipoUsuarios
from .views import registroCaja
from .views import stock
from .views import password_reset
from .views import transferencias
from .views import movimientosCaja
from .views import creditos
from .views import clientes
from .views import proveedores
from .views import imposicionPlacas
from .views import regiones
from .views import provincias
from .views import distritos
from .views import sucursales
from .views import almacenes
from .views import cajas
from .views import historialCajas
from .views import tipo_comprobante
from .views import serie_comprobante
from .views import registro
from .views import firmaDigital


urlpatterns = [
    # ============================================
    # LOGIN Y AUTENTICACIÓN
    # ============================================
    path('', login.index, name="index"),
    path('auth/in/', login.login, name="login"),
    path('auth/out/', login.logout, name="logout"),
    
    # Registro de usuarios
    path('auth/reg/', registro.registro_usuario, name='registro_usuario'),
    path('api/dni/', registro.autocompletar_dni_registro, name='autocompletar_dni_registro'),
    path('api/perms/', registro.verificar_permisos_usuario, name='verificar_permisos'),
    path('api/dni/', registro.autocompletar_dni_registro, name='autocompletar_dni_registro'),
    
    # Autenticación 2FA
    path('auth/2fa/', login.verificar_2fa, name="verificar_2fa"),
    path('auth/2fa/resend/', login.reenviar_codigo_2fa, name="reenviar_codigo_2fa"),
    path('auth/2fa/cancel/', login.cancelar_2fa, name="cancelar_2fa"),
    
    # Recuperación de contraseña
    path('auth/reset/', password_reset.solicitar_recuperacion, name="solicitar_recuperacion"),
    path('auth/reset/<str:token>/', password_reset.restablecer_contrasena, name="restablecer_contrasena"),

    # ============================================
    # API - MANEJO DE CAJA
    # ============================================
    path('api/caja/datos/', login.obtener_datos_apertura, name="obtener_datos_apertura"),
    path('api/caja/list/', login.obtener_cajas_almacenes, name="obtener_cajas_almacenes"),
    path('api/ctx/change/', login.cambiar_contexto, name="cambiar_contexto"),
    path('api/caja/open/', login.abrir_caja, name="abrir_caja"),
    path('api/caja/close/', login.cerrar_caja, name="cerrar_caja"),
    path('api/caja/balance/', login.obtener_saldo_actual, name='obtener_saldo_actual'),

    # ============================================
    # PANEL DE CONTROL
    # ============================================
    path('sys/home/', cpanel.cpanel, name="cpanel"),

    # ============================================
    # MÓDULO: VENTAS (vnt)
    # ============================================
    path('sys/vnt/', ventas.ventas, name="ventas"),
    path('sys/vnt/new/', ventas.nueva_venta, name="nuevaVenta"),
    path('sys/vnt/series/', ventas.obtener_series, name="obtenerSeries"),
    path('sys/vnt/print/<str:eid>/', ventas.imprimir_comprobante, name="imprimir_comprobante"),
    path('sys/vnt/get/<str:eid>/', ventas.obtener_venta, name='obtener_venta'),
    path('sys/vnt/upd/<str:eid>/', ventas.actualizar_venta, name='actualizar_venta'),
    path('sys/vnt/del/<str:eid>/', ventas.eliminar_venta, name='eliminar_venta'),

    # ============================================
    # MÓDULO: COMPRAS (cmp)
    # ============================================
    path('sys/cmp/', compras.compras, name="compras"),
    path('sys/cmp/new/', compras.nueva_compra, name="agregarCompras"),
    path('api/cmp/get/<str:eid>/', compras.obtener_compra, name='obtener_compra'),
    path('sys/cmp/upd/<str:eid>/', compras.actualizar_compra, name='actualizar_compra'),
    path('sys/cmp/del/<str:eid>/', compras.eliminar_compra, name='eliminar_compra'),
    
    # ============================================
    # MÓDULO: PRODUCTOS (prd)
    # ============================================
    path('sys/prd/', productos.productos, name="productos"),
    path('sys/prd/add/', productos.agregar, name="productosAgregar"),
    path('sys/prd/edit/', productos.editado, name="productosEditado"),
    path('sys/prd/del/<str:eid>/', productos.eliminar, name="eliminarProducto"),
    
    # ============================================
    # MÓDULO: REPUESTOS (rps)
    # ============================================
    path('sys/rps/', repuestos.repuestos, name="repuestos"),
    path('sys/rps/add/', repuestos.agregar_repuesto, name="agregarRepuesto"),
    path('sys/rps/edit/', repuestos.editar_repuesto, name="editarRepuesto"),
    path('sys/rps/del/<str:eid>/', repuestos.eliminar_repuesto, name="eliminarRepuesto"),
    
    # ============================================
    # MÓDULO: CLIENTES (cli)
    # ============================================
    path('sys/cli/', clientes.clientes, name='clientes'),
    path('sys/cli/add/', clientes.agregar_cliente, name='agregar_cliente'),
    path('sys/cli/edit/', clientes.editar_cliente, name='editar_cliente'),
    path('sys/cli/del/<str:eid>/', clientes.eliminar_cliente, name='eliminar_cliente'),
    path('api/cli/auto/', clientes.autocompletar_cliente, name='autocompletar_cliente'),

    # ============================================
    # MÓDULO: PROVEEDORES (prv)
    # ============================================
    path('sys/prv/', proveedores.proveedores, name='proveedores'),
    path('sys/prv/add/', proveedores.agregar_proveedor, name='agregar_proveedor'),
    path('sys/prv/edit/', proveedores.editar_proveedor, name='editar_proveedor'),
    path('sys/prv/del/<str:eid>/', proveedores.eliminar_proveedor, name='eliminar_proveedor'),
    path('api/prv/auto/', proveedores.autocompletar_proveedor, name='autocompletar_proveedor'),
    path('api/prv/last/', proveedores.obtener_ultimo_proveedor, name='obtener_ultimo_proveedor'),

    # ============================================
    # MÓDULO: CRÉDITOS (crd)
    # ============================================
    path('sys/crd/', creditos.creditos, name='creditos'),
    path('sys/crd/det/<str:eid>/', creditos.detalle_credito, name='detalle_credito'),
    path('sys/crd/pay/<str:eid>/', creditos.pagar_cuota, name='pagar_cuota'),
    path('sys/crd/void/<str:eid>/', creditos.anular_pago, name='anular_pago'),
    path('sys/crd/rpt/', creditos.reportes_creditos, name='reportes_creditos'),
    path('sys/crd/search/', creditos.buscar_cuotas_cliente, name='buscar_cuotas_cliente'),
    path('sys/crd/crono/<str:eid>/', creditos.imprimir_cronograma_credito, name='imprimir_cronograma'),
    path('sys/crd/receipt/<str:eid>/', creditos.imprimir_recibo_pago, name='imprimir_recibo_pago'),

    # ============================================
    # MÓDULO: STOCK (stk)
    # ============================================
    path('sys/stk/', stock.stock, name='stock'),

    # ============================================
    # MÓDULO: TRANSFERENCIAS (trf)
    # ============================================
    path('sys/trf/', transferencias.transferencias, name='transferencias'),
    path('sys/trf/new/', transferencias.nueva_transferencia, name='nueva_transferencia'),
    path('sys/trf/confirm/<str:eid>/', transferencias.confirmar_transferencia, name='confirmar_transferencia'),
    path('sys/trf/reject/<str:eid>/', transferencias.rechazar_transferencia, name='rechazar_transferencia'),
    path('api/stk/alm/', transferencias.obtener_stock_almacen, name='obtener_stock_almacen'),

    # ============================================
    # MÓDULO: MOVIMIENTOS DE CAJA (mcj)
    # ============================================
    path('sys/mcj/', movimientosCaja.movimientos_caja, name='movimientos_caja'),
    path('sys/mcj/egress/', movimientosCaja.registrar_egreso, name='registrar_egreso'),
    path('sys/mcj/report/', movimientosCaja.reporte_caja, name='reporte_caja'),
    path('sys/mcj/edit/<str:eid>/', movimientosCaja.editar_movimiento, name='editar_movimiento'),
    path('sys/mcj/delete/<str:eid>/', movimientosCaja.eliminar_movimiento, name='eliminar_movimiento'),

    # ============================================
    # MÓDULO: HISTORIAL DE CAJAS (hcj)
    # ============================================
    path('sys/hcj/', historialCajas.historial_cajas, name='historial_cajas'),
    path('sys/hcj/reopen/<str:eid>/', historialCajas.solicitar_reapertura, name='solicitar_reapertura'),
    path('sys/hcj/verify/', historialCajas.verificar_codigo_reapertura, name='verificar_codigo_reapertura'),
    path('sys/hcj/close/<str:eid>/', historialCajas.cerrar_caja_reabierta, name='cerrar_caja_reabierta'),

    # ============================================
    # MÓDULO: IMPOSICIÓN DE PLACAS (ipl)
    # ============================================
    path('sys/ipl/', imposicionPlacas.imposicion_placas, name='imposicion_placas'),
    path('sys/ipl/new/', imposicionPlacas.nueva_imposicion, name='nueva_imposicion'),
    path('sys/ipl/edit/<str:eid>/', imposicionPlacas.editar_imposicion, name='editar_imposicion'),
    path('sys/ipl/status/<str:eid>/', imposicionPlacas.cambiar_estado_imposicion, name='cambiar_estado_imposicion'),
    path('sys/ipl/del/<str:eid>/', imposicionPlacas.eliminar_imposicion, name='eliminar_imposicion'),
    path('sys/ipl/det/<str:eid>/', imposicionPlacas.detalle_imposicion, name='detalle_imposicion'),
    path('sys/ipl/vehicles/', imposicionPlacas.obtener_vehiculos_venta, name='obtener_vehiculos_venta'),
    path('sys/ipl/print/<str:eid>/', imposicionPlacas.imprimir_constancia, name='imprimir_constancia_placa'),

    # ============================================
    # CATÁLOGOS: CATEGORÍAS (cat)
    # ============================================
    path('cat/cat/', categorias.categorias, name="categorias"),
    path('cat/cat/add/', categorias.agregar, name="agregarCategorias"),
    path('cat/cat/edit/', categorias.editar, name="editarCategorias"),
    path('cat/cat/del/<str:eid>/', categorias.eliminar, name="categoriasEliminar"),
    
    # ============================================
    # CATÁLOGOS: MARCAS (mrc)
    # ============================================
    path('cat/mrc/', marcas.marcas, name="marcas"),
    path('cat/mrc/add/', marcas.agregar, name="agregarMarcas"),
    path('cat/mrc/edit/', marcas.editar, name="editarMarcas"),
    path('cat/mrc/del/<str:eid>/', marcas.eliminar, name="marcasEliminar"),

    # ============================================
    # CATÁLOGOS: COLORES (clr)
    # ============================================
    path('cat/clr/', colores.colores, name="colores"),
    path('cat/clr/add/', colores.agregar, name="agregarColores"),
    path('cat/clr/edit/', colores.editar, name="editarColores"),
    path('cat/clr/del/<str:eid>/', colores.eliminar, name="coloresEliminar"),

    # ============================================
    # CATÁLOGOS: CILINDRADAS (cil)
    # ============================================
    path('cat/cil/', cilindradas.cilindradas, name="cilindradas"),
    path('cat/cil/add/', cilindradas.agregar, name="agregarCilindradas"),
    path('cat/cil/edit/', cilindradas.editar, name="editarCilindradas"),
    path('cat/cil/del/<str:eid>/', cilindradas.eliminar, name="cilindradasEliminar"),
    
    # ============================================
    # CATÁLOGOS: ESTADO PRODUCTOS (est)
    # ============================================
    path('cat/est/', estadoproductos.estadoproductos, name="estadoproductos"),
    path('cat/est/add/', estadoproductos.agregar, name="agregarEstadoProductos"),
    path('cat/est/edit/', estadoproductos.editar, name="editarEstadoProductos"),
    path('cat/est/del/<str:eid>/', estadoproductos.eliminar, name="estadoproductosEliminar"),

    # ============================================
    # CATÁLOGOS: UNIDADES (und)
    # ============================================
    path('cat/und/', unidades.unidades, name='unidades'),
    path('cat/und/on/<str:eid>/', unidades.activo, name='unidadesActivo'),
    path('cat/und/off/<str:eid>/', unidades.desactivo, name='unidadesDesactivo'),

    # ============================================
    # CONFIGURACIÓN: USUARIOS (usr)
    # ============================================
    path('cfg/usr/', usuarios.usuarios, name="usuarios"),
    path('cfg/usr/add/', usuarios.agregar, name="usuarioAgregar"),
    path('cfg/usr/edit/', usuarios.editar, name="usuarioEditar"),
    path('cfg/usr/del/<str:eid>/', usuarios.eliminar, name="usuarioEliminar"),

    # ============================================
    # CONFIGURACIÓN: TIPOS DE USUARIO (tusr)
    # ============================================
    path('cfg/tusr/', tipoUsuarios.tipoUsuarios, name="tipoUsuarios"),
    path('cfg/tusr/add/', tipoUsuarios.tipousuariosAgregar, name="tipousuariosAgregar"),
    path('cfg/tusr/edit/', tipoUsuarios.tipousuariosEditar, name="tipousuariosEditar"),
    path('cfg/tusr/del/<str:eid>/', tipoUsuarios.tipousuariosEliminar, name="tipousuariosEliminar"),

    # ============================================
    # CONFIGURACIÓN: PERMISOS (prm)
    # ============================================
    path('cfg/prm/', permisos.permisos, name="permisos"),
    path('cfg/prm/add/', permisos.agregaPermiso, name="agregaPermiso"),
    path('cfg/prm/edit/', permisos.editarPermiso, name='editarPermiso'),
    path('cfg/prm/del/<str:eid>/', permisos.eliminarPermiso, name="eliminarPermiso"),

    # ============================================
    # CONFIGURACIÓN: EMPRESA (emp)
    # ============================================
    path('cfg/emp/', configuracion.configuracion, name="configuracion"),
    path('cfg/emp/edit/', configuracion.editarEmpresa, name="editarEmpresa"),
    path('cfg/emp/prod/<str:eid>/', configuracion.produccion, name="produccion"),
    path('cfg/emp/dev/<str:eid>/', configuracion.desarrollo, name="desarrollo"),
    path('api/emp/ruc/', configuracion.obtener_datos_empresa_por_ruc, name='obtener_empresa_ruc'),

    # ============================================
    # CONFIGURACIÓN: CAJAS (caj)
    # ============================================
    path('cfg/caj/', cajas.cajas, name='cajas'),
    path('cfg/caj/del/<str:eid>/', cajas.cajasEliminar, name='cajasEliminar'),
    path('cfg/caj/add/', cajas.agregarCajas, name='agregarCajas'),
    path('cfg/caj/edit/', cajas.editarCajas, name='editarCajas'),
    path('api/caj/suc/', cajas.obtenerSucursalesPorEmpresa, name='obtenerSucursalesPorEmpresaCajas'),

    # ============================================
    # UBICACIÓN: REGIONES (reg)
    # ============================================
    path('loc/reg/', regiones.regiones, name='regiones'),
    path('loc/reg/del/<str:eid>/', regiones.regionesEliminar, name='regionesEliminar'),
    path('loc/reg/add/', regiones.agregarRegiones, name='agregarRegiones'),
    path('loc/reg/edit/', regiones.editarRegiones, name='editarRegiones'),

    # ============================================
    # UBICACIÓN: PROVINCIAS (prv)
    # ============================================
    path('loc/prv/', provincias.provincias, name='provincias'),
    path('loc/prv/del/<str:eid>/', provincias.provinciasEliminar, name='provinciasEliminar'),
    path('loc/prv/add/', provincias.agregarProvincias, name='agregarProvincias'),
    path('loc/prv/edit/', provincias.editarProvincias, name='editarProvincias'),

    # ============================================
    # UBICACIÓN: DISTRITOS (dis)
    # ============================================
    path('loc/dis/', distritos.distritos, name='distritos'),
    path('loc/dis/del/<str:eid>/', distritos.distritosEliminar, name='distritosEliminar'),
    path('loc/dis/add/', distritos.agregarDistritos, name='agregarDistritos'),
    path('loc/dis/edit/', distritos.editarDistritos, name='editarDistritos'),
    path('api/loc/prv/', distritos.obtenerProvinciasPorRegion, name='obtenerProvinciasPorRegion'),

    # ============================================
    # UBICACIÓN: SUCURSALES (suc)
    # ============================================
    path('loc/suc/', sucursales.sucursales, name='sucursales'),
    path('loc/suc/del/<str:eid>/', sucursales.sucursalesEliminar, name='sucursalesEliminar'),
    path('loc/suc/add/', sucursales.agregarSucursales, name='agregarSucursales'),
    path('loc/suc/edit/', sucursales.editarSucursales, name='editarSucursales'),
    path('api/suc/prv/', sucursales.obtenerProvinciasPorRegion, name='obtenerProvinciasPorRegionSucursales'),
    path('api/suc/dis/', sucursales.obtenerDistritosPorProvincia, name='obtenerDistritosPorProvincia'),

    # ============================================
    # UBICACIÓN: ALMACENES (alm)
    # ============================================
    path('loc/alm/', almacenes.almacenes, name='almacenes'),
    path('loc/alm/del/<str:eid>/', almacenes.almacenesEliminar, name='almacenesEliminar'),
    path('loc/alm/add/', almacenes.agregarAlmacenes, name='agregarAlmacenes'),
    path('loc/alm/edit/', almacenes.editarAlmacenes, name='editarAlmacenes'),
    path('api/alm/suc/', almacenes.obtenerSucursalesPorEmpresa, name='obtenerSucursalesPorEmpresa'),

    # ============================================
    # COMPROBANTES: TIPOS (tcp)
    # ============================================
    path('doc/tcp/', tipo_comprobante.tipo_comprobante, name='tipo_comprobante'),
    path('doc/tcp/add/', tipo_comprobante.agregar_tipo_comprobante, name='agregar_tipo_comprobante'),
    path('doc/tcp/edit/', tipo_comprobante.editar_tipo_comprobante, name='editar_tipo_comprobante'),
    path('doc/tcp/del/<str:eid>/', tipo_comprobante.eliminar_tipo_comprobante, name='eliminar_tipo_comprobante'),

    # ============================================
    # COMPROBANTES: SERIES (ser)
    # ============================================
    path('doc/ser/', serie_comprobante.serie_comprobante, name='serie_comprobante'),
    path('doc/ser/add/', serie_comprobante.agregar_serie_comprobante, name='agregar_serie_comprobante'),
    path('doc/ser/edit/', serie_comprobante.editar_serie_comprobante, name='editar_serie_comprobante'),
    path('doc/ser/del/<str:eid>/', serie_comprobante.eliminar_serie_comprobante, name='eliminar_serie_comprobante'),

    # ============================================
    # MÓDULO: FIRMA DIGITAL (frd)
    # ============================================
    path('sys/frd/', firmaDigital.firma_digital, name='firma_digital'),
    path('sys/frd/firmar/', firmaDigital.firmar_documento, name='firmar_documento'),
    path('sys/frd/download/<int:iddocumento>/', firmaDigital.descargar_documento_firmado, name='descargar_documento_firmado'),
    path('sys/frd/verify/', firmaDigital.verificar_documento, name='verificar_documento'),



]