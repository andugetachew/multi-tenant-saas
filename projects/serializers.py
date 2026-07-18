from rest_framework import serializers
from .models import Project, Task
from .models import TaskTemplate

class ProjectSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(source="tasks.count", read_only=True)

    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ("organization", "created_by", "created_at", "updated_at")


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    assigned_to_email = serializers.EmailField(
        source="assigned_to.email", read_only=True
    )

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ("project", "created_by", "created_at", "updated_at")



class TaskTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTemplate
        fields = ["id", "organization", "name", "description", "priority", "estimated_hours", "created_at"]
        read_only_fields = ["id", "organization", "created_at"]