# projects/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from rest_framework import viewsets
from django import forms
from django.views.generic import DeleteView

from .models import Project, Task, WorkSession
from .serializers import ProjectSerializer, TaskSerializer, WorkSessionSerializer

# Frontend views
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        queryset = Project.objects.all()
        status = self.request.GET.get('status')
        
        if status and status != 'all':
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('priority', '-last_worked_on')

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

# New Views for Actions
class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ['name', 'description', 'status', 'priority']
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project_list')

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ['name', 'description', 'status', 'priority']
    template_name = 'projects/project_form.html'
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.pk})

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    fields = ['title', 'description', 'is_completed']
    template_name = 'projects/task_form.html'
    
    def form_valid(self, form):
        form.instance.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.kwargs['project_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return context

class WorkSessionCreateView(LoginRequiredMixin, CreateView):
    model = WorkSession
    fields = ['notes']
    template_name = 'projects/work_session_form.html'
    
    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.instance.project = project
        form.instance.start_time = timezone.now()
        
        # Update the project's last_worked_on time
        project.last_worked_on = timezone.now()
        project.save()
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.kwargs['project_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        context['now'] = timezone.now()
        return context

class StartSessionView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        session = WorkSession.objects.create(
            project=project,
            start_time=timezone.now()
        )
        project.last_worked_on = timezone.now()
        project.save()
        return reverse('projects:project_detail', kwargs={'pk': project.pk})

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

class WorkSessionUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkSession
    fields = ['notes', 'end_time']
    template_name = 'projects/work_session_form.html'
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.project.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        context['editing'] = True
        return context

class WorkSessionDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkSession
    template_name = 'projects/work_session_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.project.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context