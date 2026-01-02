# software/templatetags/url_filters.py

from django import template
from software.utils.url_encryptor import encrypt_id, encrypt_id_safe

register = template.Library()


@register.filter(name='encrypt_id')
def encrypt_id_filter(value):
    """
    Filtro para encriptar IDs en templates
    
    Uso:
        {{ venta.idventa|encrypt_id }}
        <a href="{% url 'editar_venta' eid=venta.idventa|encrypt_id %}">Editar</a>
    """
    if value is None:
        return ''
    return encrypt_id_safe(value, fallback='')


@register.filter(name='eid')
def eid_filter(value):
    """
    Alias corto para encrypt_id
    
    Uso:
        {{ venta.idventa|eid }}
        <a href="{% url 'editar_venta' eid=venta.idventa|eid %}">Editar</a>
    """
    if value is None:
        return ''
    return encrypt_id_safe(value, fallback='')