# projects/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "projects"

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'sessions', views.WorkSessionViewSet)

urlpatterns = [
    # Frontend URLs
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    
    # API URLs
    path('api/', include(router.urls)),
]