from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', login, name='login'),
    path('', index, name="index"),
    path('webcam-stream/<int:id>/', webcam_stream, name='webcam-stream'),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
