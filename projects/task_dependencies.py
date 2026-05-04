from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Task


class TaskDependencyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = Task.objects.get(
            id=task_id, project__organization=request.user.organization
        )
        depends_on_id = request.data.get("depends_on")
        depends_on = Task.objects.get(
            id=depends_on_id, project__organization=request.user.organization
        )
        task.dependencies.add(depends_on)
        return Response(
            {"message": f"Task {task_id} now depends on task {depends_on_id}"}
        )

    def get(self, request, task_id):
        task = Task.objects.get(
            id=task_id, project__organization=request.user.organization
        )
        dependencies = task.dependencies.all()
        return Response(
            {
                "task": task.title,
                "dependencies": [
                    {"id": t.id, "title": t.title, "status": t.status}
                    for t in dependencies
                ],
                "blocked": task.status == "pending"
                and not all(d.status == "completed" for d in dependencies),
            }
        )
