
from django.urls import path

from .views import index, greed, get_content_eds





urlpatterns = [

    path('greed/', greed, name='greed'),
    path('contenteds', get_content_eds, name="contenteds" ),
    path('', index, name='preds'),

]
