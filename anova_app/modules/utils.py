"""
工具函数模块
包含错误处理、显示函数和其他实用工具
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Any, Dict, List, Optional, Union, Callable
import traceback
import warnings
import sys
import os

warnings.filterwarnings('ignore')

# 错误处理装饰器
def handle_errors(func: Callable) -> Callable:
    """
    错误处理装饰器，捕获函数执行中的异常并显示错误信息
    
    Parameters
    ----------
    func : Callable
        要装饰的函数
    
    Returns
    -------
    Callable
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"函数 {func.__name__} 执行出错: {str(e)}"
            display_error(error_msg)
            # 在开发模式下显示详细跟踪
            if st.session_state.get('debug_mode', False):
                st.code(traceback.format_exc())
            return None
    return wrapper

# 显示函数
def display_error(message: str, 
                  details: Optional[str] = None,
                  icon: str = "❌") -> None:
    """
    显示错误信息
    
    Parameters
    ----------
    message : str
        错误消息
    details : str, optional
        详细信息
    icon : str, optional
        图标，默认 "❌"
    """
    with st.container():
        st.error(f"{icon} {message}")
        if details:
            with st.expander("查看详细信息"):
                st.text(details)

def display_warning(message: str,
                    details: Optional[str] = None,
                    icon: str = "⚠️") -> None:
    """
    显示警告信息
    
    Parameters
    ----------
    message : str
        警告消息
    details : str, optional
        详细信息
    icon : str, optional
        图标，默认 "⚠️"
    """
    with st.container():
        st.warning(f"{icon} {message}")
        if details:
            with st.expander("查看详细信息"):
                st.text(details)

def display_success(message: str,
                    details: Optional[str] = None,
                    icon: str = "✅") -> None:
    """
    显示成功信息
    
    Parameters
    ----------
    message : str
        成功消息
    details : str, optional
        详细信息
    icon : str, optional
        图标，默认 "✅"
    """
    with st.container():
        st.success(f"{icon} {message}")
        if details:
            with st.expander("查看详细信息"):
                st.text(details)

def display_info(message: str,
                 details: Optional[str] = None,
                 icon: str = "ℹ️") -> None:
    """
    显示信息
    
    Parameters
    ----------
    message : str
        信息消息
    details : str, optional
        详细信息
    icon : str, optional
        图标，默认 "ℹ️"
    """
    with st.container():
        st.info(f"{icon} {message}")
        if details:
            with st.expander("查看详细信息"):
                st.text(details)

