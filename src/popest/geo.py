"""Geographic utilities: FIPS codes, county lists, crosswalks."""

STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
    "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
    "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
    "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
    "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
    "56": "WY", "72": "PR",
}

STATE_ABBREV_TO_FIPS = {v: k for k, v in STATE_FIPS.items()}

EXCLUDE_FIPS = {"72"}  # Puerto Rico


def all_state_fips() -> list[str]:
    return [f for f in STATE_FIPS if f not in EXCLUDE_FIPS]


def fips_to_state(fips: str) -> str:
    return STATE_FIPS.get(fips[:2], "??")


def is_valid_county_fips(fips: str) -> bool:
    if len(fips) != 5:
        return False
    state = fips[:2]
    county = fips[2:]
    if state in EXCLUDE_FIPS:
        return False
    if state not in STATE_FIPS:
        return False
    return county != "000"
