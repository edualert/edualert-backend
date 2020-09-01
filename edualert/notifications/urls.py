from django.urls import path
from . import views

app_name = 'notifications'
urlpatterns = [
    path('my-sent-messages/', views.MySentMessageList.as_view(), name='my-sent-message-list'),
    path('my-sent-messages/<int:id>/', views.MySentMessageDetail.as_view(), name='my-sent-message-detail'),
    path('my-received-messages/', views.MyReceivedMessageList.as_view(), name='my-received-message-list'),
    path('my-received-messages/<int:id>/mark-as-read/', views.MyReceivedMessageMarkAsRead.as_view(), name='my-received-message-mark-as-read'),
    path('my-received-messages/<int:id>/', views.MyReceivedMessageDetail.as_view(), name='my-received-message-detail')
]
