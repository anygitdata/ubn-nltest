"""
preds.urls
"""


from django.urls import path

from .views import index, greed, get_content_eds, get_content_eds_html



urlpatterns = [

    path('greed/', greed, name='greed'),
    path('contenteds/', get_content_eds, name="contenteds" ),
    path('contentedstag/', get_content_eds_html, name="contentedstag" ),
    path('', index, name='preds'),

]
