# DNA Evolutionary Archive — §4.3

Evidence that evolutionary constraint leaves a detectable structural signature in DNA. Exon/intron separation and fork-column calibration. Instrument has no genetic code knowledge.

## Scripts

| Script | Purpose | Runtime |
|--------|---------|---------|
| `_dna_genomic.py` | Exon/intron 3-cavity Self. 3-mer encoding, 256-nt genomic-order windows. N=200 transcripts. | ~3min |
| `_dna_fork2.py` | 4-species fork column (Pongo/Gorilla/Pan/Homo). AHSG single-gene calibration. | ~1min |
| `_dna_validate.py` | Multi-seed validation, κ ablation, window sweep, dinucleotide shuffle control. | ~5min |

## Data

- **Human TE atlas**: transcript sequences + CDS masks (parquet)
- **4-species hominid alignments**: Pongo, Gorilla, Pan, Homo (per-gene FASTA)
- **GENCODE v49 GTF**: primary assembly annotation

Expected locations under the repo-root `data/` directory:

- transcript parquet / TE table: `data/rna/te/te_human.parquet`
- hominid alignments: `data/dna/hominid/DNA_vs_Protein_Alignments/...`

Raw parquet and FASTA files must be obtained from GENCODE, TE atlas, and the hominid alignment source.

## Run Order

```powershell
cd experiments\dna
python _dna_genomic.py      # exon/intron baseline (population evidence)
python _dna_fork2.py         # AHSG fork column (single-gene calibration)
python _dna_validate.py      # multi-seed + ablation confirmation
```

## Dependencies

`numpy`, `pandas`, `pyarrow` (parquet). Core instrument: `code/geruon.py`, `code/geme.py` (stdlib only).

## Key Results

- Exon/intron: d=−0.97 (n=200 transcripts, 10,606 windows). Shuffle collapses to d=−0.10. Δd=+0.87.
- AHSG fork column: d=+1.51 (single-gene, n=1). AHSG identified under positive selection (Sabeti 2007, Nielsen 2005). Per-gene pooled did NOT generalize (mean d=0.13±0.22).
- Dinucleotide shuffle preserves base composition but destroys 3-nt periodicity → signal drops.
- κ ablation confirms multi-lens Self is load-bearing.

## What Didn't Work

- **Per-gene generalization**: AHSG fork column (d=+1.51, single gene) did not generalize when pooled across genes (mean d=0.13±0.22). Fork signal is gene-specific, not a universal conservation metric.
- **Solo Geruon on DNA**: signal much weaker without multi-lens Self. Required amplifier for exon/intron separation.
- **3-mer alone**: dinucleotide shuffle destroys 3-nt periodicity → signal drops to d=-0.10. Signal depends on codon-scale sequential structure, not base composition.
