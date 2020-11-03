
from django.urls import path

from .views import index, greed





urlpatterns = [

    path('greed/', greed, name='greed'),
    path('', index, name='preds'),

]
