from moviles.models import Movil, MovilStatus, MovilGeocode

camiones = Movil.objects.filter(alias__startswith='CAMION').order_by('alias')
for movil in camiones:
    status = MovilStatus.objects.filter(movil=movil).first()
    geocode = MovilGeocode.objects.filter(movil=movil).first()
    print('---')
    print('ID:', movil.id)
    print('Alias:', movil.alias)
    print('Patente:', movil.patente)
    print('Código:', movil.codigo)
    print('GPS ID:', movil.gps_id)
    if status:
        print('Status -> lat:', status.ultimo_lat, 'lon:', status.ultimo_lon, 'fecha_gps:', status.fecha_gps)
    else:
        print('Status -> None')
    if geocode:
        print('Geocode ->', geocode.direccion_formateada)
    else:
        print('Geocode -> None')
