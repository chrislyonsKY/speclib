# speclib — Federated Spectral Research Platform

**Design Spec — 2026-04-03**
**Status:** Approved for implementation planning

---

## 1. Problem

Existing spectral libraries (USGS splib07, ECOSTRESS, ASTER/JPL) are static archives.
They are published once, never updated, and carry no context about real-world use.
Researchers who collect field spectra have no good way to publish them with peer review,
attribution, and discoverability. The options are a supplementary ZIP nobody finds, or nothing.

There is no "data journal" for spectral measurements.

## 2. Core Concept

speclib is a **federated, peer-reviewed spectral data repository with an integrated
analysis workbench**.

Three things differentiate it:

1. **You can publish to it.** Upload field spectra, submit for chapter review, get a
   citable DOI. Your data joins the library with permanent attribution.

2. **It's organized by chapters.** A chapter is a thematic or regional collection
   maintained by a research group. Chapters have maintainers who review submissions
   for their domain. This solves governance without a central editorial board.

3. **It's a workspace, not just a catalog.** Spectral matching, sensor separability
   analysis, and exportable endmember bundles mean researchers use speclib *during*
   their work, not just before it.

### Headline Pitch

> Publish your spectral data. Get a DOI. Get peer review. Get found.

## 3. Audience

| Audience | Primary need |
|----------|-------------|
| Field researchers | Publish and cite their spectral measurements |
| Remote sensing analysts | Build sensor-specific endmember sets for classification |
| Ecologists / land managers | Identify and monitor species spectrally |
| Students and educators | Learn spectral analysis with real data and tools |

## 4. Three Interfaces

| Interface | Audience | Purpose |
|-----------|----------|---------|
| **Web viewer** | Everyone | Browse, discover, compare, analyze, download |
| **Python (PyPI) / R (CRAN) packages** | Analysts & researchers | Programmatic access, scripting, pipeline integration |
| **REST API** | Developers & tool authors | Machine-readable access; powers the packages and contribution pipeline |

### 4.1 Web Viewer (Static — GitHub Pages)

The public face of speclib. Already functional with 2,700+ spectra. Enhancements:

- Chapter landing pages with contributor credits and citation info
- Spectral matching upload widget
- Sensor separability comparison tool
- Endmember collection builder with export
- Contribution intake form (routes to FastAPI backend)
- Seasonal/phenological comparison view when temporal data exists

### 4.2 Python Package (PyPI)

Thin client over the REST API with local caching. Install size stays small;
data is fetched on demand.

```python
import speclib

# Load a chapter
lib = speclib.load("ky-invasives")

# Search
pear = lib.search("Pyrus calleryana", canopy="upper")

# Resample to a sensor
s2 = pear.resample("sentinel-2")

# Export
s2.export("envi")          # .sli + .hdr
s2.export("csv")           # columnar CSV
s2.export("geojson")       # with collection coordinates

# Spectral matching
from speclib import match
results = match(my_spectrum, library="ky-invasives", method="sam")

# Separability
from speclib import separability
sep = separability(["Pyrus calleryana", "Quercus alba"], sensor="landsat-9")
sep.plot()
```

### 4.3 R Package (CRAN)

Same API semantics, R-native interface. Targets the ecology community where R dominates.

```r
library(speclib)

lib <- sl_load("ky-invasives")
pear <- sl_search(lib, "Pyrus calleryana", canopy = "upper")
sl_export(sl_resample(pear, "sentinel-2"), "envi")

# Spectral matching
results <- sl_match(my_spectrum, library = "ky-invasives", method = "sam")

# Separability
sep <- sl_separability(c("Pyrus calleryana", "Quercus alba"), sensor = "landsat-9")
plot(sep)
```

### 4.4 REST API (FastAPI)

Stateless server. Validates contributions, creates GitHub PRs, queries the Parquet
layer. No database required for v1.

