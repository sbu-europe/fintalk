from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('agent/query/', views.agent_query, name='agent_query'),
]
