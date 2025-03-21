# projects/views.py
from django.views.generic import ListView, DetailView
from rest_framework import viewsets

from .models import Project, Task, WorkSession
from .serializers import ProjectSerializer, TaskSerializer, WorkSessionSerializer

# Frontend views
class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        queryset = Project.objects.all()
        status = self.request.GET.get('status')
        
        if status and status != 'all':
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('priority', '-last_worked_on')

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

# API views
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class WorkSessionViewSet(viewsets.ModelViewSet):
    queryset = WorkSession.objects.all()
    serializer_class = WorkSessionSerializer
    