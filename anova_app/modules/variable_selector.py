"""
变量选择模块
提供 UI 小部件用于选择分组变量和检测变量
"""

import streamlit as st
import pandas as pd
from typing import Tuple, List, Optional
from data_loader import get_column_types

def select_variables(df: pd.DataFrame) -> Tuple[Optional[str], List[str]]:
    """
    显示变量选择界面并返回用户选择
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    
    Returns
    -------
    Tuple[Optional[str], List[str]]
        (分组变量, 检测变量列表)
    """
    if df is None or df.empty:
        return None, []
    
    # 获取列分类
    col_types = get_column_types(df)
    
    # 分组变量选择（类别型或低基数列）
    st.subheader("分组变量选择")
    
    # 推荐的分组变量候选
    categorical_candidates = col_types['categorical']
    numeric_candidates = [col for col in col_types['numeric'] if df[col].nunique() < 10]
    all_candidates = categorical_candidates + numeric_candidates
    
    if not all_candidates:
        st.warning("未找到合适的候选分组变量。请确保数据中包含类别型列或低基数的数值列。")
        # 允许选择任何列作为分组变量
        all_candidates = list(df.columns)
    
    group_var = st.selectbox(
        "选择分组变量（自变量，类别型）",
        options=[''] + all_candidates,
        help="用于分组的变量，通常是类别型或有限的离散值",
        key="group_var_select"
    )
    
    if group_var == '':
        group_var = None
    
    # 检测变量选择（数值型）
    st.subheader("检测变量选择")
    
    # 推荐的检测变量候选（数值型）
    numeric_cols = col_types['numeric']
    
    if not numeric_cols:
        st.warning("未找到数值型列。方差分析需要数值型因变量。")
        # 允许选择任何列作为检测变量（但会警告）
        numeric_cols = list(df.columns)
    
    measure_vars = st.multiselect(
        "选择检测变量（因变量，数值型）",
        options=numeric_cols,
        default=[],
        help="用于分析的数值型变量，可多选",
        key="measure_vars_select"
    )
    
    # 显示选择预览
    if group_var:
        unique_groups = df[group_var].nunique()
        st.info(f"分组变量 '{group_var}' 有 {unique_groups} 个水平: {', '.join(map(str, df[group_var].unique()[:10]))}")
    
    if measure_vars:
        st.info(f"已选择 {len(measure_vars)} 个检测变量: {', '.join(measure_vars)}")
    
    # 验证选择
    if group_var and measure_vars:
        # 检查分组变量是否至少有两个水平
        if df[group_var].nunique() < 2:
            st.error(f"分组变量 '{group_var}' 需要至少 2 个不同的水平，当前只有 {df[group_var].nunique()} 个。")
            return None, []
        
        # 检查检测变量是否为数值型
        non_numeric_vars = []
        for var in measure_vars:
            if not pd.api.types.is_numeric_dtype(df[var]):
                non_numeric_vars.append(var)
        
        if non_numeric_vars:
            st.error(f"以下检测变量不是数值型: {', '.join(non_numeric_vars)}")
            return group_var, []
    
    return group_var, measure_vars

def select_multiple_factors(df: pd.DataFrame) -> List[str]:
    """
    选择多个因素变量（用于多因素 ANOVA）
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    
    Returns
    -------
    List[str]
        因素变量列表
    """
    if df is None or df.empty:
        return []
    
    col_types = get_column_types(df)
    
    # 推荐的因素变量候选
    categorical_candidates = col_types['categorical']
    numeric_candidates = [col for col in col_types['numeric'] if df[col].nunique() < 10]
    all_candidates = categorical_candidates + numeric_candidates
    
    if not all_candidates:
        all_candidates = list(df.columns)
    
    factors = st.multiselect(
        "选择因素变量（多因素 ANOVA）",
        options=all_candidates,
        default=[],
        help="选择多个分组变量进行多因素方差分析",
        key="factors_select"
    )
    
    # 验证因素变量
    valid_factors = []
    for factor in factors:
        if df[factor].nunique() < 2:
            st.warning(f"因素变量 '{factor}' 只有 {df[factor].nunique()} 个水平，将被忽略。")
        else:
            valid_factors.append(factor)
    
    if len(valid_factors) > 3:
        st.warning("选择的因素变量过多（>3），可能导致分析复杂度过高。")
    
    return valid_factors

def select_covariates(df: pd.DataFrame) -> List[str]:
    """
    选择协变量（用于 ANCOVA）
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    
    Returns
    -------
    List[str]
        协变量列表
    """
    if df is None or df.empty:
        return []
    
    col_types = get_column_types(df)
    
    # 协变量应为数值型
    covariate_candidates = col_types['numeric']
    
    covariates = st.multiselect(
        "选择协变量（ANCOVA）",
        options=covariate_candidates,
        default=[],
        help="选择数值型协变量进行协方差分析",
        key="covariates_select"
    )
    
    return covariates

def get_variable_summary(df: pd.DataFrame, group_var: str, measure_vars: List[str]) -> dict:
    """
    获取变量选择的摘要信息
    
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
    dict
        摘要信息
    """
    summary = {
        'group_variable': group_var,
        'measure_variables': measure_vars,
        'sample_size': len(df),
        'group_summary': {},
        'measure_summary': {}
    }
    
    if group_var:
        group_summary = df[group_var].describe()
        summary['group_summary'] = {
            'count': int(group_summary.get('count', 0)),
            'unique': df[group_var].nunique(),
            'top': group_summary.get('top', ''),
            'freq': int(group_summary.get('freq', 0)) if 'freq' in group_summary else 0
        }
    
    for var in measure_vars:
        if var in df.columns:
            var_summary = df[var].describe()
            summary['measure_summary'][var] = {
                'count': int(var_summary.get('count', 0)),
                'mean': float(var_summary.get('mean', 0)),
                'std': float(var_summary.get('std', 0)),
                'min': float(var_summary.get('min', 0)),
                '25%': float(var_summary.get('25%', 0)),
                '50%': float(var_summary.get('50%', 0)),
                '75%': float(var_summary.get('75%', 0)),
                'max': float(var_summary.get('max', 0))
            }
    
    return summary

if __name__ == "__main__":
    # 模块测试
    import sys
    sys.path.append('..')
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'group': ['A', 'A', 'B', 'B', 'C', 'C'],
        'value1': [1.2, 2.3, 3.4, 4.5, 5.6, 6.7],
        'value2': [10, 20, 30, 40, 50, 60],
        'category': ['X', 'Y', 'X', 'Y', 'X', 'Y']
    })
    
    print("变量选择测试")
    print("数据列:", list(test_data.columns))
    
    # 模拟 Streamlit 选择（无法直接运行，仅演示）
    group, measures = select_variables(test_data)
    print(f"分组变量: {group}, 检测变量: {measures}")