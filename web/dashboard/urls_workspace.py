"""
Workspace URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views_workspace import FindingCommentViewSet, InvitationAcceptView, WorkspaceViewSet


router = DefaultRouter()
router.register(r"workspaces", WorkspaceViewSet, basename="workspace")
router.register(r"comments", FindingCommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "invitation/<str:token>/accept/",
        InvitationAcceptView.as_view(),
        name="workspace-invitation-accept",
    ),
]
