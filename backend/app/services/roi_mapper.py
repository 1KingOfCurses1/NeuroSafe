import logging
import numpy as np
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

ROI_NAMES = ["V1", "V2", "V3", "V4", "MT+"]

# Maps Destrieux atlas parcel names → visual cortex ROI.
# Based on Destrieux et al. (2010) and standard visual cortex anatomy.
DESTRIEUX_TO_ROI: Dict[str, List[str]] = {
    "V1":  ["G_and_S_calcarine_Sulc", "S_calcarine"],
    "V2":  ["G_cuneus"],
    "V3":  ["G_oc-temp_med-Lingual", "G_ling"],
    "V4":  ["G_oc-temp_lat-fus", "G_oc-temp_med-Parahip"],
    "MT+": ["G_temp_sup-Lateral", "S_temporal_sup", "S_temporal_transverse"],
}

# fsaverage5: 10,242 vertices per hemisphere (20,484 total).
N_VERTS_PER_HEMI = 10242
N_VERTS_TOTAL = N_VERTS_PER_HEMI * 2

# Approximate fallback vertex ranges for visual areas in fsaverage5 FreeSurfer
# ordering, used only when nilearn atlas download is unavailable.
FALLBACK_ROI_RANGES: Dict[str, tuple] = {
    "V1":  (2800, 3400),
    "V2":  (3400, 3900),
    "V3":  (3900, 4400),
    "V4":  (4400, 4900),
    "MT+": (5400, 5900),
}


class RoiMapper:
    """
    Maps the 20,484 vertices of the fsaverage5 cortical surface to named
    visual cortex ROIs (V1, V2, V3, V4, MT+) using the Destrieux atlas.

    extract_roi_timeseries() converts a (n_timesteps, n_vertices) TRIBE v2
    activation tensor into per-ROI scalar timeseries aligned with danger scoring.
    """

    def __init__(self) -> None:
        self._vertex_roi_map: Optional[Dict[str, np.ndarray]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_roi_vertices(self, roi_name: str) -> np.ndarray:
        """Return vertex indices belonging to roi_name."""
        return self._roi_map.get(roi_name, np.empty(0, dtype=int))

    def extract_roi_timeseries(
        self,
        activations: np.ndarray,        # (n_timesteps, n_vertices)
        roi_names: List[str] = ROI_NAMES,
    ) -> Dict[str, List[float]]:
        """
        Average vertex activations within each ROI per timestep, then scale
        to the 0-3 danger-scoring range expected by DangerScoringService.

        TRIBE v2 outputs z-scored BOLD predictions per vertex.
          1. Take the 90th-percentile activation across ROI vertices per timestep
             (captures peaks without being dominated by a single noisy vertex).
          2. Clip negatives to 0 (below-baseline is not dangerous).
          3. Cap at 4.0 (preserves headroom above the critical threshold of 2.8).
        """
        roi_map = self._roi_map
        n_timesteps = activations.shape[0]

        # Pad to expected vertex count if the model returns fewer
        if activations.shape[1] < N_VERTS_TOTAL:
            padded = np.zeros((n_timesteps, N_VERTS_TOTAL), dtype=np.float32)
            padded[:, : activations.shape[1]] = activations
            activations = padded

        result: Dict[str, List[float]] = {}
        for roi in roi_names:
            verts = roi_map.get(roi, np.empty(0, dtype=int))
            if verts.size == 0:
                result[roi] = [0.0] * n_timesteps
                continue

            roi_vals = np.percentile(activations[:, verts], 90, axis=1)
            scaled = np.clip(roi_vals, 0.0, 4.0)
            result[roi] = [round(float(v), 4) for v in scaled]

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _roi_map(self) -> Dict[str, np.ndarray]:
        if self._vertex_roi_map is None:
            self._vertex_roi_map = self._build_roi_map()
        return self._vertex_roi_map

    def _build_roi_map(self) -> Dict[str, np.ndarray]:
        try:
            return self._build_destrieux_map()
        except Exception as e:
            logger.warning(
                f"Destrieux atlas unavailable ({e}). "
                "Using fallback anatomical vertex ranges."
            )
            return self._build_fallback_map()

    def _build_destrieux_map(self) -> Dict[str, np.ndarray]:
        from nilearn import datasets

        logger.info("Fetching Destrieux atlas for fsaverage5 (cached after first run)...")
        destrieux = datasets.fetch_atlas_surf_destrieux(mesh="fsaverage5")

        lh_labels = np.asarray(destrieux["map_left"])   # (10242,)
        rh_labels = np.asarray(destrieux["map_right"])  # (10242,)

        raw_names = destrieux["labels"]
        label_names: List[str] = [
            n.decode() if isinstance(n, bytes) else str(n) for n in raw_names
        ]
        name_to_idx = {n: i for i, n in enumerate(label_names)}

        roi_map: Dict[str, np.ndarray] = {}
        for roi, parcels in DESTRIEUX_TO_ROI.items():
            verts: List[int] = []
            for parcel in parcels:
                idx = name_to_idx.get(parcel)
                if idx is None:
                    hits = [n for n in name_to_idx if parcel.lower() in n.lower()]
                    if hits:
                        idx = name_to_idx[hits[0]]
                if idx is not None:
                    verts.extend(int(v) for v in np.where(lh_labels == idx)[0])
                    verts.extend(
                        int(v) + N_VERTS_PER_HEMI
                        for v in np.where(rh_labels == idx)[0]
                    )

            roi_map[roi] = np.array(verts, dtype=int)
            logger.info(f"  ROI {roi}: {len(verts)} vertices")

        return roi_map

    def _build_fallback_map(self) -> Dict[str, np.ndarray]:
        roi_map: Dict[str, np.ndarray] = {}
        for roi, (lo, hi) in FALLBACK_ROI_RANGES.items():
            lh = np.arange(lo, hi, dtype=int)
            rh = lh + N_VERTS_PER_HEMI
            roi_map[roi] = np.concatenate([lh, rh])
            logger.info(f"  Fallback ROI {roi}: vertices {lo}-{hi} (both hemis)")
        return roi_map


roi_mapper = RoiMapper()
