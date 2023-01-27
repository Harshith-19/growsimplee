from django.contrib import admin
from django.urls import path, include
from .views import ProductView, start, home


urlpatterns = [
    path('home/', home),
    path('start/', start.as_view()),
    path('product/', ProductView.as_view()),
]