"""
ANOVA 执行模块
根据前提检验结果执行适当的 ANOVA 检验
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import pingouin as pg
from typing import Dict, List, Tuple, Optional, Union
import warnings

warnings.filterwarnings('ignore')

def perform_anova(df: pd.DataFrame,
                  group_var: str,
                  measure_vars: List[str],
                  normality_results: Optional[Dict] = None,
                  homogeneity_results: Optional[Dict] = None,
                  alpha: float = 0.05) -> Dict:
    """
    执行 ANOVA 分析
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_vars : List[str]
        检测变量列表
    normality_results : Dict, optional
        正态性检验结果
    homogeneity_results : Dict, optional
        方差齐性检验结果
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        ANOVA 结果
    """
    results = {
        'by_variable': {},
        'overall_conclusion': {},
        'alpha': alpha
    }
    
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    for var in measure_vars:
        if var not in df.columns:
            continue
            
        # 检查数据是否足够
        valid_data = df[[group_var, var]].dropna()
        if len(valid_data) < 3:
            results['by_variable'][var] = {
                'error': 'Insufficient data',
                'recommendation': 'Need at least 3 observations'
            }
            continue
        
        # 确定检验方法
        test_type = determine_test_type(var, normality_results, homogeneity_results)
        
        # 执行相应的检验
        if test_type == 'one_way_anova':
            anova_result = one_way_anova(df, group_var, var, alpha)
        elif test_type == 'welch_anova':
            anova_result = welch_anova(df, group_var, var, alpha)
        elif test_type == 'kruskal_wallis':
            anova_result = kruskal_wallis(df, group_var, var, alpha)
        else:
            # 默认使用标准 ANOVA
            anova_result = one_way_anova(df, group_var, var, alpha)
        
        # 添加检验类型信息
        anova_result['test_type'] = test_type
        anova_result['variable'] = var
        anova_result['group_variable'] = group_var
        
        results['by_variable'][var] = anova_result
    
    # 整体结论
    significant_vars = []
    for var, result in results['by_variable'].items():
        if 'significant' in result and result['significant']:
            significant_vars.append(var)
    
    results['overall_conclusion'] = {
        'significant_variables': significant_vars,
        'total_tested': len(measure_vars),
        'significant_count': len(significant_vars),
        'significance_rate': len(significant_vars) / len(measure_vars) if measure_vars else 0
    }
    
    # 添加顶层显著标志
    results['significant'] = len(significant_vars) > 0
    
    return results

def determine_test_type(var: str,
                        normality_results: Optional[Dict],
                        homogeneity_results: Optional[Dict]) -> str:
    """
    根据前提检验结果确定使用哪种检验方法
    
    Parameters
    ----------
    var : str
        变量名
    normality_results : Dict
        正态性检验结果
    homogeneity_results : Dict
        方差齐性检验结果
    
    Returns
    -------
    str
        检验类型：'one_way_anova', 'welch_anova', 'kruskal_wallis'
    """
    # 默认使用标准 ANOVA
    default_test = 'one_way_anova'
    
    if normality_results is None or homogeneity_results is None:
        return default_test
    
    # 检查正态性
    normal = None
    if var in normality_results.get('conclusion', {}):
        normal = normality_results['conclusion'][var].get('data_normal')
    
    # 检查方差齐性
    homogeneous = None
    if var in homogeneity_results.get('conclusion', {}):
        homogeneous = homogeneity_results['conclusion'][var].get('homogeneous')
    
    # 决策逻辑
    if normal is None or homogeneous is None:
        return default_test
    
    if normal and homogeneous:
        return 'one_way_anova'
    elif normal and not homogeneous:
        return 'welch_anova'
    else:  # 非正态
        return 'kruskal_wallis'

def one_way_anova(df: pd.DataFrame,
                  group_var: str,
                  measure_var: str,
                  alpha: float = 0.05) -> Dict:
    """
    执行标准单因素 ANOVA
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        ANOVA 结果
    """
    try:
        # 使用 pingouin 进行 ANOVA（提供更详细的结果）
        anova_df = pg.anova(data=df, dv=measure_var, between=group_var, detailed=True)
        
        # 提取结果
        if not anova_df.empty:
            result_row = anova_df.iloc[0]
            f_value = float(result_row['F'])
            p_value = float(result_row['p-unc'])
            df_between = float(result_row['DF'])
            df_within = float(result_row['DF'].iloc[1]) if len(anova_df) > 1 else None
            
            # 计算效应量 (eta-squared)
            ss_between = float(result_row['SS'])
            ss_total = anova_df['SS'].sum()
            eta_sq = ss_between / ss_total if ss_total > 0 else 0
            
            # 计算偏 eta-squared
            ss_within = ss_total - ss_between
            eta_sq_partial = ss_between / (ss_between + ss_within) if (ss_between + ss_within) > 0 else 0
            
            significant = p_value < alpha
            
            result = {
                'test': 'One-way ANOVA',
                'f_value': f_value,
                'p_value': p_value,
                'df_between': df_between,
                'df_within': df_within,
                'ss_between': ss_between,
                'ss_within': ss_within,
                'ss_total': ss_total,
                'eta_squared': eta_sq,
                'eta_squared_partial': eta_sq_partial,
                'significant': significant,
                'alpha': alpha,
                'anova_table': anova_df.to_dict('records'),
                'error': None
            }
        else:
            result = {
                'test': 'One-way ANOVA',
                'error': 'ANOVA computation failed',
                'significant': False
            }
            
    except Exception as e:
        # 回退到 scipy 的 f_oneway
        try:
            groups = df[group_var].unique()
            group_data = [df[df[group_var] == g][measure_var].dropna().values for g in groups]
            
            if len(group_data) < 2:
                raise ValueError("At least 2 groups required")
            
            f_value, p_value = stats.f_oneway(*group_data)
            
            # 计算自由度
            n_total = sum(len(g) for g in group_data)
            k = len(group_data)
            df_between = k - 1
            df_within = n_total - k
            
            # 计算平方和（近似）
            grand_mean = np.concatenate(group_data).mean()
            ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in group_data)
            ss_total = sum(((x - grand_mean) ** 2 for g in group_data for x in g))
            ss_within = ss_total - ss_between
            
            eta_sq = ss_between / ss_total if ss_total > 0 else 0
            
            significant = p_value < alpha
            
            result = {
                'test': 'One-way ANOVA (scipy)',
                'f_value': float(f_value),
                'p_value': float(p_value),
                'df_between': float(df_between),
                'df_within': float(df_within),
                'ss_between': float(ss_between),
                'ss_within': float(ss_within),
                'ss_total': float(ss_total),
                'eta_squared': float(eta_sq),
                'significant': significant,
                'alpha': alpha,
                'error': None
            }
        except Exception as e2:
            result = {
                'test': 'One-way ANOVA',
                'error': f"Both methods failed: {str(e2)[:200]}",
                'significant': False
            }
    
    return result

def welch_anova(df: pd.DataFrame,
                group_var: str,
                measure_var: str,
                alpha: float = 0.05) -> Dict:
    """
    执行 Welch's ANOVA（方差不齐时使用）
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        Welch's ANOVA 结果
    """
    try:
        # 使用 pingouin 的 welch_anova
        welch_df = pg.welch_anova(data=df, dv=measure_var, between=group_var)
        
        if not welch_df.empty:
            result_row = welch_df.iloc[0]
            f_value = float(result_row['F'])
            p_value = float(result_row['p-unc'])
            df_between = float(result_row['DF'])
            df_within = float(result_row['DF'].iloc[1]) if len(welch_df) > 1 else None
            
            # Welch's ANOVA 不计算传统的效应量
            significant = p_value < alpha
            
            result = {
                'test': "Welch's ANOVA",
                'f_value': f_value,
                'p_value': p_value,
                'df_between': df_between,
                'df_within': df_within,
                'significant': significant,
                'alpha': alpha,
                'welch_table': welch_df.to_dict('records'),
                'error': None,
                'note': 'Welch ANOVA does not assume equal variances'
            }
        else:
            result = {
                'test': "Welch's ANOVA",
                'error': 'Welch ANOVA computation failed',
                'significant': False
            }
            
    except Exception as e:
        # 回退到自定义实现
        try:
            groups = df[group_var].unique()
            group_data = [df[df[group_var] == g][measure_var].dropna().values for g in groups]
            
            if len(group_data) < 2:
                raise ValueError("At least 2 groups required")
            
            # Welch's ANOVA 手动计算
            n_groups = len(group_data)
            group_means = [g.mean() for g in group_data]
            group_vars = [g.var(ddof=1) for g in group_data]
            group_sizes = [len(g) for g in group_data]
            
            # 加权均值
            weights = [n / v for n, v in zip(group_sizes, group_vars)]
            weighted_mean = sum(w * m for w, m in zip(weights, group_means)) / sum(weights)
            
            # 计算 F 统计量
            numerator = sum(w * (m - weighted_mean) ** 2 for w, m in zip(weights, group_means)) / (n_groups - 1)
            denominator = 1 + (2 * (n_groups - 2) / (n_groups ** 2 - 1)) * sum((1 - w / sum(weights)) ** 2 / (group_sizes[i] - 1) 
                                                                              for i, w in enumerate(weights))
            f_value = numerator / denominator
            
            # 自由度
            df_between = n_groups - 1
            df_within = (n_groups ** 2 - 1) / (3 * sum((1 - w / sum(weights)) ** 2 / (group_sizes[i] - 1) 
                                                      for i, w in enumerate(weights)))
            
            # P 值
            p_value = 1 - stats.f.cdf(f_value, df_between, df_within)
            
            significant = p_value < alpha
            
            result = {
                'test': "Welch's ANOVA (manual)",
                'f_value': float(f_value),
                'p_value': float(p_value),
                'df_between': float(df_between),
                'df_within': float(df_within),
                'significant': significant,
                'alpha': alpha,
                'error': None,
                'note': 'Manual implementation of Welch ANOVA'
            }
        except Exception as e2:
            result = {
                'test': "Welch's ANOVA",
                'error': f"Welch ANOVA failed: {str(e2)[:200]}",
                'significant': False
            }
    
    return result

def kruskal_wallis(df: pd.DataFrame,
                   group_var: str,
                   measure_var: str,
                   alpha: float = 0.05) -> Dict:
    """
    执行 Kruskal-Wallis H 检验（非参数替代）
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_var : str
        检测变量
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        Kruskal-Wallis 结果
    """
    try:
        groups = df[group_var].unique()
        group_data = [df[df[group_var] == g][measure_var].dropna().values for g in groups]
        
        if len(group_data) < 2:
            raise ValueError("At least 2 groups required")
        
        # 执行 Kruskal-Wallis 检验
        h_stat, p_value = stats.kruskal(*group_data)
        
        # 计算效应量 (epsilon-squared)
        n_total = sum(len(g) for g in group_data)
        epsilon_sq = (h_stat - (len(groups) - 1)) / (n_total - len(groups)) if n_total > len(groups) else 0
        
        significant = p_value < alpha
        
        result = {
            'test': 'Kruskal-Wallis H test',
            'h_statistic': float(h_stat),
            'p_value': float(p_value),
            'df': len(groups) - 1,
            'epsilon_squared': float(epsilon_sq),
            'significant': significant,
            'alpha': alpha,
            'error': None,
            'note': 'Non-parametric alternative to one-way ANOVA'
        }
        
    except Exception as e:
        result = {
            'test': 'Kruskal-Wallis H test',
            'error': f"Kruskal-Wallis failed: {str(e)[:200]}",
            'significant': False
        }
    
    return result

def two_way_anova(df: pd.DataFrame,
                  factor1: str,
                  factor2: str,
                  measure_var: str,
                  alpha: float = 0.05) -> Dict:
    """
    执行双因素 ANOVA
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    factor1 : str
        第一个因素变量
    factor2 : str
        第二个因素变量
    measure_var : str
        检测变量
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        双因素 ANOVA 结果
    """
    try:
        # 使用 pingouin 的双因素 ANOVA
        anova_df = pg.anova(data=df, dv=measure_var, between=[factor1, factor2], detailed=True)
        
        if not anova_df.empty:
            results = []
            for idx, row in anova_df.iterrows():
                source = row['Source']
                if source == 'Residual':
                    continue
                    
                result = {
                    'source': source,
                    'f_value': float(row['F']),
                    'p_value': float(row['p-unc']),
                    'df_between': float(row['DF']),
                    'df_within': float(anova_df[anova_df['Source'] == 'Residual']['DF'].iloc[0]) if 'Residual' in anova_df['Source'].values else None,
                    'ss': float(row['SS']),
                    'ms': float(row['MS']),
                    'eta_squared_partial': float(row['np2']) if 'np2' in row else None,
                    'significant': float(row['p-unc']) < alpha
                }
                results.append(result)
            
            # 检查交互作用
            interaction_present = any(r['source'].endswith('*') or '*' in r['source'] for r in results)
            
            result = {
                'test': 'Two-way ANOVA',
                'results': results,
                'anova_table': anova_df.to_dict('records'),
                'interaction_present': interaction_present,
                'alpha': alpha,
                'error': None
            }
        else:
            result = {
                'test': 'Two-way ANOVA',
                'error': 'Two-way ANOVA computation failed',
                'significant': False
            }
            
    except Exception as e:
        # 回退到 statsmodels
        try:
            formula = f'{measure_var} ~ C({factor1}) + C({factor2}) + C({factor1}):C({factor2})'
            model = ols(formula, data=df).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)
            
            results = []
            for idx, row in anova_table.iterrows():
                result = {
                    'source': idx,
                    'f_value': float(row['F']),
                    'p_value': float(row['PR(>F)']),
                    'df_between': float(row['df']),
                    'ss': float(row['sum_sq']),
                    'ms': float(row['sum_sq'] / row['df']) if row['df'] > 0 else 0,
                    'significant': float(row['PR(>F)']) < alpha
                }
                results.append(result)
            
            result = {
                'test': 'Two-way ANOVA (statsmodels)',
                'results': results,
                'anova_table': anova_table.to_dict('records'),
                'interaction_present': any(r['source'].endswith(':') for r in results),
                'alpha': alpha,
                'error': None
            }
        except Exception as e2:
            result = {
                'test': 'Two-way ANOVA',
                'error': f"Two-way ANOVA failed: {str(e2)[:200]}",
                'significant': False
            }
    
    return result

def get_anova_summary(anova_results: Dict) -> pd.DataFrame:
    """
    将 ANOVA 结果转换为摘要表格
    
    Parameters
    ----------
    anova_results : Dict
        ANOVA 结果
    
    Returns
    -------
    pd.DataFrame
        摘要表格
    """
    summary_data = []
    
    for var, result in anova_results.get('by_variable', {}).items():
        if 'error' in result:
            continue
            
        summary_data.append({
            'Variable': var,
            'Test': result.get('test', 'Unknown'),
            'F/H Statistic': result.get('f_value', result.get('h_statistic', None)),
            'P Value': result.get('p_value', None),
            'Significant': result.get('significant', False),
            'Effect Size': result.get('eta_squared', result.get('epsilon_squared', None)),
            'DF Between': result.get('df_between', None),
            'DF Within': result.get('df_within', None)
        })
    
    return pd.DataFrame(summary_data) if summary_data else pd.DataFrame()

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
    
    print("单因素 ANOVA 测试")
    anova_result = one_way_anova(test_data, 'group', 'value1')
    print(f"F值: {anova_result.get('f_value', 'N/A'):.2f}, P值: {anova_result.get('p_value', 'N/A'):.4f}")
    
    print("\nWelch ANOVA 测试")
    welch_result = welch_anova(test_data, 'group', 'value1')
    print(f"F值: {welch_result.get('f_value', 'N/A'):.2f}, P值: {welch_result.get('p_value', 'N/A'):.4f}")
    
    print("\nKruskal-Wallis 测试")
    kw_result = kruskal_wallis(test_data, 'group', 'value1')
    print(f"H统计量: {kw_result.get('h_statistic', 'N/A'):.2f}, P值: {kw_result.get('p_value', 'N/A'):.4f}")