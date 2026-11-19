"""Method: travel and library population estimates.

P = Enplanements / Enplanements_Per_Capita
P = Transit_Trips / Transit_Trips_Per_Capita
P = Library_Visits / Library_Visits_Per_Capita

All numerators are metered counts; the per-capita constants are
census-informed. Registered library borrowers are reported alongside.
"""

from popest.constants import (
    ENPLANEMENTS_PER_CAPITA,
    LIBRARY_VISITS_PER_CAPITA,
    TRANSIT_TRIPS_PER_CAPITA,
)
from popest.travel import enplanements, library_survey, transit_trips


def estimate() -> dict:
    results = {}

    faa = enplanements()
    if faa:
        for label, per in [("central", ENPLANEMENTS_PER_CAPITA.central),
                           ("low", ENPLANEMENTS_PER_CAPITA.high),
                           ("high", ENPLANEMENTS_PER_CAPITA.low)]:
            results[f"enplanements_{label}"] = faa["total"] / per
        results["enplanements_count"] = faa["total"]
        results["enplanements_year"] = faa["year"]

    ntd = transit_trips()
    if ntd:
        for label, per in [("central", TRANSIT_TRIPS_PER_CAPITA.central),
                           ("low", TRANSIT_TRIPS_PER_CAPITA.high),
                           ("high", TRANSIT_TRIPS_PER_CAPITA.low)]:
            results[f"transit_{label}"] = ntd["total"] / per
        results["transit_trips_count"] = ntd["total"]
        results["transit_year"] = ntd["year"]

    lib = library_survey()
    if lib:
        for label, per in [("central", LIBRARY_VISITS_PER_CAPITA.central),
                           ("low", LIBRARY_VISITS_PER_CAPITA.high),
                           ("high", LIBRARY_VISITS_PER_CAPITA.low)]:
            results[f"library_visits_{label}"] = lib["visits"] / per
        results["library_visits_count"] = lib["visits"]
        results["registered_borrowers_reported"] = lib[
            "registered_borrowers"]
        results["library_fiscal_year"] = lib["fiscal_year"]

    return results
