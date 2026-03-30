import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# 创建测试数据，分组变量为字符串数字，但顺序混乱
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

print("原始数据中的唯一组别顺序:", data['group'].unique())
print("分组后均值:")
means = data.groupby('group')['value'].mean()
for group, mean in means.items():
    print(f"  {group}: {mean}")

# 绘制箱线图
fig, ax = plt.subplots()
sns.boxplot(x='group', y='value', data=data, ax=ax)
# 获取 x 轴刻度标签
xticklabels = [t.get_text() for t in ax.get_xticklabels()]
print("箱线图 x 轴刻度顺序:", xticklabels)
plt.close()

# 绘制小提琴图
fig, ax = plt.subplots()
sns.violinplot(x='group', y='value', data=data, ax=ax)
xticklabels = [t.get_text() for t in ax.get_xticklabels()]
print("小提琴图 x 轴刻度顺序:", xticklabels)
plt.close()

# 测试 seaborn 是否按照数据中出现的顺序排序
# 打乱数据顺序
shuffled = data.sample(frac=1).reset_index(drop=True)
print("\n打乱后数据中的唯一组别顺序:", shuffled['group'].unique())
fig, ax = plt.subplots()
sns.boxplot(x='group', y='value', data=shuffled, ax=ax)
xticklabels = [t.get_text() for t in ax.get_xticklabels()]
print("打乱数据后箱线图 x 轴刻度顺序:", xticklabels)
plt.close()

# 测试分组变量为数值型，但转换为字符串的情况
data_numeric = pd.DataFrame({
    'group': np.repeat([2, 1, 3], n_per_group),
    'value': np.concatenate([
        np.random.normal(10, 2, n_per_group),
        np.random.normal(12, 2, n_per_group),
        np.random.normal(15, 3, n_per_group)
    ])
})
data_numeric['group'] = data_numeric['group'].astype(str)
print("\n数值型转换为字符串后的唯一组别顺序:", data_numeric['group'].unique())
fig, ax = plt.subplots()
sns.boxplot(x='group', y='value', data=data_numeric, ax=ax)
xticklabels = [t.get_text() for t in ax.get_xticklabels()]
print("数值型转换为字符串后箱线图 x 轴刻度顺序:", xticklabels)
plt.close()