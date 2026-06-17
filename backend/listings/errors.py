"""Listings-specific domain errors (stable codes for the error envelope)."""

from __future__ import annotations

from rest_framework import status

from core.exceptions import TerminalError


class InvalidAssetType(TerminalError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_asset_type"
    default_detail = "Unknown asset class/type — no spec template exists."


class SpecInvalid(TerminalError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "spec_invalid"
    default_detail = "One or more spec fields are invalid."


class ListingNotEditable(TerminalError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "listing_not_editable"
    default_detail = "Archived or removed listings cannot be edited."
