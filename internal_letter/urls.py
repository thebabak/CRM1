from django.urls import path
from . import views

app_name = 'internal_letter'

urlpatterns = [
    path('', views.letter_list, name='list'),
    path('create/', views.letter_create, name='create'),
    path('<int:pk>/', views.letter_detail, name='detail'),
    path('<int:pk>/send/', views.letter_send, name='send'),
    path('<int:pk>/delete/', views.letter_delete, name='delete'),
    path('<int:pk>/mark-unread/', views.letter_mark_unread, name='mark_unread'),
]
