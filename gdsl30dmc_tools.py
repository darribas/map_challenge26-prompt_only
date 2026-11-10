"""Shared tooling for the #30DayMapChallenge Day 10 notebooks.

Data loading and contiguity for Imago's small-area AlphaEarth embeddings, plus the Imago-styled
Polaroid cards (satellite photo of highlighted areas, caption strip, UK locator).
"""
from pathlib import Path

import contextily as cx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
from libpysal import graph
from matplotlib import font_manager
from matplotlib import patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"
FONT_DIR = ROOT / "fonts"

# --- Data ---------------------------------------------------------------------------------------


def load_areas(year=2024):
    """Small areas (LSOAs / Data Zones / SDZs) with their 64 mean embedding bands, indexed by area code."""
    areas = gpd.read_file(DATA_DIR / f"extracted-lsoa-geopackage_{year}_output.gpkg")
    return areas.set_index("data_zone_code")


def band_columns(areas):
    return [c for c in areas.columns if c.startswith("band")]


def nation(areas):
    """First letter of the area code: E(ngland), W(ales), S(cotland), N(orthern Ireland)."""
    return pd.Series(areas.index.str[0], index=areas.index)


def contiguity(areas):
    """Neighbour graph: polygons that touch or overlap.

    Fuzzy contiguity equals queen contiguity plus pairs whose polygons overlap, which recovers the
    England–Scotland border links that queen contiguity misses (the two nations' polygons overlap there).
    """
    return graph.Graph.build_fuzzy_contiguity(areas)


def drop_isolates(areas, g):
    """Remove areas with no neighbours from both the table and the graph."""
    areas = areas.drop(g.isolates)
    return areas, g.subgraph(areas.index)


def uk_outline(areas, cache=DATA_DIR / "uk_outline.parquet"):
    """Simplified UK silhouette, built from the areas once and cached to disk.

    Each nation is merged with GEOS's fast coverage union, which needs polygons that tile without gaps or
    overlaps; when that fails (Northern Ireland), it falls back to a standard union of lightly simplified
    polygons. Holes and parts under 20 km² are dropped, then the result is simplified by 1.5 km.
    """
    if cache is not None and Path(cache).exists():
        return gpd.read_parquet(cache).geometry

    def merge(geoms):
        try:
            return shapely.coverage_union_all(geoms)
        except shapely.errors.GEOSException:  # polygons not cleanly tiled
            return shapely.union_all(shapely.simplify(geoms, 200))

    merged = shapely.union_all([merge(sub.values) for _, sub in areas.geometry.groupby(nation(areas))])
    outline = gpd.GeoSeries([shapely.MultiPolygon([
        shapely.Polygon(p.exterior).simplify(1500) for p in shapely.get_parts(merged) if p.area > 20e6
    ])], crs=areas.crs)
    if cache is not None:
        outline.to_frame("geometry").to_parquet(cache)
    return outline


def pair_distances(areas=None, g=None, cache=DATA_DIR / "pair_distances_2024.parquet"):
    """Cosine distance for every neighbouring pair (each pair once, a < b), cached to disk.

    Without `areas` and `g`, loads the cache (or builds it from the 2024 data, dropping isolates).
    """
    if cache is not None and Path(cache).exists():
        return pd.read_parquet(cache)["dist"]
    if areas is None or g is None:
        areas = load_areas()
        areas, g = drop_isolates(areas, contiguity(areas))
    adj = g.adjacency.reset_index()
    adj = adj[adj["focal"] < adj["neighbor"]]
    emb = areas[band_columns(areas)].to_numpy()
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
    pos = pd.Series(np.arange(len(areas)), index=areas.index)
    dist = 1 - (emb[pos[adj["focal"]]] * emb[pos[adj["neighbor"]]]).sum(axis=1)
    out = pd.Series(dist, index=pd.MultiIndex.from_arrays([adj["focal"], adj["neighbor"]], names=["a", "b"]),
                    name="dist")
    if cache is not None:
        out.to_frame().to_parquet(cache)
    return out


