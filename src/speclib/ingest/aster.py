"""ASTER/JPL spectral library ingestion adapter.

Thin wrapper around EcostressAdapter since ASTER and ECOSTRESS
share nearly identical file formats. Differences are handled
by the source config (license, citation, source library enum).

Reference: Baldridge et al. (2009), Remote Sensing of Environment.
"""

from __future__ import annotations

from speclib.ingest.ecostress import EcostressAdapter


class AsterAdapter(EcostressAdapter):
    """Ingestion adapter for the ASTER/JPL spectral library.

    Uses the same parsing logic as EcostressAdapter. The source
    library, license, and citation are determined from the YAML
    config file (data/upstream/aster_jpl.yaml).
    """
