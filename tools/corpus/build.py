#!/usr/bin/env python3
"""Build disposable discovery indexes and audience projections.

The inputs remain authoritative in their native homes. This builder knows a few
deterministic adapter paths and one colocated sidecar shape; it deliberately does not
try to turn every domain record into a universal ontology.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CATALOG_PATH = ROOT / "corpus" / "sources.json"
AUDIENCES_PATH = ROOT / "corpus" / "audiences.json"
TOKENS_PATH = ROOT / "tools" / "site" / "tokens.css"
PUBLIC_BASE = "https://djcdevelopment.github.io/baseline/"
AM4_BASE = "https://am4.tail8e749c.ts.net"


class CorpusError(Exception):
    pass


def read_json(path: Path) -> Any:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise CorpusError(f"{path.relative_to(ROOT)}: duplicate JSON key {key!r}")
            out[key] = value
        return out

    try:
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=no_duplicates)
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusError(f"cannot read {path.relative_to(ROOT)}: {exc}") from exc


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_parts(parts: list[tuple[str, bytes]]) -> str:
    h = hashlib.sha256()
    for name, blob in parts:
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(str(len(blob)).encode("ascii"))
        h.update(b"\0")
        h.update(blob)
        h.update(b"\0")
    return h.hexdigest()


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CorpusError(f"{label} must be a non-empty string")
    return value.strip()


def parse_time(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CorpusError(f"{label} is not an ISO-8601 timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise CorpusError(f"{label} must include a UTC offset")
    return parsed


def load_audiences() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    doc = read_json(AUDIENCES_PATH)
    if doc.get("schema_version") != 1 or not isinstance(doc.get("roles"), list):
        raise CorpusError("corpus/audiences.json must be schema version 1 with a roles array")
    roles = sorted(doc["roles"], key=lambda role: role.get("order", 0))
    by_id: dict[str, dict[str, Any]] = {}
    for index, role in enumerate(roles):
        label = f"corpus/audiences.json roles[{index}]"
        role_id = require_string(role.get("id"), f"{label}.id")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", role_id):
            raise CorpusError(f"{label}.id is not a lowercase slug: {role_id}")
        if role_id in by_id:
            raise CorpusError(f"duplicate audience id: {role_id}")
        for key in ("label", "short_label", "question", "promise"):
            require_string(role.get(key), f"{label}.{key}")
        if not isinstance(role.get("order"), int):
            raise CorpusError(f"{label}.order must be an integer")
        by_id[role_id] = role
    return roles, by_id


def validate_audience_ids(values: Any, label: str, audience_by_id: dict[str, Any]) -> list[str]:
    if not isinstance(values, list) or not values:
        raise CorpusError(f"{label} must be a non-empty array")
    if len(values) != len(set(values)):
        raise CorpusError(f"{label} contains duplicate audience IDs")
    unknown = [value for value in values if value not in audience_by_id]
    if unknown:
        raise CorpusError(f"{label} references unknown audience IDs: {', '.join(map(str, unknown))}")
    return list(values)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def manifest_records(catalog: dict[str, Any], audience_by_id: dict[str, Any]) -> list[dict[str, Any]]:
    paths: set[Path] = set()
    for pattern in catalog.get("artifact_globs", []):
        paths.update(path for path in ROOT.glob(pattern) if path.is_file())
    records: list[dict[str, Any]] = []
    allowed_kinds = {"story", "guide", "portal"}
    for manifest_path in sorted(paths):
        doc = read_json(manifest_path)
        label = rel(manifest_path)
        if doc.get("schema_version") != 1:
            raise CorpusError(f"{label}.schema_version must be 1")
        record_id = require_string(doc.get("id"), f"{label}.id")
        if not re.fullmatch(r"[a-z][a-z0-9-]*:[a-z0-9][a-z0-9-]*", record_id):
            raise CorpusError(f"{label}.id must have kind:slug form")
        kind = require_string(doc.get("kind"), f"{label}.kind")
        if kind not in allowed_kinds:
            raise CorpusError(f"{label}.kind must be one of {sorted(allowed_kinds)}")
        audience_doc = doc.get("audiences")
        if not isinstance(audience_doc, dict):
            raise CorpusError(f"{label}.audiences must be an object")
        primary = validate_audience_ids(audience_doc.get("primary"), f"{label}.audiences.primary", audience_by_id)
        relevant = validate_audience_ids(audience_doc.get("relevant"), f"{label}.audiences.relevant", audience_by_id)
        if set(primary) & set(relevant):
            raise CorpusError(f"{label}: primary and relevant audiences must not overlap")
        published = require_string(doc.get("published_at"), f"{label}.published_at")
        parse_time(published, f"{label}.published_at")
        updated = doc.get("updated_at") or published
        parse_time(updated, f"{label}.updated_at")
        source_names = doc.get("source_files")
        if not isinstance(source_names, list) or not source_names:
            raise CorpusError(f"{label}.source_files must be a non-empty array")
        parent = manifest_path.parent.resolve()
        source_paths: list[Path] = []
        for source_name in source_names:
            require_string(source_name, f"{label}.source_files[]")
            source_path = (manifest_path.parent / source_name).resolve()
            try:
                source_path.relative_to(parent)
            except ValueError as exc:
                raise CorpusError(f"{label}: source {source_name!r} escapes the artifact directory") from exc
            if not source_path.is_file():
                raise CorpusError(f"{label}: source file does not exist: {source_name}")
            source_paths.append(source_path)
        parts = [(label, canonical(doc))]
        parts.extend((rel(path), path.read_bytes()) for path in source_paths)
        records.append({
            "id": record_id,
            "kind": kind,
            "title": require_string(doc.get("title"), f"{label}.title"),
            "summary": require_string(doc.get("summary"), f"{label}.summary"),
            "audiences": primary + relevant,
            "primary_audiences": primary,
            "url": require_string(doc.get("canonical_url"), f"{label}.canonical_url"),
            "published_at": published,
            "updated_at": updated,
            "source": {
                "authority": "colocated-artifact",
                "locator": label,
                "files": [rel(path) for path in source_paths],
                "sha256": digest_parts(parts),
            },
            "facets": doc.get("facets", {}),
            "data": doc,
        })
    return records


def workbench_records(path: Path, audience_by_id: dict[str, Any]) -> list[dict[str, Any]]:
    doc = read_json(path)
    tools = doc.get("tools")
    if not isinstance(tools, list) or not tools:
        raise CorpusError(f"{rel(path)} must contain a non-empty tools array")
    records = []
    for index, tool in enumerate(tools):
        label = f"{rel(path)}#/tools/{index}"
        tool_id = require_string(tool.get("id"), f"{label}.id")
        audiences = validate_audience_ids(tool.get("audiences"), f"{label}.audiences", audience_by_id)
        records.append({
            "id": f"tool:{tool_id}",
            "kind": "tool",
            "title": require_string(tool.get("name"), f"{label}.name"),
            "summary": require_string(tool.get("one_liner"), f"{label}.one_liner"),
            "audiences": audiences,
            "primary_audiences": audiences[:1],
            "url": f"{AM4_BASE}/workbench#{tool_id}",
            "published_at": None,
            "updated_at": None,
            "source": {
                "authority": "workbench-catalog",
                "locator": f"{rel(path)}#/tools/{tool_id}",
                "sha256": hashlib.sha256(canonical(tool)).hexdigest(),
            },
            "facets": {
                "status": tool.get("status"),
                "access": (tool.get("access") or {}).get("kind"),
                "ownership": (tool.get("ownership") or {}).get("state"),
            },
            "data": tool,
        })
    return records


def roadmap_records(adapter: dict[str, Any], path: Path, audience_by_id: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = adapter.get("audiences_by_kind") or {}
    records = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            note = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CorpusError(f"{rel(path)}:{line_number}: {exc}") from exc
        kind = require_string(note.get("kind"), f"{rel(path)}:{line_number}.kind")
        audiences = validate_audience_ids(mapping.get(kind), f"{rel(path)} adapter audiences_by_kind.{kind}", audience_by_id)
        note_id = require_string(note.get("id"), f"{rel(path)}:{line_number}.id")
        at = require_string(note.get("at"), f"{rel(path)}:{line_number}.at")
        parse_time(at, f"{rel(path)}:{line_number}.at")
        records.append({
            "id": f"roadmap:{note_id}",
            "kind": "roadmap-note",
            "title": require_string(note.get("summary"), f"{rel(path)}:{line_number}.summary"),
            "summary": require_string(note.get("impact"), f"{rel(path)}:{line_number}.impact"),
            "audiences": audiences,
            "primary_audiences": audiences[:1],
            "url": require_string(adapter.get("url"), "roadmap adapter url").format(id=note_id),
            "published_at": at,
            "updated_at": at,
            "source": {
                "authority": "append-only-roadmap-journal",
                "locator": f"{rel(path)}#L{line_number}",
                "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            },
            "facets": {"kind": kind, "milestones": note.get("milestones", [])},
            "data": note,
        })
    return records


def discord_records(path: Path, audience_by_id: dict[str, Any]) -> list[dict[str, Any]]:
    capture = read_json(path)
    if capture.get("schema_version") != 1 or not isinstance(capture.get("posts"), list):
        raise CorpusError(f"{rel(path)} must be schema version 1 with a posts array")
    records = []
    for index, post in enumerate(capture["posts"]):
        label = f"{rel(path)}#/posts/{index}"
        audiences = validate_audience_ids(post.get("audiences"), f"{label}.audiences", audience_by_id)
        created = require_string(post.get("created_at"), f"{label}.created_at")
        parse_time(created, f"{label}.created_at")
        updated = post.get("edited_at") or created
        parse_time(updated, f"{label}.edited_at")
        content = require_string(post.get("content"), f"{label}.content")
        summary = re.sub(r"\s+", " ", re.sub(r"[#*_>`]", "", content)).strip()
        if len(summary) > 280:
            summary = summary[:277].rstrip() + "..."
        thread_id = require_string(post.get("thread_id"), f"{label}.thread_id")
        records.append({
            "id": f"dispatch:{thread_id}",
            "kind": "dispatch",
            "title": require_string(post.get("title"), f"{label}.title"),
            "summary": summary,
            "audiences": audiences,
            "primary_audiences": audiences[:1],
            "url": require_string(post.get("url"), f"{label}.url"),
            "published_at": created,
            "updated_at": updated,
            "source": {
                "authority": "discord-forum-starter-post",
                "locator": f"discord://{capture.get('guild_id')}/{thread_id}/{post.get('message_id')}",
                "mirror": rel(path),
                "sha256": hashlib.sha256(canonical(post)).hexdigest(),
            },
            "facets": {"format": post.get("format"), "tags": post.get("tags", [])},
            "data": post,
        })
    return records


def build_index() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    catalog = read_json(CATALOG_PATH)
    if catalog.get("schema_version") != 1:
        raise CorpusError("corpus/sources.json.schema_version must be 1")
    roles, audience_by_id = load_audiences()
    records = manifest_records(catalog, audience_by_id)
    streams: dict[str, Any] = {}
    for adapter in catalog.get("adapters", []):
        path = ROOT / require_string(adapter.get("path"), "corpus adapter path")
        if not path.exists() and adapter.get("optional") is True:
            continue
        if not path.is_file():
            raise CorpusError(f"adapter source does not exist: {rel(path)}")
        kind = adapter.get("kind")
        if kind == "workbench":
            records.extend(workbench_records(path, audience_by_id))
        elif kind == "roadmap-jsonl":
            records.extend(roadmap_records(adapter, path, audience_by_id))
        elif kind == "discord-dispatches":
            capture = read_json(path)
            records.extend(discord_records(path, audience_by_id))
            streams["dispatches"] = {
                "authority": capture.get("authority"),
                "channel_url": capture.get("channel_url"),
                "mirror": rel(path),
                "source_watermark": capture.get("source_watermark"),
            }
        else:
            raise CorpusError(f"unknown adapter kind: {kind}")

    seen: set[str] = set()
    for record in records:
        if record["id"] in seen:
            raise CorpusError(f"duplicate corpus record id: {record['id']}")
        seen.add(record["id"])
    records.sort(key=lambda item: item["id"])
    times = [record["updated_at"] for record in records if record.get("updated_at")]
    index = {
        "schema_version": 1,
        "notice": "GENERATED acceleration structure. Rebuild from authoritative artifacts; do not edit.",
        "generated_by": "tools/corpus/build.py",
        "source_catalog": "corpus/sources.json",
        "as_of": max(times, key=lambda value: parse_time(value, "record timestamp")) if times else None,
        "audiences": roles,
        "streams": streams,
        "records": records,
    }
    index["build_fingerprint"] = hashlib.sha256(canonical({"audiences": roles, "streams": streams, "records": records})).hexdigest()
    return index, roles


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def ascii_html(value: str) -> str:
    return value.encode("ascii", "xmlcharrefreplace").decode("ascii")


def page_shell(title: str, description: str, body: str, canonical_url: str) -> str:
    tokens = TOKENS_PATH.read_text(encoding="utf-8")
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(description)}"><link rel="canonical" href="{e(canonical_url)}">
<style>*{{box-sizing:border-box}}{tokens}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.6}}
a{{color:var(--wood);text-underline-offset:.2em}}.wrap{{max-width:68rem;margin:auto;padding:0 20px}}
.top{{border-bottom:1px solid var(--line);background:var(--scrim);position:sticky;top:0;z-index:2}}.nav{{min-height:58px;display:flex;align-items:center;gap:1rem;flex-wrap:wrap}}
.nav strong{{font-family:var(--mono);margin-right:auto}}.nav a{{font-family:var(--mono);font-size:.75rem;color:var(--muted);text-decoration:none}}
header{{padding:4.2rem 0 2.2rem}}.eyebrow{{font:700 .66rem var(--mono);letter-spacing:.15em;text-transform:uppercase;color:var(--wood)}}
h1{{font:700 clamp(2rem,6vw,4rem)/1.05 var(--mono);letter-spacing:-.04em;max-width:20ch;margin:.6rem 0 1rem}}h2{{font:700 1.35rem var(--mono);margin:0 0 .8rem}}h3{{font:700 1rem var(--mono);margin:0}}
.lede{{max-width:43rem;color:var(--muted);font-size:1.08rem}}section{{margin:2.5rem 0 4rem}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:.8rem}}
.card{{display:flex;flex-direction:column;gap:.55rem;padding:1rem 1.1rem;border:1px solid var(--line);border-radius:6px;background:var(--paper)}}.card p{{margin:0;color:var(--muted);font-size:.91rem}}
.meta{{font:700 .62rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--dim)}}.roles{{display:flex;flex-wrap:wrap;gap:.5rem}}
.chip{{display:inline-block;padding:.35rem .55rem;border:1px solid var(--line2);border-radius:999px;font:700 .68rem var(--mono);text-decoration:none;color:var(--muted)}}
.chip.current{{border-color:var(--wood);color:var(--wood)}}.note{{border-left:2px solid var(--amber);padding:.7rem 1rem;color:var(--muted);max-width:46rem}}
.stream{{display:grid;gap:.65rem}}.entry{{padding:1rem 0;border-top:1px solid var(--line);display:grid;gap:.35rem}}.entry time{{font:.68rem var(--mono);color:var(--dim)}}
footer{{border-top:1px solid var(--line);padding:2rem 0 3rem;color:var(--dim);font:.68rem/1.6 var(--mono)}}
@media(max-width:650px){{.top{{position:static}}.nav strong{{width:100%;margin-top:.7rem}}header{{padding-top:2.5rem}}}}
</style></head><body>
<div class="top"><nav class="wrap nav" aria-label="Baseline"><strong>BASELINE</strong><a href="{PUBLIC_BASE}">Home</a><a href="{PUBLIC_BASE}updates/">Updates</a><a href="{PUBLIC_BASE}explore/">Explore all</a><a href="{AM4_BASE}/workbench">Live Workbench</a></nav></div>
{body}
<footer><div class="wrap">Projection rebuilt from named authoritative artifacts. <a href="{PUBLIC_BASE}corpus/index.json">Inspect the generated index</a> or <a href="https://github.com/djcdevelopment/baseline/tree/main/corpus">read the corpus contract</a>.</div></footer>
</body></html>"""
    return ascii_html(doc)


