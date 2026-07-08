from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from core.pagination import StandardPagination, CursorPagination


class PaginationTestCase(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_standard_pagination_default_page_size(self):
        paginator = StandardPagination()
        request = Request(self.factory.get("/api/test/"))
        page_size = paginator.get_page_size(request)
        self.assertEqual(page_size, 20)

    def test_standard_pagination_custom_page_size(self):
        paginator = StandardPagination()
        request = Request(self.factory.get("/api/test/", {"page_size": 50}))

        page_size = paginator.get_page_size(request)

        self.assertLessEqual(page_size, 50)
        self.assertGreater(page_size, 0)

    def test_cursor_pagination_ordering(self):
        paginator = CursorPagination()
        self.assertEqual(paginator.ordering, "-created_at")