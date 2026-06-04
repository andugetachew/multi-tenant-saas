from django.db import models


class Project(models.Model):
    organization = models.ForeignKey(
        "organizations.organization", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo = models.ImageField(upload_to="project_logos/", null=True, blank=True)
    cover_image = models.ImageField(upload_to="project_covers/", null=True, blank=True)
    tags = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated tags"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("archived", "Archived"),
            ("completed", "Completed"),
        ],
        default="active",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["organization", "status", "created_at"]),
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    assigned_to = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
    )
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_task = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="subtasks"
    )
    dependencies = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="dependent_tasks"
    )
    estimated_hours = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    actual_hours = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["project", "priority"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["project", "status", "due_date"]),
        ]

    def __str__(self):
        return self.title


class TaskTemplate(models.Model):
    organization = models.ForeignKey(
        "organizations.organization", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=20, choices=Task.PRIORITY_CHOICES, default="medium"
    )
    estimated_hours = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RecurringTask(models.Model):
    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=20, choices=Task.PRIORITY_CHOICES, default="medium"
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    next_due_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.frequency})"


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="task_attachments/%Y/%m/%d/")
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
