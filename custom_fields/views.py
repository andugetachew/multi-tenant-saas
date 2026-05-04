from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomField, CustomFieldValue
from .serializers import CustomFieldSerializer, CustomFieldValueSerializer


class CustomFieldListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomFieldSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomField.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class CustomFieldValueView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        from projects.models import Project

        project = Project.objects.get(
            id=project_id, organization=request.user.organization
        )
        values = CustomFieldValue.objects.filter(project=project)
        serializer = CustomFieldValueSerializer(values, many=True)
        return Response(serializer.data)

    def post(self, request, project_id):
        from projects.models import Project

        project = Project.objects.get(
            id=project_id, organization=request.user.organization
        )
        field_id = request.data.get("field_id")
        value = request.data.get("value")

        field = CustomField.objects.get(
            id=field_id, organization=request.user.organization
        )

        obj, created = CustomFieldValue.objects.update_or_create(
            project=project, field=field, defaults={"value": value}
        )

        serializer = CustomFieldValueSerializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
