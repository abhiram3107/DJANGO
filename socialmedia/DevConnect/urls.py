# urls.py
from django.urls import path
from . import views
from .views import CustomTokenObtainPairView, CustomTokenRefreshView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('create_post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('myposts/', views.my_posts, name='myposts'), 
    path('post/<int:post_id>/comment/', views.comment_on_post, name='comment_on_post'),
    path('author/<int:user_id>/', views.author_profile, name='author_profile'),
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    #-----------------------------------API-----------------------------------------------------------
    path('api/register/', views.api_register_user, name='api_register_user'),
    path('api/login/', views.api_login_user, name='api_login_user'),
    path('api/logout/', views.api_logout_user, name='api_logout_user'),
    path('api/user/', views.get_user_info, name='get_user_info'),
    path('user/', views.current_user, name='current-user'),
    path('api/posts/', views.api_list_posts, name='api_list_posts'),
    path('api/user/posts/', views.api_user_posts, name='api_user_posts'),
    path('api/posts/create/', views.api_create_post, name='api_create_post'),
    path('api/posts/<int:post_id>/edit/', views.api_edit_post, name='api_edit_post'),
    path('api/posts/<int:post_id>/delete/', views.api_delete_post, name='api_delete_post'),
    path('api/posts/<int:post_id>/like/', views.api_like_post, name='api_like_post'),
    path('api/like-status/<int:post_id>/', views.api_like_status, name='api_like_status'),
    path('api/posts/<int:post_id>/comment/', views.api_comment_on_post, name='api_comment_on_post'),
    path('api/profile/', views.api_get_profile, name='api_get_profile'),
    path('api/profile/<int:user_id>/', views.api_get_profile, name='api_get_profile_by_id'),
    path('api/profile/edit/', views.api_edit_profile, name='api_edit_profile'),
    path('api/follow/<int:user_id>/', views.api_follow_user, name='api_follow_user'),
    path('api/unfollow/<int:user_id>/', views.api_unfollow_user, name='api_unfollow_user'),
    path('api/follow/<int:user_id>/status/', views.api_follow_status, name='api_follow_status'),   
    path('api/followers/<str:username>/', views.api_user_followers, name='user-followers'),
    path('api/following/<str:username>/', views.api_user_following, name='user-following'),

    
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),


]