# 结果显示函数
def display_anova_results(anova_results: Dict,
                          assumption_results: Optional[Dict] = None,
                          posthoc_results: Optional[Dict] = None) -> None:
    """
    显示 ANOVA 结果
    
    Parameters
    ----------
    anova_results : Dict
        ANOVA 结果
    assumption_results : Dict, optional
        假设检验结果
    posthoc_results : Dict, optional
        事后检验结果
    """
    if not anova_results:
        display_warning("没有可用的 ANOVA 结果")
        return
    
    # 显示假设检验结果
    if assumption_results:
        with st.expander("📋 前提假设检验结果", expanded=True):
            # 正态性检验
            if 'normality' in assumption_results:
                st.subheader("正态性检验 (Shapiro-Wilk)")
                # 整体检验结果（可选）
                norm_data = []
                for var, result in assumption_results['normality'].get('overall', {}).items():
                    if result:
                        norm_data.append({
                            '变量': var,
                            '统计量': f"{result.get('statistic', 'N/A'):.3f}" if result.get('statistic') is not None else 'N/A',
                            'P 值': f"{result.get('p_value', 'N/A'):.4f}" if result.get('p_value') is not None else 'N/A',
                            '是否正态': '是' if result.get('normal') else '否' if result.get('normal') is not None else 'N/A'
                        })
                
                if norm_data:
                    st.dataframe(pd.DataFrame(norm_data), use_container_width=True)
                else:
                    st.info("无整体正态性检验结果")
                
                # 分层（亚组）正态性检验
                if 'by_group' in assumption_results['normality']:
                    st.subheader("各亚组正态性检验")
                    any_non_normal = False
                    for var, group_dict in assumption_results['normality']['by_group'].items():
                        group_data = []
                        for group_name, group_result in group_dict.items():
                            if group_result:
                                p_val = group_result.get('p_value')
                                normal = group_result.get('normal')
                                if normal is False:
                                    any_non_normal = True
                                group_data.append({
                                    '变量': var,
                                    '亚组': group_name,
                                    '样本量': group_result.get('n', 'N/A'),
                                    '统计量': f"{group_result.get('statistic', 'N/A'):.3f}" if group_result.get('statistic') is not None else 'N/A',
                                    'P 值': f"{p_val:.4f}" if p_val is not None else 'N/A',
                                    '是否正态': '是' if normal else '否' if normal is not None else 'N/A'
                                })
                        if group_data:
                            st.write(f"**变量: {var}**")
                            st.dataframe(pd.DataFrame(group_data), use_container_width=True)
                    
                    # 醒目提示：如果有亚组不满足正态性
                    if any_non_normal:
                        st.error("⚠️ 注意：至少有一个亚组不满足正态性（P < 0.05）。建议使用非参数检验（Kruskal-Wallis）。")
                else:
                    st.info("无亚组正态性检验结果")
            
            # 方差齐性检验
            if 'homogeneity' in assumption_results:
                st.subheader("方差齐性检验 (Levene)")
                homo_data = []
                for var, result in assumption_results['homogeneity'].get('by_variable', {}).items():
                    if result:
                        homo_data.append({
                            '变量': var,
                            '统计量': f"{result.get('statistic', 'N/A'):.3f}" if result.get('statistic') is not None else 'N/A',
                            'P 值': f"{result.get('p_value', 'N/A'):.4f}" if result.get('p_value') is not None else 'N/A',
                            '是否齐性': '是' if result.get('homogeneous') else '否' if result.get('homogeneous') is not None else 'N/A'
                        })
                
                if homo_data:
                    st.dataframe(pd.DataFrame(homo_data), use_container_width=True)
                else:
                    st.info("无方差齐性检验结果")
    
    # 显示 ANOVA 结果
    with st.expander("📈 ANOVA 结果", expanded=True):
        anova_data = []
        for var, result in anova_results.get('by_variable', {}).items():
            if result.get('error'):
                continue
                
            f_value = result.get('f_value', result.get('h_statistic'))
            p_value = result.get('p_value')
            
            if p_value is not None:
                anova_data.append({
                    '变量': var,
                    '检验方法': result.get('test', ''),
                    'F/H 统计量': f"{f_value:.3f}" if f_value is not None else 'N/A',
                    'P 值': f"{p_value:.4f}",
                    '显著性': '显著' if result.get('significant') else '不显著',
                    '效应量': f"{result.get('eta_squared', result.get('epsilon_squared', 'N/A')):.3f}" if result.get('eta_squared') is not None else 'N/A'
                })
        
        if anova_data:
            st.dataframe(pd.DataFrame(anova_data), use_container_width=True)
            
            # 显著性总结
            sig_vars = [d['变量'] for d in anova_data if d['显著性'] == '显著']
            if sig_vars:
                st.success(f"显著变量: {', '.join(sig_vars)}")
            else:
                st.info("没有显著变量")
        else:
            st.info("无 ANOVA 结果")
    
    # 显示事后检验结果
    if posthoc_results:
        with st.expander("🔍 事后两两比较结果", expanded=False):
            for var, result in posthoc_results.get('by_variable', {}).items():
                if not result.get('pairwise_results'):
                    continue
                
                st.subheader(f"变量: {var}")
                
                posthoc_data = []
                for pair_result in result['pairwise_results']:
                    p_value = pair_result.get('p_value')
                    if p_value is None:
                        continue
                    
                    posthoc_data.append({
                        '组1': pair_result['group1'],
                        '组2': pair_result['group2'],
                        '均值差': f"{pair_result.get('mean_diff', 'N/A'):.3f}" if pair_result.get('mean_diff') is not None else 'N/A',
                        'P 值': f"{p_value:.4f}",
                        '显著性': '显著' if pair_result.get('significant') else '不显著',
                        '95% CI': f"[{pair_result.get('ci_lower', 'N/A'):.3f}, {pair_result.get('ci_upper', 'N/A'):.3f}]" if pair_result.get('ci_lower') is not None else 'N/A'
                    })
                
                if posthoc_data:
                    st.dataframe(pd.DataFrame(posthoc_data), use_container_width=True)
                    
                    # 显示显著对
                    sig_pairs = [(d['组1'], d['组2']) for d in posthoc_data if d['显著性'] == '显著']
                    if sig_pairs:
                        st.info(f"显著差异对: {', '.join([f'{g1}-{g2}' for g1, g2 in sig_pairs])}")
                else:
                    st.info("无事后再比较结果")

