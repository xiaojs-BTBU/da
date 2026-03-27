"""
统计计算模块
执行描述性统计、正态性检验、方差齐性检验
"""

import pandas as pd
import numpy as np
from scipy import stats
import pingouin as pg
from typing import Dict, List, Tuple, Optional, Union
import warnings

warnings.filterwarnings('ignore')

def descriptive_stats(df: pd.DataFrame, 
                      group_var: str, 
                      measure_vars: List[str]) -> Dict:
    """
    计算各组的描述性统计
    
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
    Dict
        包含描述性统计的字典
    """
    results = {
        'overall': {},
        'by_group': {},
        'summary_table': None
    }
    
    # 确保分组变量为字符串类型（便于分组）
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    # 整体描述性统计（不分组）
    for var in measure_vars:
        if var not in df.columns:
            continue
            
        data = df[var].dropna()
        if len(data) == 0:
            results['overall'][var] = None
            continue
            
        results['overall'][var] = {
            'n': len(data),
            'mean': float(data.mean()),
            'std': float(data.std()),
            'median': float(data.median()),
            'min': float(data.min()),
            'max': float(data.max()),
            'q1': float(data.quantile(0.25)),
            'q3': float(data.quantile(0.75)),
            'skew': float(data.skew()) if len(data) > 2 else None,
            'kurtosis': float(data.kurtosis()) if len(data) > 3 else None
        }
    
    # 按分组描述性统计
    groups = df[group_var].unique()
    
    for var in measure_vars:
        if var not in df.columns:
            continue
            
        results['by_group'][var] = {}
        
        for group in groups:
            group_data = df[df[group_var] == group][var].dropna()
            if len(group_data) == 0:
                results['by_group'][var][group] = None
                continue
                
            results['by_group'][var][group] = {
                'n': len(group_data),
                'mean': float(group_data.mean()),
                'std': float(group_data.std()),
                'median': float(group_data.median()),
                'min': float(group_data.min()),
                'max': float(group_data.max()),
                'q1': float(group_data.quantile(0.25)),
                'q3': float(group_data.quantile(0.75)),
                'se': float(group_data.std() / np.sqrt(len(group_data))) if len(group_data) > 0 else None,
                'ci_lower': None,
                'ci_upper': None
            }
            
            # 计算 95% 置信区间
            if len(group_data) >= 2:
                ci = stats.t.interval(0.95, len(group_data)-1, 
                                      loc=group_data.mean(), 
                                      scale=group_data.std()/np.sqrt(len(group_data)))
                results['by_group'][var][group]['ci_lower'] = float(ci[0])
                results['by_group'][var][group]['ci_upper'] = float(ci[1])
    
    # 创建汇总表格（用于显示）
    summary_data = []
    for var in measure_vars:
        for group in groups:
            if var in results['by_group'] and group in results['by_group'][var]:
                stats_dict = results['by_group'][var][group]
                summary_data.append({
                    'Variable': var,
                    'Group': group,
                    'N': stats_dict['n'],
                    'Mean': stats_dict['mean'],
                    'Std': stats_dict['std'],
                    'Median': stats_dict['median'],
                    'Min': stats_dict['min'],
                    'Max': stats_dict['max'],
                    'SE': stats_dict['se'],
                    'CI Lower': stats_dict['ci_lower'],
                    'CI Upper': stats_dict['ci_upper']
                })
    
    results['summary_table'] = pd.DataFrame(summary_data) if summary_data else None
    
    return results