def role_chips(roles: list[dict[str, Any]], current: str | None = None) -> str:
    return '<div class="roles">' + "".join(
        f'<a class="chip{" current" if role["id"] == current else ""}" href="{PUBLIC_BASE}for/{e(role["id"])}/">{e(role["short_label"])}</a>'
        for role in roles
    ) + "</div>"


def record_card(record: dict[str, Any]) -> str:
    facet = record.get("facets", {})
    detail = facet.get("status") or record["kind"].replace("-", " ")
    return f'<article class="card"><div class="meta">{e(detail)}</div><h3><a href="{e(record["url"])}">{e(record["title"])}</a></h3><p>{e(record["summary"])}</p></article>'


def role_page(role: dict[str, Any], roles: list[dict[str, Any]], records: list[dict[str, Any]]) -> str:
    role_id = role["id"]
    core = [r for r in records if role_id in r["audiences"] and r["kind"] in {"story", "guide", "portal", "tool"}]
    core.sort(key=lambda r: (role_id not in r["primary_audiences"], {"story": 0, "portal": 1, "guide": 2, "tool": 3}.get(r["kind"], 9), r["title"]))
    recent = [r for r in records if role_id in r["audiences"] and r["kind"] == "roadmap-note"]
    recent.sort(key=lambda r: parse_time(r["published_at"], r["id"]), reverse=True)
    body = f"""<header class="wrap"><div class="eyebrow">A view, not a fence</div><h1>{e(role['label'])}</h1><p class="lede">{e(role['promise'])}</p><p class="note"><strong>Your question:</strong> {e(role['question'])} Start here, then cross the lane whenever something catches your eye.</p></header>
<main class="wrap"><section><h2>Choose another lens</h2>{role_chips(roles, role_id)}</section>
<section><h2>Start in your lane</h2><div class="grid">{''.join(record_card(r) for r in core)}</div></section>
<section><h2>Recent work touching this lane</h2><div class="stream">{''.join(stream_entry(r) for r in recent[:6])}</div><p><a href="{PUBLIC_BASE}explore/">Explore everything, including work outside this lens &rarr;</a></p></section></main>"""
    return page_shell(f"{role['label']} - Baseline", role["promise"], body, f"{PUBLIC_BASE}for/{role_id}/")


