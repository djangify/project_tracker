# projects/admin.py
from django.contrib import admin
from .models import Project, Task, TaskCompletion, WorkSession

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ('title', 'status', 'scheduled_date', 'order')
    ordering = ('order',)

class WorkSessionInline(admin.TabularInline):
    model = WorkSession
    extra = 0
    fields = ('task', 'start_time', 'end_time', 'notes')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'priority', 'created_at', 'last_worked_on')
    list_filter = ('status', 'priority')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'
    inlines = [TaskInline, WorkSessionInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'recurrence', 'scheduled_date', 'order', 'created_at')
    list_filter = ('status', 'recurrence', 'project', 'scheduled_date')
    search_fields = ('title', 'description')
    list_editable = ('status', 'order')


@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ('task', 'period_start', 'completed_at')
    list_filter = ('period_start',)
    search_fields = ('task__title',)

@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('project', 'task', 'start_time', 'end_time', 'duration_minutes')
    list_filter = ('project',)
    search_fields = ('notes',)
    raw_id_fields = ('project', 'task')
