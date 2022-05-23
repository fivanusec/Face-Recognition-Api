from uuid import uuid4

from rest_framework.serializers import ModelSerializer, ValidationError, Serializer

from django.conf import settings

from api.model import Students, Attendance
from api.utils import TokenHandler


class StudentSerializer(ModelSerializer):
    class Meta:
        model = Students
        fields = "__all__"

    def create(self, validated_data):
        student = Students.objects.create(
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            year=validated_data["year"],
            field_of_study=validated_data["field_of_study"],
        )
        student.save()
        return student

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.year = validated_data.get("year", instance.year)
        instance.field_of_study = validated_data.get(
            "field_of_study", instance.field_of_study
        )
        instance.verified = True
        instance.save()
        return instance


class AttendanceSerializer(ModelSerializer):
    class Meta:
        model = Attendance
        fields = ('student', 'subject')

    def create(self, validated_data):
        attendance = Attendance.objects.create(
            student=validated_data['student'],
            subject=validated_data['subject'],
            token=str(uuid4())
        )
        attendance.save()
        return attendance


class ConfirmAttendanceSerializer(Serializer):
    def update(self, instance, validated_data=None):
        instance.confirmed = True
        instance.save()
        return instance
