import sys
sys.path.append('.')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from modules.visualizer import create_barplot_with_scatter
np.random.seed(42)
groups = ['2', '1', '3']
n_per_group = 10
data = pd.DataFrame({
    'group': np.repeat(groups, n_per_group),
    'value': np.concatenate([
        np.random.normal(10, 2, n_per_group),
        np.random.normal(12, 2, n_per_group),
        np.random.normal(15, 3, n_per_group)
    ])
})
fig = create_barplot_with_scatter(data, 'group', 'value')
ax = fig.axes[0]
xticks = [t.get_text() for t in ax.get_xticklabels()]
print('Barplot xticks:', xticks)
bars = ax.patches
if bars:
    width = bars[0].get_width()
    print('Bar width:', width)
plt.close(fig)
# 验证顺序
if xticks == ['1', '2', '3']:
    print('PASS: Barplot order correct')
else:
    print('FAIL: Barplot order incorrect')
# 验证宽度是否接近0.8
if abs(width - 0.8) < 0.01:
    print('PASS: Bar width correct')
else:
    print('WARN: Bar width unexpected')