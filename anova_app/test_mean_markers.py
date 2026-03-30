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

# 辅助函数：获取均值标记的x坐标
def get_mean_marker_x(ax):
    # 查找红色边缘的圆圈标记
    for line in ax.lines:
        if line.get_marker() == 'o' and line.get_markeredgecolor() == 'red':
            xdata = line.get_xdata()
            if len(xdata) > 0:
                return xdata[0]
    return None

# 箱线图
fig1 = create_boxplot(data, 'group', 'value', show_means=True)
ax1 = fig1.axes[0]
xticks1 = [t.get_text() for t in ax1.get_xticklabels()]
print('Boxplot xticks:', xticks1)
for i, group in enumerate(xticks1):
    mean = data[data['group'] == group]['value'].mean()
    print(f'  Group {group} mean: {mean}')
mean_x = get_mean_marker_x(ax1)
if mean_x is not None:
    print(f'Mean marker x coordinate: {mean_x}')
    # 检查是否每个组都有一个均值标记
    # 实际上，每个组都有一个标记，但我们需要收集所有标记
    # 更简单的方法：收集所有红色圆圈
    mean_xs = []
    for line in ax1.lines:
        if line.get_marker() == 'o' and line.get_markeredgecolor() == 'red':
            mean_xs.append(line.get_xdata()[0])
    print('All mean marker x coordinates:', mean_xs)
    # 验证顺序
    expected_xs = list(range(len(xticks1)))
    if mean_xs == expected_xs:
        print('✅ Boxplot mean markers aligned with xticks')
    else:
        print('❌ Boxplot mean markers misaligned')
else:
    print('No mean markers found')
plt.close(fig1)

# 小提琴图
fig2 = create_violinplot(data, 'group', 'value', show_means=True)
ax2 = fig2.axes[0]
xticks2 = [t.get_text() for t in ax2.get_xticklabels()]
print('Violin xticks:', xticks2)
mean_xs2 = []
for line in ax2.lines:
    if line.get_marker() == 'o' and line.get_markeredgecolor() == 'red':
        mean_xs2.append(line.get_xdata()[0])
print('All mean marker x coordinates:', mean_xs2)
if mean_xs2 == list(range(len(xticks2))):
    print('✅ Violin mean markers aligned with xticks')
else:
    print('❌ Violin mean markers misaligned')
plt.close(fig2)