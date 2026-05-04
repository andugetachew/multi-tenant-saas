import re
from collections import Counter
from django.db.models import Q
from projects.models import Project, Task
from comments.models import Comment


class AITaskSuggester:
    def __init__(self, user):
        self.user = user
        self.org = user.organization

    def extract_keywords(self, text):
        # Simple keyword extraction
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "are", "was"}
        return [w for w in words if w not in stopwords]

    def suggest_tasks(self, project_id):
        project = Project.objects.get(id=project_id, organization=self.org)

        # Get comments from project
        comments = Comment.objects.filter(project=project)
        comment_text = " ".join([c.content for c in comments])

        # Extract keywords
        keywords = self.extract_keywords(comment_text)

        # Find similar tasks from other projects
        similar_tasks = Task.objects.filter(
            Q(project__organization=self.org)
            & (Q(title__icontains=keywords[0]) if keywords else Q())
        ).exclude(project=project)[:5]

        suggestions = []
        for task in similar_tasks:
            suggestions.append(
                {
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,
                    "similarity_score": 0.8,
                    "reason": f'Based on keywords: {", ".join(keywords[:3])}',
                }
            )

        # If no similar tasks, suggest based on project name
        if not suggestions:
            project_keywords = self.extract_keywords(project.name)
            suggestions.append(
                {
                    "title": f"Complete {project.name} documentation",
                    "description": f"Document all features and functionality for {project.name}",
                    "priority": "medium",
                    "similarity_score": 0.5,
                    "reason": "Based on project requirements",
                }
            )

            suggestions.append(
                {
                    "title": f"Review {project.name} codebase",
                    "description": "Perform code review and optimization",
                    "priority": "high",
                    "similarity_score": 0.5,
                    "reason": "Best practice recommendation",
                }
            )

        return suggestions
