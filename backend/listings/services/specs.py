"""Spec validation against templates (FSD §5.2, doc 05).

``validate_specs`` checks provided fields by kind/options and (optionally, at
publish) that all required fields are present. ``missing_required_specs`` is the
publish-gate helper. Listings stamp ``spec_template_version`` from the matched
template.
"""

from __future__ import annotations

from numbers import Real

from listings.errors import InvalidAssetType, SpecInvalid
from listings.models import SpecTemplate


def get_template(
    asset_class: str, asset_type: str, version: int | None = None
) -> SpecTemplate | None:
    qs = SpecTemplate.objects.filter(asset_class=asset_class, asset_type=asset_type)
    if version is not None:
        qs = qs.filter(version=version)
    return qs.order_by("-version").first()


def _is_number(value) -> bool:
    # bool is a Real in Python, but never a valid spec number.
    return isinstance(value, Real) and not isinstance(value, bool)


def _field_error(fdef: dict, value) -> str | None:
    kind = fdef["kind"]
    if kind == "number":
        return None if _is_number(value) else "Must be a number."
    if kind == "text":
        return None if isinstance(value, str) else "Must be text."
    if kind == "boolean":
        return None if isinstance(value, bool) else "Must be true or false."
    if kind == "select":
        return None if value in fdef.get("options", []) else "Not a valid option."
    if kind == "multi":
        if not isinstance(value, list):
            return "Must be a list of options."
        invalid = [v for v in value if v not in fdef.get("options", [])]
        return f"Invalid options: {invalid}." if invalid else None
    return None


def _is_present(value) -> bool:
    return value not in (None, "", [])


def validate_specs(*, asset_class: str, asset_type: str, specs: dict, require: bool = False):
    """Validate ``specs`` against the template. Returns ``(clean, version)``.

    Always checks field kinds/options for provided fields. When ``require`` is
    True (publish), also enforces that required fields are present. Unknown
    fields (not in the template) are dropped.
    """
    template = get_template(asset_class, asset_type)
    if template is None:
        raise InvalidAssetType()

    specs = specs or {}
    errors: dict[str, str] = {}
    clean: dict = {}
    for name, fdef in template.fields.items():
        present = name in specs and _is_present(specs[name])
        if not present:
            if require and fdef.get("required"):
                errors[name] = "This field is required."
            continue
        err = _field_error(fdef, specs[name])
        if err:
            errors[name] = err
        else:
            clean[name] = specs[name]

    if errors:
        raise SpecInvalid(fields=errors)
    return clean, template.version


def missing_required_specs(template: SpecTemplate, specs: dict) -> list[str]:
    """Required template fields absent from ``specs`` (publish gate)."""
    specs = specs or {}
    return [
        name
        for name, fdef in template.fields.items()
        if fdef.get("required") and not (name in specs and _is_present(specs[name]))
    ]
