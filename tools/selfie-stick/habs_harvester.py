#!/usr/bin/env python3
"""Harvest a small, reproducible HABS measured-drawing corpus from loc.gov.

This is an acquisition and normalization probe.  It deliberately stops before
interpreting drawing geometry or producing Valheim pieces/ZDOs.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import warnings
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
COLLECTION_SLUG = (
    "historic-american-buildings-landscapes-and-engineering-records"
)
COLLECTION_URL = f"https://www.loc.gov/collections/{COLLECTION_SLUG}/"
DEFAULT_SPEC = HERE / "habs-corpus.json"
DEFAULT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_USER_AGENT = (
    "Valheim-HABS-RnD/0.1 "
    "(https://www.loc.gov/collections/historic-american-buildings-"
    "landscapes-and-engineering-records/)"
)
SCHEMA_METADATA = "loc-habs-metadata/v1"
SCHEMA_BUILDING_MANIFEST = "loc-habs-building-manifest/v1"
SCHEMA_CORPUS_MANIFEST = "loc-habs-corpus-manifest/v1"
SCHEMA_SEARCH = "loc-habs-search/v1"
SCHEMA_ACQUISITION_PLAN = "loc-habs-acquisition-plan/v1"
DEFAULT_TOTAL_BUDGET = 2_147_483_648
DEFAULT_BUILDING_BUDGET = 805_306_368
DEFAULT_SHEET_BUDGET = 536_870_912


class AcquisitionBudgetError(RuntimeError):
    """Raised when a planned or streaming acquisition exceeds a hard limit."""

STATE_NAMES = {
    "AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas",
    "CA": "california", "CO": "colorado", "CT": "connecticut",
    "DE": "delaware", "DC": "district of columbia", "FL": "florida",
    "GA": "georgia", "HI": "hawaii", "ID": "idaho", "IL": "illinois",
    "IN": "indiana", "IA": "iowa", "KS": "kansas", "KY": "kentucky",
    "LA": "louisiana", "ME": "maine", "MD": "maryland",
    "MA": "massachusetts", "MI": "michigan", "MN": "minnesota",
    "MS": "mississippi", "MO": "missouri", "MT": "montana",
    "NE": "nebraska", "NV": "nevada", "NH": "new hampshire",
    "NJ": "new jersey", "NM": "new mexico", "NY": "new york",
    "NC": "north carolina", "ND": "north dakota", "OH": "ohio",
    "OK": "oklahoma", "OR": "oregon", "PA": "pennsylvania",
    "RI": "rhode island", "SC": "south carolina", "SD": "south dakota",
    "TN": "tennessee", "TX": "texas", "UT": "utah", "VT": "vermont",
    "VA": "virginia", "WA": "washington", "WV": "west virginia",
    "WI": "wisconsin", "WY": "wyoming",
}

BUILDING_TYPE_TERMS = {
    "barn": ("barn", "barns"),
    "cabin": ("cabin", "cabins", "log cabin", "log cabins"),
    "farmhouse": ("farmhouse", "farmhouses", "farm house", "farm houses"),
    "house": ("house", "houses", "dwelling", "dwellings", "residence"),
    "schoolhouse": ("schoolhouse", "school house", "school"),
    "shed": ("shed", "sheds"),
    "stable": ("stable", "stables"),
}

ROLE_PATTERNS = {
    "plan": re.compile(r"\b(?:floor\s+|site\s+|roof\s+)?plans?\b", re.I),
    "elevation": re.compile(r"\belevations?\b", re.I),
    # `sectionz` is an observed LOC caption typo (co0395), preserved in the title.
    "section": re.compile(r"\b(?:cross[ -])?(?:sections?|sectionz)\b", re.I),
    "detail": re.compile(r"\bdetails?\b", re.I),
    "axonometric": re.compile(r"\b(?:axonometric|isometric)\b", re.I),
    "perspective": re.compile(r"\bperspective\b", re.I),
}

TRANSIENT_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="%(prog)s 0.1")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser(
        "search", help="query LOC and return records that expose measured drawings"
    )
    add_client_args(search)
    add_filter_args(search)
    search.add_argument("--limit", type=positive_int, default=20)
    search.add_argument(
        "--scan-limit", type=positive_int, default=1000,
        help="maximum raw API results to inspect before local filtering",
    )
    search.add_argument("--output", type=Path, help="write JSON as well as stdout")

    plan = subparsers.add_parser(
        "plan", help="resolve exact drawing URLs and HTTP sizes without downloading them"
    )
    add_client_args(plan)
    add_filter_args(plan)
    plan.add_argument("--spec", type=Path, help="frozen selection JSON")
    plan.add_argument(
        "--id", action="append", default=[], metavar="LOC_ID",
        help="plan an exact LOC control number; repeatable",
    )
    plan.add_argument("--count", type=positive_int, default=20)
    plan.add_argument("--scan-limit", type=positive_int, default=1000)
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument(
        "--format", choices=("master-tiff", "reference-jpeg"),
        default="master-tiff",
    )
    plan.add_argument("--max-sheets-per-building", type=positive_int, default=6)
    add_budget_args(plan)

    harvest = subparsers.add_parser(
        "harvest", help="resolve item resources and build the normalized corpus"
    )
    add_client_args(harvest)
    add_filter_args(harvest)
    harvest.add_argument(
        "--spec", type=Path,
        help=f"frozen selection JSON (defaults to {DEFAULT_SPEC.name} without filters)",
    )
    harvest.add_argument(
        "--plan", type=Path,
        help="download only the exact URLs and byte sizes in a frozen acquisition plan",
    )
    harvest.add_argument(
        "--id", action="append", default=[], metavar="LOC_ID",
        help="harvest an exact LOC control number; repeatable",
    )
    harvest.add_argument("--count", type=positive_int, default=20)
    harvest.add_argument("--scan-limit", type=positive_int, default=1000)
    harvest.add_argument("--output", type=Path, default=DEFAULT_CORPUS)
    harvest.add_argument(
        "--format", choices=("master-tiff", "reference-jpeg"),
        default="master-tiff",
        help="download masters for readable dimensions, or smaller 1024px references",
    )
    harvest.add_argument(
        "--max-sheets-per-building", type=nonnegative_int, default=0,
        help="0 downloads every resolved drawing sheet",
    )
    harvest.add_argument(
        "--no-download", action="store_true",
        help="write resolved metadata/manifests without fetching drawing bytes",
    )

    verify = subparsers.add_parser(
        "verify", help="verify corpus structure, hashes, dimensions, and counts"
    )
    verify.add_argument("--output", type=Path, default=DEFAULT_CORPUS)
    verify.add_argument("--expected-buildings", type=nonnegative_int, default=0)
    return parser.parse_args(argv)


def add_client_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeout", type=positive_float, default=90.0)
    parser.add_argument("--retries", type=nonnegative_int, default=4)
    parser.add_argument(
        "--request-delay", type=nonnegative_float, default=0.20,
        help="minimum delay between LOC requests",
    )
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--program", choices=("HABS", "HAER", "HALS", "ANY"), default="HABS",
        help="survey program; this proof corpus defaults to architectural HABS records",
    )
    parser.add_argument(
        "--building-type",
        help="local title/subject type filter, also supplied to LOC keyword search",
    )
    parser.add_argument(
        "--state", help="state name or postal abbreviation; sent as a location facet",
    )
    parser.add_argument(
        "--location", help="additional LOC location facet, such as a county or city",
    )
    parser.add_argument("--date-from", type=year_int)
    parser.add_argument("--date-to", type=year_int)
    parser.add_argument("--keyword", help="free-text LOC metadata/full-text query")


def add_budget_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-total-bytes", type=positive_int, default=DEFAULT_TOTAL_BUDGET)
    parser.add_argument(
        "--max-building-bytes", type=positive_int, default=DEFAULT_BUILDING_BUDGET
    )
    parser.add_argument("--max-sheet-bytes", type=positive_int, default=DEFAULT_SHEET_BUDGET)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def year_int(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 9999:
        raise argparse.ArgumentTypeError("must be a four-digit year from 0001 to 9999")
    return parsed


class LocClient:
    def __init__(
        self, user_agent: str, timeout: float, retries: int, request_delay: float
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.retries = retries
        self.request_delay = request_delay
        self.last_request = 0.0

    def _throttle(self) -> None:
        remaining = self.request_delay - (time.monotonic() - self.last_request)
        if remaining > 0:
            time.sleep(remaining)

    def open(
        self, url: str, *, method: str = "GET", headers: dict[str, str] | None = None
    ):
        request_headers = {
            "Accept": "application/json" if "fo=json" in url else "*/*",
            "User-Agent": self.user_agent,
        }
        if headers:
            request_headers.update(headers)

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            self._throttle()
            request = urllib.request.Request(
                url, headers=request_headers, method=method
            )
            try:
                response = urllib.request.urlopen(request, timeout=self.timeout)
                self.last_request = time.monotonic()
                return response
            except urllib.error.HTTPError as error:
                self.last_request = time.monotonic()
                if error.code == 304:
                    return error
                last_error = error
                if error.code not in TRANSIENT_HTTP_CODES or attempt >= self.retries:
                    raise
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(8.0, 0.5 * 2**attempt)
                time.sleep(delay)
            except (TimeoutError, urllib.error.URLError) as error:
                self.last_request = time.monotonic()
                last_error = error
                if attempt >= self.retries:
                    raise
                time.sleep(min(8.0, 0.5 * 2**attempt))
        raise RuntimeError(f"request failed: {last_error}")

    def get_json(self, url: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with self.open(url) as response:
                    payload = response.read()
                value = json.loads(payload)
                if not isinstance(value, dict):
                    raise ValueError(f"expected JSON object from {url}")
                return value
            except (
                json.JSONDecodeError,
                UnicodeDecodeError,
                http.client.IncompleteRead,
                ConnectionError,
                TimeoutError,
                urllib.error.URLError,
            ) as error:
                last_error = error
                if attempt >= self.retries:
                    raise RuntimeError(
                        f"LOC returned malformed JSON after {attempt + 1} attempts: {url}: {error}"
                    ) from error
                time.sleep(min(8.0, 0.5 * 2**attempt))
        raise RuntimeError(f"JSON request failed: {last_error}")

    def head(self, url: str) -> dict[str, str]:
        with self.open(url, method="HEAD") as response:
            return {key.lower(): value for key, value in response.headers.items()}


def client_from_args(args: argparse.Namespace) -> LocClient:
    return LocClient(
        user_agent=args.user_agent,
        timeout=args.timeout,
        retries=args.retries,
        request_delay=args.request_delay,
    )


def normalize_state(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    return STATE_NAMES.get(stripped.upper(), stripped.casefold())


def validate_date_range(args: argparse.Namespace) -> None:
    if args.date_from and args.date_to and args.date_from > args.date_to:
        raise ValueError("--date-from must not be later than --date-to")


def has_live_filters(args: argparse.Namespace) -> bool:
    return any(
        getattr(args, name, None)
        for name in ("building_type", "state", "location", "date_from", "date_to", "keyword")
    )


def filters_from_args(args: argparse.Namespace) -> dict[str, Any]:
    validate_date_range(args)
    return {
        "program": args.program,
        "building_type": args.building_type,
        "state": normalize_state(args.state),
        "location": args.location.strip().casefold() if args.location else None,
        "date_from": args.date_from,
        "date_to": args.date_to,
        "date_basis": "building_structure_dates_in_item_notes",
        "keyword": args.keyword,
    }


def search_url(filters: dict[str, Any], page: int, page_size: int) -> str:
    query_terms = [
        value.strip()
        for value in (filters.get("building_type"), filters.get("keyword"))
        if value and value.strip()
    ]
    facets = []
    if filters.get("state"):
        facets.append(f"location:{filters['state']}")
    if filters.get("location"):
        facets.append(f"location:{filters['location']}")

    params: dict[str, str | int] = {
        "fo": "json",
        "at": "results,pagination",
        "c": page_size,
        "sp": page,
        "sb": "title_s",
    }
    if query_terms:
        params["q"] = " ".join(query_terms)
    if facets:
        params["fa"] = "|".join(facets)
    return COLLECTION_URL + "?" + urllib.parse.urlencode(params)


def flatten_labels(value: Any) -> list[str]:
    labels: list[str] = []
    if value is None:
        return labels
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        labels.extend(str(key) for key in value)
        return labels
    if isinstance(value, list):
        for element in value:
            labels.extend(flatten_labels(element))
    return labels


def item_id(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        raise ValueError(f"cannot derive LOC id from {value!r}")
    result = parts[-1]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", result):
        raise ValueError(f"unsafe LOC id {result!r}")
    return result


def survey_program(caption: str) -> str | None:
    match = re.search(r"\bSurvey\s+(HABS|HAER|HALS)\b", caption, re.I)
    return match.group(1).upper() if match else None


def drawing_resources(resources: Any, program: str) -> list[dict[str, Any]]:
    if not isinstance(resources, list):
        return []
    matches = []
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        caption = str(resource.get("caption") or "")
        found_program = survey_program(caption)
        if not caption.casefold().startswith("drawings from survey"):
            continue
        if program != "ANY" and found_program != program:
            continue
        matches.append(resource)
    return matches


def matches_building_type(result: dict[str, Any], building_type: str | None) -> bool:
    if not building_type:
        return True
    normalized = building_type.strip().casefold()
    terms = BUILDING_TYPE_TERMS.get(normalized, (normalized,))
    haystack = " ".join(
        [str(result.get("title") or ""), *flatten_labels(result.get("subject")),
         *flatten_labels(result.get("subjects"))]
    ).casefold()
    return any(re.search(rf"\b{re.escape(term)}\b", haystack) for term in terms)


def search_candidates(
    client: LocClient,
    filters: dict[str, Any],
    *,
    limit: int,
    scan_limit: int,
) -> tuple[list[dict[str, Any]], list[str], dict[str, int | None]]:
    page_size = min(150, max(25, min(scan_limit, limit * 5)))
    page = 1
    scanned = 0
    reported_counts: dict[str, int | None] = {"items": None, "pages": None}
    candidates: dict[str, dict[str, Any]] = {}
    query_urls: list[str] = []

    while scanned < scan_limit and len(candidates) < limit:
        url = search_url(filters, page, page_size)
        query_urls.append(url)
        payload = client.get_json(url)
        results = payload.get("results") or []
        if reported_counts["items"] is None:
            pagination = payload.get("pagination") or {}
            raw_items = pagination.get("of")
            raw_pages = pagination.get("total")
            reported_counts = {
                "items": int(raw_items) if isinstance(raw_items, (int, float)) else None,
                "pages": int(raw_pages) if isinstance(raw_pages, (int, float)) else None,
            }
        if not results:
            break

        for result in results:
            scanned += 1
            if scanned > scan_limit or not isinstance(result, dict):
                break
            resources = drawing_resources(result.get("resources"), filters["program"])
            if not resources or not matches_building_type(result, filters.get("building_type")):
                continue
            loc_id = item_id(str(result.get("id") or result.get("url") or ""))
            building_dates: list[dict[str, Any]] = []
            if filters.get("date_from") or filters.get("date_to"):
                detail = client.get_json(detail_url(loc_id))
                detail_item = detail.get("item")
                if not isinstance(detail_item, dict):
                    continue
                building_dates = extract_structure_dates(detail_item)
                start = int(filters.get("date_from") or 1)
                end = int(filters.get("date_to") or 9999)
                if not any(start <= date["year"] <= end for date in building_dates):
                    continue
            drawing_count = sum(
                int(resource.get("files") or 0)
                for resource in resources
                if isinstance(resource.get("files"), (int, float))
            )
            candidates[loc_id] = {
                "loc_id": loc_id,
                "item_url": https_url(str(result.get("id") or result.get("url"))),
                "title": result.get("title"),
                "location": sorted(set(flatten_labels(result.get("location"))), key=str.casefold),
                "subjects": sorted(set(flatten_labels(result.get("subject"))), key=str.casefold),
                "building_structure_dates": building_dates,
                "drawing_sheet_count": drawing_count,
                "drawing_resources": [
                    {
                        "caption": resource.get("caption"),
                        "files": resource.get("files"),
                        "url": https_url(resource.get("url")),
                    }
                    for resource in resources
                ],
            }
        pagination = payload.get("pagination") or {}
        if not pagination.get("next") or len(results) < page_size:
            break
        page += 1

    ordered = sorted(
        candidates.values(),
        key=lambda candidate: ((candidate.get("title") or "").casefold(), candidate["loc_id"]),
    )[:limit]
    return ordered, query_urls, reported_counts


def https_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if value.startswith("http://"):
        return "https://" + value[len("http://"):]
    return value


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def write_json_if_changed(path: Path, value: Any) -> bool:
    payload = canonical_json(value)
    if path.exists() and path.read_bytes() == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)
    return True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_loc_id(value: str) -> str:
    value = value.strip()
    if value.startswith("http://") or value.startswith("https://"):
        value = item_id(value)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValueError(f"unsafe LOC id {value!r}")
    return value


def load_selection(args: argparse.Namespace, client: LocClient) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if args.id:
        buildings = [
            {"loc_id": clean_loc_id(loc_id), "building_type": args.building_type}
            for loc_id in args.id
        ]
        return buildings, {"kind": "explicit-ids", "ids": [b["loc_id"] for b in buildings]}

    if args.spec or not has_live_filters(args):
        spec_path = (args.spec or DEFAULT_SPEC).resolve()
        spec = load_json(spec_path)
        buildings = spec.get("buildings")
        if not isinstance(buildings, list) or not buildings:
            raise ValueError(f"selection spec has no buildings: {spec_path}")
        normalized = []
        for building in buildings:
            if not isinstance(building, dict) or not building.get("loc_id"):
                raise ValueError(f"invalid building entry in {spec_path}: {building!r}")
            entry = dict(building)
            entry["loc_id"] = clean_loc_id(str(entry["loc_id"]))
            normalized.append(entry)
        try:
            displayed_path = spec_path.relative_to(HERE).as_posix()
        except ValueError:
            displayed_path = str(spec_path)
        return normalized, {
            "kind": "frozen-spec",
            "path": displayed_path,
            "sha256": sha256_file(spec_path),
            "schema": spec.get("schema"),
            "description": spec.get("description"),
        }

    filters = filters_from_args(args)
    candidates, urls, reported_counts = search_candidates(
        client, filters, limit=args.count, scan_limit=args.scan_limit
    )
    if len(candidates) < args.count:
        raise RuntimeError(
            f"query produced {len(candidates)} drawing records, fewer than --count {args.count}"
        )
    buildings = [
        {
            "loc_id": candidate["loc_id"],
            "building_type": args.building_type,
            "selection_reason": "deterministic live LOC query result",
        }
        for candidate in candidates
    ]
    return buildings, {
        "kind": "live-query",
        "filters": filters,
        "query_urls": urls,
        "reported_counts": reported_counts,
    }


def detail_url(loc_id: str) -> str:
    params = urllib.parse.urlencode({"fo": "json", "at": "item,resources"})
    return f"https://www.loc.gov/item/{loc_id}/?{params}"


def extract_survey_numbers(item: dict[str, Any], resources: list[dict[str, Any]]) -> list[str]:
    text = "\n".join(
        [*flatten_labels(item.get("notes")),
         *(str(resource.get("caption") or "") for resource in resources)]
    )
    values = re.findall(r"\b(?:HABS|HAER|HALS)\s+[A-Z0-9.-]+(?:-[A-Z0-9.-]+)*", text, re.I)
    return sorted({re.sub(r"\s+", " ", value).strip() for value in values}, key=str.casefold)


def extract_structure_dates(item: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for note in flatten_labels(item.get("notes")):
        match = re.search(
            r"Building/structure dates?:\s*(?P<year>\d{4})(?:\s+(?P<label>.*?))?\s*$",
            note,
            re.I,
        )
        if match:
            results.append(
                {"year": int(match.group("year")), "label": (match.group("label") or "").strip() or None,
                 "source": note}
            )
    return results


def find_state(location: list[str]) -> str | None:
    normalized = {value.casefold() for value in location}
    for state in STATE_NAMES.values():
        if state in normalized:
            return state
    return None


def normalize_metadata(
    loc_id: str,
    item: dict[str, Any],
    resources: list[dict[str, Any]],
    selection: dict[str, Any],
) -> dict[str, Any]:
    locations = sorted(set(flatten_labels(item.get("location"))), key=str.casefold)
    subjects = sorted(
        set(flatten_labels(item.get("subject")) + flatten_labels(item.get("subjects"))),
        key=str.casefold,
    )
    rights_values = flatten_labels(item.get("rights"))
    rights_information = item.get("rights_information")
    rights_advisory = item.get("rights_advisory")
    rights_text = "\n".join(
        [*rights_values, str(rights_information or ""), str(rights_advisory or "")]
    )
    rights_urls = sorted(set(re.findall(r"https?://[^\s<>\"]+", rights_text)))
    item_url = f"https://www.loc.gov/item/{loc_id}/"

    return {
        "schema": SCHEMA_METADATA,
        "building_id": loc_id,
        "title": item.get("title"),
        "description": item.get("description"),
        "building_type": selection.get("building_type"),
        "selection_reason": selection.get("selection_reason"),
        "identifiers": {
            "loc_control_number": item.get("control_number") or loc_id,
            "loc_item_id": https_url(item.get("id")) or item_url,
            "loc_item_url": item_url,
            "loc_api_url": detail_url(loc_id),
            "call_number": item.get("call_number"),
            "shelf_id": item.get("shelf_id"),
            "survey_numbers": extract_survey_numbers(item, resources),
            "alternate_urls": sorted(
                {url for url in (https_url(value) for value in flatten_labels(item.get("aka"))) if url}
            ),
        },
        "location": {"terms": locations, "state": find_state(locations), "place": item.get("place")},
        "subjects": subjects,
        "contributors": item.get("contributor_names") or flatten_labels(item.get("contributors")),
        "dates": {
            "api_date": item.get("date"),
            "created_published": item.get("created_published"),
            "created_published_date": item.get("created_published_date"),
            "building_structure_dates": extract_structure_dates(item),
            "source_created": item.get("source_created"),
            "source_modified": item.get("source_modified"),
            "record_created": item.get("created"),
            "record_modified": item.get("modified"),
        },
        "media": {
            "medium": item.get("medium"),
            "medium_brief": item.get("medium_brief"),
            "online_format": item.get("online_format"),
            "original_format": item.get("original_format"),
        },
        "notes": item.get("notes"),
        "rights": {
            "statements": rights_values,
            "rights_information": rights_information,
            "rights_advisory": rights_advisory,
            "source_urls": rights_urls,
        },
        "repository": item.get("repository"),
        "source_collection": item.get("source_collection"),
        "loc_source_metadata": item,
    }


def normalize_file_groups(value: Any) -> list[list[dict[str, Any]]]:
    if not isinstance(value, list):
        return []
    if value and all(isinstance(element, dict) for element in value):
        return [value]
    groups = []
    for element in value:
        if isinstance(element, list):
            groups.append([variant for variant in element if isinstance(variant, dict)])
        elif isinstance(element, dict):
            groups.append([element])
    return [group for group in groups if group]


def classify_title(title: str, override: Any = None) -> tuple[list[str], str]:
    if isinstance(override, str):
        roles = [override.casefold()]
    elif isinstance(override, list):
        roles = [str(value).casefold() for value in override if value]
    else:
        matches = []
        for role, pattern in ROLE_PATTERNS.items():
            found = pattern.search(title)
            if found:
                matches.append((found.start(), role))
        roles = [role for _, role in sorted(matches)]
    roles = list(dict.fromkeys(roles))
    return roles, (roles[0] if roles else "drawing")


def normalized_variants(group: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variants = []
    for variant in group:
        normalized = dict(variant)
        if "url" in normalized:
            normalized["url"] = https_url(normalized["url"])
        if "aka" in normalized:
            normalized["aka"] = https_url(normalized["aka"])
        variants.append(normalized)
    return variants


def resolve_sheets(
    resources: list[dict[str, Any]],
    program: str,
    selection: dict[str, Any],
) -> list[dict[str, Any]]:
    sheets = []
    global_index = 0
    overrides = selection.get("sheet_roles") or {}
    for resource_index, resource in enumerate(resources):
        caption = str(resource.get("caption") or "")
        found_program = survey_program(caption)
        if resource not in drawing_resources([resource], program):
            continue
        for resource_sheet_index, group in enumerate(normalize_file_groups(resource.get("files")), start=1):
            global_index += 1
            caption_variant = next(
                (variant for variant in group if variant.get("use") == "caption"), None
            )
            title = str(
                (caption_variant or {}).get("title")
                or f"{caption.strip()} sheet {resource_sheet_index}"
            )
            roles, primary_role = classify_title(
                title, overrides.get(str(global_index)) or overrides.get(global_index)
            )
            sheets.append(
                {
                    "sheet_index": global_index,
                    "resource_index": resource_index,
                    "resource_sheet_index": resource_sheet_index,
                    "survey_program": found_program,
                    "resource_caption": caption or None,
                    "resource_url": https_url(resource.get("url")),
                    "resource_image": https_url(resource.get("image")),
                    "title": title,
                    "roles": roles,
                    "primary_role": primary_role,
                    "loc_resource_id": https_url((caption_variant or {}).get("aka")),
                    "variants": normalized_variants(group),
                }
            )
    return sheets


def select_variant(sheet: dict[str, Any], download_format: str) -> dict[str, Any]:
    candidates = [
        variant for variant in sheet["variants"]
        if isinstance(variant.get("url"), str)
        and variant["url"].startswith("https://")
        and variant.get("use") != "caption"
    ]
    if download_format == "master-tiff":
        preferred = [
            variant for variant in candidates
            if str(variant.get("mimetype") or "").casefold() in ("image/tiff", "image/tif")
            or str(variant.get("url")).casefold().endswith((".tif", ".tiff"))
        ]
        if preferred:
            return max(preferred, key=lambda value: int(value.get("size") or 0))
    else:
        preferred = [
            variant for variant in candidates
            if str(variant.get("mimetype") or "").casefold() in ("image/jpeg", "image/jpg")
            or str(variant.get("url")).casefold().endswith((".jpg", ".jpeg"))
        ]
        if preferred:
            return max(
                preferred,
                key=lambda value: (
                    int(value.get("width") or 0) * int(value.get("height") or 0),
                    int(value.get("size") or 0),
                ),
            )
    if not candidates:
        raise RuntimeError(f"no downloadable image variant for {sheet['title']}")
    return max(candidates, key=lambda value: int(value.get("size") or 0))


def extension_for_variant(variant: dict[str, Any]) -> str:
    parsed = urllib.parse.urlparse(str(variant["url"]))
    suffix = Path(parsed.path).suffix.casefold()
    if suffix in (".tif", ".tiff", ".jpg", ".jpeg", ".png", ".jp2"):
        return ".tif" if suffix == ".tiff" else suffix
    guessed = mimetypes.guess_extension(str(variant.get("mimetype") or ""))
    return guessed or ".bin"


def select_sheets(sheets: list[dict[str, Any]], maximum: int) -> list[dict[str, Any]]:
    if maximum == 0 or len(sheets) <= maximum:
        return sheets
    selected_indexes = []
    for desired_role in ("plan", "elevation", "section"):
        match = next(
            (sheet for sheet in sheets if desired_role in sheet["roles"] and sheet["sheet_index"] not in selected_indexes),
            None,
        )
        if match:
            selected_indexes.append(match["sheet_index"])
    for sheet in sheets:
        if len(selected_indexes) >= maximum:
            break
        if sheet["sheet_index"] not in selected_indexes:
            selected_indexes.append(sheet["sheet_index"])
    selected = [sheet for sheet in sheets if sheet["sheet_index"] in selected_indexes[:maximum]]
    return sorted(selected, key=lambda sheet: sheet["sheet_index"])


def required_http_bytes(headers: dict[str, str], source_url: str) -> int:
    value = headers.get("content-length")
    if value is None or not value.strip().isdigit() or int(value) <= 0:
        raise AcquisitionBudgetError(
            f"missing or invalid HTTP Content-Length for {source_url}"
        )
    return int(value)


def check_planned_budget(
    *, loc_id: str, sheet_bytes: int, building_bytes: int, total_bytes: int,
    sheet_limit: int, building_limit: int, total_limit: int,
) -> None:
    if sheet_bytes > sheet_limit:
        raise AcquisitionBudgetError(
            f"{loc_id}: sheet requires {sheet_bytes} bytes, limit is {sheet_limit}"
        )
    if building_bytes > building_limit:
        raise AcquisitionBudgetError(
            f"{loc_id}: building requires {building_bytes} bytes, limit is {building_limit}"
        )
    if total_bytes > total_limit:
        raise AcquisitionBudgetError(
            f"selection requires {total_bytes} bytes, limit is {total_limit}"
        )


def budget_tracker(plan: dict[str, Any]) -> dict[str, int]:
    limits = plan.get("budgets") or {}
    return {
        "sheet_limit": int(limits["per_sheet_bytes"]),
        "building_limit": int(limits["per_building_bytes"]),
        "total_limit": int(limits["total_bytes"]),
        "building_bytes": 0,
        "total_bytes": 0,
    }


def image_properties(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image
    except ImportError:
        return {"width": None, "height": None, "format": None, "mode": None}
    prior_limit = Image.MAX_IMAGE_PIXELS
    try:
        # HABS master sheets legitimately exceed Pillow's web-image safety threshold.
        # We inspect headers only and never decode their pixel arrays here.
        Image.MAX_IMAGE_PIXELS = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                return {
                    "width": int(image.width),
                    "height": int(image.height),
                    "format": image.format,
                    "mode": image.mode,
                }
    finally:
        Image.MAX_IMAGE_PIXELS = prior_limit


def prior_downloads(manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not manifest:
        return {}
    result = {}
    for sheet in manifest.get("drawings") or []:
        download = sheet.get("download") if isinstance(sheet, dict) else None
        if isinstance(download, dict) and download.get("source_url"):
            result[str(download["source_url"])] = download
    return result


def download_file(
    client: LocClient,
    source_url: str,
    destination: Path,
    api_size: int | None,
    prior: dict[str, Any] | None,
    *,
    planned_bytes: int | None = None,
    budget: dict[str, int] | None = None,
) -> tuple[dict[str, Any], str]:
    if planned_bytes is not None and planned_bytes <= 0:
        raise AcquisitionBudgetError(f"invalid planned byte count for {source_url}")
    if budget is not None and planned_bytes is not None:
        check_planned_budget(
            loc_id="stream",
            sheet_bytes=planned_bytes,
            building_bytes=budget["building_bytes"] + planned_bytes,
            total_bytes=budget["total_bytes"] + planned_bytes,
            sheet_limit=budget["sheet_limit"],
            building_limit=budget["building_limit"],
            total_limit=budget["total_limit"],
        )
    if destination.exists() and prior and prior.get("source_url") == source_url:
        expected_hash = prior.get("sha256")
        expected_bytes = prior.get("bytes")
        local_bytes = destination.stat().st_size
        if expected_hash and expected_bytes == local_bytes and sha256_file(destination) == expected_hash:
            headers = client.head(source_url)
            remote_bytes = required_http_bytes(headers, source_url) if planned_bytes else (
                int(headers.get("content-length") or 0) or None
            )
            remote_modified = headers.get("last-modified")
            bytes_agree = remote_bytes is None or remote_bytes == local_bytes
            modified_agrees = (
                not prior.get("last_modified")
                or not remote_modified
                or prior.get("last_modified") == remote_modified
            )
            plan_agrees = planned_bytes is None or planned_bytes == local_bytes == remote_bytes
            if bytes_agree and modified_agrees and plan_agrees:
                stable = dict(prior)
                stable["last_modified"] = remote_modified or prior.get("last_modified")
                stable["etag"] = headers.get("etag") or prior.get("etag")
                stable["api_bytes"] = api_size
                stable["api_bytes_match"] = api_size == local_bytes if api_size else None
                if budget is not None:
                    budget["building_bytes"] += local_bytes
                    budget["total_bytes"] += local_bytes
                return stable, "cached"

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    last_error: Exception | None = None
    for attempt in range(client.retries + 1):
        digest = hashlib.sha256()
        byte_count = 0
        response_headers: dict[str, str] = {}
        try:
            with client.open(source_url) as response, temporary.open("wb") as output:
                response_headers = {
                    key.lower(): value for key, value in response.headers.items()
                }
                if planned_bytes is not None:
                    response_bytes = required_http_bytes(response_headers, source_url)
                    if response_bytes != planned_bytes:
                        raise AcquisitionBudgetError(
                            f"HTTP size changed for {source_url}: planned {planned_bytes}, got {response_bytes}"
                        )
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    byte_count += len(block)
                    if planned_bytes is not None and byte_count > planned_bytes:
                        raise AcquisitionBudgetError(
                            f"stream exceeded planned size for {source_url}"
                        )
                    if budget is not None:
                        check_planned_budget(
                            loc_id="stream",
                            sheet_bytes=byte_count,
                            building_bytes=budget["building_bytes"] + byte_count,
                            total_bytes=budget["total_bytes"] + byte_count,
                            sheet_limit=budget["sheet_limit"],
                            building_limit=budget["building_limit"],
                            total_limit=budget["total_limit"],
                        )
                    output.write(block)
                    digest.update(block)
            header_bytes = int(response_headers.get("content-length") or 0) or None
            if header_bytes is not None and header_bytes != byte_count:
                raise RuntimeError(
                    f"short download for {source_url}: expected HTTP {header_bytes}, got {byte_count}"
                )
            os.replace(temporary, destination)
            break
        except AcquisitionBudgetError:
            if temporary.exists():
                temporary.unlink()
            raise
        except (
            http.client.IncompleteRead,
            ConnectionError,
            TimeoutError,
            urllib.error.URLError,
            RuntimeError,
        ) as error:
            last_error = error
            if temporary.exists():
                temporary.unlink()
            if attempt >= client.retries:
                raise RuntimeError(
                    f"download failed after {attempt + 1} attempts: {source_url}: {error}"
                ) from error
            time.sleep(min(8.0, 0.5 * 2**attempt))
    else:
        raise RuntimeError(f"download failed: {source_url}: {last_error}")

    properties = image_properties(destination)
    if budget is not None:
        budget["building_bytes"] += byte_count
        budget["total_bytes"] += byte_count
    record = {
        "source_url": source_url,
        "local_path": "drawings/" + destination.name,
        "mime_type": response_headers.get("content-type"),
        "api_bytes": api_size,
        "api_bytes_match": api_size == byte_count if api_size else None,
        "bytes": byte_count,
        "sha256": digest.hexdigest(),
        "last_modified": response_headers.get("last-modified"),
        "etag": response_headers.get("etag"),
        "width": properties["width"],
        "height": properties["height"],
        "image_format": properties["format"],
        "image_mode": properties["mode"],
    }
    return record, "downloaded"


def harvest_building(
    client: LocClient,
    corpus_root: Path,
    selection: dict[str, Any],
    program: str,
    download_format: str,
    max_sheets: int,
    no_download: bool,
) -> tuple[dict[str, Any], Counter]:
    loc_id = selection["loc_id"]
    payload = client.get_json(detail_url(loc_id))
    item = payload.get("item")
    resources = payload.get("resources")
    if not isinstance(item, dict) or not isinstance(resources, list):
        raise RuntimeError(f"LOC detail response lacks item/resources for {loc_id}")
    response_id = item_id(str(item.get("id") or f"https://www.loc.gov/item/{loc_id}/"))
    if response_id.casefold() != loc_id.casefold():
        raise RuntimeError(f"requested {loc_id}, received {response_id}")

    building_dir = corpus_root / loc_id
    manifest_path = building_dir / "manifest.json"
    prior_manifest = load_json(manifest_path) if manifest_path.exists() else None
    prior_by_url = prior_downloads(prior_manifest)
    sheets = resolve_sheets(resources, program, selection)
    if not sheets:
        raise RuntimeError(f"{loc_id} has no downloadable {program} drawing resources")
    chosen_sheets = select_sheets(sheets, max_sheets)

    role_counters: Counter = Counter()
    run_counts: Counter = Counter()
    normalized_drawings = []
    for sheet in chosen_sheets:
        role = sheet["primary_role"]
        role_counters[role] += 1
        variant = select_variant(sheet, download_format)
        filename = f"{role}-{role_counters[role]:02d}{extension_for_variant(variant)}"
        destination = building_dir / "drawings" / filename
        api_size = int(variant.get("size") or 0) or None
        source_url = str(variant["url"])
        prior_download = prior_by_url.get(source_url)
        if no_download and destination.exists() and prior_download:
            local_bytes = destination.stat().st_size
            if (
                prior_download.get("bytes") == local_bytes
                and prior_download.get("sha256") == sha256_file(destination)
            ):
                download = dict(prior_download)
                download["api_bytes"] = api_size
                download["api_bytes_match"] = api_size == local_bytes if api_size else None
                run_counts["preserved"] += 1
            else:
                raise RuntimeError(
                    f"--no-download refuses to replace invalid cached metadata for {destination}"
                )
        elif no_download:
            download = {
                "source_url": source_url,
                "local_path": "drawings/" + filename,
                "mime_type": variant.get("mimetype"),
                "api_bytes": api_size,
                "api_bytes_match": None,
                "bytes": None,
                "sha256": None,
                "last_modified": None,
                "etag": None,
                "width": variant.get("width") or None,
                "height": variant.get("height") or None,
                "image_format": None,
                "image_mode": None,
            }
            run_counts["planned"] += 1
        else:
            download, disposition = download_file(
                client, source_url, destination, api_size, prior_download
            )
            run_counts[disposition] += 1
        normalized_sheet = dict(sheet)
        normalized_sheet["download"] = download
        normalized_drawings.append(normalized_sheet)

    metadata = normalize_metadata(loc_id, item, resources, selection)
    write_json_if_changed(building_dir / "metadata.json", metadata)
    manifest = {
        "schema": SCHEMA_BUILDING_MANIFEST,
        "building_id": loc_id,
        "title": item.get("title"),
        "loc_item_url": f"https://www.loc.gov/item/{loc_id}/",
        "loc_api_url": detail_url(loc_id),
        "source_collection_url": COLLECTION_URL,
        "source_modified": item.get("source_modified") or item.get("modified"),
        "download_format": download_format,
        "resource_count": len(resources),
        "resolved_drawing_sheet_count": len(sheets),
        "selected_drawing_sheet_count": len(chosen_sheets),
        "unselected_sheet_indexes": [
            sheet["sheet_index"] for sheet in sheets if sheet not in chosen_sheets
        ],
        "rights": metadata["rights"],
        "drawings": normalized_drawings,
    }
    write_json_if_changed(manifest_path, manifest)
    building_summary = {
        "building_id": loc_id,
        "title": item.get("title"),
        "building_type": selection.get("building_type"),
        "state": metadata["location"]["state"],
        "survey_numbers": metadata["identifiers"]["survey_numbers"],
        "drawing_count": len(normalized_drawings),
        "roles": sorted({role for sheet in normalized_drawings for role in sheet["roles"]}),
        "bytes": sum(int(sheet["download"].get("bytes") or 0) for sheet in normalized_drawings),
        "path": loc_id,
    }
    return building_summary, run_counts


def plan_building(
    client: LocClient,
    selection: dict[str, Any],
    program: str,
    download_format: str,
    max_sheets: int,
    budgets: dict[str, int],
    prior_total: int,
) -> dict[str, Any]:
    loc_id = selection["loc_id"]
    payload = client.get_json(detail_url(loc_id))
    item = payload.get("item")
    resources = payload.get("resources")
    if not isinstance(item, dict) or not isinstance(resources, list):
        raise RuntimeError(f"LOC detail response lacks item/resources for {loc_id}")
    response_id = item_id(str(item.get("id") or f"https://www.loc.gov/item/{loc_id}/"))
    if response_id.casefold() != loc_id.casefold():
        raise RuntimeError(f"requested {loc_id}, received {response_id}")

    sheets = resolve_sheets(resources, program, selection)
    if not sheets:
        raise RuntimeError(f"{loc_id} has no downloadable {program} drawing resources")
    chosen_sheets = select_sheets(sheets, max_sheets)
    role_counters: Counter = Counter()
    planned_drawings = []
    building_bytes = 0
    for sheet in chosen_sheets:
        role = sheet["primary_role"]
        role_counters[role] += 1
        variant = select_variant(sheet, download_format)
        source_url = str(variant["url"])
        headers = client.head(source_url)
        http_bytes = required_http_bytes(headers, source_url)
        building_bytes += http_bytes
        check_planned_budget(
            loc_id=loc_id,
            sheet_bytes=http_bytes,
            building_bytes=building_bytes,
            total_bytes=prior_total + building_bytes,
            sheet_limit=budgets["per_sheet_bytes"],
            building_limit=budgets["per_building_bytes"],
            total_limit=budgets["total_bytes"],
        )
        filename = f"{role}-{role_counters[role]:02d}{extension_for_variant(variant)}"
        planned_sheet = dict(sheet)
        planned_sheet["acquisition"] = {
            "source_url": source_url,
            "local_path": "drawings/" + filename,
            "http_bytes": http_bytes,
            "api_bytes": int(variant.get("size") or 0) or None,
            "mime_type": headers.get("content-type") or variant.get("mimetype"),
            "last_modified": headers.get("last-modified"),
            "etag": headers.get("etag"),
        }
        planned_drawings.append(planned_sheet)

    metadata = normalize_metadata(loc_id, item, resources, selection)
    return {
        "building_id": loc_id,
        "selection": selection,
        "metadata": metadata,
        "title": item.get("title"),
        "source_modified": item.get("source_modified") or item.get("modified"),
        "resource_count": len(resources),
        "resolved_drawing_sheet_count": len(sheets),
        "selected_drawing_sheet_count": len(chosen_sheets),
        "unselected_sheet_indexes": [
            sheet["sheet_index"] for sheet in sheets if sheet not in chosen_sheets
        ],
        "http_bytes": building_bytes,
        "drawings": planned_drawings,
    }


def validate_acquisition_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema") != SCHEMA_ACQUISITION_PLAN or plan.get("status") != "PASS":
        raise ValueError("acquisition plan is not a passing v1 plan")
    budgets = plan.get("budgets")
    buildings = plan.get("buildings")
    if not isinstance(budgets, dict) or not isinstance(buildings, list) or not buildings:
        raise ValueError("acquisition plan lacks budgets or buildings")
    expected_keys = {"total_bytes", "per_building_bytes", "per_sheet_bytes"}
    if not expected_keys.issubset(budgets):
        raise ValueError("acquisition plan has incomplete budgets")
    seen: set[str] = set()
    total = 0
    for building in buildings:
        loc_id = clean_loc_id(str(building.get("building_id") or ""))
        if loc_id.casefold() in seen:
            raise ValueError(f"duplicate LOC id in acquisition plan: {loc_id}")
        seen.add(loc_id.casefold())
        building_total = 0
        drawings = building.get("drawings")
        if not isinstance(drawings, list) or not drawings:
            raise ValueError(f"{loc_id}: acquisition plan has no drawings")
        for sheet in drawings:
            acquisition = sheet.get("acquisition") if isinstance(sheet, dict) else None
            if not isinstance(acquisition, dict):
                raise ValueError(f"{loc_id}: planned drawing lacks acquisition record")
            source_url = acquisition.get("source_url")
            if not isinstance(source_url, str) or not source_url.startswith("https://"):
                raise ValueError(f"{loc_id}: acquisition URL is not HTTPS")
            sheet_bytes = int(acquisition.get("http_bytes") or 0)
            building_total += sheet_bytes
            check_planned_budget(
                loc_id=loc_id,
                sheet_bytes=sheet_bytes,
                building_bytes=building_total,
                total_bytes=total + building_total,
                sheet_limit=int(budgets["per_sheet_bytes"]),
                building_limit=int(budgets["per_building_bytes"]),
                total_limit=int(budgets["total_bytes"]),
            )
        if building.get("http_bytes") != building_total:
            raise ValueError(f"{loc_id}: planned building byte total mismatch")
        total += building_total
    totals = plan.get("totals") or {}
    if totals.get("http_bytes") != total:
        raise ValueError("acquisition plan total byte count mismatch")


def harvest_planned_building(
    client: LocClient,
    corpus_root: Path,
    building: dict[str, Any],
    download_format: str,
    budget: dict[str, int],
) -> tuple[dict[str, Any], Counter]:
    loc_id = building["building_id"]
    building_dir = corpus_root / loc_id
    manifest_path = building_dir / "manifest.json"
    prior_manifest = load_json(manifest_path) if manifest_path.exists() else None
    prior_by_url = prior_downloads(prior_manifest)
    budget["building_bytes"] = 0
    normalized_drawings = []
    run_counts: Counter = Counter()
    for sheet in building["drawings"]:
        acquisition = sheet["acquisition"]
        source_url = acquisition["source_url"]
        destination = resolved_child(building_dir, acquisition["local_path"])
        download, disposition = download_file(
            client,
            source_url,
            destination,
            acquisition.get("api_bytes"),
            prior_by_url.get(source_url),
            planned_bytes=int(acquisition["http_bytes"]),
            budget=budget,
        )
        normalized_sheet = dict(sheet)
        normalized_sheet["download"] = download
        normalized_drawings.append(normalized_sheet)
        run_counts[disposition] += 1

    metadata = building["metadata"]
    write_json_if_changed(building_dir / "metadata.json", metadata)
    manifest = {
        "schema": SCHEMA_BUILDING_MANIFEST,
        "building_id": loc_id,
        "title": building.get("title"),
        "loc_item_url": f"https://www.loc.gov/item/{loc_id}/",
        "loc_api_url": detail_url(loc_id),
        "source_collection_url": COLLECTION_URL,
        "source_modified": building.get("source_modified"),
        "download_format": download_format,
        "resource_count": building["resource_count"],
        "resolved_drawing_sheet_count": building["resolved_drawing_sheet_count"],
        "selected_drawing_sheet_count": building["selected_drawing_sheet_count"],
        "unselected_sheet_indexes": building["unselected_sheet_indexes"],
        "rights": metadata["rights"],
        "drawings": normalized_drawings,
    }
    write_json_if_changed(manifest_path, manifest)
    summary = {
        "building_id": loc_id,
        "title": building.get("title"),
        "building_type": building["selection"].get("building_type"),
        "state": metadata["location"]["state"],
        "survey_numbers": metadata["identifiers"]["survey_numbers"],
        "drawing_count": len(normalized_drawings),
        "roles": sorted({role for sheet in normalized_drawings for role in sheet["roles"]}),
        "bytes": budget["building_bytes"],
        "path": loc_id,
    }
    return summary, run_counts


def command_search(args: argparse.Namespace) -> int:
    filters = filters_from_args(args)
    client = client_from_args(args)
    candidates, urls, reported_counts = search_candidates(
        client, filters, limit=args.limit, scan_limit=args.scan_limit
    )
    payload = {
        "schema": SCHEMA_SEARCH,
        "collection_url": COLLECTION_URL,
        "filters": filters,
        "query_urls": urls,
        "reported_counts": reported_counts,
        "result_count": len(candidates),
        "results": candidates,
    }
    if args.output:
        write_json_if_changed(args.output.resolve(), payload)
    sys.stdout.buffer.write(canonical_json(payload))
    return 0


def command_plan(args: argparse.Namespace) -> int:
    validate_date_range(args)
    client = client_from_args(args)
    selection, selection_receipt = load_selection(args, client)
    budgets = {
        "total_bytes": args.max_total_bytes,
        "per_building_bytes": args.max_building_bytes,
        "per_sheet_bytes": args.max_sheet_bytes,
    }
    buildings = []
    total_bytes = 0
    seen: set[str] = set()
    for index, selected in enumerate(selection, start=1):
        loc_id = selected["loc_id"]
        if loc_id.casefold() in seen:
            raise ValueError(f"duplicate LOC id in selection: {loc_id}")
        seen.add(loc_id.casefold())
        print(
            f"[{index:02d}/{len(selection):02d}] HEAD {loc_id}",
            file=sys.stderr,
            flush=True,
        )
        building = plan_building(
            client,
            selected,
            args.program,
            args.format,
            args.max_sheets_per_building,
            budgets,
            total_bytes,
        )
        buildings.append(building)
        total_bytes += building["http_bytes"]
    plan = {
        "schema": SCHEMA_ACQUISITION_PLAN,
        "status": "PASS",
        "collection_url": COLLECTION_URL,
        "program": args.program,
        "selection": selection_receipt,
        "normalization": {
            "download_format": args.format,
            "max_sheets_per_building": args.max_sheets_per_building,
        },
        "budgets": budgets,
        "totals": {
            "buildings": len(buildings),
            "drawings": sum(len(building["drawings"]) for building in buildings),
            "http_bytes": total_bytes,
        },
        "buildings": buildings,
    }
    validate_acquisition_plan(plan)
    output = args.output.resolve()
    write_json_if_changed(output, plan)
    receipt = {
        "status": "PASS",
        "plan": str(output),
        "sha256": sha256_file(output),
        **plan["totals"],
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


def command_harvest_plan(args: argparse.Namespace) -> int:
    if args.no_download:
        raise ValueError("--no-download cannot be combined with --plan")
    if args.spec or args.id or has_live_filters(args):
        raise ValueError("--plan cannot be combined with selection inputs")
    plan_path = args.plan.resolve()
    plan = load_json(plan_path)
    validate_acquisition_plan(plan)
    client = client_from_args(args)
    corpus_root = args.output.resolve()
    corpus_root.mkdir(parents=True, exist_ok=True)
    tracker = budget_tracker(plan)
    summaries = []
    run_counts: Counter = Counter()
    for index, building in enumerate(plan["buildings"], start=1):
        loc_id = building["building_id"]
        print(
            f"[{index:02d}/{len(plan['buildings']):02d}] {loc_id}",
            file=sys.stderr,
            flush=True,
        )
        summary, counts = harvest_planned_building(
            client,
            corpus_root,
            building,
            plan["normalization"]["download_format"],
            tracker,
        )
        summaries.append(summary)
        run_counts.update(counts)
    if tracker["total_bytes"] != plan["totals"]["http_bytes"]:
        raise RuntimeError("downloaded bytes do not equal the frozen acquisition plan")
    corpus_manifest = {
        "schema": SCHEMA_CORPUS_MANIFEST,
        "collection": {
            "name": "Historic American Buildings Survey/Historic American Engineering Record/Historic American Landscapes Survey",
            "url": COLLECTION_URL,
            "program": plan["program"],
        },
        "selection": {
            "kind": "frozen-acquisition-plan",
            "path": str(plan_path),
            "sha256": sha256_file(plan_path),
            "source_selection": plan["selection"],
        },
        "normalization": {
            **plan["normalization"],
            "drawing_roles": sorted(ROLE_PATTERNS),
            "unclassified_role": "drawing",
        },
        "acquisition_budgets": plan["budgets"],
        "building_count": len(summaries),
        "drawing_count": sum(summary["drawing_count"] for summary in summaries),
        "downloaded_bytes": tracker["total_bytes"],
        "buildings": summaries,
    }
    write_json_if_changed(corpus_root / "manifest.json", corpus_manifest)
    receipt = {
        "status": "PASS",
        "corpus": str(corpus_root),
        "plan_sha256": sha256_file(plan_path),
        "buildings": len(summaries),
        "drawings": corpus_manifest["drawing_count"],
        "bytes": corpus_manifest["downloaded_bytes"],
        "run": dict(sorted(run_counts.items())),
        "manifest": str(corpus_root / "manifest.json"),
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


def command_harvest(args: argparse.Namespace) -> int:
    if args.plan:
        return command_harvest_plan(args)
    validate_date_range(args)
    client = client_from_args(args)
    selection, selection_receipt = load_selection(args, client)
    corpus_root = args.output.resolve()
    corpus_root.mkdir(parents=True, exist_ok=True)

    summaries = []
    run_counts: Counter = Counter()
    seen = set()
    for index, building in enumerate(selection, start=1):
        loc_id = building["loc_id"]
        if loc_id.casefold() in seen:
            raise ValueError(f"duplicate LOC id in selection: {loc_id}")
        seen.add(loc_id.casefold())
        print(f"[{index:02d}/{len(selection):02d}] {loc_id}", file=sys.stderr, flush=True)
        summary, counts = harvest_building(
            client,
            corpus_root,
            building,
            args.program,
            args.format,
            args.max_sheets_per_building,
            args.no_download,
        )
        summaries.append(summary)
        run_counts.update(counts)

    corpus_manifest = {
        "schema": SCHEMA_CORPUS_MANIFEST,
        "collection": {
            "name": "Historic American Buildings Survey/Historic American Engineering Record/Historic American Landscapes Survey",
            "url": COLLECTION_URL,
            "program": args.program,
        },
        "selection": selection_receipt,
        "normalization": {
            "download_format": args.format,
            "max_sheets_per_building": args.max_sheets_per_building,
            "drawing_roles": sorted(ROLE_PATTERNS),
            "unclassified_role": "drawing",
        },
        "building_count": len(summaries),
        "drawing_count": sum(summary["drawing_count"] for summary in summaries),
        "downloaded_bytes": sum(summary["bytes"] for summary in summaries),
        "buildings": summaries,
    }
    write_json_if_changed(corpus_root / "manifest.json", corpus_manifest)
    receipt = {
        "status": "PASS",
        "corpus": str(corpus_root),
        "buildings": len(summaries),
        "drawings": corpus_manifest["drawing_count"],
        "bytes": corpus_manifest["downloaded_bytes"],
        "run": dict(sorted(run_counts.items())),
        "manifest": str(corpus_root / "manifest.json"),
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


def resolved_child(root: Path, relative: str) -> Path:
    candidate = (root / Path(relative)).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"manifest path escapes building directory: {relative}")
    return candidate


def command_verify(args: argparse.Namespace) -> int:
    corpus_root = args.output.resolve()
    errors = []
    manifest_path = corpus_root / "manifest.json"
    if not manifest_path.exists():
        errors.append(f"missing {manifest_path}")
        root_manifest: dict[str, Any] = {}
    else:
        root_manifest = load_json(manifest_path)
    buildings = root_manifest.get("buildings") or []
    if root_manifest.get("schema") != SCHEMA_CORPUS_MANIFEST:
        errors.append("unexpected or missing corpus manifest schema")
    if args.expected_buildings and len(buildings) != args.expected_buildings:
        errors.append(f"expected {args.expected_buildings} buildings, found {len(buildings)}")
    declared_building_dirs = {
        summary.get("building_id") for summary in buildings
        if isinstance(summary, dict) and isinstance(summary.get("building_id"), str)
    }
    actual_building_dirs = {
        path.name for path in corpus_root.iterdir() if path.is_dir()
    } if corpus_root.exists() else set()
    unexpected_building_dirs = sorted(actual_building_dirs - declared_building_dirs)
    if unexpected_building_dirs:
        errors.append(f"unexpected building directories: {unexpected_building_dirs}")

    checked_files = 0
    checked_bytes = 0
    checked_drawings = 0
    role_counts: Counter = Counter()
    for summary in buildings:
        loc_id = summary.get("building_id")
        if not isinstance(loc_id, str):
            errors.append(f"invalid building summary: {summary!r}")
            continue
        building_dir = corpus_root / loc_id
        metadata_path = building_dir / "metadata.json"
        building_manifest_path = building_dir / "manifest.json"
        if not metadata_path.exists() or not building_manifest_path.exists():
            errors.append(f"{loc_id}: missing metadata.json or manifest.json")
            continue
        metadata = load_json(metadata_path)
        building_manifest = load_json(building_manifest_path)
        if metadata.get("building_id") != loc_id or building_manifest.get("building_id") != loc_id:
            errors.append(f"{loc_id}: identifier mismatch")
        declared_files = set()
        building_drawings = building_manifest.get("drawings") or []
        building_checked_bytes = 0
        if summary.get("drawing_count") != len(building_drawings):
            errors.append(f"{loc_id}: root/building drawing count mismatch")
        for sheet in building_drawings:
            checked_drawings += 1
            for role in sheet.get("roles") or []:
                role_counts[role] += 1
            if not sheet.get("roles"):
                role_counts["unclassified"] += 1
            download = sheet.get("download") or {}
            relative = download.get("local_path")
            if not relative:
                errors.append(f"{loc_id}: drawing lacks local_path")
                continue
            declared_files.add(Path(relative).as_posix())
            path = resolved_child(building_dir.resolve(), str(relative))
            if not path.exists():
                errors.append(f"{loc_id}: missing {relative}")
                continue
            byte_count = path.stat().st_size
            checked_files += 1
            checked_bytes += byte_count
            building_checked_bytes += byte_count
            if download.get("bytes") != byte_count:
                errors.append(f"{loc_id}: byte count mismatch for {relative}")
            if download.get("sha256") != sha256_file(path):
                errors.append(f"{loc_id}: SHA-256 mismatch for {relative}")
            properties = image_properties(path)
            if (
                properties["width"] is not None
                and download.get("width")
                and download.get("width") != properties["width"]
            ):
                errors.append(f"{loc_id}: width mismatch for {relative}")
            if (
                properties["height"] is not None
                and download.get("height")
                and download.get("height") != properties["height"]
            ):
                errors.append(f"{loc_id}: height mismatch for {relative}")
        drawings_dir = building_dir / "drawings"
        partial_files = sorted(
            path.name for path in drawings_dir.glob("*.part") if path.is_file()
        ) if drawings_dir.exists() else []
        if partial_files:
            errors.append(f"{loc_id}: partial drawing files: {partial_files}")
        actual_files = {
            path.relative_to(building_dir).as_posix()
            for path in drawings_dir.glob("*") if path.is_file()
        } if drawings_dir.exists() else set()
        unexpected = sorted(actual_files - declared_files)
        if unexpected:
            errors.append(f"{loc_id}: unexpected drawing files: {unexpected}")
        if summary.get("bytes") != building_checked_bytes:
            errors.append(f"{loc_id}: root/building byte count mismatch")

    if root_manifest.get("building_count") != len(buildings):
        errors.append("corpus building_count does not match building summaries")
    if root_manifest.get("drawing_count") != checked_drawings:
        errors.append("corpus drawing_count does not match building manifests")
    if root_manifest.get("downloaded_bytes") != checked_bytes:
        errors.append("corpus downloaded_bytes does not match local drawings")

    receipt = {
        "status": "FAIL" if errors else "PASS",
        "corpus": str(corpus_root),
        "buildings": len(buildings),
        "files": checked_files,
        "bytes": checked_bytes,
        "roles": dict(sorted(role_counts.items())),
        "errors": errors,
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "search":
            return command_search(args)
        if args.command == "plan":
            return command_plan(args)
        if args.command == "harvest":
            return command_harvest(args)
        if args.command == "verify":
            return command_verify(args)
        raise AssertionError(args.command)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
