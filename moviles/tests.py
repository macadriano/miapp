# Tests for moviles app
from django.test import TestCase
from .models import Movil, MovilStatus, MovilGeocode


class MovilModelTest(TestCase):
    def setUp(self):
        self.movil = Movil.objects.create(
            patente='ABC123',
            alias='Test Mobile',
            gps_id='123456789'
        )
    
    def test_movil_str(self):
        self.assertEqual(str(self.movil), 'Test Mobile')
    
    def test_movil_get_equipo_gps(self):
        # Test when no equipment is found
        equipo = self.movil.get_equipo_gps()
        self.assertIsNone(equipo)


class MovilStatusModelTest(TestCase):
    def setUp(self):
        self.movil = Movil.objects.create(patente='ABC123')
        self.status = MovilStatus.objects.create(
            movil=self.movil,
            ultimo_lat=-34.6037,
            ultimo_lon=-58.3816,
            estado_conexion='conectado'
        )
    
    def test_status_str(self):
        self.assertIn('ABC123', str(self.status))


class MovilGeocodeModelTest(TestCase):
    def setUp(self):
        self.movil = Movil.objects.create(patente='ABC123')
        self.geocode = MovilGeocode.objects.create(
            movil=self.movil,
            direccion_formateada='Test Address',
            provincia='Buenos Aires'
        )
    
    def test_geocode_str(self):
        self.assertIn('ABC123', str(self.geocode))
