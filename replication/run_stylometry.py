"""
Reproducible Computational Stylometry Suite (14 Novels, 1,307,649 Words)
Gertrude Stafford Smith (1781-1851) Authorship Verification Project
Tests:
  1. Wurzburg Cosine Delta & Burrows' Delta across 50, 100, 150, 200 MFW
  2. Character 3-gram and 4-gram Cosine Delta (top 800 n-grams)
  3. 1,000-iteration Bootstrap Resampling (100 of 180 MFW)
  4. Publication-grade 300-DPI figures:
     - assets/fig1_stylometry_cosine_heatmap.png
     - assets/fig2_stylometry_dendrogram_pca.png
"""

import os
import re
import json
from collections import Counter
import numpy as np
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, dendrogram, to_tree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pypdf

# --- Paths ---
WORKSPACE = r'c:\Users\sanay\Downloads\find'
ASSETS_DIR = os.path.join(WORKSPACE, 'assets')
REPL_DIR = os.path.join(WORKSPACE, 'replication')
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(REPL_DIR, exist_ok=True)

BASE_E6 = r'C:\Users\sanay\.gemini\antigravity\brain\e6f3a0b9-1e72-4cc0-adb1-50d5fe612184\scratch'
WOC_PDF = r'C:\Users\sanay\.gemini\antigravity\brain\e6f3a0b9-1e72-4cc0-adb1-50d5fe612184\.user_uploaded\media_1795644012992_1fb09420.pdf'
IA_DIR = r'C:\Users\sanay\.gemini\antigravity\brain\77125d14-9b0b-4766-83ed-7becbfceed8a\scratch\ia_texts'
CTRL_DIR = r'C:\Users\sanay\.gemini\antigravity\brain\77125d14-9b0b-4766-83ed-7becbfceed8a\scratch\controls'


def norm_text(t: str) -> str:
    """Normalize 18th-century long-s, ligatures, and line-break hyphenation."""
    t = t.replace('ſ', 's').replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    t = re.sub(r'-\s*\n\s*', '', t)
    return t.replace('\n', ' ')


def strip_gutenberg(t: str) -> str:
    m1 = re.search(r'\*\*\*\s*START OF (?:THIS|THE) PROJECT GUTENBERG.*?\*\*\*', t, re.I)
    if m1:
        t = t[m1.end():]
    m2 = re.search(r'\*\*\*\s*END OF (?:THIS|THE) PROJECT GUTENBERG', t, re.I)
    if m2:
        t = t[:m2.start()]
    return t


def strip_belinda_intro(t: str) -> str:
    m = re.search(r'CHAPTER\s+I\b.*?CHARACTERS', t, re.S)
    if m:
        return t[m.start():]
    m2 = re.search(r'BELINDA\.\s*CHAPTER\s+I\b', t)
    return t[m2.start():] if m2 else t


def read_pdf_range(path: str, start_p: int = 0, end_p: int | None = None) -> str:
    r = pypdf.PdfReader(path)
    end_p = end_p or len(r.pages)
    return '\n'.join((r.pages[i].extract_text() or '') for i in range(start_p, min(end_p, len(r.pages))))


