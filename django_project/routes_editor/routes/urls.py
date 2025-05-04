from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('routes/', views.route_list, name='route_list'),
    path('routes/create/', views.route_create, name='route_create'),
    path('routes/<int:pk>/', views.route_detail, name='route_detail'),
    path('routes/<int:pk>/add_point/', views.add_point, name='add_point'),
    path('routes/<int:route_pk>/delete_point/<int:point_pk>/', views.delete_point, name='delete_point'),
]