def neighbourhood_distances(areas=None, g=None, cache=DATA_DIR / "neighbourhood_distances_2024.parquet"):
    """Per-area `mean_dist` (average cosine distance to each neighbour) and `lag_dist` (cosine distance to the
    average neighbour, i.e. the spatial lag on the row-standardised graph), cached to disk.

    Without `areas` and `g`, loads the cache (or builds it from the 2024 data, dropping isolates).
    """
    if cache is not None and Path(cache).exists():
        return pd.read_parquet(cache)
    if areas is None or g is None:
        areas = load_areas()
        areas, g = drop_isolates(areas, contiguity(areas))
    emb = np.ascontiguousarray(areas[band_columns(areas)].to_numpy())
    lag = g.transform("r").lag(emb)
    unit = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
    pairs = pair_distances(areas, g)
    both = pd.concat([pairs.reset_index(), pairs.reset_index().rename(columns={"a": "b", "b": "a"})])
    out = pd.DataFrame({
        "mean_dist": both.groupby("a")["dist"].mean().reindex(areas.index),
        "lag_dist": 1 - (unit(emb) * unit(lag)).sum(axis=1),
    }, index=areas.index)
    if cache is not None:
        out.to_parquet(cache)
    return out


# --- Polaroid cards ------------------------------------------------------------------------------

# Official Imago palette (brand guidelines); "imago_grey" is the Imago data service colour
IMAGO = {"navy": "#24226F", "grey": "#B8BCD1", "green": "#03CEA3", "orange": "#FF8F42",
         "light_grey": "#E2E5F3", "blue": "#1877CF", "dark_grey": "#8C91A8", "white": "#FFFFFF",
         "imago_grey": "#4A4A49"}
WASH = 0.55  # share of white blended into imagery outside the highlighted areas

# Imago's brand font, Figtree (static TTFs from github.com/erikdkennedy/figtree, OFL licence)
for weight in ["Regular", "Bold"]:
    font_manager.fontManager.addfont(str(FONT_DIR / f"Figtree-{weight}.ttf"))
TEXT = dict(family="Figtree", weight="bold", color=IMAGO["imago_grey"])
# Typewriter faces for the haiku caption: Special Elite (Apache licence) and Courier Prime (OFL), from github.com/google/fonts
for name in ["SpecialElite-Regular", "CourierPrime-Regular"]:
    font_manager.fontManager.addfont(str(FONT_DIR / f"{name}.ttf"))
HAIKU_FONT = "Special Elite"

# Square photo with even white borders on top and sides and a much deeper caption strip below,
# in roughly real Polaroid proportions (bottom ≈ 4-5× the side border). Sizes in inches.
CARD_W, BORDER, STRIP = 8, 0.45, 2.0
CARD_H = CARD_W - BORDER + STRIP


def _halo(lw):
    return [pe.Stroke(linewidth=lw + 1.6, foreground=(0, 0, 0, 0.55)), pe.Normal()]


def _washed_imagery(frame, crs, keep, wash=WASH):
    """Esri satellite imagery for `frame` (x0, y0, x1, y1 in `crs`), reprojected to `crs` and washed out towards
    white outside the geometry `keep`. Returns an RGB array and its extent."""
    bounds = gpd.GeoSeries([shapely.box(*frame)], crs=crs).to_crs(3857).total_bounds
    img, ext = cx.bounds2img(*bounds, source=cx.providers.Esri.WorldImagery)
    img, ext = cx.warp_tiles(img, ext, t_crs=crs)
    rgb = img[..., :3] / 255
    h, w = rgb.shape[:2]
    xx, yy = np.meshgrid(np.linspace(ext[0], ext[1], w), np.linspace(ext[3], ext[2], h))
    inside = shapely.contains_xy(keep, xx, yy)[..., None]
    return np.where(inside, rgb, rgb * (1 - wash) + wash), ext


