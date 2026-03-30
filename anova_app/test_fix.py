import sys
sys.path.append('.')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from modules.visualizer import create_boxplot, create_violinplot

# 创建测试数据，组别顺序混乱
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

print("原始数据中的组别顺序:", data['group'].unique())
print("分组均值 (按组别排序):")
means = data.groupby('group')['value'].mean()
for group, mean in means.items():
    print(f"  {group}: {mean}")

# 生成箱线图
fig1 = create_boxplot(data, 'group', 'value', show_means=True)
# 保存图像以供检查
fig1.savefig('test_boxplot.png', dpi=100)
plt.close(fig1)
print("箱线图已保存为 test_boxplot.png")

# 生成小提琴图
fig2 = create_violinplot(data, 'group', 'value', show_means=True)
fig2.savefig('test_violin.png', dpi=100)
plt.close(fig2)
print("小提琴图已保存为 test_violin.png")

# 检查均值标记位置（通过模拟）
# 我们可以手动计算图表的 x 轴顺序
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

fig, ax = plt.subplots()
# 绘制箱线图以获取刻度顺序
import seaborn as sns
sns.boxplot(x='group', y='value', data=data, ax=ax)
xtick_labels = [t.get_text() for t in ax.get_xticklabels()]
print("箱线图 x 轴刻度顺序:", xtick_labels)
plt.close(fig)

# 验证均值标记是否与刻度顺序对齐
# 均值标记的 x 坐标应该与刻度索引相同
# 我们可以在创建图表后检查，但这里仅打印信息
print("\n验证:")
print("如果均值标记位置正确，则每个组别的均值应位于其对应的刻度位置。")
print("请检查生成的图像中红圈是否位于每个箱子的中心。")

# 另外测试柱状图（如果需要）
from modules.visualizer import create_barplot_with_scatter
fig3 = create_barplot_with_scatter(data, 'group', 'value')
fig3.savefig('test_bar.png', dpi=100)
plt.close(fig3)
print("柱状图已保存为 test_bar.png")

print("\n测试完成。")