from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('maintenance-dashboard/', views.maintenance_dashboard, name='maintenance_dashboard'),
    path('quality-dashboard/', views.quality_dashboard, name='quality_dashboard'),
    path('test/', views.test, name='test')

]