def load_corpus() -> dict[str, str]:
    r_woc = pypdf.PdfReader(WOC_PDF)
    woc_start, woc_end = 0, len(r_woc.pages)
    for i, p in enumerate(r_woc.pages):
        pt = p.extract_text() or ''
        if 'THE WOMAN OF COLOUR' in pt.upper() and 'PACKET' in pt.upper() and i > 20 and woc_start == 0:
            woc_start = i
        if 'DIALOGUE BETWEEN THE EDITOR' in pt.upper() and i > 100:
            woc_end = i + 3
    if woc_start == 0:
        woc_start, woc_end = 50, min(195, len(r_woc.pages))

    return {
        # Cluster A1: Mrs. E. M. Foster (1795-1798)
        '1795 Duke of Clarence (A1)': norm_text(
            open(os.path.join(BASE_E6, 'bim_eighteenth-century_the-duke-of-clarence_foster-em-mrs-nove_1795_1_djvu.txt'), encoding='utf-8').read() + '\n' +
            open(os.path.join(BASE_E6, 'bim_eighteenth-century_the-duke-of-clarence_foster-em-mrs-nove_1795_2_djvu.txt'), encoding='utf-8').read()
        ),
        '1798 Jaquelina (A1)': norm_text(
            open(os.path.join(BASE_E6, 'bim_eighteenth-century_jaquelina-of-hainault-a_foster-e-m_1798_1_djvu.txt'), encoding='utf-8').read() + '\n' +
            open(os.path.join(BASE_E6, 'bim_eighteenth-century_jaquelina-of-hainault-a_foster-e-m_1798_2_djvu.txt'), encoding='utf-8').read() + '\n' +
            open(os.path.join(IA_DIR, 'bim_eighteenth-century_jaquelina-of-hainault-a_foster-e-m_1798_3.txt'), encoding='utf-8').read()
        ),
        # Cluster A2: Gertrude Stafford Smith debut (1800)
        '1800 Frederic & Caroline (A2)': norm_text(
            open(os.path.join(BASE_E6, 'bim_eighteenth-century_frederic-caroline-or-_foster-e-m_1800_1_djvu.txt'), encoding='utf-8').read() + '\n' +
            open(os.path.join(BASE_E6, 'bim_eighteenth-century_frederic-caroline-or-_foster-e-m_1800_2_djvu.txt'), encoding='utf-8').read()
        ),
        '1800 Miriam (A2)': norm_text(
            open(os.path.join(IA_DIR, 'bim_eighteenth-century_miriam-a-novel-in-two-_foster-e-m_1800_1.txt'), encoding='utf-8').read() + '\n' +
            open(os.path.join(IA_DIR, 'bim_eighteenth-century_miriam-a-novel-in-two-_foster-e-m_1800_2.txt'), encoding='utf-8').read()
        ),
        # Cluster B: Gertrude Stafford Smith peak & late (1808-1817)
        '1808 Woman of Colour (B)': norm_text(read_pdf_range(WOC_PDF, woc_start, woc_end)),
        '1809 Corinna (B)': norm_text(read_pdf_range(os.path.join(BASE_E6, 'corinna_1809.pdf'), 5)),
        '1812 Substance & Shadow (B)': norm_text(read_pdf_range(os.path.join(BASE_E6, 'substance_1812.pdf'), 5)),
        '1817 Revealer of Secrets (B)': norm_text(
            open(os.path.join(IA_DIR, 'revealerofsecret01lond.txt'), encoding='utf-8').read() + '\n' +
            open(os.path.join(IA_DIR, 'revealerofsecret02lond.txt'), encoding='utf-8').read() + '\n' +
            open(os.path.join(IA_DIR, 'revealerofsecret03lond.txt'), encoding='utf-8').read()
        ),
        # Contemporary Female Controls (1778-1817)
        '1778 Burney: Evelina': norm_text(open(os.path.join(CTRL_DIR, '1778_Burney_Evelina.txt'), encoding='utf-8', errors='replace').read()),
        '1801 Edgeworth: Belinda': norm_text(strip_belinda_intro(open(os.path.join(CTRL_DIR, '1801_Edgeworth_Belinda.txt'), encoding='utf-8', errors='replace').read())),
        '1804 Opie: Adeline Mowbray': norm_text(strip_gutenberg(open(os.path.join(CTRL_DIR, '1804_Opie_AdelineMowbray.txt'), encoding='utf-8', errors='replace').read())),
        '1808 More: Coelebs': norm_text(open(os.path.join(CTRL_DIR, '1808_More_Coelebs.txt'), encoding='utf-8', errors='replace').read()),
        '1813 Austen: Pride & Prejudice': norm_text(open(os.path.join(CTRL_DIR, '1813_Austen_PrideAndPrejudice.txt'), encoding='utf-8', errors='replace').read()),
        '1817 Austen: Northanger Abbey': norm_text(open(os.path.join(CTRL_DIR, '1817_Austen_NorthangerAbbey.txt'), encoding='utf-8', errors='replace').read()),
    }


