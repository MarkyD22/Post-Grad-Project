from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    #path('', views.item_list, name='item_list'),
    path('add/', views.add_item, name='add_item'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('test/', views.test, name='test')

]
