---
title: GeneGrammar / SHP
parent: Experiments
nav_order: 5
has_children: true
---

# GeneGrammar / SHP

GeneGrammar is a practical genomic sequence experiment built from the SHP
readout: a calibrated, zero-training structural spectroscopy tool for nucleotide
streams.

The input is ordinary CDS/cDNA sequence data. The output is a CDS/UTR structural
matrix that can be used for first-pass gene, region, and isoform triage.

## What SHP Measures

SHP compares two views of the same local nucleotide window:

- **chroma**: which 3-mers are present;
- **rhythm**: which adjacent 3-mer transitions occur;
- **cross-harm**: Jaccard distance between the two binary activation sets;
- **fixed_wit**: event rate above a fair-IID calibration threshold.

For the current DNA setting:

```text
k = 4
n = 3
D = 64
W = 128 nt
theta0 = 0.0999
```

No functional labels, expression values, conservation scores, or disease
annotations enter the SHP calculation after CDS/UTR sequence extraction.

![SHP method]({{ site.baseurl }}/assets/images/genegrammar/fig1_shp_method.png)

## Genome-Scale Result

The current human scan processes:

- 19,491 protein-coding genes;
- 224,518 transcript isoforms;
- Ensembl release 115 CDS/cDNA input;
- CDS and UTR structural features from the same calibrated readout.

The core genome-wide result is that almost half of CDS regions are structurally
quiescent under the calibrated event threshold, while UTRs show a slightly
higher event rate in the filtered matrix.

![Calibration and genome distribution]({{ site.baseurl }}/assets/images/genegrammar/fig2_calibration_genome.png)

## Regime Signatures

The SHP matrix separates broad gene regimes without using those labels during
feature computation:

- MHC/HLA genes: low CDS activity with high UTR activity;
- neural genes: elevated CDS activity;
- KRTAP genes: the only CDS-led regime in the current panel;
- HOX and AD-associated panels: distinct intermediate signatures.

These are structural signatures, not causal biological claims.

![Regime signatures]({{ site.baseurl }}/assets/images/genegrammar/fig3_regime_signatures.png)

## Functional Orthogonality

SHP is not a GC-content proxy. Broad gene-symbol classes occupy positions in
CDS/UTR SHP space that do not reduce to GC similarity. A low-dimensional
nearest-centroid baseline already recovers some categories above chance, while
others remain near chance.

The honest public interpretation is not "SHP predicts function." It is:

> SHP provides a compact, annotation-free structural coordinate that can be
> compared against existing biological annotations and used to nominate
> follow-up regions.

![Functional orthogonality]({{ site.baseurl }}/assets/images/genegrammar/fig4_functional_orthogonality.png)

## Relationship To NoHarm

NoHarm v0.2 is the warm-start corrected transcript-isoform scanner. GeneGrammar
provides the SHP dual-axis coordinate planned for NoHarm v0.3 as an optional
`--dual` mode.

The intended relationship:

```text
NoHarm v0.2      static + frame-economy isoform coordinates
GeneGrammar/SHP  calibrated CDS/UTR dual-axis structural spectroscopy
NoHarm v0.3      integrates SHP as --dual for gene and region triage
```

## Status

Research preview, June 2026.

The current figures are generated from the local Stage 1 matrix by
`genegrammar/paper/scripts/make_paper_figures.py` in the development workspace.
The public-facing claim boundary is deliberately conservative: SHP is a
screening coordinate and hypothesis generator, not a diagnostic or mechanistic
biology claim by itself.
