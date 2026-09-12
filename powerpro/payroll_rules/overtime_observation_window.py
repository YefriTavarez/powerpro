"""Explicit bounded historical observation; never changes authorization limits."""
from datetime import timedelta
from powerpro.payroll_rules.overtime import _as_datetime


def normalize_window(value,base_start,base_end):
    if value is None:return None
    if not isinstance(value,dict) or set(value)!={'start','end'} or not value.get('start') or not value.get('end'):
        raise ValueError('Indique inicio y fin de la ventana histórica.')
    start,end=_as_datetime(value['start']),_as_datetime(value['end'])
    base_start,base_end=_as_datetime(base_start),_as_datetime(base_end)
    if start.tzinfo or end.tzinfo:
        raise ValueError('Use la hora local del sitio sin sufijo de zona horaria.')
    if end<=start or end-start>timedelta(hours=24):
        raise ValueError('La ventana histórica debe ser positiva y no superar 24 horas.')
    if start>base_start or end<base_end:
        raise ValueError('La ventana histórica debe conservar toda la jornada ya documentada.')
    return {'start':start.isoformat(),'end':end.isoformat()}
