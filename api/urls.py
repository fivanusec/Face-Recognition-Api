from django.urls import path
from .views import Image, CreateNewModel

urlpatterns = [
    path("image/", Image.as_view(), name="New image"),
    path("model/", CreateNewModel.as_view(), name="Create new model")
]