```
# Public (read)
GET  /api/v1/spectra                      Search / filter catalog
GET  /api/v1/spectra/{id}                 Single spectrum with arrays
GET  /api/v1/chapters                     List chapters with metadata
GET  /api/v1/chapters/{slug}              Chapter detail + contributor list
GET  /api/v1/collections                  List curated endmember collections
GET  /api/v1/collections/{id}             Collection with spectra
POST /api/v1/match                        Spectral matching (upload unknown)
POST /api/v1/separability                 Sensor separability analysis

# Authenticated (GitHub OAuth)
POST /api/v1/contribute                   Submit spectra for chapter review
GET  /api/v1/reviews                      Maintainer review queue
POST /api/v1/reviews/{id}/accept          Accept submission
POST /api/v1/reviews/{id}/reject          Reject with comments
POST /api/v1/reviews/{id}/request-changes Request revisions

# Export
GET  /api/v1/export/{id}?format=envi      Export spectrum in requested format
GET  /api/v1/collections/{id}/export       Export full collection as bundle
```

## 5. Chapter Governance

### 5.1 What Is a Chapter

A chapter is a curated collection with:

- **Scope** — thematic or regional (e.g., "KY Invasive Species", "Sonoran Desert Minerals")
- **Maintainers** — 1–3 researchers who review submissions
- **Review policy** — required metadata fields, quality checks, acceptance criteria
- **Citation** — the chapter is citable via DOI; individual spectra within it are also citable
- **Data branch** — chapter data lives on a dedicated git branch; merges trigger static site rebuild

### 5.2 Launch Chapters

| Chapter | Slug | Maintainer | Status |
|---------|------|-----------|--------|
| USGS Spectral Library v7 | `usgs-splib07` | Read-only (reference) | Ingested |
| Kentucky Invasive Species | `ky-invasives` | Chris Lyons | Ingested |
| Community | `community` | Project admins | Catch-all for unaffiliated submissions |

### 5.3 Creating New Chapters

Research groups propose chapters via the API with: scope description, maintainer list,
review policy, and initial seed data. Project admins approve. This is how speclib scales —
each chapter brings its own reviewers.

### 5.4 Submission Flow

```
Researcher uploads spectra + metadata via web form or API
  → Server validates format, checks required fields, runs automated QC
  → Creates GitHub PR against the chapter's data branch
  → PR includes: rendered spectral plots, QC report, side-by-side with existing spectra
  → Chapter maintainer reviews using GitHub review tools
  → Accept: PR merges, CI rebuilds static site, DOI minted
  → Request changes: contributor revises and updates PR
  → Reject: PR closed with comments
```

### 5.5 Why GitHub PRs for v1

- No custom review UI to build — GitHub's review tools are mature
- Full audit trail (comments, diffs, approvals) for free
- Researchers already have GitHub accounts
- CI runs automated QC checks as status checks on the PR
- Scales naturally; move to custom dashboard only if GitHub becomes a bottleneck

## 6. Contribution Pipeline

### 6.1 What a Contributor Provides

**Required:**
- Spectral data files (CSV, ASD binary, SVC, SPECPR, or speclib JSON)
- Material identification (species/mineral name, binomial if applicable)
- Instrument make and model
- Collection date
- Location (lat/lon or place name)
- Collection method (leaf clip, contact probe, field-of-view, etc.)

**Optional:**
- Field photos
- Vegetation indices
- Sampling protocol description
- Associated publication DOI
- Measurement uncertainty / replicates

### 6.2 What a Contributor Gets

- Peer review from a domain expert (chapter maintainer)
- Persistent DOI for the submission (via Zenodo or DataCite)
- Citable record, e.g.:
  > Lyons, W.C. (2024). Pyrus calleryana leaf reflectance, Bernheim Forest, KY.
  > speclib:ky-invasives. https://doi.org/10.xxxxx
