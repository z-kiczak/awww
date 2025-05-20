from rest_framework_nested import routers
from .views import RouteViewSet, PointViewSet

router = routers.DefaultRouter()
router.register(r'routes', RouteViewSet, basename='route')  # /api/routes/

points_router = routers.NestedSimpleRouter(
    router, 
    r'routes', 
    lookup='route'  # Nazwa parametru w URL (będzie route_pk)
)
points_router.register(
    r'points', 
    PointViewSet, 
    basename='route-points'  # /api/routes/{route_pk}/points/
)

urlpatterns = router.urls + points_router.urls