# 数据验证函数
def validate_inputs(df: pd.DataFrame,
                    group_var: str,
                    measure_vars: List[str]) -> tuple:
    """
    验证用户输入
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_vars : List[str]
        检测变量列表
    
    Returns
    -------
    tuple
        (是否有效, 错误消息)
    """
    # 检查数据框
    if df is None or df.empty:
        return False, "数据框为空或未加载"
    
    # 检查分组变量
    if not group_var or group_var not in df.columns:
        return False, f"分组变量 '{group_var}' 不存在于数据中"
    
    # 检查分组变量水平
    unique_groups = df[group_var].nunique()
    if unique_groups < 2:
        return False, f"分组变量 '{group_var}' 需要至少 2 个不同的水平，当前只有 {unique_groups} 个"
    
    # 检查检测变量
    if not measure_vars:
        return False, "未选择检测变量"
    
    for var in measure_vars:
        if var not in df.columns:
            return False, f"检测变量 '{var}' 不存在于数据中"
        
        # 检查是否为数值型
        if not pd.api.types.is_numeric_dtype(df[var]):
            return False, f"检测变量 '{var}' 不是数值类型"
        
        # 检查是否有足够的非缺失值
        non_missing = df[var].notna().sum()
        if non_missing < 3:
            return False, f"检测变量 '{var}' 的有效数据点太少（{non_missing} 个），至少需要 3 个"
    
    return True, "输入验证通过"

# 文件处理函数
def save_dataframe_to_csv(df: pd.DataFrame, 
                          filename: str) -> str:
    """
    将 DataFrame 保存为 CSV 文件
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    filename : str
        文件名
    
    Returns
    -------
    str
        保存的文件路径
    """
    import os
    
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 添加扩展名
    if not filename.lower().endswith('.csv'):
        filename = f'{filename}.csv'
    
    filepath = os.path.join('output', filename)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    return filepath

def save_figure_to_file(fig: plt.Figure,
                        filename: str,
                        dpi: int = 300,
                        format: str = 'png') -> str:
    """
    将图形保存为文件
    
    Parameters
    ----------
    fig : plt.Figure
        图形对象
    filename : str
        文件名
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
    
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 添加扩展名
    if not filename.lower().endswith(f'.{format}'):
        filename = f'{filename}.{format}'
    
    filepath = os.path.join('output', filename)
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', format=format)
    
    return filepath

# 辅助函数
def format_p_value(p_value: float) -> str:
    """
    格式化 P 值
    
    Parameters
    ----------
    p_value : float
        P 值
    
    Returns
    -------
    str
        格式化的 P 值字符串
    """
    if p_value is None:
        return "N/A"
    
    if p_value < 0.001:
        return "< 0.001"
    elif p_value < 0.01:
        return f"{p_value:.3f}"
    elif p_value < 0.05:
        return f"{p_value:.3f}"
    else:
        return f"{p_value:.3f}"

def get_significance_stars(p_value: float) -> str:
    """
    根据 P 值获取显著性星号
    
    Parameters
    ----------
    p_value : float
        P 值
    
    Returns
    -------
    str
        显著性星号
    """
    if p_value is None:
        return ""
    
    if p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    else:
        return "ns"

def create_download_button(data: Union[str, bytes],
                          file_name: str,
                          mime_type: str,
                          button_text: str = "下载文件") -> None:
    """
    创建下载按钮
    
    Parameters
    ----------
    data : Union[str, bytes]
        数据内容
    file_name : str
        文件名
    mime_type : str
        MIME 类型
    button_text : str, optional
        按钮文本，默认 "下载文件"
    """
    st.download_button(
        label=button_text,
        data=data,
        file_name=file_name,
        mime=mime_type
    )

# 会话状态管理
def init_session_state() -> None:
    """
    初始化 session state 变量
    """
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'group_var' not in st.session_state:
        st.session_state.group_var = None
    if 'measure_vars' not in st.session_state:
        st.session_state.measure_vars = []
    if 'anova_results' not in st.session_state:
        st.session_state.anova_results = None
    if 'posthoc_results' not in st.session_state:
        st.session_state.posthoc_results = None
    if 'assumption_results' not in st.session_state:
        st.session_state.assumption_results = None
    if 'figures' not in st.session_state:
        st.session_state.figures = {}
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False

def clear_session_state() -> None:
    """
    清除 session state 变量
    """
    keys = list(st.session_state.keys())
    for key in keys:
        del st.session_state[key]
    
    # 重新初始化
    init_session_state()

if __name__ == "__main__":
    # 模块测试
    print("工具函数模块测试")
    
    # 测试 P 值格式化
    print(f"P 值格式化测试: 0.0001 -> {format_p_value(0.0001)}")
    print(f"P 值格式化测试: 0.01 -> {format_p_value(0.01)}")
    print(f"P 值格式化测试: 0.5 -> {format_p_value(0.5)}")
    
    # 测试显著性星号
    print(f"显著性星号测试: 0.0001 -> {get_significance_stars(0.0001)}")
    print(f"显著性星号测试: 0.01 -> {get_significance_stars(0.01)}")
    print(f"显著性星号测试: 0.03 -> {get_significance_stars(0.03)}")
    print(f"显著性星号测试: 0.1 -> {get_significance_stars(0.1)}")