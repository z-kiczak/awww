"""
URL configuration for routes_editor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from routes import views as routes_views
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token

schema_view = get_schema_view(
    openapi.Info(
        title="Route Editor API",
        default_version='v1',
        description="API for managing routes and points",
    ),
    public=True,
)

urlpatterns = [
    # Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication (Web Interface)
    path('accounts/', include([
        path('login/', auth_views.LoginView.as_view(
            template_name='registration/login.html',
            redirect_authenticated_user=True
        ), name='login'),
        path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
        path('register/', routes_views.register, name='register'),
    ])),
    
    # API Authentication
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    
    # Web Interface
    path('', include('routes.urls')),  # Contains your template views
    
    # API Endpoints
    path('api/', include('routes.api_urls')),  # Contains DRF ViewSets
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)