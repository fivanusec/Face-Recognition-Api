from rest_framework.serializers import ModelSerializer, ValidationError

from api.model import Students


class StudentSerializer(ModelSerializer):
    class Meta:
        model = Students
        fields = '__all__'
