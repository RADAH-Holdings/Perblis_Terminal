"""Request/response shapes for the listings API."""

from __future__ import annotations

from rest_framework import serializers

from listings.models import SpecTemplate


class SpecTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecTemplate
        fields = ["asset_class", "asset_type", "version", "fields"]
        read_only_fields = fields
