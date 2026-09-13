#!/usr/bin/env python3
"""Judge a candidate pose before the shutter, from the pieces alone.

frame_forecast.py already reprojects a build's point set through a pose and reports how much
of the frame it fills. This lifts that into a per-candidate callable the planner can run over
every pose it considers, adds the two things the 2026-09-12 light table said the eye
rewards and the geometry can see -- sky above the subject, and a bearing on the build's true
long axis -- and gives each candidate one bounded rank so a planner can keep the top few.

Harvested from deepagents-shot-director (`director/positioning.py`,
`director/typology_classifier.py`), rewritten without numpy so it runs wherever the
planner does; the typology profiles are copied verbatim. The rank is a v0: it orders
candidates, it does not certify them. The light table does that, and a fitted critic
replaces this order when ~150 decided pairs exist.

Pure functions only. No duckdb, no image, no game.
"""
import math

import frame_forecast   # project / coverage / camera_basis / mass_radii: pure

# The eye kept frames with more sky 58 % of the time; past this much of the frame the
# veto already calls it "aiming at air".
SKY_TARGET = 0.25
SKY_CEILING = 0.60

# Typology -> camera modulation, verbatim from typology_classifier.py.
PROFILES = {
    "SpireOrTower": {"elevationDeg": 20.0, "aimHeightRatio": 0.32, "standoffM": 90.0, "margin": 1.20,
                     "intent": "heroic verticality; low elevation looking up against the sky"},
    "LonghouseHall": {"elevationDeg": 32.0, "aimHeightRatio": 0.40, "standoffM": 110.0, "margin": 1.15,
                      "intent": "corner facade; reveal the long roofline and the gable"},
    "SprawlingCompound": {"elevationDeg": 46.0, "aimHeightRatio": 0.50, "standoffM": 180.0, "margin": 1.12,
                          "intent": "high overview; the layout, courtyards, the settlement"},
    "SkyPlatform": {"elevationDeg": 16.0, "aimHeightRatio": 0.20, "standoffM": 120.0, "margin": 1.18,
                    "intent": "horizon level; silhouette, not cloud void"},
    "HomesteadVilla": {"elevationDeg": 35.0, "aimHeightRatio": 0.42, "standoffM": 100.0, "margin": 1.15,
                       "intent": "three-quarter view; landscape setting and craft"},
    "CompactOutpost": {"elevationDeg": 36.0, "aimHeightRatio": 0.45, "standoffM": 65.0, "margin": 1.20,
                       "intent": "close and intimate; frontier craftsmanship"},
}


def typology(size_x, size_y, size_z, pieces, min_y=0.0):
    """classify_cluster_morphology, unchanged."""
    length = max(size_x, size_z)
    width = max(min(size_x, size_z), 1.0)
    height = size_y
    diagonal = math.sqrt(length * length + width * width)
    if min_y > 400.0:
        return "SkyPlatform"
    if (height / max(length, 1.0) > 0.82) or (height > 40.0 and length < 32.0):
        return "SpireOrTower"
    if pieces >= 4000 or length * width >= 7500.0 or diagonal >= 135.0:
        return "SprawlingCompound"
    if length / width >= 1.7 and height >= 5.0:
        return "LonghouseHall"
    if pieces >= 1200:
        return "HomesteadVilla"
    return "CompactOutpost"


def pca_orientation(points):
    """Horizontal principal axis of a point set: the bearing a longhouse actually faces.

    A 2x2 covariance has a closed-form eigenvector, so no numpy is needed. Angles are
    clockwise from +Z in degrees, the convention plan_shots and the receipts share."""
    n = float(len(points))
    if not n:
        raise ValueError("no points")
    cx = sum(p[0] for p in points) / n
    cy = sum(p[1] for p in points) / n
    cz = sum(p[2] for p in points) / n
    sxx = sum((p[0] - cx) ** 2 for p in points) / n
    szz = sum((p[2] - cz) ** 2 for p in points) / n
    sxz = sum((p[0] - cx) * (p[2] - cz) for p in points) / n
    # Largest eigenvalue of [[sxx, sxz], [sxz, szz]] and its eigenvector.
    trace, det = sxx + szz, sxx * szz - sxz * sxz
    lam = trace / 2.0 + math.sqrt(max(0.0, trace * trace / 4.0 - det))
    if abs(sxz) > 1e-9:
        vx, vz = lam - szz, sxz
    elif sxx >= szz:
        vx, vz = 1.0, 0.0
    else:
        vx, vz = 0.0, 1.0
    norm = math.hypot(vx, vz) or 1.0
    vx, vz = vx / norm, vz / norm
    along = [(p[0] - cx) * vx + (p[2] - cz) * vz for p in points]
    across = [-(p[0] - cx) * vz + (p[2] - cz) * vx for p in points]
    length = max(along) - min(along)
    width = max(across) - min(across)
    ys = [p[1] for p in points]
    principal = math.degrees(math.atan2(vx, vz)) % 360.0
    return {"centroid": (round(cx, 2), round(cy, 2), round(cz, 2)),
            "principalAngleDeg": round(principal, 2), "facadeAngleDeg": round((principal + 90.0) % 360.0, 2),
            "obbLength": round(length, 2), "obbWidth": round(width, 2), "height": round(max(ys) - min(ys), 2),
            "minY": round(min(ys), 2), "eccentricity": round(length / max(width, 1.0), 2)}


def sky_band(projected):
    """Share of the frame's height above the subject's projected top: sky, unless terrain
    rises behind it -- which the pose cannot know, and the veto later will."""
    tops = [sy for _, sy, _ in projected if abs(sy) <= 1.0]
    if not tops:
        return 0.0
    top = max(tops)                       # +1 is the top edge of the frame
    return round(max(0.0, (1.0 - top) / 2.0), 4)


def forecast(points, cam, aim):
    """Everything geometry can say about one candidate pose, plus one bounded rank."""
    projected = frame_forecast.project(points, cam, aim)
    cover = frame_forecast.coverage(projected, len(points))
    sky = sky_band(projected)
    # Full framing first (nothing cropped, the mass visible), then sky near the target
    # band; a pose that shows only air is already the veto's business.
    sky_term = 1.0 - min(1.0, abs(sky - SKY_TARGET) / SKY_TARGET) if sky <= SKY_CEILING else 0.0
    rank = round(cover["inFrameFraction"] * math.sqrt(max(cover["bboxFill"], 0.0)) * (0.6 + 0.4 * sky_term), 5)
    return {**cover, "skyBand": sky, "rank": rank}


def bearings(orientation, extra=()):
    """Where to stand: the facade corners the long axis implies, plus any the caller adds."""
    facade = orientation["facadeAngleDeg"]
    out = [(facade + 45.0) % 360.0, (facade - 45.0) % 360.0]
    for angle in extra:
        if all(abs(((angle - o + 180.0) % 360.0) - 180.0) > 10.0 for o in out):
            out.append(angle % 360.0)
    return out
