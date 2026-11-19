"""Method: meter-count population estimates.

P = Residential_Electricity_Meters x Persons_Per_Meter
P = Residential_Gas_Customers x Persons_Per_Gas_Customer

The numerators are physical meter counts (EIA-861 Bundled+Delivery
customers; EIA dnav gas consumers). The per-meter constants are
census-informed (household size, seasonal discounts, gas share).
"""

from popest.constants import (
    GAS_PERSONS_PER_CUSTOMER,
    PERSONS_PER_METER,
)
from popest.meters import (
    residential_electricity_meters,
    residential_gas_customers,
)


def estimate() -> dict:
    results = {}

    meters = residential_electricity_meters()
    if not meters.empty:
        total = float(meters["meters"].sum())
        for label, per in [("central", PERSONS_PER_METER.central),
                           ("low", PERSONS_PER_METER.low),
                           ("high", PERSONS_PER_METER.high)]:
            results[f"electricity_meters_{label}"] = total * per
        results["meters_count"] = total

    gas = residential_gas_customers()
    if gas:
        for label, per in [("central", GAS_PERSONS_PER_CUSTOMER.central),
                           ("low", GAS_PERSONS_PER_CUSTOMER.low),
                           ("high", GAS_PERSONS_PER_CUSTOMER.high)]:
            results[f"gas_meters_{label}"] = gas["customers"] * per
        results["gas_customers_count"] = gas["customers"]
        results["gas_year"] = gas["year"]

    return results
