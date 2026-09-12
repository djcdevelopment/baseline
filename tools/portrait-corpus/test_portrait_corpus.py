"""Offline tests for the portrait-corpus tooling. No corpus, no door, no E:\\ -- a synthetic
receipts.ndjson and four tiny PNGs stand in for the real thing.

    python -m pytest tools/portrait-corpus/test_portrait_corpus.py -q
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_catalog  # noqa: E402
import extract_attributes  # noqa: E402

VOCAB = json.loads((HERE / "vocab.json").read_text(encoding="utf-8"))


def _png(path: Path, colour, white_patch: bool = False, size: int = 1024) -> None:
    im = Image.new("RGB", (size, size), colour)
    if white_patch:
        im.paste((255, 255, 255), (0, size // 2, size, size))
    im.save(path)


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    assets = tmp_path / "assets"
    assets.mkdir()
    rows = []
    concept = "viking_carpenter_f_artisan"
    for n in range(1, 5):
        aid = f"{concept}_s{n}"
        p = assets / f"{aid}.png"
        _png(p, (90, 70, 50), white_patch=(n == 4))
        rows.append({
            "asset_id": aid, "concept_id": concept, "character_name": "Astrid the Beam-Carver",
            "discipline": "Carpenter", "gender": "Female", "aspect": "Square (1:1)", "width": 1024, "height": 1024,
            "seed": 1000 + n, "seed_idx": n, "steps": 18, "job_id": f"job_{n}", "lane": "b70@bus4",
            "duration_seconds": 18.9, "batch": "Viking Builder Profiles", "created_at": "2026-09-10T23:10:55Z",
            "asset_path": str(p), "sha256": build_catalog.hashlib.sha256(p.read_bytes()).hexdigest(),
            "prompt": "Waist-up profile portrait of a skilled female Viking timber joiner. Confident proud expression, auburn hair.",
        })
    # a corrupt take: the receipt sha matches the bad bytes, as in the real corpus
    bad = assets / f"{concept}_s5.png"
    bad.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    rows.append({**rows[0], "asset_id": f"{concept}_s5", "seed_idx": 5, "seed": 1005, "job_id": "job_5",
                 "asset_path": str(bad), "sha256": build_catalog.hashlib.sha256(bad.read_bytes()).hexdigest()})
    (tmp_path / "receipts.ndjson").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return tmp_path


def test_slug_and_theme():
    assert build_catalog.parse_slug("viking_harbor_m_dockmaster") == {"archetype": "harbor", "gender_code": "m", "variant": "dockmaster"}
    assert build_catalog.theme_for("Viking Lore & Hearth") == "lore-hearth"
    with pytest.raises(ValueError):
        build_catalog.parse_slug("viking_nonsense")


def test_vocab_roles_cover_every_receipt_label():
    labels = {v["receipt_label"] for v in VOCAB["role"].values()}
    assert len(VOCAB["role"]) == 24 and len(labels) == 24
    assert all(v["label"] for v in VOCAB["role"].values())
    assert {f["tag"] for f in VOCAB["facets"]["order"]} <= set(VOCAB) | {"role", "theme"}


def test_build_catalog_flags_corrupt_and_bg_dropped(corpus: Path, tmp_path: Path):
    out_concepts = tmp_path / "concepts.json"
    r = subprocess.run([sys.executable, str(HERE / "build_catalog.py"), "--corpus", str(corpus),
                        "--out-concepts", str(out_concepts)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    cat = json.loads((corpus / "catalog.json").read_text(encoding="utf-8"))
    by = {a["asset_id"]: a for a in cat["assets"]}
    assert cat["n_assets"] == 5 and cat["n_usable"] == 3
    assert by["viking_carpenter_f_artisan_s5"]["reject"] == ["corrupt"]
    assert by["viking_carpenter_f_artisan_s5"]["sha256_verified"] is True   # sha cannot catch a corrupt render
    assert by["viking_carpenter_f_artisan_s4"]["reject"] == ["bg_dropped"]
    assert by["viking_carpenter_f_artisan_s1"]["reject"] == []
    doc = json.loads(out_concepts.read_text(encoding="utf-8"))
    c = doc["concepts"][0]
    assert c["role"] == "carpenter" and c["presentation"] == "woman" and c["theme"] == "builders"
    assert c["n_takes"] == 5 and c["n_usable"] == 3
    assert set(c["takes"]["picked"]) == {"viking_carpenter_f_artisan_s1", "viking_carpenter_f_artisan_s2", "viking_carpenter_f_artisan_s3"}
    assert {r["asset_id"] for r in c["takes"]["rejected"]} == {"viking_carpenter_f_artisan_s4", "viking_carpenter_f_artisan_s5"}


def test_picks_override_and_rejected_by_eye(corpus: Path, tmp_path: Path):
    picks = tmp_path / "picks.json"
    picks.write_text(json.dumps({"schema": "x", "note": "y", "viking_carpenter_f_artisan": {
        "pick": ["viking_carpenter_f_artisan_s3"], "reject": ["viking_carpenter_f_artisan_s1"], "why": "test"}}), encoding="utf-8")
    out_concepts = tmp_path / "concepts.json"
    r = subprocess.run([sys.executable, str(HERE / "build_catalog.py"), "--corpus", str(corpus),
                        "--out-concepts", str(out_concepts), "--picks", str(picks)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    c = json.loads(out_concepts.read_text(encoding="utf-8"))["concepts"][0]
    assert c["takes"]["source"] == "manual" and c["takes"]["picked"] == ["viking_carpenter_f_artisan_s3"]
    assert any(r["asset_id"].endswith("_s1") and r["why"] == ["rejected_by_eye"] for r in c["takes"]["rejected"])


def test_rank_takes_alternates_facing():
    rows = [
        {"asset_id": "a", "face": {"confidence": 3, "frac": 0.2, "cx_offset": 0.0, "facing": "left"}, "white_excess": 0.0, "border_z": 0},
        {"asset_id": "b", "face": {"confidence": 3, "frac": 0.2, "cx_offset": 0.01, "facing": "left"}, "white_excess": 0.0, "border_z": 0},
        {"asset_id": "c", "face": {"confidence": 3, "frac": 0.2, "cx_offset": 0.02, "facing": "right"}, "white_excess": 0.0, "border_z": 0},
        {"asset_id": "d", "face": {"confidence": 1, "frac": 0.2, "cx_offset": 0.0, "facing": "left"}, "white_excess": 0.0, "border_z": 0},
    ]
    assert build_catalog.rank_takes(rows, 2) == ["a", "c"]            # one of each facing before a second left
    assert build_catalog.rank_takes(rows, 4) == ["a", "b", "c", "d"]  # each facing may fill half the strip


def test_parse_array_salvages_truncated_reply():
    good = '[{"concept_id":"x","age":"elder"},{"concept_id":"y","age":"young"}]'
    items, truncated = extract_attributes.parse_array("```json\n" + good + "\n```")
    assert [i["concept_id"] for i in items] == ["x", "y"] and truncated is False
    cut = '[{"concept_id":"x","age":"elder"},{"concept_id":"y","age":"you'
    items, truncated = extract_attributes.parse_array(cut)
    assert [i["concept_id"] for i in items] == ["x"] and truncated is True


def test_ingest_validates_against_vocab(tmp_path: Path):
    concepts = [{"concept_id": "viking_carpenter_f_artisan", "prompt": "p"}]
    work = tmp_path / "work"
    extract_attributes.prepare(concepts, work, 12)
    reply = [{"concept_id": "viking_carpenter_f_artisan", "age": "unspecified", "hair": "auburn", "hair_style": "braided",
              "beard": "none", "mood": "proud", "setting": "workshop", "palette": "ember", "kit": "civilian",
              "companion": "unspecified", "headwear": "none", "magic": "false", "face_paint": False, "props": ["adze", "try-square"]}]
    (work / "batch-1.result.json").write_text(json.dumps({"ok": True, "text": json.dumps(reply), "backend": "gcp-gemini",
                                                          "model": "gemini-3.5-flash"}), encoding="utf-8")
    out = tmp_path / "attributes.json"
    rc = extract_attributes.ingest(concepts, work, out)
    doc = json.loads(out.read_text(encoding="utf-8"))
    row = doc["concepts"][0]
    assert row["age"] == "adult" and "age" in row["defaulted"]          # unspecified -> axis default
    assert row["companion"] == "none" and row["magic"] is False
    assert row["hair"] == "brown"                                          # off-vocabulary "auburn" -> default + review
    assert rc == 2 and any(r.get("axis") == "hair" and r["value"] == "auburn" for r in doc["review"])


# ---- review.py: the contact-sheet pass ----------------------------------------------------

import threading  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402

import review  # noqa: E402


def _catalogued(corpus: Path, tmp_path: Path) -> Path:
    """The synthetic corpus with catalog.json + concepts.json built the ordinary way."""
    out_concepts = tmp_path / "concepts.json"
    r = subprocess.run([sys.executable, str(HERE / "build_catalog.py"), "--corpus", str(corpus),
                        "--out-concepts", str(out_concepts)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return out_concepts


def _post(url: str, body: object) -> tuple[int, dict]:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_review_refuses_bad_verdicts_and_writes_nothing(corpus: Path, tmp_path: Path):
    concepts = _catalogued(corpus, tmp_path)
    picks = tmp_path / "picks.json"
    state = review.ReviewState(corpus, concepts, picks)
    c = "viking_carpenter_f_artisan"
    a = lambda n: f"{c}_s{n}"  # noqa: E731
    bad = [
        ({"concept_id": "viking_nobody_m_x", "pick": [a(1)], "reject": []}, "unknown concept"),
        ({"concept_id": c, "pick": ["viking_miner_m_prospector_s1"], "reject": []}, "is not a take of"),
        ({"concept_id": c, "pick": [a(1)], "reject": [a(1)], "reasons": {a(1): "x"}}, "picked and rejected at once"),
        ({"concept_id": c, "pick": [], "reject": [a(1)], "reasons": {a(1): "x"}}, "at least one take"),
        ({"concept_id": c, "pick": [a(1)], "reject": [a(2)]}, "without a reason"),
        ({"concept_id": c, "pick": [a(5)], "reject": []}, "cannot be picked"),   # corrupt in the catalog
        ({"concept_id": c, "pick": [a(4)], "reject": []}, "cannot be picked"),   # bg_dropped
        ({"concept_id": c, "pick": [a(1), a(1)], "reject": []}, "listed twice"),
        ("nonsense", "must be an object"),
    ]
    for body, needle in bad:
        status, doc = state.apply(body)
        assert status == 400 and needle in doc["error"], (body, doc)
    assert not picks.exists(), "a refused verdict must not create or touch picks.json"


def test_review_round_trip_lands_in_build_catalog_as_manual(corpus: Path, tmp_path: Path):
    concepts = _catalogued(corpus, tmp_path)
    picks = tmp_path / "picks.json"
    state = review.ReviewState(corpus, concepts, picks)
    server = review.serve(state, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        c = "viking_carpenter_f_artisan"
        # The page itself, the catalog and a PNG are served; a path outside assets/ is not.
        with urllib.request.urlopen(base + "/", timeout=5) as resp:
            assert resp.status == 200 and b"Portrait review" in resp.read()
        with urllib.request.urlopen(base + f"/assets/{c}_s1.png", timeout=5) as resp:
            assert resp.headers["Content-Type"] == "image/png"
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(base + "/assets/../receipts.ndjson", timeout=5)
        status, doc = _post(base + "/picks", {"concept_id": c, "pick": [f"{c}_s3", f"{c}_s1"],
                                              "reject": [f"{c}_s2"], "reasons": {f"{c}_s2": "off model"}})
        assert status == 200 and doc["ok"] and doc["reviewed"] == 1, doc
        written = json.loads(picks.read_text(encoding="utf-8"))
        assert written["schema"] == review.PICKS_SCHEMA
        entry = written[c]
        assert entry["pick"] == [f"{c}_s3", f"{c}_s1"] and entry["reject"] == [f"{c}_s2"]
        assert entry["why"] == "off model" and entry["reasons"] == {f"{c}_s2": "off model"} and entry["reviewed_at"]
        # GET /picks.json reflects the write; a clear removes the concept and leaves the file valid.
        with urllib.request.urlopen(base + "/picks.json", timeout=5) as resp:
            assert c in json.loads(resp.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
    # build_catalog.py reads the verdict as a manual strip in the order the human set.
    out = tmp_path / "concepts-after.json"
    r = subprocess.run([sys.executable, str(HERE / "build_catalog.py"), "--corpus", str(corpus),
                        "--out-concepts", str(out), "--picks", str(picks)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    after = json.loads(out.read_text(encoding="utf-8"))["concepts"][0]
    assert after["takes"]["source"] == "manual"
    assert after["takes"]["picked"] == [f"{c}_s3", f"{c}_s1"]
    assert any(x["asset_id"] == f"{c}_s2" and "rejected_by_eye" in x["why"] for x in after["takes"]["rejected"])
    # And a clear puts it back to auto.
    state2 = review.ReviewState(corpus, concepts, picks)
    status, doc = state2.apply({"concept_id": c, "clear": True})
    assert status == 200 and doc["cleared"] and c not in json.loads(picks.read_text(encoding="utf-8"))