def _distance_strip(fig, value, rect, measure="pair"):
    """Slim histogram of a distance measure over the whole dataset, with `value` marked on it.

    measure -- "pair" (all neighbouring pairs, see `pair_distances`) or "mean_dist" / "lag_dist" (all areas,
               see `neighbourhood_distances`)
    """
    if measure == "pair":
        dist, unit = pair_distances().to_numpy(), "neighbouring pairs"
    else:
        dist, unit = neighbourhood_distances()[measure].to_numpy(), f"areas on {measure}"
    ax = fig.add_axes(rect)
    bins = np.linspace(0, max(dist.max(), value) * 1.02, 160)
    counts, edges = np.histogram(dist, bins=bins, density=True)
    mids = (edges[:-1] + edges[1:]) / 2
    ax.fill_between(mids, counts, color=IMAGO["light_grey"], lw=0)
    ax.plot(mids, counts, color=IMAGO["dark_grey"], lw=0.8)
    ax.axvline(value, color=IMAGO["imago_grey"], lw=1.4)
    ax.scatter([value], [counts.max() * 1.1], s=22, color=IMAGO["imago_grey"], zorder=3, clip_on=False)
    rank = int((dist > value).sum()) + 1
    right = value < bins[-1] * 0.6
    label = f"#{rank:,} of {len(dist):,} {unit}"
    ax.text(value + (1 if right else -1) * bins[-1] * 0.012, counts.max() * 1.1, label, fontsize=7.5,
            va="center", ha="left" if right else "right", **TEXT)
    ax.set_xlim(bins[0], bins[-1]); ax.set_ylim(0, counts.max() * 1.1)
    ax.set_yticks([])
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(IMAGO["dark_grey"]); ax.spines["bottom"].set_linewidth(0.6)
    ax.tick_params(axis="x", length=2, width=0.6, color=IMAGO["dark_grey"], labelsize=6, pad=1.5,
                   labelcolor=IMAGO["imago_grey"])
    ax.set_xticks(np.arange(0, bins[-1], 0.1))
    for t in ax.get_xticklabels():
        t.set_family("Figtree")
    ax.patch.set_alpha(0)
    return ax


def _embedding_strip(fig, emb, rect, style="paired"):
    """One column per embedding band comparing the orange area's value with the green one's.

    style -- "paired" (orange and green bars side by side), "overlay" (both in the same slot, semi-transparent, so
             bands where they agree merge and the gaps stand out), "shared" (like "overlay", but the part both share
             is grey and only the excess is coloured) or "diff" (a single bar, orange minus green, coloured by
             whichever area is higher)
    """
    a, b = (np.asarray(v, dtype=float) for v in emb)
    ax = fig.add_axes(rect)
    i = np.arange(len(a))
    if style == "paired":
        ax.bar(i - 0.21, a, width=0.42, color=IMAGO["orange"], lw=0)
        ax.bar(i + 0.21, b, width=0.42, color=IMAGO["green"], lw=0)
        top = np.abs(np.r_[a, b]).max() * 1.05
    elif style == "overlay":
        ax.bar(i, a, width=0.75, color=IMAGO["orange"], alpha=0.6, lw=0)
        ax.bar(i, b, width=0.75, color=IMAGO["green"], alpha=0.6, lw=0)
        top = np.abs(np.r_[a, b]).max() * 1.05
    elif style == "shared":
        same = np.sign(a) == np.sign(b)
        common = np.where(same, np.sign(a) * np.minimum(np.abs(a), np.abs(b)), 0)
        ax.bar(i, common, width=0.75, color=IMAGO["grey"], lw=0)
        for v, colour in [(a, IMAGO["orange"]), (b, IMAGO["green"])]:
            ax.bar(i, v - common, bottom=common, width=0.75, color=colour, lw=0)
        top = np.abs(np.r_[a, b]).max() * 1.05
    elif style == "diff":
        d = a - b
        ax.bar(i, d, width=0.75, color=np.where(d >= 0, IMAGO["orange"], IMAGO["green"]), lw=0)
        top = np.abs(d).max() * 1.05
    else:
        raise ValueError(f"unknown style {style!r}")
    ax.axhline(0, color=IMAGO["dark_grey"], lw=0.6)
    ax.set_xlim(-0.8, len(a) - 0.2); ax.set_ylim(-top, top)
    ax.set_yticks([])
    for side in ax.spines:
        ax.spines[side].set_visible(False)
    ticks = [0] + list(range(7, len(a) - 8, 8))  # bands are numbered from 1, as in the data's columns
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(k + 1) for k in ticks], family="Figtree")
    ax.tick_params(axis="x", length=0, labelsize=6, pad=1.5, labelcolor=IMAGO["imago_grey"])
    ax.text(len(a) - 0.2, -top, "embedding band", fontsize=6, va="top", ha="right",
            transform=ax.transData, **{**TEXT, "weight": "regular"})
    ax.patch.set_alpha(0)
    return ax


