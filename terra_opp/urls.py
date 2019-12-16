from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'terra_opp'

router = SimpleRouter()

router.register(r'viewpoints', views.ViewpointViewSet, basename='viewpoint')
router.register(r'campaigns', views.CampaignViewSet, basename='campaign')
router.register(r'pictures', views.PictureViewSet, basename='picture')

urlpatterns = router.urls

urlpatterns += [
    path(
        'viewpoints/<int:pk>/pdf',
        views.ViewpointPdf.as_view(),
        name='viewpoint-pdf',
    ),
    path(
        'viewpoints/<int:pk>/zip-pictures',
        views.ViewpointZipPictures.as_view(),
        name='viewpoint-zip',
    ),
]
