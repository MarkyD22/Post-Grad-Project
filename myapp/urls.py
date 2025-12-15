from django.urls import path
from . import views

urlpatterns = [
    # Home and auth
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main dashboard router
    path('dashboard/', views.dashboard, name='dashboard'),
    path('default-dashboard/', views.default_dashboard, name='default_dashboard'),
    
    # Role-specific dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('maintenance-dashboard/', views.maintenance_dashboard, name='maintenance_dashboard'),
    path('quality-dashboard/', views.quality_dashboard, name='quality_dashboard'),
    
    # Equipment views - SPECIFIC URLS FIRST!
    path('equipment/', views.equipment_list, name='equipment_list'),
    #path('equipment/create/', views.equipment_create, name='equipment_create'),  
    path('equipment/<str:machine_id>/complete/', views.mark_task_complete, name='mark_task_complete'),  # ← Specific action
    path('equipment/<str:machine_id>/', views.equipment_detail, name='equipment_detail'),  # ← Generic detail view LAST
    
    # Administrator equipment management
    path('administrator/add-equipment/', views.admin_add_equipment, name='admin_add_equipment'),
    path('administrator/edit-equipment/<str:machine_id>/', views.admin_edit_equipment, name='admin_edit_equipment'),
    path('administrator/delete-equipment/<str:machine_id>/', views.admin_delete_equipment, name='admin_delete_equipment'),
    path('administrator/complete-procedure/<str:machine_id>/', views.admin_complete_procedure, name='admin_complete_procedure'),
    
    # Maintenance user actions
    path('maintenance/add-equipment/', views.maintenance_add_equipment, name='maintenance_add_equipment'),
    path('maintenance/delete-equipment/<str:machine_id>/', views.maintenance_delete_equipment, name='maintenance_delete_equipment'),
    path('maintenance/complete-procedure/<str:machine_id>/', views.maintenance_complete_procedure, name='maintenance_complete_procedure'),
    
    # API endpoints
    path('api/equipment/<int:pk>/status/', views.equipment_api_status, name='equipment_api_status'),
    path('api/equipment/list/', views.equipment_api_list, name='equipment_api_list'),
    path('api/equipment/stats/', views.equipment_api_stats, name='equipment_api_stats'),
]