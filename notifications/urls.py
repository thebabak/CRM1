from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_inbox, name='inbox'),
    path('create/', views.notification_create, name='create'),
    path('sent/', views.notification_sent_list, name='sent'),
    path('<int:pk>/', views.notification_detail, name='detail'),
    path('sent/<int:pk>/', views.notification_sent_detail, name='sent_detail'),
]
