# LOC HABS measured-drawing harvester

This is a deliberately narrow R&D acquisition probe: can a repeatable process find,
resolve, download, and normalize a small corpus of measured architectural drawings
from the Library of Congress HABS/HAER/HALS collection? It does **not** interpret
drawing geometry, create a building graph, choose Valheim prefabs, or write ZDOs.

`habs_harvester.py` uses only the public `loc.gov` JSON API and downloadable resources;
no API key or authentication is required. The frozen `habs-corpus.json` selection is
20 small cabins, houses, farmhouses, and barns. It is frozen by LOC control number so
new search results cannot silently change the proof corpus.

## Exact run

From `tools/selfie-stick`:

```powershell
python .\habs_harvester.py harvest
python .\habs_harvester.py verify --expected-buildings 20
```

For a budgeted blind acquisition, resolve exact resources and HTTP sizes first, then
download only that frozen plan:

```powershell
python .\habs_harvester.py plan `
  --spec .\habs-corpus-v3-holdout.json `
  --output .\habs-corpus-v3-acquisition-plan.json `
  --max-sheets-per-building 6

python .\habs_harvester.py harvest `
  --plan .\habs-corpus-v3-acquisition-plan.json `
  --output .\out\loc-habs-v3-holdout\corpus
```

`plan` performs item resolution and HEAD requests but downloads no raster bytes. It
requires a positive `Content-Length` for every selected sheet and defaults to hard limits
of 536,870,912 bytes per sheet, 805,306,368 per building, and 2,147,483,648 total. Planned
harvests reject a changed or missing response length before streaming, abort if a stream
crosses any limit, delete the `.part` file, and atomically publish only a byte-exact result.
The v3 replacement run verified 29 masters / 123,099,962 bytes against acquisition-plan
SHA-256 `3fa84fbd64bf72489e13c742ecf20e9932cb1c293eea1b244d4ef2f137a3dc51`.

The default output is local and ignored by Git:

```text
out/loc-habs/corpus/
  manifest.json
  <loc-control-number>/
    metadata.json
    manifest.json
    drawings/
      plan-01.tif
      elevation-01.tif
      section-01.tif
      drawing-01.tif
```

`drawing-NN` is intentional: older LOC records sometimes expose only “sheet N of M,”
with no plan/elevation/section description in the API. A sheet can also carry several
roles. The file receives one deterministic primary name while `manifest.json` retains
the complete role list and every downloadable variant.

The default selects master TIFFs because dimensions and construction annotations are
often illegible in the 1024-pixel reference JPEG. For a much smaller browsing copy:

```powershell
python .\habs_harvester.py harvest --format reference-jpeg `
  --output .\out\loc-habs-reference\corpus
```

Pillow is optional. When installed, downloaded pixel dimensions, image format, and
mode are verified from the file itself. Without it, LOC-provided dimensions remain in
the variant list and local decoded dimensions are `null`.

The frozen proof run acquired **20 buildings / 69 master sheets / 127,676,740
bytes**. A second acquisition reported all 69 drawings as cached and left a sentinel
TIFF's modification time unchanged. Mechanical verification passed all file paths,
byte counts, SHA-256 hashes, decoded dimensions, and the exact 20-building gate.
Visual spot checks covered explicit modern metadata and a legacy generic record:
Alfred's Cabin retained a dimensioned plan, section, and four elevations; the Dyer and
Banta barns respectively retained a dimensioned plan/section and dimensioned
plans/sections/elevations; and the generically titled
Bertolet-Herbein sheets were valid title, site, and dimensioned floor-plan sheets.

## Searching and filtering

`search` returns only records whose result metadata contains a `Drawings from Survey
...` resource. HABS is the default; `--program HAER`, `--program HALS`, and
`--program ANY` are available for exploration.

```powershell
# Cabins in Tennessee
python .\habs_harvester.py search --building-type cabin --state TN --limit 20

# Barns in a county, using LOC's location facets
python .\habs_harvester.py search --building-type barn `
  --state Montana --location "Gallatin County" --limit 20

# Construction-date range plus free-text metadata/full-text query
python .\habs_harvester.py search --building-type house `
  --date-from 1800 --date-to 1899 --keyword timber --limit 20
```

Filter mapping is explicit:

