# projects/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from rest_framework import viewsets

from .models import Project, Task, WorkSession
from .serializers import ProjectSerializer, TaskSerializer, WorkSessionSerializer

# Frontend views
class ProjectListView(ListView):
    model = Project
    template_name = 'projects/index.html'
    context_object_name = 'projects'
    ordering = ['priority', '-last_worked_on']

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/detail.html'
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