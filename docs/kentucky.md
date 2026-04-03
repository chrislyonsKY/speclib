# Kentucky Chapter

The Kentucky chapter contains spectral signatures collected within the Commonwealth, with a focus on invasive species, regional minerals, and mine reclamation sites.

## Invasive Species

Seed data from **Lyons, Gyawali, Cristan, Acharya, Gebremedhin, & Andries (2024)** includes field-measured reflectance spectra for invasive plant species in Kentucky recreation areas:

- *Lonicera maackii* (Amur honeysuckle) — 136 leaf reflectance spectra across canopy positions
- Additional species to be added as field campaigns continue

Spectra were collected using a CID CI-710 leaf spectrometer with an Ocean Optics USB4000 sensor (345 - 1,035 nm, 3,648 channels) and processed following standard protocols for leaf-level measurements.

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
  author = {Lyons, W. Christopher and Gyawali, Buddhi R. and Cristan, Richard and Acharya, Sandesh and Gebremedhin, Maheteme and Andries, Kirk},
  title = {Evaluating spectral properties of invasive plant species in Kentucky recreation areas},
  journal = {International Journal of Remote Sensing},
  volume = {45},
  number = {18},
  pages = {6470--6494},
  year = {2024},
  doi = {10.1080/01431161.2024.2391095}
}
```
