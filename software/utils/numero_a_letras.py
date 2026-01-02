# utils/numero_a_letras.py
"""
Utilidad para convertir números a letras en español
Para uso en recibos y documentos contables
"""

UNIDADES = (
    '', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE'
)

DECENAS = (
    'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISEIS',
    'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE'
)

DECENAS_COMPLETAS = (
    '', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA',
    'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA'
)

CENTENAS = (
    '', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS',
    'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS'
)


def numero_a_letras(numero):
    """
    Convierte un número decimal a letras en español
    Ejemplo: 154.50 -> "CIENTO CINCUENTA Y CUATRO Y 50/100"
    """
    from decimal import Decimal
    
    # Convertir a Decimal si no lo es
    if not isinstance(numero, Decimal):
        numero = Decimal(str(numero))
    
    # Separar parte entera y decimal
    partes = str(numero).split('.')
    parte_entera = int(partes[0])
    parte_decimal = partes[1] if len(partes) > 1 else '00'
    
    # Asegurar que la parte decimal tenga 2 dígitos
    if len(parte_decimal) == 1:
        parte_decimal = parte_decimal + '0'
    elif len(parte_decimal) > 2:
        parte_decimal = parte_decimal[:2]
    
    # Convertir parte entera a letras
    if parte_entera == 0:
        letras_entero = 'CERO'
    else:
        letras_entero = convertir_grupo(parte_entera)
    
    # Construir resultado
    resultado = f"{letras_entero} Y {parte_decimal}/100"
    
    return resultado


def convertir_grupo(numero):
    """
    Convierte un número entero (0-999999999) a letras
    """
    if numero == 0:
        return 'CERO'
    
    resultado = []
    
    # Millones
    if numero >= 1000000:
        millones = numero // 1000000
        if millones == 1:
            resultado.append('UN MILLON')
        else:
            resultado.append(convertir_centenas(millones) + ' MILLONES')
        numero = numero % 1000000
    
    # Miles
    if numero >= 1000:
        miles = numero // 1000
        if miles == 1:
            resultado.append('MIL')
        else:
            resultado.append(convertir_centenas(miles) + ' MIL')
        numero = numero % 1000
    
    # Centenas
    if numero > 0:
        resultado.append(convertir_centenas(numero))
    
    return ' '.join(resultado)


def convertir_centenas(numero):
    """
    Convierte un número de 0-999 a letras
    """
    if numero == 0:
        return ''
    
    resultado = []
    
    # Centenas
    centena = numero // 100
    if centena > 0:
        if numero == 100:
            resultado.append('CIEN')
        else:
            resultado.append(CENTENAS[centena])
    
    # Decenas y unidades
    resto = numero % 100
    
    if resto >= 10 and resto < 20:
        # 10-19
        resultado.append(DECENAS[resto - 10])
    elif resto >= 20:
        # 20-99
        decena = resto // 10
        unidad = resto % 10
        
        if unidad == 0:
            resultado.append(DECENAS_COMPLETAS[decena])
        else:
            if decena == 2:
                resultado.append('VEINTI' + UNIDADES[unidad])
            else:
                resultado.append(DECENAS_COMPLETAS[decena] + ' Y ' + UNIDADES[unidad])
    elif resto > 0:
        # 1-9
        if resto == 1 and numero > 1:
            resultado.append('UNO')
        else:
            resultado.append(UNIDADES[resto])
    
    return ' '.join(resultado)


# Ejemplos de uso:
if __name__ == '__main__':
    print(numero_a_letras(154.00))  # CIENTO CINCUENTA Y CUATRO Y 00/100
    print(numero_a_letras(0.10))    # CERO Y 10/100
    print(numero_a_letras(1234.56)) # MIL DOSCIENTOS TREINTA Y CUATRO Y 56/100
    print(numero_a_letras(100.00))  # CIEN Y 00/100