
import requests
from typing import Dict, Optional
from django.conf import settings


class TokenPeruAPI:
    """Cliente para la API de APIs.net.pe (DeColecta)"""
    
    BASE_URL = "https://api.decolecta.com/v1"
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa el cliente de la API
        
        Args:
            token: Token de autenticación. Si no se proporciona, se obtiene de settings.TOKENPERU_TOKEN
        """
        self.token = token or getattr(settings, 'TOKENPERU_TOKEN', None)
        if not self.token:
            raise ValueError("Se requiere un token de APIs.net.pe. Configure TOKENPERU_TOKEN en settings.py")
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Referer': 'https://apis.net.pe'
        }
    
    def consultar_dni(self, dni: str) -> Dict:
        """
        Consulta información REAL de una persona por DNI desde RENIEC
        
        Args:
            dni: Número de DNI (8 dígitos)
            
        Returns:
            Dict con la información de la persona
        """
        if not dni or len(dni) != 8 or not dni.isdigit():
            raise ValueError("El DNI debe tener 8 dígitos numéricos")
        
        url = f"{self.BASE_URL}/reniec/dni"
        params = {'numero': dni}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # Mapear campos de APIs.net.pe al formato estándar
            return {
                'dni': result.get('document_number', result.get('numeroDocumento', dni)),
                'nombres': result.get('first_name', result.get('nombres', '')),
                'apellido_paterno': result.get('first_last_name', result.get('apellidoPaterno', '')),
                'apellido_materno': result.get('second_last_name', result.get('apellidoMaterno', '')),
                'nombre_completo': result.get('full_name', f"{result.get('first_last_name', '')} {result.get('second_last_name', '')} {result.get('first_name', '')}".strip()),
                'codigo_verificacion': result.get('codigoVerificacion', result.get('verification_code', '')),
                'fecha_nacimiento': result.get('fechaNacimiento', result.get('birth_date', '')),
                'sexo': result.get('sexo', result.get('gender', '')),
                'ubigeo': result.get('ubigeo', result.get('ubigeo_code', '')),
                'direccion': result.get('direccion', result.get('address', ''))
            }
                
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Token inválido o expirado")
            elif response.status_code == 404:
                raise ValueError("Documento no encontrado en RENIEC")
            elif response.status_code == 429:
                raise ValueError("Límite de consultas excedido")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('mensaje', error_data.get('error', str(e)))
                except:
                    error_msg = str(e)
                raise ValueError(f"Error en la API: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error de conexión: {e}")
    
    def consultar_ruc(self, ruc: str) -> Dict:
        """
        Consulta información REAL de una empresa por RUC desde SUNAT
        
        Args:
            ruc: Número de RUC (11 dígitos)
            
        Returns:
            Dict con la información de la empresa
        """
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            raise ValueError("El RUC debe tener 11 dígitos numéricos")
        
        url = f"{self.BASE_URL}/sunat/ruc"
        params = {'numero': ruc}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # Mapear campos de APIs.net.pe al formato estándar
            return {
                'ruc': result.get('numero_documento', result.get('numeroDocumento', ruc)),
                'razon_social': result.get('razon_social', result.get('nombre', '')),
                'nombre_comercial': result.get('nombre_comercial', result.get('nombreComercial', '')),
                'tipo_contribuyente': result.get('tipo_contribuyente', result.get('tipoContribuyente', '')),
                'estado': result.get('estado', ''),
                'condicion': result.get('condicion', ''),
                'direccion': result.get('direccion', ''),
                'departamento': result.get('departamento', ''),
                'provincia': result.get('provincia', ''),
                'distrito': result.get('distrito', ''),
                'ubigeo': result.get('ubigeo', ''),
                'fecha_inscripcion': result.get('fecha_inscripcion', result.get('fechaInscripcion', '')),
                'actividad_economica': result.get('actividad_economica', result.get('actividadEconomica', [])),
                # Campos adicionales de SUNAT
                'via_tipo': result.get('via_tipo', result.get('viaTipo', '')),
                'via_nombre': result.get('via_nombre', result.get('viaNombre', '')),
                'numero': result.get('numero', ''),
                'interior': result.get('interior', ''),
                'lote': result.get('lote', ''),
                'departamento_dir': result.get('dpto', ''),
                'manzana': result.get('manzana', ''),
                'kilometro': result.get('kilometro', ''),
                'es_agente_retencion': result.get('es_agente_retencion', False),
                'es_buen_contribuyente': result.get('es_buen_contribuyente', False)
            }
                
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Token inválido o expirado")
            elif response.status_code == 404:
                raise ValueError("Documento no encontrado en SUNAT")
            elif response.status_code == 429:
                raise ValueError("Límite de consultas excedido")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('mensaje', error_data.get('error', str(e)))
                except:
                    error_msg = str(e)
                raise ValueError(f"Error en la API: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error de conexión: {e}")
    
    def consultar_ruc_completo(self, ruc: str) -> Dict:
        """
        Consulta información COMPLETA de una empresa por RUC desde SUNAT
        Incluye información adicional como representantes, trabajadores, etc.
        
        Args:
            ruc: Número de RUC (11 dígitos)
            
        Returns:
            Dict con la información completa de la empresa
        """
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            raise ValueError("El RUC debe tener 11 dígitos numéricos")
        
        url = f"{self.BASE_URL}/sunat/ruc/full"
        params = {'numero': ruc}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
                
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Token inválido o expirado")
            elif response.status_code == 404:
                raise ValueError("Documento no encontrado en SUNAT")
            elif response.status_code == 429:
                raise ValueError("Límite de consultas excedido")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('mensaje', error_data.get('error', str(e)))
                except:
                    error_msg = str(e)
                raise ValueError(f"Error en la API: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error de conexión: {e}")


# Funciones de utilidad para usar directamente
def consultar_dni(dni: str, token: Optional[str] = None) -> Dict:
    """Función de utilidad para consultar DNI"""
    api = TokenPeruAPI(token)
    return api.consultar_dni(dni)


def consultar_ruc(ruc: str, token: Optional[str] = None) -> Dict:
    """Función de utilidad para consultar RUC"""
    api = TokenPeruAPI(token)
    return api.consultar_ruc(ruc)


def consultar_documento(numero: str, token: Optional[str] = None) -> Dict:
    """
    Función inteligente que detecta si es DNI o RUC y consulta automáticamente
    
    Args:
        numero: Número de documento (8 para DNI, 11 para RUC)
        token: Token de autenticación (opcional)
        
    Returns:
        Dict con la información y el tipo de documento
    """
    if not numero or not numero.isdigit():
        raise ValueError("El documento debe contener solo números")
    
    api = TokenPeruAPI(token)
    
    if len(numero) == 8:
        resultado = api.consultar_dni(numero)
        resultado['tipo_documento'] = 'DNI'
        resultado['id_tipo_entidad'] = 1  # DNI según tu tabla tipo_entidad
        return resultado
    elif len(numero) == 11:
        resultado = api.consultar_ruc(numero)
        resultado['tipo_documento'] = 'RUC'
        resultado['id_tipo_entidad'] = 6  # RUC según tu tabla tipo_entidad
        return resultado
    else:
        raise ValueError("El documento debe tener 8 dígitos (DNI) o 11 dígitos (RUC)")