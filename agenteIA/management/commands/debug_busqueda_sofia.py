"""
Comando para depurar la búsqueda de Sofia
"""
from django.core.management.base import BaseCommand
from moviles.models import Movil
import re


class Command(BaseCommand):
    help = 'Depura la búsqueda de Sofia para ver por qué no encuentra ciertos móviles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--buscar',
            type=str,
            help='Nombre específico a buscar (ej: ASN773, camion2)',
        )

    def handle(self, *args, **options):
        buscar_especifico = options.get('buscar')
        
        print("=== DEPURACIÓN BÚSQUEDA SOFIA ===\n")
        
        if buscar_especifico:
            busquedas = [buscar_especifico]
        else:
            busquedas = ['ASN773', 'camion2', 'CAMION2', 'asn773']
        
        for busqueda in busquedas:
            print(f"🔍 Buscando: '{busqueda}'")
            
            # Búsqueda como en acciones.py
            movil = Movil.objects.filter(patente__icontains=busqueda).first()
            
            if movil:
                print(f"  ✅ Encontrado por PATENTE: {movil}")
                print(f"     Patente: {movil.patente}")
                print(f"     Alias: {movil.alias}")
                print(f"     Código: {movil.codigo}")
            else:
                movil = Movil.objects.filter(alias__icontains=busqueda).first()
                if movil:
                    print(f"  ✅ Encontrado por ALIAS: {movil}")
                    print(f"     Patente: {movil.patente}")
                    print(f"     Alias: {movil.alias}")
                    print(f"     Código: {movil.codigo}")
                else:
                    movil = Movil.objects.filter(codigo__icontains=busqueda).first()
                    if movil:
                        print(f"  ✅ Encontrado por CÓDIGO: {movil}")
                        print(f"     Patente: {movil.patente}")
                        print(f"     Alias: {movil.alias}")
                        print(f"     Código: {movil.codigo}")
                    else:
                        print(f"  ❌ NO ENCONTRADO")
            print()
        
        # Mostrar todos los móviles disponibles
        print("\n=== TODOS LOS MÓVILES DISPONIBLES ===")
        moviles = Movil.objects.all()
        if moviles:
            for m in moviles:
                print(f"  - Patente: {m.patente or 'N/A'}, Alias: {m.alias or 'N/A'}, Código: {m.codigo or 'N/A'}")
        else:
            print("  ⚠️ No hay móviles registrados en la base de datos")
        
        # Probar extracción con regex
        print("\n=== PROBANDO EXTRACCIÓN CON REGEX ===")
        textos_prueba = [
            "donde esta el ASN773",
            "donde esta camion2",
            "donde esta el camion 2",
            "posicion del ASN 773",
        ]
        
        patron = r'\b([A-Z]{2,4})\s*(\d{2,4})\b'
        for texto in textos_prueba:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                extraido = (match.group(1) + match.group(2)).upper()
                print(f"  '{texto}' → '{extraido}'")
            else:
                print(f"  '{texto}' → NO EXTRAÍDO CON REGEX DE PATENTE")

