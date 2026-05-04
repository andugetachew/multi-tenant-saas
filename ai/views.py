from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .suggestions import AITaskSuggester


class AITaskSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        suggester = AITaskSuggester(request.user)
        suggestions = suggester.suggest_tasks(project_id)
        return Response({"project_id": project_id, "suggestions": suggestions})
