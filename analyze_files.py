import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.gridspec import GridSpec
import os

# ── Завантаження даних ──────────────────────────────────────────
sizes = np.fromfile('/home/viktor/unix_labs/file_analyser/file_sizes_raw.txt',
                    dtype=np.int64, sep='\n')
total = len(sizes)
print(f"Всього файлів: {total:,}")
print(f"Порожніх (0 байт): {(sizes == 0).sum():,}  ({(sizes == 0).mean()*100:.1f}%)")
print(f"Мін: {sizes.min()} байт")
print(f"Макс: {sizes.max():,} байт  ({sizes.max()/1024**3:.2f} ГБ)")
print(f"Медіана: {np.median(sizes):,.0f} байт")
print(f"Середнє: {sizes.mean():,.0f} байт")

# ── Процентилі ─────────────────────────────────────────────────
pcts = [50, 75, 80, 85, 90, 95, 99]
print("\nПроцентилі:")
for p in pcts:
    v = np.percentile(sizes, p)
    print(f"  {p}%: {v:>12,.0f} байт  ({v/1024:.1f} КБ)")

# Знаходимо найвужчий діапазон що покриває 90% файлів
nonzero = sizes[sizes > 0]
nonzero_sorted = np.sort(nonzero)
target_frac = 0.90
window = int(len(nonzero_sorted) * target_frac)
min_range = np.inf
best_lo, best_hi = 0, 0
for i in range(len(nonzero_sorted) - window):
    r = nonzero_sorted[i + window] - nonzero_sorted[i]
    if r < min_range:
        min_range = r
        best_lo = nonzero_sorted[i]
        best_hi = nonzero_sorted[i + window]
print(f"\n90% ненульових файлів: [{best_lo:,} – {best_hi:,}] байт  "
      f"([{best_lo/1024:.1f} – {best_hi/1024:.1f}] КБ)")

# ── Підготовка даних для гістограм ─────────────────────────────
def human(b):
    for unit, val in [('ГБ', 2**30), ('МБ', 2**20), ('КБ', 2**10)]:
        if b >= val:
            return f'{b/val:.1f} {unit}'
    return f'{b} Б'

OUT = '/home/viktor/unix_labs/report_plots'
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'figure.dpi': 150,
})

BLUE  = '#2563EB'
ORANGE= '#F59E0B'
GREEN = '#10B981'
RED   = '#EF4444'

# ══════════════════════════════════════════════════════════════
# Рис. 1 — Логарифмічна гістограма (основна)
# ══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 5))

bins_log = np.logspace(0, np.log10(sizes.max() + 1), 80)
counts, edges = np.histogram(sizes[sizes > 0], bins=bins_log)
pct_counts = counts / total * 100

ax.bar(edges[:-1], pct_counts, width=np.diff(edges),
       align='edge', color=BLUE, alpha=0.85, edgecolor='white', linewidth=0.3)

ax.set_xscale('log')
ax.set_xlabel('Розмір файлу (байти, лог. шкала)', fontsize=12)
ax.set_ylabel('Частка файлів (%)', fontsize=12)
ax.set_title('Розподіл файлів за розміром (лог. шкала)', fontsize=14, fontweight='bold')

# Позначки на осі X
xticks = [1, 1024, 4096, 64*1024, 1024**2, 10*1024**2, 1024**3]
ax.set_xticks(xticks)
ax.set_xticklabels(['1 Б', '1 КБ', '4 КБ', '64 КБ', '1 МБ', '10 МБ', '1 ГБ'], fontsize=9)

# Виділяємо 90-й процентиль
p90 = np.percentile(sizes[sizes > 0], 90)
ax.axvline(p90, color=RED, linestyle='--', linewidth=1.5,
           label=f'90-й %: {human(int(p90))}')
ax.legend(fontsize=10)

# Аннотація нуля
zero_pct = (sizes == 0).mean() * 100
ax.text(0.01, 0.95, f'Порожніх файлів: {zero_pct:.1f}%',
        transform=ax.transAxes, fontsize=9, va='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEF3C7', alpha=0.8))

plt.tight_layout()
plt.savefig(f'{OUT}/fig1_log_histogram.png', bbox_inches='tight')
plt.close()
print("fig1 збережено")

# ══════════════════════════════════════════════════════════════
# Рис. 2 — 4 зони крупним планом (лінійна шкала)
# ══════════════════════════════════════════════════════════════
zones = [
    ('0 – 4 КБ',    0,          4*1024,    30, '#DBEAFE'),
    ('4 – 64 КБ',   4*1024,     64*1024,   30, '#D1FAE5'),
    ('64 КБ – 1 МБ',64*1024,    1024**2,   30, '#FEF3C7'),
    ('1 МБ – 1 ГБ', 1024**2,    1024**3,   30, '#FCE7F3'),
]

fig, axes = plt.subplots(1, 4, figsize=(18, 4))
fig.suptitle('Розподіл за розміром: детальний вигляд по зонах', fontsize=13, fontweight='bold')

