"""
可视化模块
生成箱线图、小提琴图、带散点的柱状图
集成 statannotations 进行显著性标注
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Union
import warnings
import matplotlib

# 尝试导入 statannotations
try:
    from statannotations.Annotator import Annotator
    STATANNOTATIONS_AVAILABLE = True
except ImportError:
    STATANNOTATIONS_AVAILABLE = False
    warnings.warn("statannotations not installed. Significance annotations will be limited.")

warnings.filterwarnings('ignore')

# 设置中文字体
def set_chinese_font():
    """设置 matplotlib 中文字体"""
    try:
        # 尝试使用系统字体
        import matplotlib.font_manager as fm
        # 查找中文字体
        chinese_fonts = [f for f in fm.fontManager.ttflist if 'hei' in f.name.lower() or 'simhei' in f.name.lower()]
        if chinese_fonts:
            font_name = chinese_fonts[0].name
        else:
            font_name = 'DejaVu Sans'
        
        matplotlib.rcParams['font.sans-serif'] = [font_name]
        matplotlib.rcParams['axes.unicode_minus'] = False
    except:
        matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

set_chinese_font()

# 设置 Seaborn 样式
sns.set_style("whitegrid")
sns.set_context("notebook", font_scale=1.2)

def create_boxplot(df: pd.DataFrame,
                   group_var: str,
                   measure_var: str,
                   posthoc_results: Optional[Dict] = None,
                   figsize: Tuple[int, int] = (10, 6),
                   palette: str = "Set2",
                   alpha: float = 0.05,
                   show_points: bool = True,
                   show_means: bool = True) -> plt.Figure:
    """
    创建箱线图
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    posthoc_results : Dict, optional
        事后检验结果
    figsize : Tuple[int, int], optional
        图形尺寸，默认 (10, 6)
    palette : str, optional
        调色板，默认 "Set2"
    alpha : float, optional
        显著性水平，默认 0.05
    show_points : bool, optional
        是否显示散点，默认 True
    show_means : bool, optional
        是否显示均值，默认 True
    
    Returns
    -------
    plt.Figure
        箱线图
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # 确保分组变量为字符串
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    # 确定组别顺序（尝试按数值排序）
    unique_groups = df[group_var].unique()
    try:
        # 尝试转换为浮点数排序
        order = sorted(unique_groups, key=lambda g: float(g))
    except ValueError:
        # 如果转换失败，按字符串排序
        order = sorted(unique_groups)
    
    # 创建箱线图
    boxplot = sns.boxplot(x=group_var, y=measure_var, data=df,
                          palette=palette, width=0.6, ax=ax,
                          showfliers=False, order=order)
    
    # 添加散点（抖动）
    if show_points:
        sns.stripplot(x=group_var, y=measure_var, data=df,
                      color='black', alpha=0.3, jitter=True,
                      size=4, ax=ax, order=order)
    
    # 添加均值标记
    if show_means:
        # 获取图表的组别顺序（按照 x 轴刻度顺序）
        xtick_labels = [t.get_text() for t in ax.get_xticklabels()]
        # 计算均值，并按照图表顺序排列
        means = df.groupby(group_var)[measure_var].mean()
        for i, group in enumerate(xtick_labels):
            if group in means.index:
                mean = means.loc[group]
                ax.plot(i, mean, 'o', markersize=10, markerfacecolor='white',
                        markeredgecolor='red', markeredgewidth=2, label='均值' if i == 0 else "")
    
    # 添加显著性标注
    if posthoc_results and measure_var in posthoc_results.get('by_variable', {}):
        var_results = posthoc_results['by_variable'][measure_var]
        if var_results.get('pairwise_results'):
            add_significance_annotations(ax, df, group_var, measure_var, 
                                         var_results, plot_type='boxplot')
    
    # 设置标题和标签
    ax.set_title(f'{measure_var} 的箱线图（按 {group_var} 分组）', fontsize=16, pad=20)
    ax.set_xlabel(group_var, fontsize=14)
    ax.set_ylabel(measure_var, fontsize=14)
    
    # 添加网格
    ax.grid(True, alpha=0.3)
    
    # 添加图例
    if show_means:
        ax.legend(loc='upper right')
    
    plt.tight_layout()
    return fig

