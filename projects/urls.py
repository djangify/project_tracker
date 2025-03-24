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
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('project/<int:pk>/start-session/', views.StartSessionView.as_view(), name='start_session'),
    path('project/<int:project_pk>/add-task/', views.TaskCreateView.as_view(), name='task_create'),
    path('project/<int:project_pk>/log-session/', views.WorkSessionCreateView.as_view(), name='session_create'),
    path('work-session/<int:pk>/edit/', views.WorkSessionUpdateView.as_view(), name='session_edit'),
    path('work-session/<int:pk>/delete/', views.WorkSessionDeleteView.as_view(), name='session_delete'),
    
    # API URLs
    path('api/', include(router.urls)),
]
