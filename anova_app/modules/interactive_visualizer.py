"""
交互式可视化模块
使用 Plotly 或 Altair 生成交互式图表
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import warnings

warnings.filterwarnings('ignore')

# 尝试导入 Plotly
try:
    import plotly.graph_objects as go
    import plotly.express as px
    import plotly.subplots as sp
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    warnings.warn("Plotly not installed. Interactive visualizations will not be available.")

# 尝试导入 Altair
try:
    import altair as alt
    ALTAR_AVAILABLE = True
except ImportError:
    ALTAR_AVAILABLE = False
    warnings.warn("Altair not installed. Altair visualizations will not be available.")

def create_interactive_boxplot(df: pd.DataFrame,
                               group_var: str,
                               measure_var: str,
                               posthoc_results: Optional[Dict] = None,
                               title: Optional[str] = None,
                               height: int = 500,
                               width: int = 800,
                               show_points: bool = True,
                               show_means: bool = True) -> go.Figure:
    """
    创建交互式箱线图（Plotly）
    
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
    title : str, optional
        标题
    height : int, optional
        高度，默认 500
    width : int, optional
        宽度，默认 800
    show_points : bool, optional
        是否显示散点，默认 True
    show_means : bool, optional
        是否显示均值，默认 True
    
    Returns
    -------
    go.Figure
        Plotly 图形对象
    """
    if not PLOTLY_AVAILABLE:
        raise ImportError("Plotly is not installed. Please install plotly to use interactive visualizations.")
    
    # 确保分组变量为字符串
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    # 创建箱线图
    if show_points:
        # 使用散点叠加
        fig = px.box(df, x=group_var, y=measure_var, 
                     color=group_var, points="all",
                     title=title or f'{measure_var} 的箱线图（按 {group_var} 分组）',
                     height=height, width=width)
    else:
        fig = px.box(df, x=group_var, y=measure_var,
                     color=group_var, points=False,
                     title=title or f'{measure_var} 的箱线图（按 {group_var} 分组）',
                     height=height, width=width)
    
    # 添加均值线
    if show_means:
        means = df.groupby(group_var)[measure_var].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=means[group_var],
            y=means[measure_var],
            mode='markers',
            marker=dict(symbol='diamond', size=12, color='red'),
            name='均值',
            hovertemplate='均值: %{y:.2f}<extra></extra>'
        ))
    
    # 添加显著性标注
    if posthoc_results and measure_var in posthoc_results.get('by_variable', {}):
        var_results = posthoc_results['by_variable'][measure_var]
        if var_results.get('pairwise_results'):
            add_interactive_annotations(fig, df, group_var, measure_var, var_results, 'boxplot')
    
    # 更新布局
    fig.update_layout(
        xaxis_title=group_var,
        yaxis_title=measure_var,
        hovermode='closest',
        showlegend=True,
        boxmode='group'
    )
    
    return fig

def create_interactive_violinplot(df: pd.DataFrame,
                                  group_var: str,
                                  measure_var: str,
                                  posthoc_results: Optional[Dict] = None,
                                  title: Optional[str] = None,
                                  height: int = 500,
                                  width: int = 800,
                                  show_points: bool = True,
                                  show_means: bool = True) -> go.Figure:
    """
    创建交互式小提琴图（Plotly）
    
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
    title : str, optional
        标题
    height : int, optional
        高度，默认 500
    width : int, optional
        宽度，默认 800
    show_points : bool, optional
        是否显示散点，默认 True
    show_means : bool, optional
        是否显示均值，默认 True
    
    Returns
    -------
    go.Figure
        Plotly 图形对象
    """
    if not PLOTLY_AVAILABLE:
        raise ImportError("Plotly is not installed. Please install plotly to use interactive visualizations.")
    
    # 确保分组变量为字符串
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    # 创建小提琴图
    if show_points:
        fig = px.violin(df, x=group_var, y=measure_var,
                        color=group_var, box=True, points="all",
                        title=title or f'{measure_var} 的小提琴图（按 {group_var} 分组）',
                        height=height, width=width)
    else:
        fig = px.violin(df, x=group_var, y=measure_var,
                        color=group_var, box=True, points=False,
                        title=title or f'{measure_var} 的小提琴图（按 {group_var} 分组）',
                        height=height, width=width)
    
    # 添加均值线
    if show_means:
        means = df.groupby(group_var)[measure_var].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=means[group_var],
            y=means[measure_var],
            mode='markers',
            marker=dict(symbol='diamond', size=12, color='red'),
            name='均值',
            hovertemplate='均值: %{y:.2f}<extra></extra>'
        ))
    
    # 添加显著性标注
    if posthoc_results and measure_var in posthoc_results.get('by_variable', {}):
        var_results = posthoc_results['by_variable'][measure_var]
        if var_results.get('pairwise_results'):
            add_interactive_annotations(fig, df, group_var, measure_var, var_results, 'violinplot')
    
    # 更新布局
    fig.update_layout(
        xaxis_title=group_var,
        yaxis_title=measure_var,
        hovermode='closest',
        showlegend=True
    )
    
    return fig

def create_interactive_barplot(df: pd.DataFrame,
                               group_var: str,
                               measure_var: str,
                               posthoc_results: Optional[Dict] = None,
                               title: Optional[str] = None,
                               height: int = 500,
                               width: int = 800,
                               error_bars: str = 'sd',
                               show_points: bool = True) -> go.Figure:
    """
    创建交互式柱状图（Plotly）
    
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
    title : str, optional
        标题
    height : int, optional
        高度，默认 500
    width : int, optional
        宽度，默认 800
    error_bars : str, optional
        误差条类型，"sd"（标准差）或 "se"（标准误），默认 "sd"
    show_points : bool, optional
        是否显示散点，默认 True
    
    Returns
    -------
    go.Figure
        Plotly 图形对象
    """
    if not PLOTLY_AVAILABLE:
        raise ImportError("Plotly is not installed. Please install plotly to use interactive visualizations.")
    
    # 确保分组变量为字符串
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    # 计算统计量
    stats_df = df.groupby(group_var)[measure_var].agg(['mean', 'std', 'count']).reset_index()
    stats_df['se'] = stats_df['std'] / np.sqrt(stats_df['count'])
    
    # 选择误差条
    if error_bars == 'se':
        yerr = stats_df['se'].values
        error_bar_title = '标准误'
    else:  # sd
        yerr = stats_df['std'].values
        error_bar_title = '标准差'
    
    # 创建柱状图
    fig = go.Figure()
    
    # 添加柱状
    fig.add_trace(go.Bar(
        x=stats_df[group_var],
        y=stats_df['mean'],
        error_y=dict(type='data', array=yerr, visible=True),
        name='均值',
        marker_color='lightblue',
        hovertemplate='均值: %{y:.2f}<br>'+error_bar_title+': %{error_y.array:.2f}<extra></extra>'
    ))
    
    # 添加散点
    if show_points:
        for group in stats_df[group_var]:
            group_data = df[df[group_var] == group][measure_var].dropna()
            fig.add_trace(go.Scatter(
                x=[group] * len(group_data),
                y=group_data,
                mode='markers',
                marker=dict(color='black', size=6, opacity=0.5),
                name='原始数据',
                showlegend=False,
                hovertemplate='值: %{y:.2f}<extra></extra>'
            ))
    
    # 添加显著性标注
    if posthoc_results and measure_var in posthoc_results.get('by_variable', {}):
        var_results = posthoc_results['by_variable'][measure_var]
        if var_results.get('pairwise_results'):
            add_interactive_annotations(fig, df, group_var, measure_var, var_results, 'barplot')
    
    # 更新布局
    fig.update_layout(
        title=title or f'{measure_var} 的柱状图（均值±{error_bar_title}，按 {group_var} 分组）',
        xaxis_title=group_var,
        yaxis_title=measure_var,
        height=height,
        width=width,
        hovermode='closest',
        showlegend=True,
        bargap=0.2
    )
    
    return fig

def create_interactive_combined_plot(df: pd.DataFrame,
                                     group_var: str,
                                     measure_var: str,
                                     posthoc_results: Optional[Dict] = None,
                                     height: int = 600,
                                     width: int = 1200) -> go.Figure:
    """
    创建交互式组合图（箱线图、小提琴图、柱状图）
    
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
    height : int, optional
        高度，默认 600
    width : int, optional
        宽度，默认 1200
    
    Returns
    -------
    go.Figure
        Plotly 图形对象
    """
    if not PLOTLY_AVAILABLE:
        raise ImportError("Plotly is not installed. Please install plotly to use interactive visualizations.")
    
    # 创建子图
    fig = sp.make_subplots(
        rows=1, cols=3,
        subplot_titles=('箱线图', '小提琴图', '柱状图'),
        horizontal_spacing=0.1
    )
    
    # 箱线图
    box_fig = create_interactive_boxplot(df, group_var, measure_var, posthoc_results, 
                                         title=None, height=height, width=width//3)
    for trace in box_fig.data:
        trace.showlegend = False
        fig.add_trace(trace, row=1, col=1)
    
    # 小提琴图
    violin_fig = create_interactive_violinplot(df, group_var, measure_var, posthoc_results,
                                               title=None, height=height, width=width//3)
    for trace in violin_fig.data:
        trace.showlegend = False
        fig.add_trace(trace, row=1, col=2)
    
    # 柱状图
    bar_fig = create_interactive_barplot(df, group_var, measure_var, posthoc_results,
                                         title=None, height=height, width=width//3)
    for trace in bar_fig.data:
        trace.showlegend = False
        fig.add_trace(trace, row=1, col=3)
    
    # 更新布局
    fig.update_layout(
        title_text=f'{measure_var} 的交互式可视化（按 {group_var} 分组）',
        height=height,
        width=width,
        showlegend=False
    )
    
    # 更新坐标轴标签
    fig.update_xaxes(title_text=group_var, row=1, col=1)
    fig.update_yaxes(title_text=measure_var, row=1, col=1)
    fig.update_xaxes(title_text=group_var, row=1, col=2)
    fig.update_yaxes(title_text=measure_var, row=1, col=2)
    fig.update_xaxes(title_text=group_var, row=1, col=3)
    fig.update_yaxes(title_text=measure_var, row=1, col=3)
    
    return fig

def add_interactive_annotations(fig: go.Figure,
                                df: pd.DataFrame,
                                group_var: str,
                                measure_var: str,
                                posthoc_results: Dict,
                                plot_type: str) -> None:
    """
    为交互式图表添加显著性标注
    
    Parameters
    ----------
    fig : go.Figure
        Plotly 图形对象
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
    # 获取组顺序
    groups = sorted(df[group_var].unique())
    group_indices = {group: i for i, group in enumerate(groups)}
    
    # 获取数据范围
    y_range = fig.layout.yaxis.range if hasattr(fig.layout.yaxis, 'range') else [0, 1]
    if y_range is None:
        # 估计 y 范围
        y_min = df[measure_var].min()
        y_max = df[measure_var].max()
        y_range = [y_min, y_max]
    
    y_min, y_max = y_range
    y_span = y_max - y_min
    
    # 计算每对组的最大 y 值
    group_stats = df.groupby(group_var)[measure_var].agg(['max', 'min', 'mean']).to_dict()
    
    # 收集所有显著对
    significant_pairs = []
    for result in posthoc_results.get('pairwise_results', []):
        if not result.get('significant', False):
            continue
        
        group1, group2 = result['group1'], result['group2']
        if group1 not in group_indices or group2 not in group_indices:
            continue
        
        significant_pairs.append({
            'group1': group1,
            'group2': group2,
            'p_value': result.get('p_value', 1.0),
            'i1': group_indices[group1],
            'i2': group_indices[group2]
        })
    
    if not significant_pairs:
        return
    
    # 为每对添加标注
    for i, pair in enumerate(significant_pairs):
        group1, group2 = pair['group1'], pair['group2']
        i1, i2 = pair['i1'], pair['i2']
        p_value = pair['p_value']
        
        # 计算标注位置
        if plot_type == 'barplot':
            y1 = group_stats['mean'][group1] if group1 in group_stats['mean'] else 0
            y2 = group_stats['mean'][group2] if group2 in group_stats['mean'] else 0
            y_top = max(y1, y2) + 0.1 * y_span
        else:
            y1 = group_stats['max'][group1] if group1 in group_stats['max'] else 0
            y2 = group_stats['max'][group2] if group2 in group_stats['max'] else 0
            y_top = max(y1, y2) + 0.05 * y_span
        
        # 星号表示
        if p_value < 0.001:
            star = '***'
        elif p_value < 0.01:
            star = '**'
        elif p_value < 0.05:
            star = '*'
        else:
            star = 'ns'
        
        # 添加标注线
        line_y = y_top + 0.02 * y_span
        
        fig.add_shape(
            type="line",
            x0=i1, y0=line_y,
            x1=i2, y1=line_y,
            line=dict(color="black", width=2),
            xref="x", yref="y"
        )
        
        fig.add_shape(
            type="line",
            x0=i1, y0=line_y,
            x1=i1, y1=line_y + 0.01 * y_span,
            line=dict(color="black", width=2),
            xref="x", yref="y"
        )
        
        fig.add_shape(
            type="line",
            x0=i2, y0=line_y,
            x1=i2, y1=line_y + 0.01 * y_span,
            line=dict(color="black", width=2),
            xref="x", yref="y"
        )
        
        # 添加星号文本
        fig.add_annotation(
            x=(i1 + i2) / 2,
            y=line_y + 0.015 * y_span,
            text=star,
            showarrow=False,
            font=dict(size=14, color="black", weight="bold"),
            xref="x", yref="y"
        )

