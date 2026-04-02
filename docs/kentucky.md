# Kentucky Chapter

The Kentucky chapter contains spectral signatures collected within the Commonwealth, with a focus on invasive species, regional minerals, and mine reclamation sites.

## Invasive Species

Seed data from **Lyons et al. (2024)** includes field-measured reflectance spectra for invasive plant species in Kentucky:

- *Lonicera maackii* (Amur honeysuckle)
- Additional species to be added as field campaigns continue

Spectra were collected using ASD FieldSpec instruments and processed following standard protocols for leaf-level and canopy-level measurements.

### Spatial Reference

All Kentucky field collection sites are georeferenced in **EPSG:3089** (Kentucky Single Zone, NAD83). GeoParquet exports include both:

- `geometry` — WGS84 (EPSG:4326) for interoperability
- `geometry_ky` — EPSG:3089 for Kentucky-specific analysis

## Regional Minerals

Kentucky mineral spectra from geological survey collections and field sampling programs.

## Reclamation

Spectral signatures from mine reclamation sites, supporting monitoring of revegetation and land recovery efforts.

## Citation

```bibtex
@article{lyons2024invasives,
  author = {Lyons, Chris and others},
  title = {Spectral characterization of invasive plant species in Kentucky},
  year = {2024},
  journal = {...},
}
```
