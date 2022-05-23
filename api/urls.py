from django.urls import path
from .views import RecognitionView, ModelView, AttendanceView, ConfirmAttendance

urlpatterns = [
    path("recognition/", RecognitionView.as_view(), name="New image"),
    path("model/", ModelView.as_view(), name="Create new model"),
    path("attendance/", AttendanceView.as_view(), name="attendance"),
    path("confirm-attendance/<str:token>", ConfirmAttendance.as_view())
]
