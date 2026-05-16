import re

from django import template

register = template.Library()


@register.filter(name="mask_cpf")
def mask_cpf(value):
    if not value:
        return "-"
    # Remove any non-numeric characters
    value = re.sub(r"\D", "", str(value))
    if len(value) == 11:
        return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"
    return value


@register.filter(name="mask_cnpj")
def mask_cnpj(value):
    if not value:
        return "-"
    value = re.sub(r"\D", "", str(value))
    if len(value) == 14:
        return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"
    return value


@register.filter(name="mask_phone")
def mask_phone(value):
    if not value:
        return "-"
    value = re.sub(r"\D", "", str(value))
    length = len(value)
    if length == 11:  # Mobile with 9 digits
        return f"({value[:2]}) {value[2:7]}-{value[7:]}"
    elif length == 10:  # Landline or old mobile
        return f"({value[:2]}) {value[2:6]}-{value[6:]}"
    return value
