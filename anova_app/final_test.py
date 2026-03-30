import sys
sys.path.append('.')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from modules.visualizer import create_boxplot, create_violinplot, create_barplot_with_scatter

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
print("=== 综合测试修复结果 ===")
print("原始数据组别顺序:", data['group'].unique())
print("期望的横坐标顺序: ['1', '2', '3']")

# 辅助函数：获取均值标记的x坐标
def get_mean_marker_xs(ax):
    xs = []
    for line in ax.lines:
        if line.get_marker() == 'o' and line.get_markeredgecolor() == 'red':
            xdata = line.get_xdata()
            if len(xdata) > 0:
                xs.append(xdata[0])
    return xs

# 1. 箱线图
fig1 = create_boxplot(data, 'group', 'value', show_means=True)
ax1 = fig1.axes[0]
xticks1 = [t.get_text() for t in ax1.get_xticklabels()]
print("\n1. 箱线图:")
print("   横坐标顺序:", xticks1)
mean_xs1 = get_mean_marker_xs(ax1)
print("   均值标记x坐标:", mean_xs1)
if xticks1 == ['1', '2', '3']:
    print("   ✅ 横坐标排序正确")
else:
    print("   ❌ 横坐标排序错误")
if mean_xs1 == [0, 1, 2]:
    print("   ✅ 均值标记对齐正确")
else:
    print("   ❌ 均值标记对齐错误")
plt.close(fig1)

# 2. 小提琴图
fig2 = create_violinplot(data, 'group', 'value', show_means=True)
ax2 = fig2.axes[0]
xticks2 = [t.get_text() for t in ax2.get_xticklabels()]
print("\n2. 小提琴图:")
print("   横坐标顺序:", xticks2)
mean_xs2 = get_mean_marker_xs(ax2)
print("   均值标记x坐标:", mean_xs2)
if xticks2 == ['1', '2', '3']:
    print("   ✅ 横坐标排序正确")
else:
    print("   ❌ 横坐标排序错误")
if mean_xs2 == [0, 1, 2]:
    print("   ✅ 均值标记对齐正确")
else:
    print("   ❌ 均值标记对齐错误")
plt.close(fig2)

# 3. 柱状图
fig3 = create_barplot_with_scatter(data, 'group', 'value')
ax3 = fig3.axes[0]
xticks3 = [t.get_text() for t in ax3.get_xticklabels()]
print("\n3. 柱状图:")
print("   横坐标顺序:", xticks3)
# 检查柱子宽度
bars = ax3.patches
if bars:
    width = bars[0].get_width()
    print("   柱子宽度:", width)
    if abs(width - 0.8) < 0.01:
        print("   ✅ 柱子宽度正常 (0.8)")
    else:
        print("   ⚠️ 柱子宽度异常，当前宽度:", width)
else:
    print("   未找到柱子")
if xticks3 == ['1', '2', '3']:
    print("   ✅ 横坐标排序正确")
else:
    print("   ❌ 横坐标排序错误")
plt.close(fig3)

print("\n=== 测试完成 ===")