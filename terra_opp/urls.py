from rest_framework.routers import SimpleRouter

from . import views

app_name = 'terra_opp'

router = SimpleRouter()

router.register(r'viewpoints', views.ViewpointViewSet, basename='viewpoint')
router.register(r'campaigns', views.CampaignViewSet, basename='campaign')
router.register(r'pictures', views.PictureViewSet, basename='picture')

urlpatterns = router.urls