def create_violinplot(df: pd.DataFrame,
                      group_var: str,
                      measure_var: str,
                      posthoc_results: Optional[Dict] = None,
                      figsize: Tuple[int, int] = (10, 6),
                      palette: str = "muted",
                      alpha: float = 0.05,
                      show_points: bool = True,
                      show_means: bool = True,
                      inner: str = "quartile") -> plt.Figure:
    """
    创建小提琴图
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    posthoc_results : Dict, optional
        事后检验结果
    figsize : Tuple[int, int], optional
        图形尺寸，默认 (10, 6)
    palette : str, optional
        调色板，默认 "muted"
    alpha : float, optional
        显著性水平，默认 0.05
    show_points : bool, optional
        是否显示散点，默认 True
    show_means : bool, optional
        是否显示均值，默认 True
    inner : str, optional
        内部显示，默认 "quartile"
    
    Returns
    -------
    plt.Figure
        小提琴图
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # 确保分组变量为字符串
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    # 确定组别顺序（尝试按数值排序）
    unique_groups = df[group_var].unique()
    try:
        # 尝试转换为浮点数排序
        order = sorted(unique_groups, key=lambda g: float(g))
    except ValueError:
        # 如果转换失败，按字符串排序
        order = sorted(unique_groups)
    
    # 创建小提琴图
    violin = sns.violinplot(x=group_var, y=measure_var, data=df,
                            palette=palette, inner=inner, ax=ax,
                            cut=0, bw=0.2, order=order)
    
    # 添加散点（抖动）
    if show_points:
        sns.stripplot(x=group_var, y=measure_var, data=df,
                      color='black', alpha=0.3, jitter=True,
                      size=4, ax=ax, zorder=1, order=order)
    
    # 添加均值标记
    if show_means:
        # 获取图表的组别顺序（按照 x 轴刻度顺序）
        xtick_labels = [t.get_text() for t in ax.get_xticklabels()]
        # 计算均值，并按照图表顺序排列
        means = df.groupby(group_var)[measure_var].mean()
        for i, group in enumerate(xtick_labels):
            if group in means.index:
                mean = means.loc[group]
                ax.plot(i, mean, 'o', markersize=10, markerfacecolor='white',
                        markeredgecolor='red', markeredgewidth=2, label='均值' if i == 0 else "")
    
    # 添加显著性标注
    if posthoc_results and measure_var in posthoc_results.get('by_variable', {}):
        var_results = posthoc_results['by_variable'][measure_var]
        if var_results.get('pairwise_results'):
            add_significance_annotations(ax, df, group_var, measure_var,
                                         var_results, plot_type='violinplot')
    
    # 设置标题和标签
    ax.set_title(f'{measure_var} 的小提琴图（按 {group_var} 分组）', fontsize=16, pad=20)
    ax.set_xlabel(group_var, fontsize=14)
    ax.set_ylabel(measure_var, fontsize=14)
    
    # 添加网格
    ax.grid(True, alpha=0.3)
    
    # 添加图例
    if show_means:
        ax.legend(loc='upper right')
    
    plt.tight_layout()
    return fig

def create_barplot_with_scatter(df: pd.DataFrame,
                                group_var: str,
                                measure_var: str,
                                posthoc_results: Optional[Dict] = None,
                                figsize: Tuple[int, int] = (10, 6),
                                palette: str = "Blues_d",
                                alpha: float = 0.05,
                                error_bars: str = "sd",
                                jitter: float = 0.2) -> plt.Figure:
    """
    创建带散点的柱状图
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    posthoc_results : Dict, optional
        事后检验结果
    figsize : Tuple[int, int], optional
        图形尺寸，默认 (10, 6)
    palette : str, optional
        调色板，默认 "Blues_d"
    alpha : float, optional
        显著性水平，默认 0.05
    error_bars : str, optional
        误差条类型，"sd"（标准差）或 "se"（标准误），默认 "sd"
    jitter : float, optional
        散点抖动程度，默认 0.2
    
    Returns
    -------
    plt.Figure
        柱状图
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # 确保分组变量为字符串
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    # 计算统计量
    stats_df = df.groupby(group_var)[measure_var].agg(['mean', 'std', 'count']).reset_index()
    stats_df['se'] = stats_df['std'] / np.sqrt(stats_df['count'])
    
    # 选择误差条
    if error_bars == 'se':
        yerr = stats_df['se'].values
    else:  # sd
        yerr = stats_df['std'].values
    
    # 确定组别顺序（尝试按数值排序）
    unique_groups = df[group_var].unique()
    try:
        # 尝试转换为浮点数排序
        order = sorted(unique_groups, key=lambda g: float(g))
    except ValueError:
        # 如果转换失败，按字符串排序
        order = sorted(unique_groups)
    
    # 按顺序重新排序 stats_df
    stats_df = stats_df.set_index(group_var).loc[order].reset_index()
    
    # 重新计算 yerr（因为 stats_df 顺序已变）
    if error_bars == 'se':
        yerr = stats_df['se'].values
    else:  # sd
        yerr = stats_df['std'].values
    
    # 创建柱状图
    print(f"[DEBUG] 柱状图宽度参数: 0.4")
    bars = ax.bar(stats_df[group_var], stats_df['mean'],
                  yerr=yerr, capsize=5, alpha=0.7,
                  color=sns.color_palette(palette, len(stats_df)),
                  edgecolor='black', linewidth=1, width=0.4)
    
    # 添加散点（抖动）
    for i, group in enumerate(order):
        group_data = df[df[group_var] == group][measure_var].dropna()
        if len(group_data) > 0:
            # 添加抖动
            x_pos = i + np.random.uniform(-jitter, jitter, len(group_data))
            ax.scatter(x_pos, group_data, color='black', alpha=0.4,
                       s=30, edgecolors='white', linewidth=0.5, zorder=10)
    
    # 添加显著性标注
    if posthoc_results and measure_var in posthoc_results.get('by_variable', {}):
        var_results = posthoc_results['by_variable'][measure_var]
        if var_results.get('pairwise_results'):
            add_significance_annotations(ax, df, group_var, measure_var,
                                         var_results, plot_type='barplot')
    
    # 设置标题和标签
    ax.set_title(f'{measure_var} 的柱状图（均值±{error_bars.upper()}，按 {group_var} 分组）', 
                 fontsize=16, pad=20)
    ax.set_xlabel(group_var, fontsize=14)
    ax.set_ylabel(measure_var, fontsize=14)
    
    # 添加数值标签
    for i, (_, row) in enumerate(stats_df.iterrows()):
        ax.text(i, row['mean'] + yerr[i] + 0.02 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
                f'{row["mean"]:.2f}', ha='center', va='bottom', fontsize=10)
    
    # 添加网格
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    return fig

