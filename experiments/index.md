---
title: Experiments
nav_order: 3
has_children: true
---

# Experiments

Frozen EE experiment tracks plus newer applied extensions. Same instrument
family, multiple domains, zero training inside the readout.

| Domain | Core result | Controls |
|--------|-------------|----------|
| [WTC](wtc/) | Transposition equivariance 100%; 5-stage Codex loop | Cross-key Codex ablation |
| [DNA](dna/) | Exon/intron d=-0.97 (n=200) | Shuffle collapses to d=-0.10 |
| [RNA](rna/) | CDS stop 98-100% within 3 windows | Internal ATG control 98% |
| [UN](un/) | 2025 displacement 0.448, rank 1/79 | P5 ablation; FRED negative |
| [GeneGrammar / SHP](genegrammar/) | Human CDS/UTR structural matrix, 19,491 genes | Fair-IID calibration; GC/length comparison |
