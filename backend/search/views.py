"""Search API views (thin; aggregation lives in search.services.*)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from search import serializers as s
from search.services import search as search_service
from search.throttles import SearchRateThrottle


class SearchMapView(GenericAPIView):
    """Server-aggregated yards + solo listings for a viewport/radius (FSD §6).

    Public (guest browsing). All grouping, counting, distance and filtering is
    server-authoritative — clients only style and spatially cluster the result.
    """

    permission_classes = [AllowAny]
    throttle_classes = [SearchRateThrottle]
    serializer_class = s.SearchParamsSerializer

    @extend_schema(
        parameters=[s.SearchParamsSerializer],
        responses={200: s.MapResponseSerializer},
    )
    def get(self, request):
        params = s.SearchParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = search_service.map_search(filters=params.to_filters(), **params.viewport_kwargs())
        return Response(data)