def add_significance_annotations(ax,
                                 df: pd.DataFrame,
                                 group_var: str,
                                 measure_var: str,
                                 posthoc_results: Dict,
                                 plot_type: str = 'boxplot',
                                 pvalue_format: str = 'simple') -> None:
    """
    添加显著性标注
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        坐标轴对象
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    posthoc_results : Dict
        事后检验结果
    plot_type : str, optional
        图形类型，'boxplot', 'violinplot', 'barplot'
    pvalue_format : str, optional
        P 值格式，'simple'（星号）或 'full'（具体数值）
    """
    if not STATANNOTATIONS_AVAILABLE:
        # 简单的手动标注
        add_simple_annotations(ax, df, group_var, measure_var, posthoc_results, plot_type)
        return
    
    try:
        # 使用 statannotations
        pairs = []
        pvalues = []
        
        for result in posthoc_results.get('pairwise_results', []):
            pairs.append((result['group1'], result['group2']))
            pvalues.append(result['p_value'])
        
        if not pairs:
            return
        
        # 配置 annotator
        # 使用图表的组别顺序（按照 x 轴刻度顺序）
        order = [t.get_text() for t in ax.get_xticklabels()]
        annotator = Annotator(ax, pairs, data=df, x=group_var, y=measure_var,
                              order=order)
        annotator.configure(test=None, text_format='star', loc='inside' if plot_type == 'barplot' else 'outside')
        annotator.set_pvalues(pvalues)
        annotator.annotate()
        
    except Exception as e:
        # 回退到简单标注
        add_simple_annotations(ax, df, group_var, measure_var, posthoc_results, plot_type)

def add_simple_annotations(ax,
                           df: pd.DataFrame,
                           group_var: str,
                           measure_var: str,
                           posthoc_results: Dict,
                           plot_type: str) -> None:
    """
    添加简单的显著性标注（星号）
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        坐标轴对象
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    posthoc_results : Dict
        事后检验结果
    plot_type : str
        图形类型
    """
    # 获取组顺序（按照图表的 x 轴刻度顺序）
    groups = [t.get_text() for t in ax.get_xticklabels()]
    group_indices = {group: i for i, group in enumerate(groups)}
    
    # 获取数据范围
    y_min, y_max = ax.get_ylim()
    y_range = y_max - y_min
    
    # 计算每对组的最大 y 值
    group_stats = df.groupby(group_var)[measure_var].agg(['max', 'min', 'mean']).to_dict()
    
    for result in posthoc_results.get('pairwise_results', []):
        if not result.get('significant', False):
            continue
        
        group1, group2 = result['group1'], result['group2']
        if group1 not in group_indices or group2 not in group_indices:
            continue
        
        i1, i2 = group_indices[group1], group_indices[group2]
        
        # 计算标注位置
        if plot_type == 'barplot':
            y1 = group_stats['mean'][group1] if group1 in group_stats['mean'] else 0
            y2 = group_stats['mean'][group2] if group2 in group_stats['mean'] else 0
            y_top = max(y1, y2) + 0.1 * y_range
        else:
            y1 = group_stats['max'][group1] if group1 in group_stats['max'] else 0
            y2 = group_stats['max'][group2] if group2 in group_stats['max'] else 0
            y_top = max(y1, y2) + 0.05 * y_range
        
        # 绘制标注线
        line_y = y_top + 0.02 * y_range
        ax.plot([i1, i1, i2, i2], [line_y, line_y + 0.01 * y_range, 
                                   line_y + 0.01 * y_range, line_y], 
                color='black', linewidth=1)
        
        # 添加星号
        p_value = result.get('p_value', 1.0)
        if p_value < 0.001:
            star = '***'
        elif p_value < 0.01:
            star = '**'
        elif p_value < 0.05:
            star = '*'
        else:
            star = 'ns'
        
        ax.text((i1 + i2) / 2, line_y + 0.015 * y_range, star,
                ha='center', va='bottom', fontsize=12, fontweight='bold')

