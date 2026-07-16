# projects/views.py
import calendar
import json
from collections import defaultdict
from datetime import date, timedelta

from django.views.generic import ListView, DetailView, CreateView, UpdateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import F
from rest_framework import viewsets
from django import forms
from django.views.generic import DeleteView, TemplateView
from django.views.generic import View
from django.http import HttpResponseRedirect, JsonResponse

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
    fields = ['title', 'description', 'scheduled_date', 'recurrence']
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
    
class TaskToggleCompletionView(LoginRequiredMixin, View):
    """
    Toggle a task between done and planned (is_completed stays in sync via Task.save()).
    """
    def post(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=kwargs['pk'])
        task.status = 'planned' if task.status == 'done' else 'done'
        task.save()
        return HttpResponseRedirect(reverse('projects:project_detail', kwargs={'pk': task.project.id}))


class TaskToggleJSONView(LoginRequiredMixin, View):
    """Toggle done/planned and return JSON (for inline dashboard checkboxes)."""
    def post(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=kwargs['pk'])
        task.status = 'planned' if task.status == 'done' else 'done'
        task.save()
        return JsonResponse({'status': task.status, 'is_completed': task.is_completed})


class HabitToggleView(LoginRequiredMixin, View):
    """Toggle a recurring task's completion for today/this-week/this-month. Returns JSON."""
    def post(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=kwargs['pk'])
        if not task.is_habit:
            return JsonResponse({'error': 'not a recurring task'}, status=400)
        is_done = task.toggle_current_period()
        return JsonResponse({'is_done': is_done})


class TaskSetStatusView(LoginRequiredMixin, View):
    """Set a task to an explicit status (for the board). Accepts JSON or form 'status'."""
    def post(self, request, *args, **kwargs):
        task = get_object_or_404(Task, pk=kwargs['pk'])
        status = request.POST.get('status')
        if status is None:
            try:
                status = json.loads(request.body or '{}').get('status')
            except json.JSONDecodeError:
                status = None
        if status in dict(Task.STATUS_CHOICES):
            task.status = status
            task.save()
            return JsonResponse({'status': task.status, 'is_completed': task.is_completed})
        return JsonResponse({'error': 'invalid status'}, status=400)


# ---------------------------------------------------------------------------
# Task views: Table / Board / Calendar (Phase C) — all filter by ?project=<id>
# ---------------------------------------------------------------------------
class _TaskViewMixin(LoginRequiredMixin):
    def get_current_project(self):
        pid = self.request.GET.get('project')
        if pid and pid.isdigit():
            return Project.objects.filter(pk=pid).first()
        return None

    def get_tasks(self):
        qs = Task.objects.select_related('project')
        project = self.get_current_project()
        if project:
            qs = qs.filter(project=project)
        return qs

    def base_context(self, view_name):
        project = self.get_current_project()
        return {
            'projects': Project.objects.all().order_by('name'),
            'current_project': project,
            'current_project_id': str(project.id) if project else '',
            'view': view_name,
        }


class TaskTableView(_TaskViewMixin, TemplateView):
    template_name = 'projects/tasks/table.html'

    SORTABLE = {
        'project': 'project__name',
        'title': 'title',
        'status': 'status',
        'scheduled_date': 'scheduled_date',
        'estimate': 'estimate_minutes',
    }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.base_context('table'))

        sort = self.request.GET.get('sort', 'scheduled_date')
        desc = sort.startswith('-')
        key = sort[1:] if desc else sort
        field = self.SORTABLE.get(key, 'scheduled_date')

        tasks = self.get_tasks()
        if field == 'scheduled_date':
            expr = F('scheduled_date')
            expr = expr.desc(nulls_last=True) if desc else expr.asc(nulls_last=True)
            tasks = tasks.order_by(expr, 'project__name', 'order')
        else:
            tasks = tasks.order_by(('-' if desc else '') + field, 'project__name', 'order')

        # Column headers with next-sort links + direction arrows
        columns = []
        for label, ckey in [
            ('Project', 'project'), ('Task', 'title'), ('Status', 'status'),
            ('Scheduled', 'scheduled_date'), ('Estimate', 'estimate'),
        ]:
            if sort == ckey:
                nxt, arrow = '-' + ckey, '▲'
            elif sort == '-' + ckey:
                nxt, arrow = ckey, '▼'
            else:
                nxt, arrow = ckey, ''
            columns.append({'label': label, 'next': nxt, 'arrow': arrow})

        ctx['tasks'] = tasks
        ctx['columns'] = columns
        return ctx


