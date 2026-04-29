import math
from typing import Optional, List, Dict
from app.adapters.base import BaseModelAdapter, RawModelOutput

class DemoModelAdapter(BaseModelAdapter):
    """
    Deterministic demo adapter for NeuroSafe.
    Generates realistic ROI activation spikes for testing the integration layer.
    """

    @property
    def provider_name(self) -> str:
        return "demo"

    @property
    def model_name(self) -> str:
        return "neurosafe-demo-adapter"

    async def analyze_video(self, video_path: str, job_id: Optional[str] = None) -> RawModelOutput:
        duration = 30.0
        timestamps = [float(t) for t in range(int(duration) + 1)]
        
        # Generation Logic:
        # Base activation: 0.1 - 0.4
        # Spike 1: Center 15.5s, High (2.8 - 3.2)
        # Spike 2: Center 24.0s, Medium-High (2.2 - 2.6)
        
        roi_activations = {
            "V1": self._generate_activations(timestamps, spike_centers=[15.5, 24.0], peak_mult=3.2),
            "V2": self._generate_activations(timestamps, spike_centers=[15.5, 24.0], peak_mult=2.1),
            "V3": self._generate_activations(timestamps, spike_centers=[15.5, 24.0], peak_mult=1.8),
            "V4": self._generate_activations(timestamps, spike_centers=[15.5, 24.0], peak_mult=1.2),
            "MT+": self._generate_activations(timestamps, spike_centers=[15.5, 24.0], peak_mult=3.0)
        }

        output = RawModelOutput(
            duration_seconds=duration,
            timestamps=timestamps,
            roi_activations=roi_activations,
            model_name=self.model_name,
            model_provider=self.provider_name,
            metadata={
                "video_path": video_path,
                "deterministic": True,
                "spike_count": 2
            }
        )

        return self.validate_output(output)

    def _generate_activations(
        self, 
        timestamps: List[float], 
        spike_centers: List[float], 
        peak_mult: float
    ) -> List[float]:
        activations = []
        for t in timestamps:
            # Baseline: a small sine wave to look "alive" but deterministic
            val = 0.2 + 0.1 * math.sin(t * 0.5)
            
            # Add spikes
            for center in spike_centers:
                # Gaussian-like spike: height * exp(-(t - center)^2 / (2 * sigma^2))
                # Sigma 1.5 gives a nice 3-4 second spread
                spike = peak_mult * math.exp(-((t - center) ** 2) / (2 * (1.2 ** 2)))
                val = max(val, spike)
            
            activations.append(round(val, 3))
        return activations

demo_model_adapter = DemoModelAdapter()
