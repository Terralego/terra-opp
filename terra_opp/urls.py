from rest_framework.routers import SimpleRouter

from . import views

app_name = "terra_opp"

router = SimpleRouter()

router.register(r"viewpoints", views.ViewpointViewSet, basename="viewpoint")
router.register(r"campaigns", views.CampaignViewSet, basename="campaign")
router.register(r"pictures", views.PictureViewSet, basename="picture")
router.register(r"cities", views.CityViewSet, basename="city")
router.register(r"themes", views.ThemeViewSet, basename="theme")

urlpatterns = router.urls