def normality_test(df: pd.DataFrame, 
                   group_var: str, 
                   measure_vars: List[str],
                   alpha: float = 0.05) -> Dict:
    """
    执行正态性检验（Shapiro-Wilk 检验）
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_vars : List[str]
        检测变量列表
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        正态性检验结果
    """
    results = {
        'overall': {},
        'by_group': {},
        'conclusion': {},
        'all_normal': True  # 假设所有都正态
    }
    
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    groups = df[group_var].unique()
    
    for var in measure_vars:
        if var not in df.columns:
            continue
            
        # 整体正态性检验（所有数据）
        data_all = df[var].dropna()
        if len(data_all) >= 3 and len(data_all) <= 5000:
            try:
                shapiro_stat, shapiro_p = stats.shapiro(data_all)
                results['overall'][var] = {
                    'statistic': float(shapiro_stat),
                    'p_value': float(shapiro_p),
                    'normal': shapiro_p > alpha,
                    'test': 'Shapiro-Wilk',
                    'n': len(data_all)
                }
            except:
                # 如果 Shapiro 失败，使用 Kolmogorov-Smirnov 检验
                ks_stat, ks_p = stats.kstest(data_all, 'norm', 
                                             args=(data_all.mean(), data_all.std()))
                results['overall'][var] = {
                    'statistic': float(ks_stat),
                    'p_value': float(ks_p),
                    'normal': ks_p > alpha,
                    'test': 'Kolmogorov-Smirnov',
                    'n': len(data_all)
                }
        else:
            results['overall'][var] = {
                'statistic': None,
                'p_value': None,
                'normal': None,
                'test': 'Insufficient data',
                'n': len(data_all)
            }
        
        # 按分组正态性检验
        results['by_group'][var] = {}
        group_normal = True
        
        for group in groups:
            group_data = df[df[group_var] == group][var].dropna()
            if len(group_data) >= 3 and len(group_data) <= 5000:
                try:
                    shapiro_stat, shapiro_p = stats.shapiro(group_data)
                    is_normal = shapiro_p > alpha
                    results['by_group'][var][group] = {
                        'statistic': float(shapiro_stat),
                        'p_value': float(shapiro_p),
                        'normal': is_normal,
                        'test': 'Shapiro-Wilk',
                        'n': len(group_data)
                    }
                    if not is_normal:
                        group_normal = False
                except:
                    ks_stat, ks_p = stats.kstest(group_data, 'norm',
                                                 args=(group_data.mean(), group_data.std()))
                    is_normal = ks_p > alpha
                    results['by_group'][var][group] = {
                        'statistic': float(ks_stat),
                        'p_value': float(ks_p),
                        'normal': is_normal,
                        'test': 'Kolmogorov-Smirnov',
                        'n': len(group_data)
                    }
                    if not is_normal:
                        group_normal = False
            else:
                results['by_group'][var][group] = {
                    'statistic': None,
                    'p_value': None,
                    'normal': None,
                    'test': 'Insufficient data',
                    'n': len(group_data)
                }
        
        # 结论：仅基于亚组正态性判断
        # overall_normal 仅用于参考，不参与决策
        overall_normal = results['overall'][var]['normal']
        if overall_normal is None:
            overall_normal = True  # 保守假设
        
        # 数据正态性取决于所有亚组是否都正态（分层检验）
        is_normal_overall = group_normal
        
        results['conclusion'][var] = {
            'overall_normal': overall_normal,
            'all_groups_normal': group_normal,
            'data_normal': is_normal_overall,
            'recommendation': 'Parametric test' if is_normal_overall else 'Non-parametric test'
        }
        
        if not is_normal_overall:
            results['all_normal'] = False
    
    return results

