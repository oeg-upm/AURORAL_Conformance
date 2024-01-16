from django.urls import path
from . import views
from .views import validate_item, element_detail

urlpatterns = [
    path("", views.AllTD.as_view(), name="index"),
    path("valid", views.ValidTD.as_view(), name="valid"),
    path("notValid", views.NotValidTD.as_view(), name="notValid"),
    path('retrieve-endpoints', views.retrieve_endpoints_view, name='retrieve_endpoints_view'),
    path('validate-item/<str:oid>/<str:property>/', validate_item, name='validate_item'),
    path('element/<int:item_id>/', element_detail, name='element_detail')
]