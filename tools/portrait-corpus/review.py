"""Contact-sheet review for the portrait corpus: a local page that walks the concepts, shows
every take as the 128-px bust the archive will actually serve, and writes the human verdict
into picks.json -- the file build_catalog.py --picks reads to flip a concept from
takes.source "auto" to "manual" (FR-7: nothing auto-ranked is published).

    python tools/portrait-corpus/review.py ^
        --corpus E:\\omen\\DMos\\artifacts\\corpus-viking-profiles-20260910 ^
        --concepts docs/design/valheim-portrait-picker-2026-09/concepts.json ^
        --picks docs/design/valheim-portrait-picker-2026-09/picks.json

then open http://127.0.0.1:8790/ . Stdlib only; binds loopback; the PNGs are read from the
corpus and never copied. Every change on the page POSTs the concept's verdict; a bad body is
refused with the reason and nothing is written.

picks.json stays `portrait-corpus-picks/1`: per concept `pick[]` (strip order), `reject[]`,
`why` (the distinct reject reasons, joined) -- plus two keys build_catalog.py ignores,
`reasons` (asset id -> why) and `reviewed_at`. A concept absent from the file keeps its auto
ranking, so a half-finished pass is a valid file at every moment.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
PICKS_SCHEMA = "portrait-corpus-picks/1"
ASSET_NAME = re.compile(r"^[a-z0-9_]+\.png$")
# Catalog rejects a human cannot overrule from this page: the file is unreadable or the
# render dropped its background. `rejected_by_eye` is the previous human verdict and IS
# re-pickable -- that is what a review is for.
HARD_REJECTS = ("corrupt", "bg_dropped")
REASONS = ("no human face", "face too small", "off model", "near-duplicate")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def empty_picks() -> dict:
    return {
        "schema": PICKS_SCHEMA,
        "note": ("Human contact-sheet verdicts. pick = takes a builder may choose, in strip order; "
                 "reject = takes never served, with the reason. Concepts absent here keep their auto "
                 "ranking (concepts.json takes.source = auto) until reviewed. `reasons` and "
                 "`reviewed_at` are review.py's own bookkeeping; build_catalog.py ignores them."),
        "reviewed_by": "review.py",
    }


def assets_by_concept(catalog: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for row in catalog.get("assets", []):
        out.setdefault(row["concept_id"], []).append(row)
    for rows in out.values():
        rows.sort(key=lambda r: r.get("seed_idx", 0))
    return out


def validate_verdict(body: object, rows: list[dict] | None) -> tuple[str | None, dict | None]:
    """Return (error, verdict). `rows` are the catalog rows of the concept the body names.

    Pure so the tests can drive it without a socket. The verdict is the concept entry as it
    will be written: pick, reject, reasons, why, reviewed_at.
    """
    if not isinstance(body, dict):
        return "body must be an object", None
    concept_id = body.get("concept_id")
    if not isinstance(concept_id, str) or not concept_id:
        return "concept_id missing", None
    if rows is None:
        return f"unknown concept {concept_id}", None
    known = {r["asset_id"]: r for r in rows}
    pick = body.get("pick")
    reject = body.get("reject")
    reasons = body.get("reasons") or {}
    if not isinstance(pick, list) or not isinstance(reject, list) or not isinstance(reasons, dict):
        return "pick and reject must be lists, reasons an object", None
    for aid in list(pick) + list(reject):
        if not isinstance(aid, str) or aid not in known:
            return f"{aid!r} is not a take of {concept_id}", None
    if len(set(pick)) != len(pick) or len(set(reject)) != len(reject):
        return "a take is listed twice", None
    both = set(pick) & set(reject)
    if both:
        return f"picked and rejected at once: {sorted(both)}", None
    for aid in pick:
        hard = [why for why in known[aid].get("reject", []) if why in HARD_REJECTS]
        if hard:
            return f"{aid} cannot be picked: the catalog marks it {', '.join(hard)}", None
    if not pick:
        return "at least one take must be picked", None
    clean_reasons = {}
    for aid in reject:
        why = reasons.get(aid)
        if not isinstance(why, str) or not why.strip():
            return f"{aid} is rejected without a reason", None
        clean_reasons[aid] = why.strip()
    distinct = []
    for why in clean_reasons.values():
        if why not in distinct:
            distinct.append(why)
    verdict = {
        "pick": list(pick),
        "reject": list(reject),
        "why": " · ".join(distinct),
        "reasons": clean_reasons,
        "reviewed_at": now_iso(),
    }
    return None, verdict


def merge_verdict(picks: dict, concept_id: str, verdict: dict | None) -> dict:
    """A new picks document with this concept's verdict set (or removed when None)."""
    out = {k: v for k, v in picks.items()}
    out.setdefault("schema", PICKS_SCHEMA)
    if verdict is None:
        out.pop(concept_id, None)
    else:
        out[concept_id] = verdict
    return out