def homogeneity_test(df: pd.DataFrame,
                     group_var: str,
                     measure_vars: List[str],
                     alpha: float = 0.05) -> Dict:
    """
    执行方差齐性检验（Levene 检验）
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_vars : List[str]
        检测变量列表
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        方差齐性检验结果
    """
    results = {
        'by_variable': {},
        'conclusion': {},
        'all_homogeneous': True  # 假设所有都齐性
    }
    
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    for var in measure_vars:
        if var not in df.columns:
            continue
            
        # 准备分组数据
        groups_data = []
        groups = df[group_var].unique()
        
        for group in groups:
            group_data = df[df[group_var] == group][var].dropna()
            if len(group_data) > 0:
                groups_data.append(group_data)
        
        if len(groups_data) < 2:
            results['by_variable'][var] = {
                'statistic': None,
                'p_value': None,
                'homogeneous': None,
                'test': 'Insufficient groups',
                'n_groups': len(groups_data)
            }
            results['conclusion'][var] = {
                'homogeneous': None,
                'recommendation': 'Insufficient data'
            }
            continue
        
        # Levene 检验（默认使用中位数，对非正态数据更稳健）
        try:
            levene_stat, levene_p = stats.levene(*groups_data)
            is_homogeneous = levene_p > alpha
            
            results['by_variable'][var] = {
                'statistic': float(levene_stat),
                'p_value': float(levene_p),
                'homogeneous': is_homogeneous,
                'test': 'Levene (median)',
                'n_groups': len(groups_data),
                'group_sizes': [len(g) for g in groups_data]
            }
            
            results['conclusion'][var] = {
                'homogeneous': is_homogeneous,
                'recommendation': 'Standard ANOVA' if is_homogeneous else 'Welch ANOVA'
            }
            
            if not is_homogeneous:
                results['all_homogeneous'] = False
                
        except Exception as e:
            # 如果 Levene 失败，尝试 Bartlett 检验（对正态数据更敏感）
            try:
                bartlett_stat, bartlett_p = stats.bartlett(*groups_data)
                is_homogeneous = bartlett_p > alpha
                
                results['by_variable'][var] = {
                    'statistic': float(bartlett_stat),
                    'p_value': float(bartlett_p),
                    'homogeneous': is_homogeneous,
                    'test': 'Bartlett',
                    'n_groups': len(groups_data),
                    'group_sizes': [len(g) for g in groups_data]
                }
                
                results['conclusion'][var] = {
                    'homogeneous': is_homogeneous,
                    'recommendation': 'Standard ANOVA' if is_homogeneous else 'Welch ANOVA'
                }
                
                if not is_homogeneous:
                    results['all_homogeneous'] = False
                    
            except Exception as e2:
                results['by_variable'][var] = {
                    'statistic': None,
                    'p_value': None,
                    'homogeneous': None,
                    'test': f'Failed: {str(e2)[:100]}',
                    'n_groups': len(groups_data),
                    'group_sizes': [len(g) for g in groups_data]
                }
                
                results['conclusion'][var] = {
                    'homogeneous': None,
                    'recommendation': 'Check data'
                }
    
    return results

def check_assumptions(df: pd.DataFrame,
                      group_var: str,
                      measure_vars: List[str],
                      alpha: float = 0.05) -> Dict:
    """
    综合检查所有前提假设
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_vars : List[str]
        检测变量列表
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        所有假设检验结果
    """
    normality = normality_test(df, group_var, measure_vars, alpha)
    homogeneity = homogeneity_test(df, group_var, measure_vars, alpha)
    
    # 确定每个变量的推荐检验方法
    recommendations = {}
    for var in measure_vars:
        if var in normality['conclusion'] and var in homogeneity['conclusion']:
            normal = normality['conclusion'][var]['data_normal']
            homogeneous = homogeneity['conclusion'][var]['homogeneous']
            
            if normal is None or homogeneous is None:
                recommendation = 'Check data quality'
            elif normal and homogeneous:
                recommendation = 'Standard one-way ANOVA'
            elif normal and not homogeneous:
                recommendation = "Welch's ANOVA"
            elif not normal and homogeneous:
                recommendation = 'Kruskal-Wallis test'
            else:  # 非正态且方差不齐
                recommendation = 'Kruskal-Wallis test (non-normal, heterogeneous variances)'
        else:
            recommendation = 'Unable to determine'
        
        recommendations[var] = recommendation
    
    return {
        'normality': normality,
        'homogeneity': homogeneity,
        'recommendations': recommendations,
        'alpha': alpha
    }

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
        ]),
        'value2': np.concatenate([
            np.random.exponential(5, n_per_group),
            np.random.exponential(7, n_per_group),
            np.random.exponential(10, n_per_group)
        ])
    })
    
    print("描述性统计测试")
    desc = descriptive_stats(test_data, 'group', ['value1', 'value2'])
    print(f"整体统计: {desc['overall']['value1']['mean']:.2f}")
    
    print("\n正态性检验测试")
    norm = normality_test(test_data, 'group', ['value1', 'value2'])
    print(f"value1 整体正态性: {norm['overall']['value1']['normal']}")
    
    print("\n方差齐性检验测试")
    homo = homogeneity_test(test_data, 'group', ['value1', 'value2'])
    print(f"value1 方差齐性: {homo['by_variable']['value1']['homogeneous']}")
    
    print("\n综合假设检验")
    assumptions = check_assumptions(test_data, 'group', ['value1', 'value2'])
    for var, rec in assumptions['recommendations'].items():
        print(f"{var}: {rec}")