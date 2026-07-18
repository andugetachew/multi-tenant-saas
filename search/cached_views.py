import json
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.cache_config import cache_service
from .elastic import AdvancedSearch
import hashlib
from django.core.serializers.json import DjangoJSONEncoder

class CachedGlobalSearchView(APIView):
    """FAANG-level: Search result caching with query normalization"""

    permission_classes = [IsAuthenticated]

    # Common words that shouldn't be cached with high TTL
    STOP_WORDS = {"the", "a", "an", "and", "or", "but", "for", "nor", "so", "yet"}

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response({"error": "Search query required"}, status=400)

        # Normalize query for better cache hits
        normalized_query = self.normalize_query(query)

        # Different TTL based on query specificity
        ttl = self.get_cache_ttl(query)

        # Generate cache key
        org_id = request.user.organization_id
        cache_key = f"search:org:{org_id}:{normalized_query}"

        # Try cache
        cached = cache_service.redis_client.get(cache_key)
        if cached:
            return Response(json.loads(cached))

        # Execute search (expensive)
        search = AdvancedSearch(request.user)
        results = search.search_all(query)

        # Cache with appropriate TTL
        cache_service.redis_client.setex(cache_key, ttl, json.dumps(results, cls=DjangoJSONEncoder))


        return Response(results)

    def normalize_query(self, query):
        """Normalize query for better cache hits"""
        # Lowercase
        query = query.lower()
        # Remove stop words
        words = [w for w in query.split() if w not in self.STOP_WORDS]
        # Sort words for consistent cache key
        words.sort()
        return " ".join(words)

    def get_cache_ttl(self, query):
        """Intelligent TTL based on query characteristics"""
        word_count = len(query.split())

        if word_count > 5:
            return 30  # Complex queries: 30 seconds
        elif len(query) < 10:
            return 120  # Short queries: 2 minutes
        else:
            return 60  # Default: 1 minute