def stream_entry(record: dict[str, Any]) -> str:
    when = record.get("published_at") or ""
    date = when[:10] if when else record["kind"]
    return f'<article class="entry"><time datetime="{e(when)}">{e(date)} · {e(record["kind"].replace("-", " "))}</time><h3><a href="{e(record["url"])}">{e(record["title"])}</a></h3><p>{e(record["summary"])}</p></article>'


def explore_page(roles: list[dict[str, Any]], records: list[dict[str, Any]]) -> str:
    core = [r for r in records if r["kind"] in {"story", "guide", "portal", "tool"}]
    core.sort(key=lambda r: ({"story": 0, "portal": 1, "guide": 2, "tool": 3}.get(r["kind"], 9), r["title"]))
    recent = [r for r in records if r["kind"] == "roadmap-note"]
    recent.sort(key=lambda r: parse_time(r["published_at"], r["id"]), reverse=True)
    counts: dict[str, int] = {}
    for record in records:
        counts[record["kind"]] = counts.get(record["kind"], 0) + 1
    tally = " · ".join(f"{counts[key]} {key.replace('-', ' ')}" for key in sorted(counts))
    body = f"""<header class="wrap"><div class="eyebrow">Nothing hidden by the lenses</div><h1>Explore all</h1><p class="lede">Every audience page is a tailored table of contents over this same corpus. This view crosses the lanes; the machine-readable index retains every adapted record.</p><p class="meta">{e(tally)}</p></header>
<main class="wrap"><section><h2>Enter through a lens</h2>{role_chips(roles)}</section><section><h2>Stories, portals, and tools</h2><div class="grid">{''.join(record_card(r) for r in core)}</div></section>
<section><h2>Latest roadmap records</h2><div class="stream">{''.join(stream_entry(r) for r in recent[:25])}</div><p><a href="{AM4_BASE}/roadmap">Read the complete living roadmap &rarr;</a></p></section></main>"""
    return page_shell("Explore all - Baseline", "Cross every audience lane in the Baseline corpus.", body, f"{PUBLIC_BASE}explore/")


