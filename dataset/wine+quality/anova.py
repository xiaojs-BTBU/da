import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import pandas as pd
import os

# 1. 获取当前脚本文件所在的绝对目录
base_path = os.path.dirname(os.path.abspath(__file__))

# 2. 拼接数据文件的路径
file_path = os.path.join(base_path, 'winequality-red.csv')

# 3. 读取数据
df = pd.read_csv(file_path, sep=';')
print("数据加载成功！")


# 1. 描述性统计
df.describe().to_csv('descriptive_stats.csv')

# 2. 方差齐性检验 (Levene)
groups = [df[df['quality'] == q]['pH'] for q in sorted(df['quality'].unique())]
stat, p_levene = stats.levene(*groups)

# 3. 如果齐性合格 (p > 0.05)，进行 ANOVA
if p_levene > 0.05:
    f_stat, p_anova = stats.f_oneway(*groups)
    # 事后比较
    tukey = pairwise_tukeyhsd(endog=df['pH'], groups=df['quality'], alpha=0.05)
else:
    p_anova = float('nan')
    
# 4. 绘图 (300 DPI)
plt.figure(figsize=(10, 6), dpi=300)
sns.violinplot(x='quality', y='pH', data=df, inner=None, hue='quality', palette='pastel', legend=False)
sns.stripplot(x='quality', y='pH', data=df, color='black', alpha=0.2, jitter=True)
plt.title(f'pH Analysis (ANOVA p={p_anova:.2e})')
plt.savefig('violin_plot_ph_final.png', dpi=300)