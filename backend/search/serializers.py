"""Search request/response shapes (TSD §3.7 — the map response is a frozen contract).

The param serializer doubles as the drf-spectacular query-parameter source; the
response serializers exist to document every field of the frozen map contract
(the service already returns JSON-ready dicts — these guarantee the shape).
"""

from __future__ import annotations

from rest_framework import serializers

from listings.enums import AssetClass

from .services.filters import SearchFilters

_GROUP_BY = ("asset", "location")


class SearchParamsSerializer(serializers.Serializer):
    """Shared query params for ``search/map`` and ``search/list``."""

    bbox = serializers.CharField(
        required=False, help_text="Viewport as 'min_lng,min_lat,max_lng,max_lat'."
    )
    lat = serializers.FloatField(required=False, min_value=-90, max_value=90)
    lng = serializers.FloatField(required=False, min_value=-180, max_value=180)
    radius_km = serializers.FloatField(
        required=False, min_value=0.1, max_value=500, help_text="Radius around lat/lng in km."
    )
    asset_class = serializers.ChoiceField(choices=AssetClass.choices, required=False)
    q = serializers.CharField(
        required=False, max_length=200, help_text="Matches title + description."
    )
    price_min = serializers.IntegerField(
        required=False, min_value=0, help_text="Daily price, kobo."
    )
    price_max = serializers.IntegerField(
        required=False, min_value=0, help_text="Daily price, kobo."
    )
    spec_min = serializers.FloatField(required=False, help_text="★ headline spec for the class.")
    spec_max = serializers.FloatField(required=False)

    def validate(self, attrs):
        bbox_raw = attrs.get("bbox")
        has_radius = (
            attrs.get("lat") is not None
            and attrs.get("lng") is not None
            and attrs.get("radius_km") is not None
        )
        if bbox_raw:
            parts = bbox_raw.split(",")
            if len(parts) != 4:
                raise serializers.ValidationError(
                    {"bbox": "Expected 'min_lng,min_lat,max_lng,max_lat'."}
                )
            try:
                min_lng, min_lat, max_lng, max_lat = (float(p) for p in parts)
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"bbox": "All four values must be numbers."}
                ) from exc
            if min_lng >= max_lng or min_lat >= max_lat:
                raise serializers.ValidationError(
                    {"bbox": "min must be less than max on each axis."}
                )
            attrs["_bbox"] = (min_lng, min_lat, max_lng, max_lat)
        elif not has_radius:
            raise serializers.ValidationError("Provide bbox, or lat, lng and radius_km.")

        if (
            attrs.get("spec_min") is not None or attrs.get("spec_max") is not None
        ) and not attrs.get("asset_class"):
            raise serializers.ValidationError(
                {"asset_class": "Required when filtering by spec_min/spec_max."}
            )
        return attrs

    def viewport_kwargs(self) -> dict:
        data = self.validated_data
        if "_bbox" in data:
            return {"bbox": data["_bbox"]}
        return {"lat": data["lat"], "lng": data["lng"], "radius_km": data["radius_km"]}

    def to_filters(self) -> SearchFilters:
        data = self.validated_data
        return SearchFilters(
            asset_class=data.get("asset_class"),
            q=data.get("q"),
            price_min=data.get("price_min"),
            price_max=data.get("price_max"),
            spec_min=data.get("spec_min"),
            spec_max=data.get("spec_max"),
        )


class ListParamsSerializer(SearchParamsSerializer):
    group_by = serializers.ChoiceField(choices=_GROUP_BY, required=False, default="asset")


# --- Response shapes (documentation of the frozen contract) ------------------


class _YardListingSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    asset_class = serializers.CharField()
    price_from = serializers.IntegerField(help_text="Daily price, kobo.")
    price_from_display = serializers.CharField()
    photo = serializers.CharField(allow_blank=True)
    available = serializers.BooleanField(
        help_text="Stubbed True until Wave 4's availability engine."
    )


class _SupplierSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField(allow_blank=True)
    logo = serializers.CharField(allow_blank=True)
    badge = serializers.CharField(allow_null=True)


class MapYardSerializer(serializers.Serializer):
    yard_id = serializers.CharField()
    name = serializers.CharField()
    point = serializers.JSONField(help_text="GeoJSON Point.")
    supplier = _SupplierSummarySerializer()
    listing_count = serializers.IntegerField(help_text="All Live listings at the yard.")
    matching_count = serializers.IntegerField(help_text="0 for a dimmed zero-match yard.")
    class_mix = serializers.ListField(child=serializers.CharField())
    price_from = serializers.IntegerField()
    price_from_display = serializers.CharField()
    distance_km = serializers.FloatField(allow_null=True)
    listings = _YardListingSummarySerializer(many=True)


class MapSoloListingSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    asset_class = serializers.CharField()
    point = serializers.JSONField(help_text="GeoJSON Point.")
    price_from = serializers.IntegerField()
    price_from_display = serializers.CharField()
    distance_km = serializers.FloatField(allow_null=True)
    photo = serializers.CharField(allow_blank=True)
    badge = serializers.CharField(allow_null=True)


class MapResponseSerializer(serializers.Serializer):
    yards = MapYardSerializer(many=True)
    listings = MapSoloListingSerializer(many=True)