def updates_page(records: list[dict[str, Any]], streams: dict[str, Any]) -> str:
    dispatches = [r for r in records if r["kind"] == "dispatch"]
    dispatches.sort(key=lambda r: parse_time(r["published_at"], r["id"]), reverse=True)
    roadmap = [r for r in records if r["kind"] == "roadmap-note"]
    roadmap.sort(key=lambda r: parse_time(r["published_at"], r["id"]), reverse=True)
    dispatch_body = "".join(stream_entry(r) for r in dispatches)
    if not dispatch_body:
        channel_url = (streams.get("dispatches") or {}).get("channel_url")
        channel_link = f' <a href="{e(channel_url)}">Open #dispatches.</a>' if channel_url else ''
        dispatch_body = f'<p class="note">The dedicated Discord dispatch forum is provisioned, but no public starter post has been captured yet. The feed stays empty rather than inventing an update from another source.{channel_link}</p>'
    body = f"""<header class="wrap"><div class="eyebrow">Two authorities, clearly named</div><h1>Updates</h1><p class="lede">Human-facing dispatches originate as tagged Discord forum posts. Engineering history originates in the append-only roadmap journal. They meet here without either becoming the other's source of truth.</p></header>
<main class="wrap"><section><h2>Dispatches from Discord</h2><p><a href="rss.xml">RSS</a> · <a href="feed.json">JSON Feed</a></p><div class="stream">{dispatch_body}</div></section>
<section><h2>Build journal</h2><p class="note">This is implementation evidence, not the editorial feed.</p><div class="stream">{''.join(stream_entry(r) for r in roadmap[:40])}</div><p><a href="{AM4_BASE}/roadmap">Read all roadmap records &rarr;</a></p></section></main>"""
    return page_shell("Updates - Baseline", "Discord dispatches and the Baseline engineering journal, with their authorities kept distinct.", body, f"{PUBLIC_BASE}updates/")


