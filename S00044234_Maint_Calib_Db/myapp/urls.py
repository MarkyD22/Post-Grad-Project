from django.urls import path
from . import views

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('add/', views.add_item, name='add_item'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

]
