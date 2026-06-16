"""Enumerations for the accounts app.

Kept separate from models so services, serializers, and migrations can import
the choices without pulling in the model layer.
"""

from __future__ import annotations

from django.db import models


class OtpPurpose(models.TextChoices):
    # Wave 1 only verifies phones at registration; the column carries a purpose
    # so the same table serves future flows (e.g. step-up auth) without reshape.
    PHONE_VERIFY = "phone_verify", "Phone verification"


class VerificationKind(models.TextChoices):
    IDENTITY = "identity", "Identity"
    BUSINESS = "business", "Business"


class VerificationState(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
