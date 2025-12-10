# projects/serializers.py
from rest_framework import serializers
from .models import Project, Task, WorkSession

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'is_completed', 'created_at', 'order']

class WorkSessionSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkSession
        fields = ['id', 'start_time', 'end_time', 'notes', 'duration_minutes']

class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    work_sessions = WorkSessionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'created_at', 
            'updated_at', 'last_worked_on', 'priority', 'tasks', 'work_sessions'
        ]
        