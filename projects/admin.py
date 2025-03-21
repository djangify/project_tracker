# projects/admin.py
from django.contrib import admin
from .models import Project, Task, WorkSession

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

class WorkSessionInline(admin.TabularInline):
    model = WorkSession
    extra = 0

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'priority', 'created_at', 'last_worked_on')
    list_filter = ('status', 'priority')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'
    inlines = [TaskInline, WorkSessionInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'project')
    search_fields = ('title', 'description')

@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('project', 'start_time', 'end_time', 'duration_minutes')
    list_filter = ('project',)
    search_fields = ('notes',)
    