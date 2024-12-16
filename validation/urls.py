from django.urls import path, include
from . import views
from .views import validate_item, element_detail
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.AllTD.as_view(), name="index"),
    path("valid", views.ValidTD.as_view(), name="valid"),
    path("notValid", views.NotValidTD.as_view(), name="notValid"),
    path("notChecked", views.NotChecked.as_view(), name="notChecked"),
    path("noAccess", views.noAccess.as_view(), name="noAccess"),
    path("AccessLevel", views.AccessLevel.as_view(), name="AccessLevel"),
    path("SyntaxLevel", views.SyntaxLevel.as_view(), name="SyntaxLevel"),
    path("SyntacticLevel", views.SyntacticLevel.as_view(), name="SyntacticLevel"),
    path("SemanticLevel", views.SemanticLevel.as_view(), name="SemanticLevel"),

    path('retrieve-endpoints', views.retrieve_endpoints_view, name='retrieve_endpoints_view'),
    path('validate-item/<str:oid>/<str:property>/', views.validate_item, name='validate_item'),
    path('validate-item/<str:oid>/<str:property>/<str:extraParameters>/', views.validate_item, name='validate_item_with_extra'),
    path('element/<int:item_id>/', element_detail, name='element_detail'),

    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]