from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .elastic import AdvancedSearch


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response({"error": "Search query required"}, status=400)

        search = AdvancedSearch(request.user)
        results = search.search_all(query)

        return Response(
            {
                "query": query,
                "total_results": sum(len(v) for v in results.values()),
                "results": results,
            }
        )
