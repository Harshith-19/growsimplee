from django.contrib import admin
from django.urls import path, include
from .views import ProductView, start, RemoveProductView, PickedUpView, home


urlpatterns = [
    path('home/', home),
    path('start/', start.as_view()),
    path('product/', ProductView.as_view()),
    path('removeproduct/', RemoveProductView.as_view()),
    path('picked/', PickedUpView.as_view()),
]