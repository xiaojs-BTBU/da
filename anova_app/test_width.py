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
bars = ax.patches
if bars:
    width = bars[0].get_width()
    print('Current bar width:', width)
    # 检查宽度是否与代码中的0.8匹配
    if abs(width - 0.8) < 0.01:
        print('Width matches 0.8 (default)')
    else:
        print('Width does NOT match 0.8, actual:', width)
else:
    print('No bars found')
plt.close(fig)

# 尝试直接修改函数的默认宽度（猴子补丁）
import modules.visualizer as viz
original_func = viz.create_barplot_with_scatter
# 创建一个新函数，但我们直接检查代码
# 读取文件内容
with open('modules/visualizer.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'width=0.8' in content:
        print("Found 'width=0.8' in visualizer.py")
    else:
        print("'width=0.8' NOT FOUND in visualizer.py")
    # 查找所有 width= 出现位置
    import re
    matches = re.findall(r'width\s*=\s*[\d.]+', content)
    print('All width assignments:', matches)