# core/views.py
from django.views.generic import TemplateView
from django.db.models import Count
from projects.models import Project

class HomeView(TemplateView):
    template_name = "core/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get project statistics for the dashboard
        context['active_projects'] = Project.objects.filter(status='active').count()
        context['paused_projects'] = Project.objects.filter(status='paused').count()
        context['completed_projects'] = Project.objects.filter(status='completed').count()
        context['total_projects'] = Project.objects.count()
        
        # Get recent projects
        context['recent_projects'] = Project.objects.all().order_by('-updated_at')[:5]
        
        # Get high priority projects
        context['priority_projects'] = Project.objects.filter(
            status='active'
        ).order_by('priority')[:5]
        
        # Get all projects for the main listing
        context['projects'] = Project.objects.all().order_by('priority', '-last_worked_on')
        
        return context
    