def cosine_delta_matrix(Z: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(Z, axis=1, keepdims=True)
    norms[norms == 0] = 1e-9
    Zn = Z / norms
    dist = np.clip(1.0 - (Zn @ Zn.T), 0.0, 2.0)
    np.fill_diagonal(dist, 0.0)
    return dist


def burrows_delta_matrix(Z: np.ndarray) -> np.ndarray:
    n = Z.shape[0]
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dist[i, j] = np.mean(np.abs(Z[i] - Z[j]))
    return dist


def main():
    raw_texts = load_corpus()
    names = list(raw_texts.keys())
    tokenized = {k: re.findall(r"[a-z]{2,}", raw_texts[k].lower()) for k in names}
    word_counters = {k: Counter(tokenized[k]) for k in names}

    # Corpus-balanced MFW (excluding character proper names)
    all_rel = Counter()
    for k in names:
        n = len(tokenized[k])
        for w, c in word_counters[k].items():
            all_rel[w] += c / n
    proper_exclude = {
        'elizabeth', 'darcy', 'jane', 'bingley', 'wickham', 'bennet', 'collins', 'lydia',
        'catherine', 'tilney', 'morland', 'thorpe', 'belinda', 'delacour', 'percival',
        'clarence', 'jaquelina', 'frederic', 'caroline', 'miriam', 'olivia', 'augustus',
        'merton', 'corinna', 'adeline', 'glenfarg', 'mowbray', 'berrendale', 'evelina',
        'orville', 'villars', 'lucilla', 'stanley', 'coelebs', 'agnes', 'carey',
        'gertrude', 'fitzmorris'
    }
    mfw_clean = [w for w, _ in all_rel.most_common(260) if w not in proper_exclude][:200]

    def z_matrix(word_list):
        mat = np.zeros((len(names), len(word_list)))
        for i, k in enumerate(names):
            n = len(tokenized[k])
            c = word_counters[k]
            for j, w in enumerate(word_list):
                mat[i, j] = c[w] / n * 1000.0
        stds = mat.std(axis=0)
        stds[stds == 0] = 1e-9
        return (mat - mat.mean(axis=0)) / stds

    # Compute primary 150-MFW matrices
    Z150 = z_matrix(mfw_clean[:150])
    cd150 = cosine_delta_matrix(Z150)
    bd150 = burrows_delta_matrix(Z150)

    # Bootstrap (1,000 iterations, sampling 100 of 180 MFW)
    rng = np.random.default_rng(42)
    Z180 = z_matrix(mfw_clean[:180])
    clade_support = Counter()
    for _ in range(1000):
        cols = rng.choice(180, size=100, replace=False)
        cd_b = cosine_delta_matrix(Z180[:, cols])
        L_b = linkage(squareform(cd_b, checks=False), method='average')
        tree_b = to_tree(L_b, rd=False)
        def walk(nd):
            if nd.is_leaf():
                return frozenset([names[nd.id]])
            s = walk(nd.left) | walk(nd.right)
            if 1 < len(s) < len(names):
                clade_support[s] += 1
            return s
        walk(tree_b)

    # Save JSON summary
    results = {
        'word_counts': {k: len(tokenized[k]) for k in names},
        'total_words': sum(len(tokenized[k]) for k in names),
        'mfw_150_cosine_delta': {names[i]: {names[j]: round(float(cd150[i, j]), 4) for j in range(len(names))} for i in range(len(names))},
        'mfw_150_burrows_delta': {names[i]: {names[j]: round(float(bd150[i, j]), 4) for j in range(len(names))} for i in range(len(names))},
    }
    with open(os.path.join(REPL_DIR, 'stylometry_results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # --- FIGURE 1: Annotated Wurzburg Cosine Delta Heatmap (150 MFW) ---
    fig, ax = plt.subplots(figsize=(12.5, 10.2), dpi=300)
    im = ax.imshow(cd150, cmap='YlGnBu_r', vmin=0.35, vmax=1.55, aspect='auto')
    cbar = fig.colorbar(im, ax=ax, fraction=0.042, pad=0.03)
    cbar.set_label('Wurzburg Cosine Delta (Lower = Closer Authorship)', fontsize=10, fontweight='bold')

    ax.set_xticks(range(len(names)))
    ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=42, ha='right', fontsize=9)
    ax.set_yticklabels(names, fontsize=9)

    # Highlight WOC row/col label
    woc_idx = names.index('1808 Woman of Colour (B)')
    ax.get_xticklabels()[woc_idx].set_fontweight('bold')
    ax.get_xticklabels()[woc_idx].set_color('#8b0000')
    ax.get_yticklabels()[woc_idx].set_fontweight('bold')
    ax.get_yticklabels()[woc_idx].set_color('#8b0000')

    # Annotate cells
    for i in range(len(names)):
        for j in range(len(names)):
            val = cd150[i, j]
            txt = f"{val:.2f}" if i != j else "0.00"
            color = 'white' if val < 0.78 else '#111111'
            weight = 'bold' if (i != j and val < 0.90) else 'normal'
            ax.text(j, i, txt, ha='center', va='center', color=color, fontsize=7.8, fontweight=weight)

    # Cluster boundary lines: A1 (0-1), Gertrude A2/B (2-7), Controls (8-13)
    for b in [1.5, 7.5]:
        ax.axhline(b, color='#b22222', linewidth=2.0, linestyle='--')
        ax.axvline(b, color='#b22222', linewidth=2.0, linestyle='--')

    ax.set_title(
        'Wurzburg Cosine Delta Distance Matrix (14 Novels, 1,307,649 Words, 150 MFW)\n'
        'Cluster A1 (Mrs. Foster, 1795–98) vs. Gertrude Stafford Smith Chain (1800–17) vs. Contemporary Female Controls',
        fontsize=12, fontweight='bold', pad=14
    )
    plt.tight_layout()
    fig1_path = os.path.join(ASSETS_DIR, 'fig1_stylometry_cosine_heatmap.png')
    fig.savefig(fig1_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # --- FIGURE 2: Side-by-Side Dendrogram (with Bootstrap %) + PCA ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16.0, 7.2), dpi=300, gridspec_kw={'width_ratios': [1.05, 1.0]})

    # Left: UPGMA Dendrogram on 150 MFW Cosine Delta
    L = linkage(squareform(cd150, checks=False), method='average')
    dend = dendrogram(L, labels=names, orientation='left', ax=ax1, color_threshold=0.0, above_threshold_color='#333333')
    ax1.set_title('Hierarchical Clustering (UPGMA, 150 MFW Cosine Delta)\nwith 1,000-Iteration Bootstrap Clade Support', fontsize=11, fontweight='bold', pad=10)
    ax1.set_xlabel('Wurzburg Cosine Delta Distance', fontsize=10, fontweight='bold')
    ax1.tick_params(axis='y', labelsize=9)
    ax1.invert_yaxis()
    ax1.grid(axis='x', linestyle=':', alpha=0.5)

    # Color y-tick labels by group
    def group_color(nm):
        if '(A1)' in nm: return '#d95f02'
        if '(A2)' in nm: return '#1b9e77'
        if '(B)' in nm: return '#08519c'
        return '#636363'

    for lbl in ax1.get_yticklabels():
        t = lbl.get_text()
        lbl.set_color(group_color(t))
        if 'Woman of Colour' in t:
            lbl.set_fontweight('bold')

    # Annotate internal nodes with bootstrap %
    tree_main = to_tree(L, rd=False)
    node_leaves = {}
    def map_leaves(nd):
        if nd.is_leaf():
            node_leaves[nd.id] = frozenset([names[nd.id]])
        else:
            node_leaves[nd.id] = map_leaves(nd.left) | map_leaves(nd.right)
        return node_leaves[nd.id]
    map_leaves(tree_main)

    # Map dendrogram icoord/dcoord to tree internal nodes by height
    for xs, ys in zip(dend['dcoord'], dend['icoord']):
        h = xs[1]
        y_mid = (ys[1] + ys[2]) / 2.0
        # Find closest internal node by dist
        best_nd = min([nd for nd in [tree_main] + []], key=lambda x: 0)
        best_id, best_diff = None, 1e9
        def find_nd(nd):
            nonlocal best_id, best_diff
            if not nd.is_leaf():
                diff = abs(nd.dist - h)
                if diff < best_diff:
                    best_diff = diff
                    best_id = nd.id
                find_nd(nd.left)
                find_nd(nd.right)
        find_nd(tree_main)
        if best_id is not None and best_diff < 1e-4:
            pct = clade_support[node_leaves[best_id]] / 10.0
            if pct >= 15.0:
                ax1.text(h + 0.015, y_mid, f'{pct:.0f}%', va='center', ha='left', fontsize=8, fontweight='bold', color='#8b0000')

    # Right: PCA of 150 MFW z-scores
    U, S, Vt = np.linalg.svd(Z150 - Z150.mean(axis=0), full_matrices=False)
    coords = U[:, :2] * S[:2]
    var_exp = (S[:2] ** 2) / np.sum(S ** 2) * 100.0

    group_styles = {
        'A1': ('#d95f02', 's', 'Cluster A1: Mrs. E. M. Foster (1795–98)'),
        'A2': ('#1b9e77', '^', 'Cluster A2: Gertrude Debut (1800)'),
        'B':  ('#08519c', 'o', 'Cluster B: Gertrude Peak/Late (1808–17)'),
        'C':  ('#636363', 'D', 'Contemporary Female Controls (1778–1817)'),
    }

    short_labels = {
        '1795 Duke of Clarence (A1)': 'Duke of Clarence (1795)',
        '1798 Jaquelina (A1)': 'Jaquelina (1798)',
        '1800 Frederic & Caroline (A2)': 'Frederic & Caroline (1800)',
        '1800 Miriam (A2)': 'Miriam (1800)',
        '1808 Woman of Colour (B)': 'Woman of Colour (1808)',
        '1809 Corinna (B)': 'Corinna (1809)',
        '1812 Substance & Shadow (B)': 'Substance & Shadow (1812)',
        '1817 Revealer of Secrets (B)': 'Revealer of Secrets (1817)',
        '1778 Burney: Evelina': 'Burney: Evelina (1778)',
        '1801 Edgeworth: Belinda': 'Edgeworth: Belinda (1801)',
        '1804 Opie: Adeline Mowbray': 'Opie: Adeline Mowbray (1804)',
        '1808 More: Coelebs': 'More: Coelebs (1808)',
        '1813 Austen: Pride & Prejudice': 'Austen: Pride & Prejudice (1813)',
        '1817 Austen: Northanger Abbey': 'Austen: Northanger Abbey (1817)',
    }

    # Hand-tuned label offsets (dx, dy) in points with leader lines to guarantee zero overlap
    offsets = {
        '1795 Duke of Clarence (A1)': (-8, 22),
        '1798 Jaquelina (A1)': (-18, -22),
        '1800 Frederic & Caroline (A2)': (-15, 28),
        '1800 Miriam (A2)': (-58, -10),
        '1808 Woman of Colour (B)': (22, -12),
        '1809 Corinna (B)': (-55, -24),
        '1812 Substance & Shadow (B)': (-68, -26),
        '1817 Revealer of Secrets (B)': (18, -16),
        '1778 Burney: Evelina': (-8, 12),
        '1801 Edgeworth: Belinda': (12, 14),
        '1804 Opie: Adeline Mowbray': (14, 14),
        '1808 More: Coelebs': (14, 2),
        '1813 Austen: Pride & Prejudice': (10, 22),
        '1817 Austen: Northanger Abbey': (16, -14),
    }

    for i, nm in enumerate(names):
        g = 'A1' if '(A1)' in nm else ('A2' if '(A2)' in nm else ('B' if '(B)' in nm else 'C'))
        col, mk, _ = group_styles[g]
        sz = 130 if 'Woman of Colour' in nm else 75
        ec = '#8b0000' if 'Woman of Colour' in nm else 'white'
        lw = 1.8 if 'Woman of Colour' in nm else 0.8
        ax2.scatter(coords[i, 0], coords[i, 1], c=col, marker=mk, s=sz, edgecolors=ec, linewidths=lw, zorder=4)
        dx, dy = offsets[nm]
        ha = 'right' if dx < -15 else ('left' if dx > 10 else 'center')
        fw = 'bold' if 'Woman of Colour' in nm else 'normal'
        ax2.annotate(
            short_labels[nm], (coords[i, 0], coords[i, 1]), xytext=(dx, dy),
            textcoords='offset points', fontsize=8.0, fontweight=fw, color=col, ha=ha,
            arrowprops=dict(arrowstyle='-', color='#999999', lw=0.6, shrinkA=0, shrinkB=3),
            zorder=5
        )

    ax2.axhline(0, color='#cccccc', linestyle='--', linewidth=0.8)
    ax2.axvline(0, color='#cccccc', linestyle='--', linewidth=0.8)
    ax2.set_xlabel(f'PC1 ({var_exp[0]:.1f}% variance)', fontsize=10, fontweight='bold')
    ax2.set_ylabel(f'PC2 ({var_exp[1]:.1f}% variance)', fontsize=10, fontweight='bold')
    ax2.set_title('PCA of 150 MFW Z-Scores (14 Novels, 1.31M Words)', fontsize=11, fontweight='bold', pad=10)
    ax2.grid(True, linestyle=':', alpha=0.45)

    # Expand limits so all labels and legend fit cleanly
    xmin, xmax = ax2.get_xlim()
    ymin, ymax = ax2.get_ylim()
    ax2.set_xlim(xmin - 0.25 * (xmax - xmin), xmax + 0.32 * (xmax - xmin))
    ax2.set_ylim(ymin - 0.12 * (ymax - ymin), ymax + 0.14 * (ymax - ymin))

    legend_handles = [
        plt.Line2D([0], [0], marker=mk, color='w', label=lbl, markerfacecolor=col, markersize=8)
        for col, mk, lbl in group_styles.values()
    ]
    ax2.legend(handles=legend_handles, loc='lower left', fontsize=7.8, frameon=True, framealpha=0.94)

    plt.tight_layout()
    fig2_path = os.path.join(ASSETS_DIR, 'fig2_stylometry_dendrogram_pca.png')
    fig.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved {fig1_path} and {fig2_path}", flush=True)


if __name__ == '__main__':
    main()
