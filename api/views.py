import os
from os import path
from uuid import uuid4

from cv2 import imread
from deepface import DeepFace
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework.views import APIView
import pandas as pd


def upload_image_handler(request):
    img = request.FILES['image']
    img_extension = path.splitext(img.name)[-1]
    img_full = settings.MEDIA_ROOT + str(uuid4()) + img_extension
    default_storage.save(img_full, img)
    return img_full


class Image(APIView):
    def post(self, request, *args, **kwargs) -> Response:
        upload = upload_image_handler(request=request)
        img = imread(upload)
        face = DeepFace.verify(img1_path=upload, img2_path=upload, model_name='Facenet')
        print(face)
        result = DeepFace.find(img, db_path=settings.REF_ROOT, model_name='Dlib')
        if not result.empty:
            data = pd.DataFrame(result)
            return Response({"Detected": os.path.split(os.path.splitext(data['identity'][0])[0])[-1]})
        return Response({"Not detected"})
