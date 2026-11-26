# Computational Stylometry Replication Package

**Project:** Authorship Verification of *The Woman of Colour: A Tale* (1808) — Gertrude Stafford Smith (1781–1851)  
**Corpus:** 14 full-length novels (**1,307,649 words**), 1778–1817:
- **Cluster A1 (Mrs. E. M. Foster, 1795–1798):** *The Duke of Clarence* (1795), *Jaquelina of Hainault* (1798, Vols. 1–3)
- **Cluster A2 (Gertrude Stafford Smith Debut, 1800):** *Frederic & Caroline* (1800), *Miriam* (1800)
- **Cluster B (Gertrude Stafford Smith Peak/Late, 1808–1817):** *The Woman of Colour* (1808), *The Corinna of England* (1809), *Substance and Shadow* (1812), *The Revealer of Secrets* (1817)
- **Contemporary Female Controls (1778–1817):** Frances Burney (*Evelina*, 1778), Maria Edgeworth (*Belinda*, 1801), Amelia Opie (*Adeline Mowbray*, 1804), Hannah More (*Coelebs in Search of a Wife*, 1808), Jane Austen (*Pride and Prejudice*, 1813; *Northanger Abbey*, 1817)

## How to Run

```powershell
python run_stylometry.py
```

**Dependencies:** `numpy`, `scipy`, `matplotlib`, `pypdf` (Python 3.10+).

## Outputs
- `stylometry_results.json` — Full 14×14 Wurzburg Cosine Delta & Burrows' Delta distance matrices (150 MFW) and exact token counts.
- `../assets/fig1_stylometry_cosine_heatmap.png` — 300-DPI annotated Wurzburg Cosine Delta distance heatmap.
- `../assets/fig2_stylometry_dendrogram_pca.png` — 300-DPI UPGMA hierarchical clustering dendrogram (with 1,000-iteration bootstrap clade support) and 2D PCA projection.
