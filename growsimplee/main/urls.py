from django.contrib import admin
from django.urls import path, include
from .views import ProductView, start


urlpatterns = [
    path('start/', start.as_view()),
    path('product/', ProductView.as_view()),
]