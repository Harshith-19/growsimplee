from django.contrib import admin
from django.urls import path, include
from .views import ProductView, start, RemoveProductView, ReachedView, ManualEditView, home


urlpatterns = [
    path('home/', home),
    path('start/', start.as_view()),
    path('product/', ProductView.as_view()),
    path('removeproduct/', RemoveProductView.as_view()),
    path('picked/', ReachedView.as_view()),
    path('manualedit/', ManualEditView.as_view()),
]