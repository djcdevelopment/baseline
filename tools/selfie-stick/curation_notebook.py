import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Selfie-stick curation")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Selfie-stick curation bench

        Every frame carries three instruments: the **LAION aesthetic** (taste),
        the **depth layers** (geometry — does the frame have near/mid/far, or is
        the camera against a wall), and the **VLM judge** (a rubric reading of
        "does this feel like you're in the scene"). None of them is the verdict;
        your eye is. This bench lets you move the thresholds and watch who
        survives.

        Run it with `marimo run curation_notebook.py` (or `marimo edit` to
        change it) from the omen-perception venv.
        """
    )
    return


@app.cell
def _():
    import base64
    import json
    import os

    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "out")

    def load(name, default):
        p = os.path.join(OUT, name)
        if not os.path.exists(p):
            return default
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)

    index = load(os.path.join("gallery", "index.json"), {"images": []})
    aesthetic = {k: v.get("aesthetic") for k, v in load("aesthetic.json", {}).items()}
    depth = load("depth.json", {})
    judge = load("judge.json", {})

    def thumb_uri(image_id):
        p = os.path.join(OUT, "gallery", "thumb", image_id + ".webp")
        if not os.path.exists(p):
            return None
        with open(p, "rb") as fh:
            return "data:image/webp;base64," + base64.b64encode(fh.read()).decode()

    return aesthetic, depth, index, judge, thumb_uri


@app.cell
def _(index, mo):
    _variants = sorted({r.get("variant") or "?" for r in index["images"]})
    variant = mo.ui.dropdown(
        options=_variants,
        value="seat_night" if "seat_night" in _variants else _variants[0],
        label="cell (vantage × condition)",
    )
    veto = mo.ui.slider(0.0, 1.0, step=0.05, value=0.45,
                        label="depth veto: max center_block")
    judge_weight = mo.ui.slider(0.0, 1.0, step=0.1, value=0.7,
                                label="rank weight: judge vs aesthetic")
    top_n = mo.ui.slider(3, 24, step=3, value=9, label="frames shown")
    mo.hstack([variant, veto, judge_weight, top_n], wrap=True)
    return judge_weight, top_n, variant, veto


@app.cell
def _(aesthetic, depth, index, judge, judge_weight, mo, thumb_uri, top_n, variant, veto):
    import html as _html

    _rows = [r for r in index["images"] if (r.get("variant") or "?") == variant.value]

    def _norm(vals):
        xs = [v for v in vals if v is not None]
        if not xs or max(xs) == min(xs):
            return lambda v: 0.5
        lo, hi = min(xs), max(xs)
        return lambda v: 0.5 if v is None else (v - lo) / (hi - lo)

    _na = _norm([aesthetic.get(r["id"]) for r in _rows])
    _nj = _norm([judge.get(r["id"], {}).get("score") for r in _rows])

    _kept, _cut = [], 0
    for _r in _rows:
        _d = depth.get(_r["id"], {})
        if _d.get("center_block", 0) > veto.value:
            _cut += 1
            continue
        _a = aesthetic.get(_r["id"])
        _j = judge.get(_r["id"], {}).get("score")
        _rank = judge_weight.value * _nj(_j) + (1 - judge_weight.value) * _na(_a)
        _kept.append((_rank, _r, _a, _j, _d))
    _kept.sort(key=lambda t: t[0], reverse=True)

    def _card(rank, r, a, j, d):
        src = thumb_uri(r["id"])
        if not src:
            return ""
        reason = _html.escape(judge.get(r["id"], {}).get("reason", ""))
        return (
            f"<div style='background:#1b2129;border-radius:8px;overflow:hidden'>"
            f"<img src='{src}' style='width:100%;display:block'>"
            f"<div style='padding:6px 9px;font-size:12px;line-height:1.35;color:#d8dee6'>"
            f"<b>{_html.escape(str(r.get('label')))}</b><br>"
            f"<span style='color:#8a95a5'>rank {rank:.2f} · judge {j if j is not None else '—'}"
            f" · laion {a if a is not None else '—'}"
            f" · block {d.get('center_block', '—')}</span><br>"
            f"<i style='color:#a9b4c4'>{reason}</i></div></div>"
        )

    _grid = "".join(_card(*t) for t in _kept[: top_n.value])
    mo.Html(
        f"<p style='color:#8a95a5;font-size:13px'>{len(_kept)} candidates, "
        f"{_cut} vetoed by depth in this cell</p>"
        f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px'>{_grid}</div>"
    )
    return


@app.cell
def _(aesthetic, depth, index, judge, mo, thumb_uri):
    # The frame rides IN the dataframe (marimo renders images in table cells),
    # so sorting by any instrument reorders pictures, not ids.
    _rows = []
    for _r in index["images"]:
        _i = _r["id"]
        if _i not in depth and _i not in judge:
            continue
        _uri = thumb_uri(_i)
        _rows.append({
            "frame": mo.image(src=_uri, height=72) if _uri else None,
            "label": _r.get("label"),
            "variant": _r.get("variant"),
            "judge": judge.get(_i, {}).get("score"),
            "aesthetic": aesthetic.get(_i),
            "center_block": depth.get(_i, {}).get("center_block"),
            "far_mass": depth.get(_i, {}).get("far_mass"),
            "depth_score": depth.get(_i, {}).get("depth_score"),
            "why": judge.get(_i, {}).get("reason"),
            "id": _i,
        })
    mo.vstack([
        mo.md(f"### All measured frames ({len(_rows)}) — sortable, images inline"),
        mo.ui.table(_rows, page_size=12),
    ])
    return


if __name__ == "__main__":
    app.run()
