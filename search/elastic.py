from django.db.models import Q
from projects.models import Project, Task


class AdvancedSearch:
    def __init__(self, user):
        self.user = user
        self.org = user.organization

    def search_all(self, query):
        results = {
            "projects": self.search_projects(query),
            "tasks": self.search_tasks(query),
            "comments": self.search_comments(query),
        }
        return results

    def search_projects(self, query):
        return Project.objects.filter(
            Q(organization=self.org)
            & (
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(tags__icontains=query)
            )
        ).values("id", "name", "description", "created_at")

    def search_tasks(self, query):
        return Task.objects.filter(
            Q(project__organization=self.org)
            & (Q(title__icontains=query) | Q(description__icontains=query))
        ).values("id", "title", "status", "priority", "project__name")

    def search_comments(self, query):
        from comments.models import Comment

        return Comment.objects.filter(
            Q(project__organization=self.org) & Q(content__icontains=query)
        ).values("id", "content", "project__name", "created_at")