for ax, (label, lo, hi, nbins, color) in zip(axes, zones):
    mask = (sizes >= lo) & (sizes < hi)
    chunk = sizes[mask]
    n = mask.sum()
    pct = n / total * 100

    ax.hist(chunk, bins=nbins, color=color, edgecolor='#475569', linewidth=0.4)
    ax.set_title(f'{label}\n{n:,} файлів ({pct:.1f}%)', fontsize=10, fontweight='bold')
    ax.set_xlabel('Розмір (байти)', fontsize=8)
    ax.set_ylabel('Кількість файлів', fontsize=8)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda x, _: human(int(x))))
    ax.tick_params(axis='x', labelsize=7, rotation=30)
    ax.tick_params(axis='y', labelsize=8)

plt.tight_layout()
plt.savefig(f'{OUT}/fig2_zones.png', bbox_inches='tight')
plt.close()
print("fig2 збережено")

# ══════════════════════════════════════════════════════════════
# Рис. 3 — Кумулятивна крива (ECDF)
# ══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 5))

sorted_s = np.sort(sizes)
cdf = np.arange(1, total + 1) / total * 100

ax.plot(sorted_s, cdf, color=BLUE, linewidth=2)
ax.set_xscale('log')
ax.set_xlabel('Розмір файлу (байти, лог. шкала)', fontsize=12)
ax.set_ylabel('Накопичена частка файлів (%)', fontsize=12)
ax.set_title('Кумулятивний розподіл (ECDF)', fontsize=14, fontweight='bold')

for pct_val, col, style in [(50, '#6B7280', ':'), (75, ORANGE, '--'),
                              (90, RED, '--'), (99, '#7C3AED', '-.')]:
    v = np.percentile(sizes, pct_val)
    ax.axvline(v, color=col, linestyle=style, linewidth=1.4,
               label=f'{pct_val}% → {human(int(v))}')
    ax.axhline(pct_val, color=col, linestyle=style, linewidth=0.8, alpha=0.5)

ax.set_xticks(xticks)
ax.set_xticklabels(['1 Б', '1 КБ', '4 КБ', '64 КБ', '1 МБ', '10 МБ', '1 ГБ'], fontsize=9)
ax.set_yticks(range(0, 101, 10))
ax.legend(fontsize=10, loc='lower right')

plt.tight_layout()
plt.savefig(f'{OUT}/fig3_ecdf.png', bbox_inches='tight')
plt.close()
print("fig3 збережено")

# ══════════════════════════════════════════════════════════════
# Рис. 4 — Кругова діаграма категорій
# ══════════════════════════════════════════════════════════════
cat_edges = [0, 1, 4096, 64*1024, 1024**2, 10*1024**2, 1024**3, sizes.max()+1]
cat_labels = ['0 Б (порожні)', '1–4 КБ', '4–64 КБ',
              '64 КБ–1 МБ', '1–10 МБ', '10 МБ–1 ГБ', '>1 ГБ']
cat_counts = []
for lo, hi in zip(cat_edges[:-1], cat_edges[1:]):
    cat_counts.append(((sizes >= lo) & (sizes < hi)).sum())

cat_counts = np.array(cat_counts)
colors_pie = ['#94A3B8','#2563EB','#10B981','#F59E0B','#EF4444','#7C3AED','#EC4899']

fig, ax = plt.subplots(figsize=(9, 7))
wedges, texts, autotexts = ax.pie(
    cat_counts, labels=None, autopct=lambda p: f'{p:.1f}%' if p > 1 else '',
    colors=colors_pie, startangle=140,
    wedgeprops=dict(edgecolor='white', linewidth=1.5),
    pctdistance=0.78)
for at in autotexts:
    at.set_fontsize(9)

ax.legend(wedges, [f'{l}  ({c:,})' for l, c in zip(cat_labels, cat_counts)],
          loc='lower left', bbox_to_anchor=(-0.15, -0.08), fontsize=9)
ax.set_title('Розподіл файлів по категоріях розміру', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{OUT}/fig4_pie.png', bbox_inches='tight')
plt.close()
print("fig4 збережено")

# ══════════════════════════════════════════════════════════════
# Друк фінальної статистики для звіту
# ══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("ФІНАЛЬНА СТАТИСТИКА ДЛЯ ЗВІТУ")
print("="*60)
print(f"Всього файлів проаналізовано: {total:,}")
print(f"Шляхи: /home, /usr, /etc, /var")
print(f"Команда збору: find /home /usr /etc /var -type f -printf \"%s\\n\"")
print()
for p in [50, 75, 80, 85, 90, 95, 99]:
    v = int(np.percentile(sizes, p))
    print(f"  {p}%: ≤ {v:>10,} байт  ({v/1024:.1f} КБ)")

print()
for lo, hi, label, col in zip(cat_edges[:-1], cat_edges[1:], cat_labels, colors_pie):
    n = ((sizes >= lo) & (sizes < hi)).sum()
    print(f"  {label:<20}: {n:>8,}  ({n/total*100:.1f}%)")