def create_combined_plot(df: pd.DataFrame,
                         group_var: str,
                         measure_var: str,
                         posthoc_results: Optional[Dict] = None,
                         figsize: Tuple[int, int] = (15, 5)) -> plt.Figure:
    """
    创建组合图（箱线图、小提琴图、柱状图）
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    posthoc_results : Dict, optional
        事后检验结果
    figsize : Tuple[int, int], optional
        图形尺寸，默认 (15, 5)
    
    Returns
    -------
    plt.Figure
        组合图
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    # 箱线图
    create_boxplot(df, group_var, measure_var, posthoc_results)
    ax1 = axes[0]
    box_fig = create_boxplot(df, group_var, measure_var, posthoc_results)
    ax1.imshow(box_fig.canvas.renderer.buffer_rgba())
    ax1.axis('off')
    ax1.set_title('箱线图', fontsize=14)
    plt.close(box_fig)
    
    # 小提琴图
    violin_fig = create_violinplot(df, group_var, measure_var, posthoc_results)
    ax2 = axes[1]
    ax2.imshow(violin_fig.canvas.renderer.buffer_rgba())
    ax2.axis('off')
    ax2.set_title('小提琴图', fontsize=14)
    plt.close(violin_fig)
    
    # 柱状图
    bar_fig = create_barplot_with_scatter(df, group_var, measure_var, posthoc_results)
    ax3 = axes[2]
    ax3.imshow(bar_fig.canvas.renderer.buffer_rgba())
    ax3.axis('off')
    ax3.set_title('带散点的柱状图', fontsize=14)
    plt.close(bar_fig)
    
    # 添加总标题
    fig.suptitle(f'{measure_var} 的可视化（按 {group_var} 分组）', fontsize=16, y=1.05)
    
    plt.tight_layout()
    return fig

def save_figure(fig: plt.Figure, 
                filename: str, 
                dpi: int = 300,
                format: str = 'png') -> str:
    """
    保存图形
    
    Parameters
    ----------
    fig : plt.Figure
        图形对象
    filename : str
        文件名（不含扩展名）
    dpi : int, optional
        分辨率，默认 300
    format : str, optional
        格式，默认 'png'
    
    Returns
    -------
    str
        保存的文件路径
    """
    import os
    # 确保目录存在
    os.makedirs('output', exist_ok=True)
    
    # 添加扩展名
    if not filename.lower().endswith(f'.{format}'):
        filename = f'{filename}.{format}'
    
    filepath = os.path.join('output', filename)
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', format=format)
    
    return filepath

if __name__ == "__main__":
    # 模块测试
    import sys
    sys.path.append('..')
    
    # 创建测试数据
    np.random.seed(42)
    n_per_group = 30
    groups = ['A', 'B', 'C']
    
    test_data = pd.DataFrame({
        'group': np.repeat(groups, n_per_group),
        'value1': np.concatenate([
            np.random.normal(10, 2, n_per_group),
            np.random.normal(12, 2, n_per_group),
            np.random.normal(15, 3, n_per_group)
        ])
    })
    
    print("创建箱线图测试")
    fig1 = create_boxplot(test_data, 'group', 'value1')
    plt.close(fig1)
    print("箱线图创建成功")
    
    print("\n创建小提琴图测试")
    fig2 = create_violinplot(test_data, 'group', 'value1')
    plt.close(fig2)
    print("小提琴图创建成功")
    
    print("\n创建柱状图测试")
    fig3 = create_barplot_with_scatter(test_data, 'group', 'value1')
    plt.close(fig3)
    print("柱状图创建成功")