def polaroid(layers, title, subtitle, locate, outline, hist=False, value=None, emb=None, emb_style="shared", haiku=None,
             haiku_font=HAIKU_FONT):
    """Polaroid-style satellite card.

    layers   -- list of (GeoDataFrame, colour, line width), drawn in order; together they set the frame and stay unwashed
    title    -- list of (text, colour or None); a coloured item gets a short bar in that colour before it
    subtitle -- second caption line
    locate   -- geometry whose centroid is marked on the UK locator
    outline  -- UK silhouette (see `uk_outline`), in the same CRS as the layers
    hist     -- if True, add a slim histogram of all neighbouring-pair distances (see `pair_distances`) to the
                caption strip, with `value` marked on it; "mean_dist" or "lag_dist" use that per-area measure instead
    emb      -- optional (orange vector, green vector): paired columns comparing the two embeddings band by band,
                in the histogram's place; with both, the caption strip grows to fit the embeddings above the histogram
    emb_style -- how to draw `emb`: "paired", "overlay", "shared" or "diff" (see `_embedding_strip`)
    haiku    -- optional three-line poem (a string with line breaks), typed in `haiku_font` in the caption strip, in place
                of the charts
    """
    areas = pd.concat([layer for layer, _, _ in layers])
    crs = areas.crs
    x0, y0, x1, y1 = areas.total_bounds
    cx_, cy_, half = (x0 + x1) / 2, (y0 + y1) / 2, 0.55 * max(x1 - x0, y1 - y0)
    x0, y0, x1, y1 = cx_ - half, cy_ - half, cx_ + half, cy_ + half  # square frame

    rgb, ext = _washed_imagery((x0, y0, x1, y1), crs, areas.union_all())

    both = bool(hist) and emb is not None
    # Deeper caption strip when it holds the embedding chart (and more again with the histogram as well)
    STRIP = globals()["STRIP"] + (0.6 if haiku else 0 if emb is None else 0.9 if both else 0.35)
    CARD_H = CARD_W - BORDER + STRIP
    fig = plt.figure(figsize=(CARD_W, CARD_H), facecolor=IMAGO["white"])
    # Thin outline drawn fully inside the canvas, so the card reads as a card even on a white page
    fig.add_artist(Rectangle((0.002, 0.002), 0.996, 0.996, transform=fig.transFigure, fill=False,
                             edgecolor=IMAGO["dark_grey"], lw=1.2))
    side = (CARD_W - 2 * BORDER) / CARD_W
    ax = fig.add_axes([BORDER / CARD_W, STRIP / CARD_H, side, side * CARD_W / CARD_H])
    ax.imshow(rgb, extent=ext, interpolation="bilinear")
    for layer, colour, lw in layers:
        layer.boundary.plot(ax=ax, color=colour, lw=lw, path_effects=_halo(lw))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_axis_off()

    # Caption strip: title (with colour keys) and subtitle on the left, UK locator on the right, credit underneath
    x, base = BORDER / CARD_W, STRIP / CARD_H
    y_title = base - 0.45 / CARD_H
    renderer = fig.canvas.get_renderer()
    for text, colour in title:
        if colour is not None:
            yc = y_title - 0.17 / CARD_H
            fig.add_artist(Line2D([x, x + 0.3 / CARD_W], [yc, yc], transform=fig.transFigure, color=colour,
                                  lw=5, solid_capstyle="round", path_effects=_halo(5)))
            x += 0.42 / CARD_W
        t = fig.text(x, y_title, text, fontsize=22, va="top", **TEXT)
        x = fig.transFigure.inverted().transform(t.get_window_extent(renderer))[1, 0] + 0.3 / CARD_W
    fig.text(BORDER / CARD_W, base - 0.95 / CARD_H, subtitle, fontsize=11, va="top", **TEXT)
    fig.text(BORDER / CARD_W, 0.22 / CARD_H, cx.providers.Esri.WorldImagery.attribution, fontsize=5.5,
             va="bottom", **{**TEXT, "weight": "regular"})
    if haiku:
        fig.text(BORDER / CARD_W + 0.15 / CARD_W, 0.5 / CARD_H, haiku.strip(), fontsize=14, va="bottom", ha="left",
                 linespacing=1.55, family=haiku_font, color=IMAGO["imago_grey"])
    chart_w = (CARD_W - 2 * BORDER - 1.4) / CARD_W
    if emb is not None:
        y, h = (1.05, 0.6) if both else (0.5, 0.6)
        _embedding_strip(fig, emb, [BORDER / CARD_W, y / CARD_H, chart_w, h / CARD_H], style=emb_style)
    if hist:
        _distance_strip(fig, value, [BORDER / CARD_W, 0.5 / CARD_H, chart_w, 0.3 / CARD_H],
                        measure="pair" if hist is True else hist)
    ins = fig.add_axes([1 - (BORDER + 0.9) / CARD_W, 0.25 / CARD_H, 0.9 / CARD_W, (STRIP - 0.55) / CARD_H])
    outline.plot(ax=ins, color=IMAGO["imago_grey"], lw=0)
    c = locate.centroid
    ins.scatter(c.x, c.y, s=40, color=IMAGO["orange"], edgecolor=IMAGO["white"], lw=0.8, zorder=3)
    ux0, uy0, ux1, uy1 = outline.total_bounds
    ins.set_xlim(ux0, ux1); ins.set_ylim(uy0, uy1); ins.set_aspect("equal"); ins.set_anchor("E"); ins.set_axis_off()
    return fig


