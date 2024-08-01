from django.urls import path
from .views import *
urlpatterns = [
    path('login/', login, name='login'),
    path('', index, name="index"),
    path('video_feed/<int:id>/', video_feed, name='video_feed'),
    path('webcam-stream/<int:id>/', webcam_stream, name='webcam-stream'),
]
