
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
from .views import numeroserie
from .views import registroCaja
from .views import stock
from .views import password_reset

urlpatterns = [


    #login
    path('', login.index, name="index"),
    path('login', login.login, name="login"),
    path('logout', login.logout, name="logout"),

    # Autenticación 2FA
    path('verificar-2fa/', login.verificar_2fa, name="verificar_2fa"),
    path('reenviar-codigo-2fa/', login.reenviar_codigo_2fa, name="reenviar_codigo_2fa"),
    path('cancelar-2fa/', login.cancelar_2fa, name="cancelar_2fa"),
    
    # Recuperación de contraseña
    path('recuperar-contrasena/', password_reset.solicitar_recuperacion, name="solicitar_recuperacion"),
    path('restablecer-contrasena/<str:token>/', password_reset.restablecer_contrasena, name="restablecer_contrasena"),

    # Nuevas rutas para manejo de caja
    path('api/obtener-datos-apertura/', login.obtener_datos_apertura, name="obtener_datos_apertura"),
    path('api/obtener-cajas-almacenes/', login.obtener_cajas_almacenes, name="obtener_cajas_almacenes"),
    path('api/cambiar-contexto/', login.cambiar_contexto, name="cambiar_contexto"),
    path('api/abrir-caja/', login.abrir_caja, name="abrir_caja"),
    path('api/cerrar-caja/', login.cerrar_caja, name="cerrar_caja"),

    
    #Usuarios
    path('usuarios', usuarios.usuarios, name="usuarios"),
    path('usuarios/agregar', usuarios.agregar, name="usuarioAgregar"),
    path('usuarios/editar', usuarios.editar, name="usuarioEditar"),
    path('usuarios/eliminar/<int:id>', usuarios.eliminar, name="usuarioEliminar"),
    
    # compras
    path('compras/', compras.compras, name="compras"),   # listado
    path('compras/agregar/', compras.nueva_compra, name="agregarCompras"), 
    #path('compras/eliminar/<int:id>', compras.eliminar, name="eliminarCompras"),
    #path('compras/agregar', compras.agregar, name="agregarCompras"),
    #path('compras/buscar', compras.buscar, name="buscarCompras"),
    #path('compras/guardar', compras.guardar, name="guardarCompras"),
    #path('compras/editar/<int:id>', compras.editar, name="editarCompras"),
    #path('compras/editado', compras.editado, name="compraEditada"),
    #path('compras/buscarFecha', compras.buscarFecha, name="buscarFecha"),
    #path('compras/export/', compras.export_compras_to_excel, name='export_compras_to_excel'),
    path('stock/', stock.stock, name='stock'),
    

    
    # ventas
    path('ventas/', ventas.ventas, name="ventas"),
    path('ventas/nueva/', ventas.nueva_venta, name="nuevaVenta"),
    path('ventas/anular/<int:id>', ventas.anular_venta, name="anularVenta"),
    path('ventas/obtener-series/', ventas.obtener_series, name="obtenerSeries"),
    path('ventas/imprimir/<int:idventa>/', ventas.imprimir_comprobante, name="imprimir_comprobante"),

    

    #categorias
    path('categorias', categorias.categorias, name="categorias"),
    path('categorias/agregar', categorias.agregar, name="agregarCategorias"),
    path('categorias/editar', categorias.editar, name="editarCategorias"),
    path('categorias/eliminarCategoria/<int:id>', categorias.eliminar, name="categoriasEliminar"),
    
    # Marcas
    path('marcas', marcas.marcas, name="marcas"),
    path('marcas/agregar', marcas.agregar, name="agregarMarcas"),
    path('marcas/editar', marcas.editar, name="editarMarcas"),
    path('marcas/eliminarMarca/<int:id>', marcas.eliminar, name="marcasEliminar"),

    # Colores
    path('colores', colores.colores, name="colores"),
    path('colores/agregar', colores.agregar, name="agregarColores"),
    path('colores/editar', colores.editar, name="editarColores"),
    path('colores/eliminarColor/<int:id>', colores.eliminar, name="coloresEliminar"),

    # Cilindradas
    path('cilindradas', cilindradas.cilindradas, name="cilindradas"),
    path('cilindradas/agregar', cilindradas.agregar, name="agregarCilindradas"),
    path('cilindradas/editar', cilindradas.editar, name="editarCilindradas"),
    path('cilindradas/eliminarCilindrada/<int:id>', cilindradas.eliminar, name="cilindradasEliminar"),
    
    # Estado Producto
    path('estadoproductos', estadoproductos.estadoproductos, name="estadoproductos"),
    path('estadoproductos/agregar', estadoproductos.agregar, name="agregarEstadoProductos"),
    path('estadoproductos/editar', estadoproductos.editar, name="editarEstadoProductos"),
    path('estadoproductos/eliminarEstadoProducto/<int:id>', estadoproductos.eliminar, name="estadoproductosEliminar"),



    #Permisos
    path('permisos', permisos.permisos, name="permisos"),
    path('permisos/agregaPermiso', permisos.agregaPermiso, name="agregaPermiso"),
    path('permisos/eliminarPermiso/<int:id>', permisos.eliminarPermiso, name="eliminarPermiso"),
     
    #productos
    path('productos', productos.productos, name="productos"),
    path('productos/agregar', productos.agregar, name="productosAgregar"),
    path('productos/editar', productos.editado, name="productosEditado"),
    path('productos/eliminarProducto/<int:idproducto>', productos.eliminar, name="eliminarProducto"),

    #Repuestos
    path('repuestos', repuestos.repuestos, name="repuestos"),
    path('repuestos/agregar', repuestos.agregar_repuesto, name="agregarRepuesto"),
    path('repuestos/editar', repuestos.editar_repuesto, name="editarRepuesto"),
    path('repuestos/eliminar/<int:id_repuesto>', repuestos.eliminar_repuesto, name="eliminarRepuesto"),
    
    #configuracion
    path('configuracion', configuracion.configuracion, name="configuracion"),
    path('configuracion/buscarProvincias', configuracion.buscarProvincias, name="buscarProvincias"),
    path('configuracion/buscarDistritos', configuracion.buscarDistritos, name="buscarDistritos"),
    path('configuracion/ubigueo', configuracion.ubigueo, name="ubigueo"),
    path('configuracion/editarEmpresa', configuracion.editarEmpresa, name="editarEmpresa"),
    path('configuracion/produccion/<int:id>', configuracion.produccion, name="produccion"),
    path('configuracion/desarrollo/<int:id>', configuracion.desarrollo, name="desarrollo"),

    #cpanel
    path('cpanel', cpanel.cpanel, name="cpanel"),

    
    #Tipo usuarios
    path('tipousuarios', tipoUsuarios.tipoUsuarios, name="tipoUsuarios"),
    path('tipousuarios/agregar', tipoUsuarios.tipousuariosAgregar, name="tipousuariosAgregar"),
    path('tipousuarios/editar', tipoUsuarios.tipousuariosEditar, name="tipousuariosEditar"),
    path('tipousuarios/eliminar/<int:id>', tipoUsuarios.tipousuariosEliminar, name="tipousuariosEliminar"),

    #Número de serie
    path('numeroserie', numeroserie.numeroserie, name="numeroserie"),
    path('numeroserie/agregar', numeroserie.numeroserieAgregar, name="numeroserieAgregar"),
    path('numeroserie/editar', numeroserie.numeroserieEditar, name="numeroserieEditar"),
    path('numeroserie/eliminar/<int:id>', numeroserie.numeroserieEliminar, name="numeroserieEliminar"),
    
    
    #REGISTROS DE CAJA
    path('cajas', registroCaja.mostrar_caja, name="MostrarCajas"),
    

]
