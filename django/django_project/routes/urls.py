from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('route_list/', views.route_list, name='route_list'),
    path('create/', views.route_create, name='route_create'),
    path('<int:pk>/', views.route_detail, name='route_detail'),
    path('<int:pk>/add_point/', views.add_point, name='add_point'),
    path('<int:route_pk>/delete_point/<int:point_pk>/', views.delete_point, name='delete_point'),
]