def area_card(areas, code, neighbours, subtitle, outline, hist=False, value=None, emb=None, emb_style="shared",
              haiku=None):
    """Card for area `code` (orange) and its `neighbours` (green); `hist`/`value`/`emb`/`emb_style`/`haiku` as in `polaroid`."""
    focal = areas.loc[[code], ["geometry"]]
    nbrs = areas.loc[list(neighbours), ["geometry"]]
    return polaroid([(nbrs, IMAGO["green"], 1.4), (focal, IMAGO["orange"], 3)],
                    title=[(code, None)], subtitle=subtitle, locate=focal.geometry.iloc[0], outline=outline,
                    hist=hist, value=value, emb=emb, emb_style=emb_style, haiku=haiku)


def pair_card(areas, a, b, subtitle, outline, hist=False, value=None, emb=None, emb_style="shared",
              haiku=None):
    """Card for neighbouring areas `a` (orange) and `b` (green); `hist`/`value`/`emb`/`emb_style`/`haiku` as in `polaroid`."""
    area_a, area_b = areas.loc[[a], ["geometry"]], areas.loc[[b], ["geometry"]]
    return polaroid([(area_b, IMAGO["green"], 2.4), (area_a, IMAGO["orange"], 2.4)],
                    title=[(a, IMAGO["orange"]), (b, IMAGO["green"])], subtitle=subtitle,
                    locate=pd.concat([area_a, area_b]).union_all(), outline=outline, hist=hist, value=value,
                    emb=emb, emb_style=emb_style, haiku=haiku)


def export_card(fig, name, dpi=200, fig_dir=FIG_DIR):
    """Save a card at full size: no bbox_inches="tight", which would trim the Polaroid margins."""
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(exist_ok=True)
    path = fig_dir / f"{name}.png"
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor(), edgecolor=fig.get_edgecolor())
    return path


# --- Contact sheets ------------------------------------------------------------------------------


def thumbnail(ax, areas, code, pad=0.3, colour=IMAGO["orange"]):
    """Square satellite thumbnail of one area: outlined, with its surroundings washed out."""
    area = areas.loc[[code], ["geometry"]]
    x0, y0, x1, y1 = area.total_bounds
    cx_, cy_, half = (x0 + x1) / 2, (y0 + y1) / 2, (0.5 + pad) * max(x1 - x0, y1 - y0)
    frame = (cx_ - half, cy_ - half, cx_ + half, cy_ + half)
    rgb, ext = _washed_imagery(frame, area.crs, area.geometry.iloc[0])
    ax.imshow(rgb, extent=ext, interpolation="bilinear")
    area.boundary.plot(ax=ax, color=colour, lw=1.5, path_effects=_halo(1.5))
    ax.set_xlim(frame[0], frame[2]); ax.set_ylim(frame[1], frame[3]); ax.set_axis_off()
    ax.set_title(f"{code} · {area.area.iloc[0] / 1e6:.2f} km²", fontsize=8, **{**TEXT, "weight": "regular"})


def contact_sheet(areas, codes, title, ncols=3, size=2.6):
    """Grid of thumbnails for `codes`, with a bold title."""
    nrows = int(np.ceil(len(codes) / ncols))
    fig, axs = plt.subplots(nrows, ncols, figsize=(ncols * size, nrows * size + 0.6), facecolor=IMAGO["white"])
    for ax in np.ravel(axs):
        ax.set_axis_off()
    for ax, code in zip(np.ravel(axs), codes):
        thumbnail(ax, areas, code)
    fig.suptitle(title, fontsize=13, **TEXT)
    fig.tight_layout()
    return fig
