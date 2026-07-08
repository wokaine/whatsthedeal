from django.urls import path

from . import views
from .views import PostDetailView, UserDetailView

app_name = "whatsthedeal"
urlpatterns = [
    path("", views.index, name="index"),
    path("posts/create/", views.create_post, name="post-create"),
    path("posts/all/", views.feed, name="post-list"),
    path("posts/view/<int:pk>/", PostDetailView.as_view(), name="post-view"),
    path("posts/<int:postid>/preference/<int:userpreference>/", views.postpreference, name="post-preference"),
    path("users/<str:username>/", UserDetailView.as_view(), name="user-view")
]