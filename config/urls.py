from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'), 
    path('profile/', views.profile_view, name='profile'), 
    path('profile/delete/', views.delete_account_view, name='delete-account'),
    path('admin-panel/', views.admin_panel, name='admin-panel'),
    path('posts/<int:post_id>/edit/', views.edit_post, name='edit-post'),
]