# Exploration log


## 2026-11-04 — Contiguity graph (all four nations, queen)

**Data (2024):** 46,844 small areas — England 33,755 LSOAs, Scotland 7,392
Data Zones, Northern Ireland 3,780 Super Data Zones, Wales 1,917 LSOAs. EPSG:27700,
64 embedding bands (`band{1..64}_mean`), no missing values. Embedding vector
lengths are 0.75–0.99 rather than 1, because they are averages of unit-length pixel vectors.

**Queen contiguity** (`Graph.build_contiguity(lsoas, rook=False)`, ~18 s):
272,424 links (counted in both directions), but only **1** England–Scotland pair. Wales–England looked fine
(99 links each way). `strict=True` was worse: zero England–Scotland links, and 326 fewer
within Northern Ireland.

**Diagnosis:** polygons within 1 m of each other show ~23 England–Scotland pairs, all at
distance 0, which *overlap* by up to ~70,000 m² (the two nations' boundaries come from different sources).
Contiguity requires polygons to touch without overlapping, so these links are dropped.

**Fix:** `Graph.build_fuzzy_contiguity(lsoas)`, which links any polygons that intersect (~3 s). It contains every queen
link plus the 21 missing England–Scotland pairs (23 in total), and nothing else changed.

**Final graph `g`:** 272,466 links, median 6 neighbours per area (max 53), **12 areas with no neighbours**,
31 disconnected pieces (mainland GB 42,777; Northern Ireland 3,779; island groups, largest 89).
The areas with no neighbours need handling before we compute dissimilarity.

## 2026-11-04 — Dropped areas with no neighbours

Removed the 12 areas with no neighbours from both `g` (`g.subgraph`) and `lsoas`/`emb`: E01019077,
S01014306, S01014332, S01014346, S01019112, S01019115, S01019116, S01019117, S01019737,
S01019747, S01019748, N20001651. Island groups with several areas were kept. Result: 46,832 areas,
272,466 links (unchanged), 19 disconnected pieces (was 31).

## 2026-11-04 — Isolates figure

Added a figure of the 12 dropped areas (overview + one zoomed panel each) to the notebook, plotting only those
areas on contextily tiles to keep it light. CartoDB tiles now require an API key (they return "API key required"
placeholders), so we use `cx.providers.Esri.WorldGrayCanvas` (no key needed). All 12 are offshore islands (Scilly, Inner
Hebrides, Orkney, Shetland, Rathlin). Note: `nb execute` gives each cell 30 s by default; the full notebook needs
`--timeout 300`.

## 2026-11-04 — Neighbour dissimilarity (cosine)

**Measure:** cosine distance between the 64-band embeddings of every pair of neighbours in `g` (fuzzy contiguity),
via `sklearn.metrics.pairwise.paired_cosine_distances`. Chosen over Euclidean because the area vectors are
averages of unit-length vectors: their length partly reflects how mixed the land cover is, and cosine ignores it.
Each pair is computed in both directions (272,466 values). Results are stored as weights of `g_dist =
graph.Graph(Series(dist, index=g.adjacency.index))`.

**Parallelism:** the areas are split into 16 groups by focal area (one per core), and each group's
pair distances are computed on a separate thread (joblib `backend="threading"`), then written back in the original order.
Benchmark (scratch): serial ~1 s; separate processes (`loky`) were *slower* (1.6–2.2 s, because
each worker has to be sent its share of the data); threads were ~4–8× faster. Bigger win:
`lsoas[band_cols].to_numpy()` stores values column by column, so picking out whole rows is slow; `np.ascontiguousarray(emb)` cut
the threaded step from ~0.66 s to ~0.16 s. The full notebook cell still takes ~0.75 s (not investigated).
Checked: every pair computed once, matches the serial result, same structure as `g`.

**Distribution:** median 0.032, IQR 0.016–0.068, mean 0.054, max 0.54. Strongly right-skewed: most
neighbours are similar, with a long tail of very different pairs.

## 2026-11-04 — Neighbourhood dissimilarity: mean_dist vs lag_dist

Two per-area scores, with equal weights for every neighbour: `mean_dist` = mean of the cosine distances to each neighbour
(`g_dist.aggregate("mean")`); `lag_dist` = cosine distance to the average neighbour embedding
(`g.transform("r").lag(emb)`). `lag_dist <= mean_dist` for every area. Spearman rank correlation 0.84. Medians 0.046 vs 0.017, max 0.456 vs
0.438. In the scatter plot, areas near the diagonal are outliers (unlike all their surroundings); areas well below it are
transitions (their neighbours differ from each other). Also built `most_dissimilar`: each area's single most dissimilar
neighbour and the distance to it.

**Top area on both measures: `E01030745`**, a pair of reservoir basins just south of Heathrow, surrounded by
housing/industry/airport (distances to those neighbours 0.39–0.54); its only similar neighbour (0.16) is the large reservoir
to the west. Expect other water/coast cases near the top of the ranking.

## 2026-11-04 — Map template (style "C1")

Iterated in the scratchpad: map of a focal area + its neighbours over satellite imagery, comparing
4 fades (dark, washed, greyscale, navy) × 5 line palettes, then an Imago-palette grid (colours taken from
imago.ac.uk CSS: indigo `#24226f`/`#181651`, orange `#ff8f42`, teal `#03cea3`, lilac `#a9afff`, grey-lavender
`#8c91a8`, amber `#ffaf39`). **Chosen: C1** = Esri.WorldImagery; outside the focal area + neighbours washed to
white (55%); focal outline orange, neighbours teal, both with a faint dark outline; UK locator inset with no box
in Imago indigo with an orange dot.

**Implementation** (notebook, `plot_focal(code)`): fetch tiles once with `cx.bounds2img` and reproject to EPSG:27700
with `cx.warp_tiles`. The wash is applied to the image pixels with a mask from `shapely.contains_xy` against the merged
outline of the focal area and its neighbours (this also allows effects like greyscale, which an overlay polygon can't do).
Attribution uses the provider's own string.

**UK outline for the inset:** merging all 46k polygons took ~8 min. `shapely.coverage_union_all` on everything fails
(the polygons overlap at national borders), so: merge each nation with coverage union (England 0.4 s, Scotland 3 s, Wales
<0.1 s; Northern Ireland isn't cleanly tiled → falls back to `union_all` on 200 m-simplified polygons), then join the four
nations, drop holes and parts under 20 km², and simplify by 1.5 km. ~26 s total.

## 2026-11-04 — Official Imago palette

Switched `plot_focal` to the official brand palette (from Imago's brand guidelines): Navy `#24226F`, Grey `#B8BCD1`,
Green `#03CEA3`, Orange `#FF8F42`, Light Grey `#E2E5F3`, Blue `#1877CF`, Dark Grey `#8C91A8`, White.
Outlines: focal Orange, neighbours Green. UK silhouette and all text (title, attribution) now Grey
`#B8BCD1` (replacing indigo/black). Note: Grey is low-contrast on the white figure background and the washed imagery.

## 2026-11-04 — Polaroid card, Figtree, Imago Grey

`plot_focal(code)` now returns a Polaroid-style card (8 × 9.15 in): a square photo (frame made square around the focal
area + neighbours) with even 0.45 in white borders on top and sides, and a 1.6 in caption strip below. The strip has the area code
(22 pt) and `mean_dist · lag_dist · n neighbours` (11 pt) in bold **Figtree** (static TTFs from
github.com/erikdkennedy/figtree, OFL, saved in `fonts/`, registered with `font_manager.addfont`), the Esri credit in
regular weight, and the UK silhouette at bottom right. Text and UK silhouette in **Imago Grey `#4A4A49`** (Imago imagery
data-service colour); locator dot Orange with a white edge. Faint Light Grey (`#E2E5F3`) card edge.
Export with `export_card(fig, name)` → `figures/<name>.png` at 200 dpi, **without** `bbox_inches="tight"` (it would trim
the Polaroid margins).
Update: caption strip deepened to 2.0 in (8 × 9.55 in card; bottom ≈ 4.4× the 0.45 in side/top border, close to real
Polaroid 600 proportions). The faint Light Grey card edge is replaced by a thin (1.2 pt) Imago Dark Grey `#8C91A8` outline drawn
just inside the canvas (a `Rectangle` in figure coordinates), so the card stays readable against a white page.

## 2026-11-04 — Top 5 areas per measure

`mean_dist` and `lag_dist` give **the same top 5 in the same order**: E01030745 (0.456/0.438, 9 neighbours), N20003012
(0.381/0.374, 4), W01001286 (0.375/0.360, 3), N20002748 (0.355/0.353, 3), E01026177 (0.315/0.308, 2). Cards exported to
`figures/<code>.png`. Ranks 2–5 are the reverse of the reservoir case: small built-up cores (town/village) inside a few
large rural neighbours (farmland, moorland/forestry, coastal peninsula, woodland). True but not very interesting. Observations:
(1) the top areas have few neighbours (2–4 vs median 6), so their averages rest on a handful of pairs; (2) with large
rural neighbours the focal area is tiny on the card. Decision: **switch from whole neighbourhoods to individual pairs of neighbours.**

## 2026-11-04 — Pairs section + pair Polaroid cards

New section "Most dissimilar neighbouring pairs": one row per pair (`area_a < area_b`), 136,233 pairs. In the raw top 20,
the reservoir `E01030745` appears 7 times (only 32 distinct areas). **Distinct pairs**: go down the ranking and skip any pair
that shares an area with a pair already chosen. Top 5: E01030710–E01030745 (0.538), E01031353–E01031359 (0.513),
E01020936–E01034298 (0.503), E01029178–E01035125 (0.484), W01001947–W01002024 (0.481).

**Template refactor:** generic `polaroid(layers, title, subtitle, locate)` (layers = list of (gdf, colour, lw), which set the frame
and stay unwashed; a title item with a colour gets a short bar in that colour before it). `plot_focal(code)` (unchanged look)
and new `plot_pair(a, b)` (A orange, B green, both 2.4 pt; caption "A ▬ B ▬" + cosine distance) are thin wrappers. Exports:
`figures/pair_<a>_<b>.png`.

Observations: most top pairs are again a strong contrast between built-up and open land (housing vs reservoir, village vs
farmland, coastal town vs farmed headland, industrial/retail vs open water). In one card (E01020936–E01034298) Esri's imagery
has **clouds**; Esri's imagery is a recent mosaic, not the 2024 imagery the embeddings were built from. In some pairs one area
is tiny relative to the other (e.g. E01035125).

## 2026-11-04 — Ideas for more interesting cards + choosing k

Pair cards were one-note (built-up vs open land every time). Two ideas: (1) restrict the search to cities (needs boundaries:
ONS area→local-authority lookup recommended, or built-up-area polygons); (2) cluster the embeddings, interpret the clusters
visually, then search at cluster level (top pair per cluster combination, and "surprising neighbours", i.e. cluster pairs adjacent
less often than chance). Plan: do (2) first, then (1) as a filter on top.

**k scan** (k-means on vectors scaled to length 1, i.e. clustering by cosine similarity; all 46,844 areas; n_init=3; silhouette on a 10k sample, cosine; ~5 s per k):

| k | silhouette | smallest | largest |
|---|---|---|---|
| 5 | 0.290 | 5,491 | 13,410 |
| 10 | 0.253 | 2,768 | 9,406 |
| 15 | 0.225 | 1,550 | 5,492 |
| 20 | 0.214 | 835 | 3,584 |
| 30 | 0.192 | 562 | 2,582 |
| 40 | 0.178 | 315 | 1,877 |
| 50 | 0.176 | 89 | 1,724 |
| 100 | 0.148 | 67 | 883 |

Silhouette falls steadily with no peak or elbow: the embeddings form continuous gradients, so k is a choice about interpretability, not a
statistical answer. Very small clusters appear between k=40 and k=50, probably rare land types (water, airports, quarries).
**Decision: k=20** for labelling (190 cluster pairs, all clusters ≥835 areas), and also record each area's k=50 cluster to keep the rare types.
Re-run in the clusters notebook (isolates dropped, 46,832 areas): k=20 silhouette 0.212, smallest 842; k=40 → 282; **k=50 → 195**;
k=75 → 72; k=100 → 67. So the sharp drop in smallest-cluster size sits between k=50 and k=75 there (the scratch run put it at
40→50, with 89 at k=50): its position is sensitive to the isolates and the random start. The fine level (k=50 vs k=75) is still open.
Development moves to a second notebook, `gdsl30dmc_clusters.ipynb`; shared tooling moved to `gdsl30dmc_tools.py`.

## 2026-11-05 — Clusters (k=20, k=100), business cores and new card options

**Clustering** (`gdsl30dmc_clusters.ipynb`): the user chose **k=20 and k=100** (this settles the "fine level still open" note above). k-means on
vectors scaled to length 1, n_init=10, clusters numbered by size (0 = largest); labels saved to `data/clusters_2024.parquet`. k=20 sizes
837–3,628; k=100 sizes 71–869. The two levels nest only loosely (median share of a k=100 cluster inside its main k=20 cluster: 0.61).
Contact sheets of the 6 most typical areas (closest to the centre) per k=20 cluster: `figures/clusters/c20_XX.png`. Draft labels: about
12 of 20 clusters are shades of residential; non-residential types are city centres/dense mixed use (18), arable (8), mixed farmland (10),
pastoral (11), woodland/parkland fringe (17), uplands (19). No industrial or water cluster at k=20. Clusters 1, 5 and 12 are mostly
Scottish/NI urban areas (England has 72% of all areas): real building styles, an embedding effect, or Data Zone size; flagged as a caveat.

**Business cores.** k=20 cluster 18 is broader than "city centres" (dense inner-city mixed use: flats, offices, institutions). At k=100,
City of London and central Manchester areas fall into **cluster 95** (6 of 10 checked) and 88 (4 of 10). Cluster 95 is the high-rise office
district (133 areas, median 0.11 km², E 114 / S 17 / N 2, 65% inside k=20 cluster 18); 88 is central mixed use. Focus on 95.
- **Pairs** (563 neighbouring pairs include a core area; top 5 distinct, core area in orange): E01035620–E01035617 (0.408, fields + campus,
  top 0.03% of all 136,233 pairs), E01034486–E01004401 (0.289, reservoir + sheds), S01017417–S01017432 (0.268), S01017414–S01017176
  (0.257, riverside park), S01017427–S01017433 (0.254). The two weak Glasgow pairs (3, 5) look alike from above: the core areas match other
  business cores and the neighbours a tenement cluster (c100 61), so the gap is plausibly offices vs flats; but the neighbours are tiny
  (0.06–0.10 km²) and at the edge of their cluster. Suggested filter for card-worthy pairs: minimum distance and/or minimum area.
- **lag_dist** (top 5 core areas): only E01034486 (0.180, the reservoir block, top 0.29% of areas) is a clear outlier; the rest are top
  3–5% (averaging neighbours dilutes contrast; most have 2–3 neighbours, some ~0.02 km²). Cards 3–5 still show towers set into
  neighbourhoods well.
- Cards: `figures/core/pair_<i>_<a>_<b>.png`, `figures/core/lag_<i>_<code>.png`; contact sheet `figures/clusters/c100_95.png`.

**Card options** (`gdsl30dmc_tools.py`):
- `pair_distances()` and `neighbourhood_distances()` compute every neighbouring-pair distance and per-area `mean_dist`/`lag_dist` once,
  cached to `data/pair_distances_2024.parquet` and `data/neighbourhood_distances_2024.parquet` (match notebook 1).
- `hist=True` (pairs) or `hist="lag_dist"`/`"mean_dist"`: slim histogram of the measure over the whole dataset in the caption strip,
  the card's value marked with a line and "top x% of N". The distribution is very skewed (median pair 0.032, max 0.538).
- `emb=(orange_vector, green_vector)`: band-by-band chart of the two embeddings, one column per band (1–64). Styles tried: `"paired"`
  (side by side; reads as texture), `"overlay"` (transparent; overlap turns a muddy teal), `"diff"` (orange minus green; clean but loses
  the values), **`"shared"` (default)**: the part both share in light Imago grey and only the excess coloured, so more grey = more alike.
  For lag cards, green is the average neighbour. The band chart replaces the histogram; with both, the caption strip grows to fit (card
  10.1 in tall instead of 9.55).

## 2026-11-09 — Distinct entities at k=100, urban screen, final cards

**Entity scan** (clusters notebook, "Distinct entities at k=100"): contact sheets of all 100 fine clusters (4 typical areas each, 9 for
candidates). Most are shades of housing, farmland or fringe. Clearly delimited entities: 99 reservoirs/inland water (71 areas), 81 industrial
and transport land, 50 industrial and retail parks, 42 golf courses and leafy suburbs, 91 woodland and heathland, 90 harbour/marina
waterfront, 87 port and coastal industrial towns, 93 coastal fringe, 95 business cores, 88 central mixed use. Landscapes: 97 Highland
mountains, 98 Scottish islands, 94 Scottish uplands, 85 English/Welsh uplands, 92 Welsh valleys. Not found: airports, quarries, campuses,
cemeteries, stand-alone docks (probably smaller than a typical area). Labels are a visual reading, not ground truth.

**Top 3 pairs per entity** (both areas ≥ 0.05 km², distinct, entity area first; 27 cards in `figures/entities/`, shared band chart).
Highlights: 99 #1 Staines (#1 of all pairs), 99 #3 Nene Washes (fields in the photo, water cluster in the embedding: likely seasonal
flooding of the washland; #22), 50 #2 Macclesfield retail park vs Peak District moors (#102), 88 central London blocks vs royal parks.
Caveats: the Cardiff Bay water/business-park pair appears under both 99 and 50; clouds in some Esri images (81 #3, 87 #1–2).

**Card tweaks:** subtitles now name the place and give an exact rank ("#22 of 136,233 pairs"); the histogram label is a rank too
(`gdsl30dmc_tools.py`), replacing "top x%", which read "top 0.00%" for the #1 pair.

**Urban screen** (both areas 0.05–2 km²): most top pairs are still housing vs urban open space (Hackney Marshes #103, Epping Forest edge,
Richmond Park). Exception: `E01004721`–`E01004722`, west London (0.317, #419), two dense terraced areas that look alike. Both are
*typical* members of their clusters (c100 68 and 69, whose centres are 0.299 apart), and contact sheets of both clusters show dense
terraces. Untested hypothesis: **street orientation** (the grids run at right angles; Sentinel-1 radar returns depend on building
orientation). Not used as a showcase card since we can't explain it; a candidate follow-up.

**Final cards** (`figures/final/`, 200 dpi, notebook section "Final cards for the submission"): 1 Staines reservoirs (0.538, #1, with
histogram), 2 Nene Washes (0.447, #22, band chart), 3 Hackney Marshes (0.375, #103, band chart; replaced Macclesfield to have one contrast
entirely within a city). Next: the user wants to replace the charts with a haiku in a typewriter font, and to try a set of
most different (Staines) + most similar pair + most similar urban pair.

## 2026-11-10 — Final submission: haiku cards, most different vs most similar

**Template:** the user found the histogram and band chart too technical for the submission. `polaroid`/`pair_card` now take
`haiku=` (three lines, in place of the charts; caption strip grows 0.6 in), set in a typewriter face: **Special Elite** (Apache;
default) or Courier Prime (OFL), both from github.com/google/fonts, in `fonts/` and registered in `gdsl30dmc_tools.py`
(`haiku_font=` to switch). Courier Prime looked more "office" and crowded the subtitle, so we kept Special Elite. The charts remain
available as options.

**New set** (the user's idea): keep the most different pair and contrast it with the most similar ones.
- Most different: `E01030745`/`E01030710`, Staines Reservoirs vs Stanwell housing (0.538, #1 of 136,233).
- Most similar: `N20000689`/`N20000681`, farmland in County Armagh (0.0004, #1 most similar). It is the minimum with or without
  an area filter.
- Most similar urban: smallest distance among pairs with both areas 0.05–1 km² (small areas = urban; the lower bound drops noisy
  tiny areas): `E01003685`/`E01003730`, terraced streets in Ilford (0.0006, #5 most similar overall).

Haiku (5-7-5): "Still black reservoir — / the next street hangs out washing. / Nothing more apart." · "Green field, hedge, green field. /
A map line says they are two; / the land knows just one." · "Same bay window, same / chimney pots, same Tuesday bins. / Two codes,
one long street." Also drafted for Nene Washes and Hackney Marshes, which are no longer used.

**Place names**, checked by reverse-geocoding each area's centre with OpenStreetMap Nominatim: Staines Reservoirs lies inside
`E01030745` (King George VI Reservoir is 426 m away, not in it) and `E01030710` is Stanwell, Spelthorne, Surrey; the Armagh pair is
between Richhill and Hamiltonsbawn, County Armagh; the Ilford pair is Loxford/Seven Kings, LB Redbridge, IG1.

**`gdsl30dmc_submission.ipynb`**, a new standalone notebook that runs start to end (~2 min): load areas → fuzzy contiguity → drop
12 isolates → pair distances computed from scratch (`cache=None`) → pick the three pairs by rule → captions (guarded by `expect`
codes, so a changed pick stops the run) → cards at 200 dpi in `figures/submission/` (`1_most_different`, `2_most_similar`,
`3_most_similar_urban`). The larger area of each pair is drawn in orange.

**Cleanup:** removed `figures/final/` (Staines, Nene Washes, Hackney Marshes) and the "Final cards" section of the clusters
notebook, which now ends with a pointer to the submission notebook.

**Post text:** the LinkedIn text for the three cards (brief, plain, no buzzwords) is the last section of
`gdsl30dmc_submission.ipynb` ("Post text"), kept in a plain-text block so the hashtags don't render as headings. It covers: the AlphaEarth
embeddings via Imago, 46,832 areas and 136,233 neighbouring pairs, the three pairs, and the point that the boundaries we use to count people
often split places the satellites see as one. It also says everything was made by prompting Claude Code (day 10 theme: prompting only).

## 2026-11-10 · Website, repository and social image

**Website:** a Quarto site with a Polaroid theme, built into `docs/` and served by GitHub Pages at
<https://darribas.org/map_challenge26-prompt_only/> (repo `darribas/map_challenge26-prompt_only`, Pages from `main` `/docs`). Pages:
the submission first (cards, how to read them, post text, how it was made), then a backstory in 11 chapters, every prompt, the full
transcript, the notebooks and this log. The conversation is threaded through: prompts appear as typed notes in the backstory, each linked
to its place in the transcript, and the home page counts come from it. `scripts/export_conversation.py` turns the Claude Code session file
into `conversation/` (thinking, system reminders and email left out, paths shortened); `scripts/build_site.py` runs before every render
and builds web images, transcript and prompt pages. The site builds without the data; `data/` and full-size exploration figures are
git-ignored.

**Social image:** `scripts/make_social.py` combines the three cards into `figures/submission/social.png` (3780 × 2000 px): title,
the cards slightly tilted on the site's table colour, and the site address underneath, for LinkedIn and other networks.
