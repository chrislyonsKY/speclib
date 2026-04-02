# Spectral Resampling

Convolve library spectra to match the spectral response of a target sensor.

## How It Works

1. The library spectrum is oversampled using cubic-spline interpolation
2. Gaussian spectral response functions for the target sensor are applied
3. Each output band is the convolution of the oversampled spectrum with the sensor's bandpass

This follows the splib07b methodology used by the USGS.

## Supported Sensors

| Sensor | Key |
|--------|-----|
| Landsat 8/9 OLI/TIRS | `L8_OLI`, `L9_OLI` |
| Sentinel-2 MSI | `S2_MSI` |
| AVIRIS-Classic | `AVIRIS` |
| AVIRIS-NG | `AVIRIS_NG` |
| EMIT | `EMIT` |
| ASD FieldSpec | `ASD_FR` |
| HyMap | `HYMAP` |
| Hyperion | `HYPERION` |
| Custom | User-defined wavelength/bandpass pairs |

## Usage

### Python

```python
spectrum = lib.search("quartz")[0]

# Resample to Landsat 8 OLI
resampled = spectrum.resample("L8_OLI")

# Resample to Sentinel-2 MSI
resampled = spectrum.resample("S2_MSI")

# Custom sensor definition
from speclib.resample import SensorResponse

custom = SensorResponse(
    wavelengths=[0.485, 0.560, 0.660, 0.865],
    bandwidths=[0.070, 0.080, 0.060, 0.040],
)
resampled = spectrum.resample(custom)
```

### CLI

```bash
speclib resample usgs_mineral_quartz_a1b2c3d4 --sensor L8_OLI --output quartz_l8.txt
```
