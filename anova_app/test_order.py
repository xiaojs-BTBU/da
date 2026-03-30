import sys
sys.path.append('.')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from modules.visualizer import create_boxplot, create_violinplot
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
fig1 = create_boxplot(data, 'group', 'value', show_means=False)
ax1 = fig1.axes[0]
print('Boxplot order:', [t.get_text() for t in ax1.get_xticklabels()])
plt.close(fig1)
fig2 = create_violinplot(data, 'group', 'value', show_means=False)
ax2 = fig2.axes[0]
print('Violin order:', [t.get_text() for t in ax2.get_xticklabels()])
plt.close(fig2)