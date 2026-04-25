"""
Plugin URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views_plugin import PluginInstallationViewSet, PluginViewSet


router = DefaultRouter()
router.register(r"plugins", PluginViewSet, basename="plugin")
router.register(r"plugin-installations", PluginInstallationViewSet, basename="plugin-installation")

urlpatterns = [
    path("", include(router.urls)),
]
