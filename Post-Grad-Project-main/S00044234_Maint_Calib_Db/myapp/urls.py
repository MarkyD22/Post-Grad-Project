from django.urls import path
from . import views

urlpatterns = [
    #Signup and login URLS
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
     path('default-dashboard/', views.default_dashboard, name='default_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('maintenance-dashboard/', views.maintenance_dashboard, name='maintenance_dashboard'),
    path('quality-dashboard/', views.quality_dashboard, name='quality_dashboard'),
    path('test/', views.test, name='test'),

    # Equipment management URLs
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/add/', views.equipment_create, name='equipment_create'),
    path('equipment/<str:machine_id>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/<str:machine_id>/edit/', views.equipment_update, name='equipment_update'),
    path('equipment/<str:machine_id>/delete/', views.equipment_delete, name='equipment_delete'),
    path('equipment/<str:machine_id>/quick-update/', views.equipment_quick_update, name='equipment_quick_update'),
    
    # API endpoints
    path('api/equipment/<str:machine_id>/status/', views.equipment_api_status, name='equipment_api_status'),
]
