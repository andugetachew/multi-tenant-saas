import pytest
from accounts.models import User
from organizations.models import Organization
from projects.models import Project, Task
from comments.models import Comment
from ai.suggestions import AITaskSuggester


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def other_org(db):
    return Organization.objects.create(name="Other Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(
        email="dev@acme.com", password="pass123", organization=org
    )


@pytest.fixture
def project(org, user):
    return Project.objects.create(organization=org, name="Website Redesign", created_by=user)


@pytest.fixture
def other_project_same_org(org, user):
    return Project.objects.create(organization=org, name="Mobile App", created_by=user)


@pytest.fixture
def other_org_project(other_org):
    return Project.objects.create(organization=other_org, name="Secret Project")


@pytest.mark.django_db
class TestExtractKeywords:
    def test_filters_stopwords_and_short_words(self, user):
        suggester = AITaskSuggester(user)
        keywords = suggester.extract_keywords(
            "The database migration and the caching layer are important"
        )
        assert "the" not in keywords
        assert "and" not in keywords
        assert "are" not in keywords
        assert "database" in keywords
        assert "migration" in keywords
        assert "caching" in keywords

    def test_words_under_three_chars_excluded(self, user):
        suggester = AITaskSuggester(user)
        keywords = suggester.extract_keywords("a an go to fix bug")
        assert "fix" in keywords
        assert "bug" in keywords
        assert "go" not in keywords
        assert "to" not in keywords


@pytest.mark.django_db
class TestSuggestTasks:
    def test_finds_similar_task_by_first_keyword(
        self, user, project, other_project_same_org
    ):
        Comment.objects.create(
            project=project, user=user, content="caching layer needs review"
        )
        matching_task = Task.objects.create(
            project=other_project_same_org, title="Implement caching layer", priority="high"
        )
        Task.objects.create(
            project=other_project_same_org, title="Unrelated deployment task", priority="low"
        )

        suggester = AITaskSuggester(user)
        suggestions = suggester.suggest_tasks(project.id)

        titles = [s["title"] for s in suggestions]
        assert matching_task.title in titles

    def test_excludes_tasks_from_current_project(self, user, project):
        Comment.objects.create(
            project=project, user=user, content="caching improvements needed"
        )
        Task.objects.create(project=project, title="caching cleanup", priority="medium")

        suggester = AITaskSuggester(user)
        suggestions = suggester.suggest_tasks(project.id)

        titles = [s["title"] for s in suggestions]
        assert "caching cleanup" not in titles

    def test_excludes_tasks_from_other_organizations(
        self, user, project, other_org_project
    ):
        Comment.objects.create(
            project=project, user=user, content="database migration issues"
        )
        Task.objects.create(
            project=other_org_project, title="database migration fix", priority="high"
        )

        suggester = AITaskSuggester(user)
        suggestions = suggester.suggest_tasks(project.id)

        titles = [s["title"] for s in suggestions]
        assert "database migration fix" not in titles

    def test_fallback_suggestions_when_no_matching_tasks(self, user, project):
        suggester = AITaskSuggester(user)
        suggestions = suggester.suggest_tasks(project.id)

        assert len(suggestions) == 2
        assert any("documentation" in s["title"].lower() for s in suggestions)
        assert any("review" in s["title"].lower() for s in suggestions)

    def test_only_first_keyword_is_actually_used_for_matching(
        self, user, project, other_project_same_org
    ):
        """
        Documents real behavior: despite the 'reason' field claiming
        'Based on keywords: x, y, z', matching only ever uses keywords[0].
        A task matching only a later keyword is NOT found.
        """
        Comment.objects.create(
            project=project, user=user,
            content="urgent bug report followed by database work",
        )
        non_matching_task = Task.objects.create(
            project=other_project_same_org,
            title="Fix database connection pool",
            priority="high",
        )

        suggester = AITaskSuggester(user)
        suggestions = suggester.suggest_tasks(project.id)

        titles = [s["title"] for s in suggestions]
        assert non_matching_task.title not in titles