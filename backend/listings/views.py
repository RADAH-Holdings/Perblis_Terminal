"""Listings API views (thin; mutation lives in listings.services.*)."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from listings import serializers as s
from listings.services import specs as specs_service


class SpecTemplateView(GenericAPIView):
    """Public read of a spec template by class + type (latest version default)."""

    permission_classes = [AllowAny]
    serializer_class = s.SpecTemplateSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("class", str, required=True),
            OpenApiParameter("type", str, required=True),
            OpenApiParameter("version", int, required=False),
        ],
        responses={200: s.SpecTemplateSerializer},
    )
    def get(self, request):
        asset_class = request.query_params.get("class", "")
        asset_type = request.query_params.get("type", "")
        version = request.query_params.get("version")
        template = specs_service.get_template(
            asset_class, asset_type, int(version) if version else None
        )
        if template is None:
            return Response(
                {"error": {"code": "not_found", "message": "No such spec template."}}, status=404
            )
        return Response(self.get_serializer(template).data)
