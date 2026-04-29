import base64
import logging
from io import BytesIO
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use("Agg")   # non-interactive backend, must be set before pyplot import
    import matplotlib.pyplot as plt
    from nilearn import datasets, plotting
    HAS_NILEARN = True
except ImportError:
    HAS_NILEARN = False
    logger.warning("nilearn/matplotlib not installed — brain rendering disabled.")

N_VERTS_PER_HEMI = 10242
RENDER_DPI = 80
RENDER_FIGSIZE = (9, 4)     # wide figure: left hemi | right hemi


class BrainRenderer:
    """
    Renders per-timestep 3D cortical activation maps using nilearn on the
    fsaverage5 inflated surface.

    render_series() accepts the full (n_timesteps, n_vertices) TRIBE v2
    activation tensor and returns a list of base64-encoded PNG frames.
    """

    def __init__(self) -> None:
        self._fsaverage5 = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_series(
        self,
        all_vertex_activations: np.ndarray,   # (n_timesteps, n_vertices)
        timestamps: List[float],
        max_frames: int = 60,
        danger_timestamps: Optional[List[float]] = None,
    ) -> List[Dict]:
        """
        Render brain surface frames for the full time series.

        Danger timesteps are always included; remaining slots are filled with
        evenly-spaced frames so the total never exceeds max_frames.

        Returns:
            List of {"timestamp", "image_b64", "danger_level", "max_activation"}
        """
        if not HAS_NILEARN or all_vertex_activations.size == 0:
            return []

        n_timesteps = len(timestamps)
        frame_indices = self._select_frame_indices(
            n_timesteps, max_frames, timestamps, danger_timestamps
        )

        vmax = float(np.percentile(all_vertex_activations, 99.5))
        vmax = max(vmax, 1.0)

        rendered: List[Dict] = []
        logger.info(f"Rendering {len(frame_indices)} brain frames (vmax={vmax:.2f})...")

        for idx in frame_indices:
            t = timestamps[idx]
            verts = all_vertex_activations[idx]
            frame_max = float(verts.max()) if verts.size else 0.0

            img_b64 = self._render_frame(verts, t, vmax)
            if img_b64 is None:
                continue

            rendered.append({
                "timestamp": t,
                "image_b64": img_b64,
                "danger_level": self._danger_level(frame_max),
                "max_activation": round(frame_max, 3),
            })

        logger.info(f"Brain rendering complete: {len(rendered)} frames.")
        return rendered

    def render_summary_frame(
        self,
        all_vertex_activations: np.ndarray,  # (n_timesteps, n_vertices)
        timestamps: List[float],
    ) -> Optional[str]:
        """
        Render a single summary frame at the peak-activation timestep.
        Returns base64 PNG or None if rendering is unavailable.
        """
        if not HAS_NILEARN or all_vertex_activations.size == 0:
            return None

        peak_idx = int(np.argmax(all_vertex_activations.max(axis=1)))
        vmax = float(np.percentile(all_vertex_activations, 99.5))
        vmax = max(vmax, 1.0)
        return self._render_frame(
            all_vertex_activations[peak_idx], timestamps[peak_idx], vmax
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_fsaverage5(self):
        if self._fsaverage5 is None:
            logger.info("Fetching fsaverage5 mesh (cached after first run)...")
            self._fsaverage5 = datasets.fetch_surf_fsaverage("fsaverage5")
        return self._fsaverage5

    def _render_frame(
        self,
        vertex_activations: np.ndarray,   # (n_vertices,)
        timestamp: float,
        vmax: float,
    ) -> Optional[str]:
        try:
            fsaverage = self._get_fsaverage5()

            n_expected = 2 * N_VERTS_PER_HEMI
            if vertex_activations.shape[0] < n_expected:
                padded = np.zeros(n_expected, dtype=np.float32)
                padded[: vertex_activations.shape[0]] = vertex_activations
                vertex_activations = padded

            lh = vertex_activations[:N_VERTS_PER_HEMI]
            rh = vertex_activations[N_VERTS_PER_HEMI: 2 * N_VERTS_PER_HEMI]

            fig, axes = plt.subplots(
                1, 2,
                figsize=RENDER_FIGSIZE,
                subplot_kw={"projection": "3d"},
                facecolor="#080818",
            )

            surf_kwargs = dict(
                colorbar=False,
                cmap="hot",
                vmin=0.0,
                vmax=vmax,
                bg_on_data=True,
            )

            plotting.plot_surf_stat_map(
                fsaverage["infl_left"],
                stat_map=lh,
                hemi="left",
                view="lateral",
                bg_map=fsaverage["sulc_left"],
                axes=axes[0],
                figure=fig,
                **surf_kwargs,
            )
            axes[0].set_title(
                f"L   t={timestamp:.1f}s", color="#cccccc", fontsize=7, pad=1
            )
            axes[0].set_facecolor("#080818")

            plotting.plot_surf_stat_map(
                fsaverage["infl_right"],
                stat_map=rh,
                hemi="right",
                view="lateral",
                bg_map=fsaverage["sulc_right"],
                axes=axes[1],
                figure=fig,
                **surf_kwargs,
            )
            axes[1].set_title(
                f"R   t={timestamp:.1f}s", color="#cccccc", fontsize=7, pad=1
            )
            axes[1].set_facecolor("#080818")

            fig.patch.set_facecolor("#080818")
            plt.tight_layout(pad=0.2)

            buf = BytesIO()
            fig.savefig(
                buf, format="png", dpi=RENDER_DPI,
                bbox_inches="tight", facecolor="#080818", edgecolor="none",
            )
            plt.close(fig)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8")

        except Exception as e:
            logger.error(f"Brain render failed at t={timestamp:.1f}s: {e}")
            try:
                plt.close("all")
            except Exception:
                pass
            return None

    def _select_frame_indices(
        self,
        n_timesteps: int,
        max_frames: int,
        timestamps: List[float],
        danger_timestamps: Optional[List[float]],
    ) -> List[int]:
        if n_timesteps <= max_frames:
            return list(range(n_timesteps))

        stride_set = set(range(0, n_timesteps, max(1, n_timesteps // max_frames)))

        danger_set: set = set()
        if danger_timestamps:
            for dt in danger_timestamps:
                closest = min(range(n_timesteps), key=lambda i: abs(timestamps[i] - dt))
                for offset in range(-2, 3):
                    idx = closest + offset
                    if 0 <= idx < n_timesteps:
                        danger_set.add(idx)

        return sorted(stride_set | danger_set)[:max_frames]

    @staticmethod
    def _danger_level(max_activation: float) -> str:
        if max_activation >= 2.8:
            return "critical"
        if max_activation >= 2.0:
            return "high"
        if max_activation >= 1.5:
            return "medium"
        return "low"


brain_renderer = BrainRenderer()
