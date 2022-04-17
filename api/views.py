import os
from os import path
from uuid import uuid4
import shutil
from cv2 import imread, imwrite
from deepface import DeepFace
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
import pandas as pd
from .utils import upload_image_handler
from .serializers import StudentSerializer
from .models import Students


class Image(APIView):
    def post(self, request, *args, **kwargs) -> Response:
        shutil.rmtree(settings.MEDIA_ROOT)
        upload = upload_image_handler(request=request)
        img = imread(upload)
        face = DeepFace.verify(img1_path=upload, img2_path=upload)
        result = DeepFace.find(img, db_path=settings.REF_ROOT, detector_backend="mtcnn", model_name="OpenFace")
        if not result.empty:
            data = pd.DataFrame(result)
            imwrite(
                filename=settings.REF_ROOT + str(
                    os.path.split(os.path.dirname(data['identity'][0]))[-1]) + "/" + str(
                    uuid4()) + str(path.splitext(upload)[-1]), img=img)
            try:
                student_data = os.path.split(os.path.dirname(data['identity'][0]))[-1]
                student_data = student_data.split()
                student = Students.objects.get(first_name=student_data[0], last_name=student_data[1])
            except Students.DoesNotExist:
                return Response({"failure": "Student does not exist in database"})
            serializer = StudentSerializer(student)
            return Response({"Detected": serializer.data})
        return Response({"Not detected"})


class CreateNewModel(APIView):
    def get(self, *args, **kwargs) -> Response:
        return Response({"models": [name for name in os.listdir(settings.REF_ROOT) if
                                    os.path.isdir(os.path.join(settings.REF_ROOT, name))]})

    def delete(self, request, *args, **kwargs) -> Response:
        if os.path.exists(settings.REF_ROOT + f"{request.data['name']} {request.data['last_name']}"):
            os.rmdir(settings.REF_ROOT + f"{request.data['name']} {request.data['last_name']}")
            return Response({"success": "Model deleted successfully"})
        return Response({"failure": "There is no model by this name!"})

    def put(self, request, *args, **kwargs):
        upload = upload_image_handler(request=request)
        img = imread(upload)
        verify = DeepFace.verify(img1_path=upload, img2_path=upload)
        if verify.get("verified"):
            imwrite(
                filename=settings.REF_ROOT + f"{request.data['name']} {request.data['last_name']}" + "/" + str(
                    uuid4()) + str(path.splitext(upload)[-1]),
                img=img)
            return Response({"success": "User is verified"})
        return Response({"failure": "User is not verified"})

    def post(self, request, *args, **kwargs) -> Response:
        if os.path.exists(settings.REF_ROOT + "representations_openface.pkl"):
            os.remove(path=settings.REF_ROOT + "representations_openface.pkl")
        os.mkdir(settings.REF_ROOT + f"{request.data['first_name']} {request.data['last_name']}")
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success" if os.path.isdir(
                    settings.REF_ROOT + f"{request.data['first_name']} {request.data['last_name']}") else "failure",
                "Model created successfully" if os.path.isdir(
                    settings.REF_ROOT + f"{request.data['first_name']} {request.data['last_name']}") else "There was an error"
            })
        return Response({"error": "There was an error"})
