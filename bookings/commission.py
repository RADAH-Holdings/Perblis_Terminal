"""
Tiered commission rate engine for Terminal.

Commission rates are determined by:
  1. Asset class (resource_type on the listing)
  2. Duration type (daily / weekly / monthly)

Flat fee rule: any booking with gross_amount < ₦25,000 attracts a fixed
₦2,500 fee regardless of asset class or duration.

Rate table per FSD v1.0 Section 4.2:

| Asset Class              | Daily | Weekly | Monthly |
|--------------------------|-------|--------|---------|
| Heavy Equipment          |  12%  |  10%   |   8%    |
| Vehicles & Transport     |  11%  |   9%   |   7%    |
| Warehouses & Storage     |  10%  |   8%   |   6%    |
| Terminals & Container    |  10%  |   8%   |   6%    |
| Facilities & Staging     |  10%  |   8%   |   6%    |
"""

from decimal import Decimal

from listings.models import ResourceType

FLAT_FEE_THRESHOLD = Decimal('25000')
FLAT_FEE_AMOUNT = Decimal('2500')

COMMISSION_RATES: dict[str, dict[str, Decimal]] = {
    ResourceType.EQUIPMENT: {
        'daily': Decimal('0.12'),
        'weekly': Decimal('0.10'),
        'monthly': Decimal('0.08'),
    },
    ResourceType.VEHICLE: {
        'daily': Decimal('0.11'),
        'weekly': Decimal('0.09'),
        'monthly': Decimal('0.07'),
    },
    ResourceType.WAREHOUSE: {
        'daily': Decimal('0.10'),
        'weekly': Decimal('0.08'),
        'monthly': Decimal('0.06'),
    },
    ResourceType.TERMINAL: {
        'daily': Decimal('0.10'),
        'weekly': Decimal('0.08'),
        'monthly': Decimal('0.06'),
    },
    ResourceType.FACILITY: {
        'daily': Decimal('0.10'),
        'weekly': Decimal('0.08'),
        'monthly': Decimal('0.06'),
    },
}


def get_commission_rate(resource_type: str, duration_type: str) -> Decimal:
    """
    Return the percentage commission rate for a given asset class and duration.
    Falls back to 10% if the resource_type or duration_type is unrecognized.
    """
    rates = COMMISSION_RATES.get(resource_type)
    if rates is None:
        return Decimal('0.10')
    return rates.get(duration_type, Decimal('0.10'))


def calculate_commission(
    gross_amount: Decimal,
    resource_type: str,
    duration_type: str,
) -> tuple[Decimal, Decimal, str]:
    """
    Calculate commission based on the tiered rate structure.

    Returns:
        (commission_amount, rate_decimal, rate_label)

    rate_label is a human-readable string stored on the booking record,
    e.g. "12%", "10%", or "₦2,500 flat".
    """
    if gross_amount < FLAT_FEE_THRESHOLD:
        return (
            FLAT_FEE_AMOUNT,
            Decimal('0'),
            '₦2,500 flat',
        )

    rate = get_commission_rate(resource_type, duration_type)
    commission = (gross_amount * rate).quantize(Decimal('0.01'))
    rate_label = f"{int(rate * 100)}%"

    return commission, rate, rate_label
