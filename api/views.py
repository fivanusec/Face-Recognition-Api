from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

import pandas as pd
import numpy as np
import os
import shutil
from os import path
from uuid import uuid4
from cv2 import imread, imwrite
from deepface import DeepFace

from .utils import upload_image_handler, DuplicateRemover, ResponseHandler, TokenHandler
from .serializer import StudentSerializer, AttendanceSerializer, ConfirmAttendanceSerializer
from .model import Students, Attendance


class RecognitionView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs) -> Response:
        shutil.rmtree(settings.MEDIA_ROOT)
        upload = upload_image_handler(request=request)
        img = imread(upload)
        DeepFace.verify(img1_path=upload, img2_path=upload)
        result = DeepFace.find(
            img,
            db_path=settings.REF_ROOT,
            detector_backend="mtcnn",
            model_name="ArcFace",
        )
        if not result.empty:
            data = pd.DataFrame(result)
            imwrite(
                filename=settings.REF_ROOT
                         + str(os.path.split(os.path.dirname(data["identity"][0]))[-1])
                         + "/"
                         + str(uuid4())
                         + str(path.splitext(upload)[-1]),
                img=img,
            )

            try:
                student_data = os.path.split(os.path.dirname(data["identity"][0]))[-1]
                student_data = student_data.split()
                student = Students.objects.filter(
                    first_name=student_data[0], last_name=student_data[1]
                ).first()
                attendance = Attendance.objects.filter(student=student.id, confirmed=False, recognition=False).first()
                handler = TokenHandler(token=attendance.token, instance=str(settings.SET_ATTENDANCE),
                                       model_instance=student)
                handler.create_token()
                handler.email_token(model_instance=Students.objects.filter(id=attendance.student.id).first())
                attendance.recognition = True
                attendance.save()
                duplicate = DuplicateRemover(
                    settings.REF_ROOT + f"{student_data[0]} {student_data[1]}"
                )
                duplicate.find_duplicates()
            except Students.DoesNotExist:
                return ResponseHandler.get().create_error_response(
                    "Student doesn't exist in database"
                )
            serializer = StudentSerializer(student)
            if not serializer.data["verified"]:
                return ResponseHandler.get().create_error_response(
                    "Student not verified"
                )
            return ResponseHandler.get().create_response(
                {
                    "detected": serializer.data,
                    "avg_cosine": np.average(data.ArcFace_cosine),
                }
            )
        return ResponseHandler.get().create_error_response(
            {"Requested picture does not match any in database"}
        )


class ModelView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, *args, **kwargs) -> Response:
        return ResponseHandler.get().create_response(
            {
                "models": [
                    name
                    for name in os.listdir(settings.REF_ROOT)
                    if os.path.isdir(os.path.join(settings.REF_ROOT, name))
                ]
            }
        )

    def delete(self, request, *args, **kwargs) -> Response:
        if os.path.exists(
                settings.REF_ROOT + f"{request.data['name']} {request.data['last_name']}"
        ):
            os.rmdir(
                settings.REF_ROOT
                + f"{request.data['name']} {request.data['last_name']}"
            )
            return ResponseHandler.get().create_error_response(
                "Model deleted successfully"
            )
        return ResponseHandler.get().create_error_response(
            "There is no model by this name!"
        )

    def put(self, request, *args, **kwargs):
        if os.path.exists(settings.REF_ROOT + "representations_arcface.pkl"):
            os.remove(path=settings.REF_ROOT + "representations_arcface.pkl")
        upload = upload_image_handler(request=request)
        img = imread(upload)
        verify = DeepFace.verify(img1_path=upload, img2_path=upload)
        if verify.get("verified"):
            imwrite(
                filename=settings.REF_ROOT
                         + f"{request.data['name']} {request.data['last_name']}"
                         + "/"
                         + str(uuid4())
                         + str(path.splitext(upload)[-1]),
                img=img,
            )
            test_recog = DeepFace.find(
                upload,
                db_path=settings.REF_ROOT,
                detector_backend="mtcnn",
                model_name="ArcFace",
            )
            if not test_recog.empty:
                student = Students.objects.filter(
                    first_name=request.data["name"], last_name=request.data["last_name"]
                ).first()
                serializer = StudentSerializer(instance=student, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return ResponseHandler.get().create_success_response(
                        "User is verified"
                    )
        return ResponseHandler.get().create_error_response("User is not verified")

    def post(self, request, *args, **kwargs) -> Response:
        os.mkdir(
            settings.REF_ROOT
            + f"{request.data['first_name']} {request.data['last_name']}"
        )
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseHandler.get().create_response(
                {
                    "success"
                    if os.path.isdir(
                        settings.REF_ROOT
                        + f"{request.data['first_name']} {request.data['last_name']}"
                    )
                    else "failure",
                    "Model created successfully"
                    if os.path.isdir(
                        settings.REF_ROOT
                        + f"{request.data['first_name']} {request.data['last_name']}"
                    )
                    else "There was an error",
                }
            )
        return ResponseHandler.get().create_error_response("There was an error")


"""
Faculty creates attendance for class and then students must confirm their attendance by going
through recognition process and then confirm identity by emailed token
"""


class AttendanceView(APIView):
    def post(self, request):
        if type(request.data) is list:
            serializer = AttendanceSerializer(data=request.data, many=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return ResponseHandler().get().create_success_response("Attendance created!")
            return ResponseHandler.get().create_error_response("There was an error while creating attendance")
        serializer = AttendanceSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return ResponseHandler().get().create_success_response("Attendance created!")
        return ResponseHandler.get().create_error_response("There was an error while creating attendance")


class ConfirmAttendance(APIView):
    def post(self, request, token):
        handler = TokenHandler(token=token)
        data = handler.get_token(instance=str(settings.SET_ATTENDANCE), token=token)
        if not data:
            return ResponseHandler.get().create_error_response("Token expired")
        serializer = ConfirmAttendanceSerializer(instance=Attendance.objects.filter(token=token).first(),
                                                 data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return ResponseHandler.get().create_success_response("Attendance confirmed")
        return ResponseHandler.get().create_error_response("There was an error while confirming your attendance")
