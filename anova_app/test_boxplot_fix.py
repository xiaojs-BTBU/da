import sys
sys.path.append('.')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from modules.visualizer import create_boxplot, create_violinplot, create_barplot_with_scatter

# 创建测试数据，组别顺序混乱，字符串数字
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
print("原始数据组别顺序:", data['group'].unique())
print("分组均值:")
means = data.groupby('group')['value'].mean()
for group, mean in means.items():
    print(f"  {group}: {mean}")

# 测试箱线图
fig1 = create_boxplot(data, 'group', 'value', show_means=True)
# 获取当前图形的坐标轴
ax1 = fig1.axes[0]
xtick_labels = [t.get_text() for t in ax1.get_xticklabels()]
print("箱线图横坐标顺序:", xtick_labels)
# 检查均值标记的x坐标
mean_markers = [child for child in ax1.get_children() if child.get_label() == '均值' or child.get_label().startswith('均值')]
if mean_markers:
    for marker in mean_markers:
        xdata = marker.get_xdata()
        print(f"均值标记x坐标: {xdata}")
else:
    # 可能通过plot添加，检查lines
    lines = ax1.lines
    for line in lines:
        if line.get_marker() == 'o' and line.get_markeredgecolor() == 'red':
            xdata = line.get_xdata()
            print(f"均值标记x坐标 (line): {xdata}")
# 保存图像
fig1.savefig('test_boxplot_fixed.png', dpi=100)
plt.close(fig1)
print("箱线图已保存")

# 测试小提琴图
fig2 = create_violinplot(data, 'group', 'value', show_means=True)
ax2 = fig2.axes[0]
xtick_labels2 = [t.get_text() for t in ax2.get_xticklabels()]
print("小提琴图横坐标顺序:", xtick_labels2)
fig2.savefig('test_violin_fixed.png', dpi=100)
plt.close(fig2)
print("小提琴图已保存")

# 测试柱状图
fig3 = create_barplot_with_scatter(data, 'group', 'value')
ax3 = fig3.axes[0]
xtick_labels3 = [t.get_text() for t in ax3.get_xticklabels()]
print("柱状图横坐标顺序:", xtick_labels3)
# 检查柱子宽度
bars = ax3.patches
if bars:
    width = bars[0].get_width()
    print(f"柱子宽度: {width}")
fig3.savefig('test_bar_fixed.png', dpi=100)
plt.close(fig3)
print("柱状图已保存")

# 验证顺序是否符合数值排序
expected_order = ['1', '2', '3']
if xtick_labels == expected_order:
    print("✅ 箱线图横坐标已按数值排序")
else:
    print("❌ 箱线图横坐标未按数值排序")
if xtick_labels2 == expected_order:
    print("✅ 小提琴图横坐标已按数值排序")
else:
    print("❌ 小提琴图横坐标未按数值排序")
if xtick_labels3 == expected_order:
    print("✅ 柱状图横坐标已按数值排序")
else:
    print("❌ 柱状图横坐标未按数值排序")

print("\n测试完成。")