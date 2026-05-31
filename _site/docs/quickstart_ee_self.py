"""Runnable EE Self quickstart.

Run from the repository root:

    python docs/quickstart_ee_self.py

This demonstrates a 3-cavity Self: three Geruons with different temporal
lenses share one BiasField and produce a cross-harm time series.
"""

from pathlib import Path
import math
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from geruon import Geruon, BiasField  # noqa: E402


DIM = 16


def make_stream(n=120, dim=DIM):
    """Generate four regimes with simple structural transitions."""
    for i in range(n):
        block = (i // 30) % 4
        vec = [0.0] * dim
        vec[block] = 1.0
        vec[(block + 1) % dim] = 0.25
        yield vec, f"block_{block}_{i}"


def cross_harm(cavities, dim=DIM):
    centroids = [g.memory.centroid() for g in cavities]
    centroids = [c for c in centroids if c is not None]
    if len(centroids) < 2:
        return None

    total = 0.0
    n = 0
    for a in range(len(centroids)):
        for b in range(a + 1, len(centroids)):
            total += math.sqrt(
                sum((centroids[a][k] - centroids[b][k]) ** 2 for k in range(dim))
            )
            n += 1
    return total / n


def main():
    bias = BiasField(vec_dim=DIM)
    cavities = [
        Geruon(vec_dim=DIM, memory_cap=24, kappa_tau=0.5, bias_field=bias),
        Geruon(vec_dim=DIM, memory_cap=24, kappa_tau=10.0, bias_field=bias),
        Geruon(vec_dim=DIM, memory_cap=24, kappa_tau=100.0, bias_field=bias),
    ]

    print("step  harm     tau_fast  tau_mid  tau_slow")
    harms = []

    for i, (vec, sig) in enumerate(make_stream(), start=1):
        for g in cavities:
            g.process_vec(vec, sig)

        harm = cross_harm(cavities)
        if harm is not None:
            harms.append(harm)

        if i == 1 or i % 30 == 0:
            print(
                f"{i:>4}  {harm or 0.0:>7.4f}  "
                f"{cavities[0].tau:>8.3f}  {cavities[1].tau:>7.3f}  "
                f"{cavities[2].tau:>8.3f}"
            )

    print("\nsummary")
    print(f"inputs:       120")
    print(f"harm samples: {len(harms)}")
    print(f"harm mean:    {sum(harms) / len(harms):.4f}")
    print(f"harm max:     {max(harms):.4f}")
    print(f"bias count:   {bias._count}")

    assert len(harms) > 0
    assert max(harms) >= 0.0
    print("\nOK: 3-cavity Self produced a cross-harm series.")


if __name__ == "__main__":
    main()