class TaskBoardView(_TaskViewMixin, TemplateView):
    template_name = 'projects/tasks/board.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.base_context('board'))
        tasks = list(self.get_tasks().order_by('scheduled_date', 'order'))
        ctx['columns'] = [
            {'key': key, 'label': label,
             'tasks': [t for t in tasks if t.status == key]}
            for key, label in Task.STATUS_CHOICES
        ]
        ctx['status_choices'] = Task.STATUS_CHOICES
        return ctx


class TaskCalendarView(_TaskViewMixin, TemplateView):
    template_name = 'projects/tasks/calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.base_context('calendar'))
        today = timezone.localdate()

        try:
            year, month = map(int, self.request.GET.get('month', '').split('-'))
            first = date(year, month, 1)
        except (ValueError, AttributeError):
            first = today.replace(day=1)

        last_day = calendar.monthrange(first.year, first.month)[1]
        month_end = first.replace(day=last_day)

        by_day = defaultdict(list)
        for t in self.get_tasks().filter(scheduled_date__range=(first, month_end)):
            by_day[t.scheduled_date].append(t)

        cal = calendar.Calendar(firstweekday=0)  # Monday
        weeks = []
        for week in cal.monthdatescalendar(first.year, first.month):
            days = []
            for d in week:
                day_tasks = by_day.get(d, [])
                project_ids = {t.project_id for t in day_tasks}
                days.append({
                    'date': d,
                    'in_month': d.month == first.month,
                    'is_today': d == today,
                    'tasks': day_tasks,
                    'clash': len(project_ids) >= 2,
                })
            weeks.append(days)

        ctx['weeks'] = weeks
        ctx['month_label'] = first.strftime('%B %Y')
        ctx['prev_month'] = (first - timedelta(days=1)).replace(day=1).strftime('%Y-%m')
        ctx['next_month'] = (month_end + timedelta(days=1)).strftime('%Y-%m')
        return ctx


class TaskQuickCreateView(LoginRequiredMixin, CreateView):
    """General task create (used by the calendar '+' and toolbar 'New task')."""
    model = Task
    fields = ['project', 'title', 'scheduled_date', 'status', 'estimate_minutes', 'recurrence']
    template_name = 'projects/tasks/task_quick_form.html'

    def get_initial(self):
        initial = super().get_initial()
        d = self.request.GET.get('date')
        if d:
            initial['scheduled_date'] = d
        pid = self.request.GET.get('project')
        if pid and pid.isdigit():
            initial['project'] = pid
        return initial

    def get_success_url(self):
        return reverse('projects:task_table')


class TaskBulkUpdateView(LoginRequiredMixin, View):
    """
    Apply one change (status / scheduled date / recurrence) or delete to many
    tasks at once, selected via checkboxes on the Tasks table view.
    """
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('task_ids')
        redirect_to = request.POST.get('next') or reverse('projects:task_table')

        if not ids:
            return HttpResponseRedirect(redirect_to)

        qs = Task.objects.filter(pk__in=ids)

        if request.POST.get('bulk_delete') == '1':
            qs.delete()
            return HttpResponseRedirect(redirect_to)

        update_fields = {}

        status = request.POST.get('bulk_status')
        if status in dict(Task.STATUS_CHOICES):
            update_fields['status'] = status
            update_fields['is_completed'] = (status == 'done')

        if request.POST.get('bulk_clear_date') == '1':
            update_fields['scheduled_date'] = None
        else:
            scheduled_date = request.POST.get('bulk_scheduled_date')
            if scheduled_date:
                update_fields['scheduled_date'] = scheduled_date

        recurrence = request.POST.get('bulk_recurrence')
        if recurrence in dict(Task.RECURRENCE_CHOICES):
            update_fields['recurrence'] = recurrence

        if update_fields:
            qs.update(**update_fields)

        return HttpResponseRedirect(redirect_to)
