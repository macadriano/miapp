from rest_framework import serializers
from .models import VectorConsulta, ConversacionSofia, ZonaInteres


class VectorConsultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VectorConsulta
        fields = '__all__'


class ConversacionSofiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversacionSofia
        fields = '__all__'


class ZonaInteresSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZonaInteres
        fields = '__all__'

