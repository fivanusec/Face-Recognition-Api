import imagehash
import os
import numpy as np

from uuid import uuid4
from PIL import Image

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.cache import cache
from django.core.mail import send_mail

from rest_framework.response import Response


class TokenHandler:
    __token = None
    instance = None
    model_instance = None

    def __init__(self, instance=None, model_instance=None, token=None):
        self.__token = str(uuid4()) if token is None else token
        self.instance = instance
        self.model_instance = model_instance

    def create_token(self) -> None:
        cache.set(self.instance + self.__token, self.model_instance.id, timeout=1000 * 60 * 60 * 24 * 3)

    def get_token(self, instance, token):
        return cache.get(instance + token)

    def retrive_token(self):
        return self.__token

    def email_token(self, model_instance):
        send_mail(
            subject="Confirm your attendance",
            message=f"Here is token to confirm your attendance {self.__token}",
            from_email=[settings.EMAIL_HOST_USER, ],
            recipient_list=[
                model_instance.email,
            ]
        )


class DuplicateRemover:
    def __init__(self, dirname, hash_size=8):
        self.dirname = dirname
        self.hash_size = hash_size

    def find_duplicates(self):
        fnames = os.listdir(self.dirname)
        hashes = {}
        duplicates = []
        print("Finding duplicates now")
        for image in fnames:
            with Image.open(os.path.join(self.dirname, image)) as img:
                temp_hash = imagehash.average_hash(img, self.hash_size)
                if temp_hash in hashes:
                    print(
                        "Duplicate {} found for Image {}".format(
                            image, hashes[temp_hash]
                        )
                    )
                    duplicates.append(image)
                else:
                    hashes[temp_hash] = image

        if len(duplicates) != 0:
            space_saved = 0
            for duplicate in duplicates:
                space_saved += os.path.getsize(os.path.join(self.dirname, duplicate))

                os.remove(os.path.join(self.dirname, duplicate))
            print("All duplicates are deleted")
        else:
            print("No Duplicates Found")

    def find_similar(self, location, similarity=80):
        fnames = os.listdir(self.dirname)
        threshold = 1 - similarity / 100
        diff_limit = int(threshold * (self.hash_size ** 2))

        with Image.open(location) as img:
            hash1 = imagehash.average_hash(img, self.hash_size).hash

        print("Finding Similar Images to {} Now!\n".format(location))
        for image in fnames:
            with Image.open(os.path.join(self.dirname, image)) as img:
                hash2 = imagehash.average_hash(img, self.hash_size).hash

                if np.count_nonzero(hash1 != hash2) <= diff_limit:
                    print(
                        "{} image found {}% similar to {}".format(
                            image, similarity, location
                        )
                    )


class ResponseHandler(object):
    __instance = None

    def __init__(self, *args, **kwargs):
        if self._initialized:
            return
        self._initialized = True

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance

    @classmethod
    def get(cls):
        if cls.__instance is not None:
            return cls.__instance
        return cls()

    def create_success_response(self, message) -> Response:
        return Response({"success": message}, status=200)

    def create_error_response(self, message) -> Response:
        return Response({"error": message}, status=400)

    def create_response(self, response) -> Response:
        return Response(response, status=200)


def upload_image_handler(request):
    img = request.FILES["image"]
    img_extension = os.path.splitext(img.name)[-1]
    img_full = settings.MEDIA_ROOT + str(uuid4()) + img_extension
    default_storage.save(img_full, img)
    return img_full