def rss_feed(records: list[dict[str, Any]], fingerprint: str) -> str:
    dispatches = [r for r in records if r["kind"] == "dispatch"]
    dispatches.sort(key=lambda r: parse_time(r["published_at"], r["id"]), reverse=True)
    items = []
    for record in dispatches:
        dt = parse_time(record["published_at"], record["id"])
        items.append(f"<item><guid isPermaLink=\"false\">{e(record['id'])}</guid><title>{e(record['title'])}</title><link>{e(record['url'])}</link><pubDate>{format_datetime(dt)}</pubDate><description>{e(record['summary'])}</description></item>")
    return "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" + (
        f'<rss version="2.0"><channel><title>Baseline dispatches</title><link>{PUBLIC_BASE}updates/</link>'
        f'<description>Public dispatches authored in the Baseline Discord forum.</description><generator>tools/corpus/build.py {fingerprint[:12]}</generator>'
        + "".join(items) + "</channel></rss>\n"
    )


def json_feed(records: list[dict[str, Any]]) -> str:
    dispatches = [r for r in records if r["kind"] == "dispatch"]
    dispatches.sort(key=lambda r: parse_time(r["published_at"], r["id"]), reverse=True)
    doc = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "Baseline dispatches",
        "home_page_url": f"{PUBLIC_BASE}updates/",
        "feed_url": f"{PUBLIC_BASE}updates/feed.json",
        "description": "Public dispatches authored in the Baseline Discord forum.",
        "items": [
            {
                "id": r["id"], "url": r["url"], "title": r["title"],
                "summary": r["summary"], "content_text": r["data"]["content"],
                "date_published": r["published_at"], "date_modified": r["updated_at"],
                "tags": r["data"].get("tags", []),
            }
            for r in dispatches
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def outputs() -> dict[Path, str]:
    index, roles = build_index()
    records = index["records"]
    catalog = read_json(CATALOG_PATH)
    configured = catalog["outputs"]
    built: dict[Path, str] = {
        ROOT / configured["index"]: json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        ROOT / configured["explore"]: explore_page(roles, records),
        ROOT / configured["updates"]: updates_page(records, index["streams"]),
        ROOT / configured["rss"]: rss_feed(records, index["build_fingerprint"]),
        ROOT / configured["json_feed"]: json_feed(records),
    }
    roles_root = ROOT / configured["roles_root"]
    for role in roles:
        built[roles_root / role["id"] / "index.html"] = role_page(role, roles, records)
    return built


def write_outputs(built: dict[Path, str]) -> None:
    for path, content in built.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {rel(path)}")


def check_outputs(built: dict[Path, str]) -> bool:
    stale = []
    for path, expected in built.items():
        actual = path.read_text(encoding="utf-8") if path.exists() else None
        if actual != expected:
            stale.append(rel(path))
    if stale:
        print("stale or missing corpus projections:", file=sys.stderr)
        for path in stale:
            print(f"  {path}", file=sys.stderr)
        print("run: python tools/corpus/build.py", file=sys.stderr)
        return False
    print(f"corpus projections match {len(built)} deterministic outputs")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare committed projections with a clean rebuild")
    args = parser.parse_args(argv)
    try:
        built = outputs()
        if args.check:
            return 0 if check_outputs(built) else 1
        write_outputs(built)
        return 0
    except CorpusError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