def write_atomic(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(doc, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def reviewed_count(picks: dict) -> int:
    return sum(1 for v in picks.values() if isinstance(v, dict) and v.get("pick"))


class ReviewState:
    """What the handler shares: the catalog rows per concept and the picks file, under a lock
    so two quick verdicts from the page cannot interleave their writes."""

    def __init__(self, corpus: Path, concepts_path: Path, picks_path: Path):
        self.corpus = corpus
        self.assets_dir = corpus / "assets"
        self.catalog_path = corpus / "catalog.json"
        self.concepts_path = concepts_path
        self.picks_path = picks_path
        self.lock = threading.Lock()
        catalog = load_json(self.catalog_path)
        self.rows = assets_by_concept(catalog)
        self.picks = load_json(picks_path) if picks_path.is_file() else empty_picks()
        if self.picks.get("schema") != PICKS_SCHEMA:
            raise SystemExit(f"{picks_path} declares schema {self.picks.get('schema')!r}, expected {PICKS_SCHEMA!r}")

    def apply(self, body: object) -> tuple[int, dict]:
        concept_id = body.get("concept_id") if isinstance(body, dict) else None
        if isinstance(body, dict) and body.get("clear") is True and isinstance(concept_id, str):
            with self.lock:
                self.picks = merge_verdict(self.picks, concept_id, None)
                write_atomic(self.picks_path, self.picks)
                return HTTPStatus.OK, {"ok": True, "concept_id": concept_id, "cleared": True,
                                       "reviewed": reviewed_count(self.picks)}
        error, verdict = validate_verdict(body, self.rows.get(concept_id) if isinstance(concept_id, str) else None)
        if error:
            return HTTPStatus.BAD_REQUEST, {"ok": False, "error": error}
        with self.lock:
            self.picks = merge_verdict(self.picks, concept_id, verdict)
            write_atomic(self.picks_path, self.picks)
            return HTTPStatus.OK, {"ok": True, "concept_id": concept_id, "verdict": verdict,
                                   "reviewed": reviewed_count(self.picks)}


def make_handler(state: ReviewState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "portrait-review/1"

        def log_message(self, fmt, *args):  # quiet: the page polls nothing, so log only writes
            if self.command == "POST":
                sys.stderr.write("%s %s\n" % (self.command, fmt % args))

        def _send(self, status: int, body: bytes, ctype: str, cache: str = "no-store") -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, doc: object) -> None:
            self._send(status, json.dumps(doc, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            path = urlsplit(self.path).path
            if path in ("/", "/index.html"):
                return self._send(HTTPStatus.OK, (HERE / "review.html").read_bytes(), "text/html; charset=utf-8")
            if path == "/catalog.json":
                return self._send(HTTPStatus.OK, state.catalog_path.read_bytes(), "application/json; charset=utf-8")
            if path == "/concepts.json":
                return self._send(HTTPStatus.OK, state.concepts_path.read_bytes(), "application/json; charset=utf-8")
            if path == "/picks.json":
                with state.lock:
                    return self._json(HTTPStatus.OK, state.picks)
            if path.startswith("/assets/"):
                name = path[len("/assets/"):]
                if not ASSET_NAME.match(name):
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "no such asset"})
                file = state.assets_dir / name
                if not file.is_file():
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "no such asset"})
                # The corpus is immutable by construction (sha-verified receipts), so the
                # browser may keep the PNGs for the whole session.
                return self._send(HTTPStatus.OK, file.read_bytes(), "image/png", cache="max-age=86400")
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self):
            path = urlsplit(self.path).path
            if path != "/picks":
                return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8") or "null")
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                return self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": f"body is not JSON: {exc}"})
            status, doc = state.apply(body)
            return self._json(status, doc)

    return Handler


def serve(state: ReviewState, host: str, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(state))
    server.daemon_threads = True
    return server


def rebuild_hint(state: ReviewState, concepts_path: Path, picks_path: Path) -> str:
    corpus = state.corpus
    return (
        "When the pass is done, re-catalog so the reviewed concepts flip to source: manual "
        "(face and attributes must ride along or the bust crops and picker tags are lost):\n"
        f"  python tools/portrait-corpus/build_catalog.py --corpus {corpus} "
        f"--face-qa {corpus / 'face_qa.json'} --attributes {corpus / 'attributes.json'} "
        f"--picks {picks_path} --out-concepts {concepts_path}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus", type=Path, required=True, help="corpus root holding catalog.json and assets/")
    parser.add_argument("--concepts", type=Path, required=True, help="concepts.json (read: order, tags, auto picks)")
    parser.add_argument("--picks", type=Path, required=True, help="picks.json to write (created when absent)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args(argv)

    state = ReviewState(args.corpus, args.concepts, args.picks)
    server = serve(state, args.host, args.port)
    total = len(state.rows)
    print(f"portrait review at http://{args.host}:{server.server_address[1]}/  "
          f"({reviewed_count(state.picks)} of {total} concepts reviewed; writes {args.picks})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print(f"\n{reviewed_count(state.picks)} of {total} concepts reviewed.")
        print(rebuild_hint(state, args.concepts, args.picks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