def create_altair_chart(df: pd.DataFrame,
                        group_var: str,
                        measure_var: str,
                        chart_type: str = 'boxplot',
                        width: int = 400,
                        height: int = 300) -> alt.Chart:
    """
    创建 Altair 图表
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    chart_type : str, optional
        图表类型，'boxplot', 'violin', 'bar'，默认 'boxplot'
    width : int, optional
        宽度，默认 400
    height : int, optional
        高度，默认 300
    
    Returns
    -------
    alt.Chart
        Altair 图表对象
    """
    if not ALTAR_AVAILABLE:
        raise ImportError("Altair is not installed. Please install altair to use Altair visualizations.")
    
    # 确保分组变量为字符串
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    if chart_type == 'boxplot':
        chart = alt.Chart(df).mark_boxplot(extent='min-max').encode(
            x=alt.X(f'{group_var}:N', title=group_var),
            y=alt.Y(f'{measure_var}:Q', title=measure_var),
            color=alt.Color(f'{group_var}:N', legend=None)
        ).properties(
            width=width,
            height=height,
            title=f'{measure_var} 的箱线图（按 {group_var} 分组）'
        )
    
    elif chart_type == 'violin':
        # Altair 没有内置的小提琴图，使用密度图模拟
        chart = alt.Chart(df).transform_density(
            measure_var,
            as_=[measure_var, 'density'],
            groupby=[group_var]
        ).mark_area(orient='horizontal').encode(
            y=alt.Y(f'{measure_var}:Q', title=measure_var),
            x=alt.X('density:Q', title='密度', stack='center'),
            color=alt.Color(f'{group_var}:N', legend=None)
        ).properties(
            width=width,
            height=height,
            title=f'{measure_var} 的小提琴图（按 {group_var} 分组）'
        )
    
    elif chart_type == 'bar':
        # 计算均值和标准误
        agg_df = df.groupby(group_var)[measure_var].agg(['mean', 'std', 'count']).reset_index()
        agg_df['se'] = agg_df['std'] / np.sqrt(agg_df['count'])
        
        base = alt.Chart(agg_df).encode(
            x=alt.X(f'{group_var}:N', title=group_var),
            color=alt.Color(f'{group_var}:N', legend=None)
        )
        
        bar = base.mark_bar().encode(
            y=alt.Y('mean:Q', title=measure_var)
        )
        
        error_bars = base.mark_errorbar(extent='ci').encode(
            y=alt.Y('mean:Q', title=measure_var)
        )
        
        chart = (bar + error_bars).properties(
            width=width,
            height=height,
            title=f'{measure_var} 的柱状图（按 {group_var} 分组）'
        )
    
    else:
        raise ValueError(f"不支持的图表类型: {chart_type}")
    
    return chart.interactive()

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
    
    if PLOTLY_AVAILABLE:
        print("创建交互式箱线图测试")
        fig1 = create_interactive_boxplot(test_data, 'group', 'value1')
        print("交互式箱线图创建成功")
        
        print("\n创建交互式小提琴图测试")
        fig2 = create_interactive_violinplot(test_data, 'group', 'value1')
        print("交互式小提琴图创建成功")
    
    if ALTAR_AVAILABLE:
        print("\n创建 Altair 图表测试")
        chart = create_altair_chart(test_data, 'group', 'value1', 'boxplot')
        print("Altair 图表创建成功")