- building type is added to LOC's `q` search and checked locally against title and
  subjects; known aliases cover cabin, house/dwelling, farmhouse, barn, stable,
  schoolhouse, and shed;
- state and location become LOC `fa=location:...` facets;
- date bounds fetch candidate item details and filter explicit `Building/structure
  dates` values from HABS notes;
- keyword becomes the API `q` query;
- results are requested in title order and normalized by title plus LOC ID.

LOC's generic date facet was not useful on the sampled HABS queries: many search records
have no facetable date, and record/documentation dates are not construction dates.
`--date-from` and `--date-to` therefore perform the extra item-detail requests and match
only explicit HABS building/structure dates. Records without that evidence are excluded
rather than assigned a guessed date.

An ad hoc filtered harvest is supported by giving filters instead of `--spec`, or exact
records can be acquired with repeated `--id` arguments. The frozen spec remains the
default when no filters or IDs are supplied.

## Normalization and provenance

`metadata.json` keeps a compact normalized view and the complete LOC `item` object.
It preserves control number, item/API/alternate URLs, call and survey numbers,
locations, subjects, contributors, record/documentation/building dates, notes,
media descriptions, repository, source collection, and all supplied rights fields.

The per-building `manifest.json` keeps every resolved drawing sheet and every LOC file
variant, including URL, MIME type, resource type, API byte size, and API dimensions.
For the selected local file it records its path, byte count, SHA-256, HTTP
Last-Modified/ETag when supplied, and decoded dimensions where Pillow is available.
The corpus-level manifest freezes the selection receipt and totals.

Writes are canonical JSON with sorted keys and are skipped when bytes are unchanged.
Before reusing a drawing, the harvester verifies the existing local SHA-256 and asks
LOC for current Content-Length/Last-Modified headers. Unchanged drawings are not
downloaded again; replacements use a same-directory temporary file and atomic rename.

Rights are metadata, not a blanket license determination. HABS item records commonly
state that U.S. Government images have no known restrictions while warning that
images copied from other sources may be restricted. The harvester preserves LOC's
full statement and source link on every building rather than rewriting it as “public
domain.”

## API behavior observed in this lap

- The collection endpoint currently combines HABS, HAER, and HALS. A `photo, print,
  drawing` original-format value does not prove measured drawings exist; the drawing
  resource caption is the useful gate.
- Search responses summarize `resources[].files` as an integer. Item-detail responses
  expand it to a nested list: one list per sheet, then TIFF/JPEG/JSON-caption variants.
- Search results frequently omit `medium`, even when item details report `Measured
  Drawing(s): N`.
- Modern sheets tend to have descriptive caption titles. Many older sheets expose only
  survey/call number plus `sheet N of M`, so their architectural role cannot be safely
  inferred from metadata alone.
- A single sheet may contain multiple roles (“section and plan” or “elevations and
  section”). Local filenames therefore cannot be treated as the complete taxonomy.
- Master TIFF variants frequently report width and height as zero in API metadata,
  while reference JPEG variants include dimensions. The harvester retains both and
  measures the downloaded master locally when Pillow is present.
- At least one sheet (`md2171`, sheet 1) reported a 995,832-byte master in item JSON
  while the server delivered a valid 17,285,104-byte TIFF matching its HTTP
  Content-Length. API and acquired sizes plus an explicit match flag are retained;
  HTTP length, SHA-256, and image decoding gate the local artifact.
- The same discrepancy can be extreme: several otherwise attractive modern surveys
  advertised compressed-looking sizes but served 130+ MiB masters per sheet. The
  frozen corpus excludes those outliers after HEAD/transfer evidence; resource
  resolution itself has no size-based blind spot.
- `created/published` usually describes when documentation was compiled, not when the
  building was erected. Construction dates, when present, are embedded in notes and
  are normalized separately without pretending they are universal.
- Resource-level URLs can be missing for data/caption groups. Drawing variants still
  carry direct downloadable storage URLs, so the manifest records both independently.
- LOC occasionally closed an item-detail response before its advertised byte count
  during this run. JSON and drawing transfers are retried with bounded backoff; a
  partial drawing remains a `.part` file only until it is discarded, never a corpus
  artifact.

This earns only the next question: whether a measured sheet can be interpreted into a
normalized building graph with explicit uncertainty. That converter is outside this
probe.