- Spectra permanently discoverable in the viewer, packages, and API
- Attribution on the chapter page
- Credit in any endmember collection that includes their data

### 6.3 Automated QC Checks

Run as CI on every submission PR:

- Wavelength array sorted ascending
- Reflectance values in [0.0, 1.0] (flag but don't reject — emissivity and transmittance exist)
- No wavelength gaps > 2x median spacing
- Minimum metadata fields present
- Signal-to-noise ratio estimate (if replicates provided)
- Duplicate detection — flag if highly similar spectrum already exists for same material/site

### 6.4 DOI Minting

On acceptance, the submission metadata is pushed to Zenodo via their API.
Zenodo returns a DOI that is stored in the spectrum's metadata and displayed
in the viewer. The chapter's Zenodo community groups all its submissions.

## 7. Workbench Features

### 7.1 Spectral Matching

Upload or paste an unknown spectrum. The server computes similarity against
the full library using:

- **Spectral Angle Mapper (SAM)** — angle between spectral vectors, invariant to brightness
- **Euclidean distance** — simple, sensitive to albedo differences
- **Pearson correlation** — shape similarity

Returns top-N matches ranked by score, with quick-compare overlay plots.

Available in: viewer (upload widget), Python/R (`match()`), API (`POST /match`).

### 7.2 Sensor Separability

Select 2+ materials and a target sensor. The system:

1. Convolves library spectra to sensor band passes (Gaussian SRF)
2. Computes per-band separability (Jeffries-Matusita distance, transformed divergence)
3. Identifies most and least discriminating bands
4. Returns a separability matrix and diagnostic plot

Answers: "Can Sentinel-2 distinguish Callery pear from white oak in the NIR?"

Available in: viewer (comparison tool), Python/R (`separability()`), API.

### 7.3 Endmember Collections

A named, citable set of spectra convolved to a specific sensor. Created by
any user, reviewed by chapter maintainers if they include chapter spectra.

**Example:** "SE US Invasive Woody Species — Sentinel-2 MSI"
- Pyrus calleryana (3 upper-canopy spectra, averaged)
- Lonicera maackii (3 upper-canopy spectra, averaged)
- Elaeagnus umbellata (from community chapter)
- 2 native hardwood endmembers (from USGS)

**Export formats:**
- ENVI spectral library (.sli + .hdr)
- CSV (sensor bands as columns)
- speclib JSON
- R-loadable RDS
- QGIS-compatible CSV

Collections get their own DOI and citation record.

### 7.4 Seasonal / Phenological View

When multiple measurements of the same species exist across different dates,
display a phenological curve showing spectral change over time. This is where
the living collection pays off — over time, speclib accumulates temporal
coverage that static libraries never will.

Requires: ≥3 measurements with dates for the same species. Renders as
wavelength-vs-reflectance faceted by date, or band-index-vs-date time series.

## 8. Data Model Changes

### 8.1 Chapter Metadata

```yaml
# data/chapters/ky-invasives/chapter.yaml
slug: ky-invasives
name: Kentucky Invasive Species
description: >
  Field spectral measurements of invasive plant species in Kentucky
  recreation areas. Leaf-level reflectance from CID CI-710 spectrometer.
maintainers:
  - github: chrislyons-ky
    name: Chris Lyons
    orcid: "0000-0000-0000-0000"
review_policy:
  required_fields: [binomial, instrument, collection_date, location, method]
  auto_qc: true
license: CC-BY-4.0
doi: "10.xxxxx/speclib.ky-invasives"
citation: >
  Lyons, W.C. et al. (2024). Kentucky Invasive Species Spectral Collection.
  speclib. https://doi.org/10.xxxxx/speclib.ky-invasives
```

### 8.2 Spectrum Metadata Extensions

New fields added to `SampleMetadata`:

```python
# Contribution provenance
contributor: str           # GitHub username
submission_date: date      # When submitted
review_date: date | None   # When accepted
doi: str | None            # Spectrum-level DOI
chapter: str               # Chapter slug

# Field context
collection_method: str     # "leaf_clip", "contact_probe", "fov_nadir", etc.
field_photos: list[str]    # URLs to associated photos
replicates: int            # Number of measurement replicates
protocol_notes: str        # Free-text sampling protocol

# Phenological context
phenophase: str | None     # "full_leaf", "senescent", "dormant", etc.
growth_stage: str | None   # "mature", "juvenile", "seedling"
```

### 8.3 Collection Model

```python
@dataclass
class SpectralCollection:
    name: str                          # "SE US Invasive Woody Species"
    slug: str                          # URL-safe identifier
    description: str
    target_sensor: str                 # "sentinel-2", "landsat-9", etc.
    spectra: list[CollectionMember]    # References to spectra + averaging config
    creator: str                       # GitHub username
    doi: str | None
    license: str
    created: datetime
```

## 9. Architecture

```
┌──────────────────────────────────────────────────────┐
│               GitHub Pages (static)                   │
│  Viewer · Chapter pages · Methodology · Collections   │
│  Pre-built JSON catalog + spectrum files               │
└────────────────────────┬─────────────────────────────┘
                         │ reads static JSON
┌────────────────────────┴─────────────────────────────┐
│            FastAPI server (lightweight)                │
│  Contribution intake · QC validation · PR creation     │
│  Search / match / separability · Collection export     │
│  Auth: GitHub OAuth (contributors + maintainers)       │
│  Stateless — no database, reads Parquet + HDF5         │
└─────────┬────────────────────────┬───────────────────┘
          │                        │
   creates PRs               reads from
          │                        │
┌─────────┴──────────┐  ┌─────────┴───────────────────┐
│  GitHub repo        │  │  Storage layer               │
│  Chapter data       │  │  HDF5 archive (truth)        │
│  branches + CI      │  │  → Parquet query layer        │
│  Automated QC       │  │  → Static JSON (for viewer)   │
│  on PR              │  │  → Zenodo (DOI metadata)       │
└────────────────────┘  └─────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│          PyPI package  ·  CRAN package                │
│  speclib.load() · search · resample · match · export  │
│  Thin client over REST API + local disk cache          │
└──────────────────────────────────────────────────────┘
```

### 9.1 Deployment

- **Static site**: GitHub Pages, rebuilt by CI on chapter branch merges
- **FastAPI server**: Single instance on Railway / Fly.io / similar (free/cheap tier)
- **DOI minting**: Zenodo API (free for open data)
- **Auth**: GitHub OAuth (free, researchers already have accounts)
- **CI**: GitHub Actions for automated QC, static site builds, and DOI registration

### 9.2 Build Pipeline

```
Contribution accepted (PR merged)
  → CI triggers
  → KyFieldAdapter (or appropriate adapter) ingests new spectra
  → HDF5 archive updated
  → Parquet query layer regenerated
  → Static JSON catalog + spectrum files rebuilt
  → GitHub Pages deployed
  → Zenodo metadata pushed, DOI activated
```

## 10. Scope Control — What Is NOT v1

- Custom review dashboard (GitHub PR reviews are sufficient for v1)
- User accounts beyond GitHub OAuth
- Real-time collaboration or commenting on spectra
- Mobile-optimized viewer
- Automated species identification from imagery
- Integration with Google Earth Engine or cloud processing
- Monetization or premium tiers

These are all reasonable future features, but none are needed to ship
the core value proposition: publish, review, cite, discover, analyze.

## 11. Success Criteria

1. A researcher can upload spectra and receive a DOI within one review cycle
2. The Python package can load any chapter, search, resample, and export in <5 lines
3. The viewer shows all contributed spectra alongside USGS reference data seamlessly
4. At least 3 chapters exist with independent maintainers within 12 months of launch
5. Spectra contributed to speclib are cited in at least one peer-reviewed paper
