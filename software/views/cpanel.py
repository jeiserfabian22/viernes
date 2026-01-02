
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.cajaModel import Caja  # asegúrate de que el nombre del modelo sea correcto


def cpanel(request):
    # Obtener datos de sesión del usuario
    id2 = request.session.get('idtipousuario')
    nombrecompleto = request.session.get('nombrecompleto')

    if id2:
        # Permisos del tipo de usuario
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)

        # Ejecutar la consulta SQL para obtener las ventas por mes
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(`ventas`.`fecha_venta`, '%Y %M') AS `mes_anio`, 
                    IFNULL(SUM(`ventadetalle`.`subtotal`), 0) AS `total`
                FROM `ventas`
                INNER JOIN `ventadetalle` 
                    ON (`ventas`.`idventa` = `ventadetalle`.`idventa`)
                WHERE `ventas`.`estado` = 1
                GROUP BY `mes_anio`
                ORDER BY `mes_anio`;
            """)
            rows = cursor.fetchall()

        # Calcular el total general de ventas
        total_general = sum(float(row[1] or 0) for row in rows)

        # Preparar los datos para el gráfico
        chart_data = []
        for row in rows:
            total_venta = float(row[1])
            porcentaje = (total_venta / total_general) * 100 if total_general > 0 else 0.0
            chart_data.append({
                'name': row[0],       # Mes y año
                'y': total_venta,     # Total de ventas del mes
                'porcentaje': round(porcentaje, 2)
            })

        # Consultar el último registro de la caja
        ultimo_registro = Caja.objects.order_by('-id_caja').first()

        if ultimo_registro and ultimo_registro.estado == 1:
            cerrar = "Caja está abierta"
        else:
            cerrar = None

        # Preparar datos para la plantilla
        data = {
            "permisos": permisos,
            'resultados': rows,
            'chart_data': chart_data,
            'nombrecompleto': nombrecompleto,
            "cerrar": cerrar
        }

        return render(request, 'cpanel.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

