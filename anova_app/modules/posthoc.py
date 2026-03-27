"""
事后检验模块
执行两两比较：Tukey HSD、Games-Howell、Dunn's test 等
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.stats.multicomp as mc
import pingouin as pg
from typing import Dict, List, Tuple, Optional, Union
import warnings
try:
    import scikit_posthocs as sp
    SKPOSTHOCS_AVAILABLE = True
except ImportError:
    SKPOSTHOCS_AVAILABLE = False
    warnings.warn("scikit-posthocs not installed. Dunn's test will use pingouin if available.")

warnings.filterwarnings('ignore')

def perform_posthoc(df: pd.DataFrame,
                    group_var: str,
                    measure_vars: List[str],
                    anova_results: Optional[Dict] = None,
                    homogeneity_results: Optional[Dict] = None,
                    alpha: float = 0.05) -> Dict:
    """
    执行事后两两比较
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str
        分组变量
    measure_vars : List[str]
        检测变量列表
    anova_results : Dict, optional
        ANOVA 结果
    homogeneity_results : Dict, optional
        方差齐性检验结果
    alpha : float, optional
        显著性水平，默认 0.05
    
    Returns
    -------
    Dict
        事后检验结果
    """
    results = {
        'by_variable': {},
        'overall_summary': {},
        'alpha': alpha
    }
    
    df = df.copy()
    df[group_var] = df[group_var].astype(str)
    
    for var in measure_vars:
        if var not in df.columns:
            continue
            
        # 检查 ANOVA 结果是否显著
        anova_sig = False
        if anova_results and var in anova_results.get('by_variable', {}):
            anova_sig = anova_results['by_variable'][var].get('significant', False)
        
        # 如果 ANOVA 不显著，通常不进行事后检验
        if not anova_sig:
            results['by_variable'][var] = {
                'performed': False,
                'reason': 'ANOVA not significant',
                'pairwise_results': None
            }
            continue
        
        # 确定使用哪种事后检验方法
        test_type = determine_posthoc_test(var, homogeneity_results, anova_results)
        
        # 执行事后检验
        if test_type == 'tukey_hsd':
            posthoc_result = tukey_hsd(df, group_var, var, alpha)
        elif test_type == 'games_howell':
            posthoc_result = games_howell(df, group_var, var, alpha)
        elif test_type == 'dunn':
            posthoc_result = dunn_test(df, group_var, var, alpha)
        else:
            # 默认使用 Tukey HSD
            posthoc_result = tukey_hsd(df, group_var, var, alpha)
        
        posthoc_result['test_type'] = test_type
        posthoc_result['variable'] = var
        posthoc_result['group_variable'] = group_var
        
        results['by_variable'][var] = posthoc_result
    
    # 创建摘要
    summary = []
    for var, result in results['by_variable'].items():
        if result.get('performed', True):
            sig_pairs = result.get('significant_pairs', [])
            summary.append({
                'variable': var,
                'test': result.get('test_type', 'Unknown'),
                'total_pairs': result.get('total_pairs', 0),
                'significant_pairs': len(sig_pairs),
                'significant_ratio': len(sig_pairs) / result.get('total_pairs', 1) if result.get('total_pairs', 0) > 0 else 0
            })
        else:
            summary.append({
                'variable': var,
                'test': 'Not performed',
                'total_pairs': 0,
                'significant_pairs': 0,
                'significant_ratio': 0
            })
    
    results['overall_summary'] = pd.DataFrame(summary) if summary else pd.DataFrame()
    
    return results

def determine_posthoc_test(var: str,
                           homogeneity_results: Optional[Dict],
                           anova_results: Optional[Dict]) -> str:
    """
    确定使用哪种事后检验方法
    
    Parameters
    ----------
    var : str
        变量名
    homogeneity_results : Dict
        方差齐性检验结果
    anova_results : Dict
        ANOVA 结果
    
    Returns
    -------
    str
        检验类型：'tukey_hsd', 'games_howell', 'dunn'
    """
    # 默认使用 Tukey HSD
    default_test = 'tukey_hsd'
    
    # 检查方差齐性
    homogeneous = None
    if homogeneity_results and var in homogeneity_results.get('conclusion', {}):
        homogeneous = homogeneity_results['conclusion'][var].get('homogeneous')
    
    # 检查 ANOVA 检验类型
    anova_test_type = None
    if anova_results and var in anova_results.get('by_variable', {}):
        anova_test_type = anova_results['by_variable'][var].get('test_type', '')
    
    # 决策逻辑
    if anova_test_type == 'kruskal_wallis':
        return 'dunn'
    elif homogeneous is False:
        return 'games_howell'
    else:
        return 'tukey_hsd'

def tukey_hsd(df: pd.DataFrame,
              group_var: str,
              measure_var: str,
              alpha: float = 0.05) -> Dict:
    """
    执行 Tukey HSD 检验
    
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
        Tukey HSD 结果
    """
    try:
        # 使用 pingouin 的 pairwise_tukey
        tukey_df = pg.pairwise_tukey(data=df, dv=measure_var, between=group_var)
        
        if not tukey_df.empty:
            # 提取显著对
            sig_pairs = []
            pairwise_results = []
            
            for _, row in tukey_df.iterrows():
                pair = (str(row['A']), str(row['B']))
                p_value = float(row['p-tukey'])
                significant = p_value < alpha
                
                pairwise_result = {
                    'group1': row['A'],
                    'group2': row['B'],
                    'mean_diff': float(row['diff']),
                    'se': float(row['se']) if 'se' in row else None,
                    'ci_lower': float(row['CI95%'][0]) if 'CI95%' in row else None,
                    'ci_upper': float(row['CI95%'][1]) if 'CI95%' in row else None,
                    'p_value': p_value,
                    'significant': significant
                }
                pairwise_results.append(pairwise_result)
                
                if significant:
                    sig_pairs.append(pair)
            
            result = {
                'test': "Tukey's HSD",
                'pairwise_results': pairwise_results,
                'significant_pairs': sig_pairs,
                'total_pairs': len(pairwise_results),
                'alpha': alpha,
                'tukey_table': tukey_df.to_dict('records'),
                'error': None
            }
        else:
            result = {
                'test': "Tukey's HSD",
                'error': 'Tukey HSD computation failed',
                'pairwise_results': None,
                'significant_pairs': []
            }
            
    except Exception as e:
        # 回退到 statsmodels
        try:
            groups = df[group_var].unique()
            group_data = [df[df[group_var] == g][measure_var].dropna().values for g in groups]
            
            # 准备数据
            endog = np.concatenate(group_data)
            groups_flat = np.concatenate([[str(g)] * len(d) for g, d in zip(groups, group_data)])
            
            # 执行 Tukey HSD
            tukey = mc.pairwise_tukeyhsd(endog=endog, groups=groups_flat, alpha=alpha)
            
            # 提取结果
            pairwise_results = []
            sig_pairs = []
            
            if hasattr(tukey, 'results_table'):
                results_table = tukey.results_table.data
                # 跳过标题行
                for row in results_table[1:]:
                    group1, group2, meandiff, p, lower, upper, reject = row
                    significant = bool(reject)
                    
                    pairwise_result = {
                        'group1': str(group1),
                        'group2': str(group2),
                        'mean_diff': float(meandiff),
                        'p_value': float(p),
                        'ci_lower': float(lower),
                        'ci_upper': float(upper),
                        'significant': significant
                    }
                    pairwise_results.append(pairwise_result)
                    
                    if significant:
                        sig_pairs.append((str(group1), str(group2)))
            
            result = {
                'test': "Tukey's HSD (statsmodels)",
                'pairwise_results': pairwise_results,
                'significant_pairs': sig_pairs,
                'total_pairs': len(pairwise_results),
                'alpha': alpha,
                'error': None
            }
        except Exception as e2:
            result = {
                'test': "Tukey's HSD",
                'error': f"Tukey HSD failed: {str(e2)[:200]}",
                'pairwise_results': None,
                'significant_pairs': []
            }
    
    return result

def games_howell(df: pd.DataFrame,
                 group_var: str,
                 measure_var: str,
                 alpha: float = 0.05) -> Dict:
    """
    执行 Games-Howell 检验（方差不齐时使用）
    
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
        Games-Howell 结果
    """
    try:
        # 使用 pingouin 的 pairwise_gameshowell
        gh_df = pg.pairwise_gameshowell(data=df, dv=measure_var, between=group_var)
        
        if not gh_df.empty:
            # 提取显著对
            sig_pairs = []
            pairwise_results = []
            
            for _, row in gh_df.iterrows():
                pair = (str(row['A']), str(row['B']))
                p_value = float(row['pval'])
                significant = p_value < alpha
                
                pairwise_result = {
                    'group1': row['A'],
                    'group2': row['B'],
                    'mean_diff': float(row['diff']),
                    'se': float(row['se']) if 'se' in row else None,
                    'ci_lower': float(row['CI95%'][0]) if 'CI95%' in row else None,
                    'ci_upper': float(row['CI95%'][1]) if 'CI95%' in row else None,
                    'p_value': p_value,
                    'significant': significant
                }
                pairwise_results.append(pairwise_result)
                
                if significant:
                    sig_pairs.append(pair)
            
            result = {
                'test': "Games-Howell",
                'pairwise_results': pairwise_results,
                'significant_pairs': sig_pairs,
                'total_pairs': len(pairwise_results),
                'alpha': alpha,
                'games_howell_table': gh_df.to_dict('records'),
                'error': None
            }
        else:
            result = {
                'test': "Games-Howell",
                'error': 'Games-Howell computation failed',
                'pairwise_results': None,
                'significant_pairs': []
            }
            
    except Exception as e:
        # 自定义实现
        try:
            groups = df[group_var].unique()
            group_data = [df[df[group_var] == g][measure_var].dropna().values for g in groups]
            
            n_groups = len(groups)
            pairwise_results = []
            sig_pairs = []
            
            # 遍历所有两两组合
            for i in range(n_groups):
                for j in range(i + 1, n_groups):
                    group1_data = group_data[i]
                    group2_data = group_data[j]
                    
                    n1, n2 = len(group1_data), len(group2_data)
                    if n1 < 2 or n2 < 2:
                        continue
                    
                    mean1, mean2 = group1_data.mean(), group2_data.mean()
                    var1, var2 = group1_data.var(ddof=1), group2_data.var(ddof=1)
                    
                    # Games-Howell 统计量
                    t_stat = abs(mean1 - mean2) / np.sqrt(var1/n1 + var2/n2)
                    
                    # 自由度 (Welch-Satterthwaite)
                    df_ws = (var1/n1 + var2/n2)**2 / ((var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1))
                    
                    # P 值
                    p_value = 2 * (1 - stats.t.cdf(t_stat, df_ws))
                    
                    # 置信区间
                    se = np.sqrt(var1/n1 + var2/n2)
                    t_crit = stats.t.ppf(1 - alpha/2, df_ws)
                    ci_lower = (mean1 - mean2) - t_crit * se
                    ci_upper = (mean1 - mean2) + t_crit * se
                    
                    significant = p_value < alpha
                    
                    pairwise_result = {
                        'group1': str(groups[i]),
                        'group2': str(groups[j]),
                        'mean_diff': float(mean1 - mean2),
                        'se': float(se),
                        't_stat': float(t_stat),
                        'df': float(df_ws),
                        'ci_lower': float(ci_lower),
                        'ci_upper': float(ci_upper),
                        'p_value': float(p_value),
                        'significant': significant
                    }
                    pairwise_results.append(pairwise_result)
                    
                    if significant:
                        sig_pairs.append((str(groups[i]), str(groups[j])))
            
            result = {
                'test': "Games-Howell (manual)",
                'pairwise_results': pairwise_results,
                'significant_pairs': sig_pairs,
                'total_pairs': len(pairwise_results),
                'alpha': alpha,
                'error': None
            }
        except Exception as e2:
            result = {
                'test': "Games-Howell",
                'error': f"Games-Howell failed: {str(e2)[:200]}",
                'pairwise_results': None,
                'significant_pairs': []
            }
    
    return result

def dunn_test(df: pd.DataFrame,
              group_var: str,
              measure_var: str,
              alpha: float = 0.05,
              method: str = 'bonferroni') -> Dict:
    """
    执行 Dunn's test（Kruskal-Wallis 的事后检验）
    
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
    method : str, optional
        多重比较校正方法，默认 'bonferroni'
    
    Returns
    -------
    Dict
        Dunn's test 结果
    """
    try:
        if SKPOSTHOCS_AVAILABLE:
            # 使用 scikit-posthocs
            # 准备数据
            groups = df[group_var].unique()
            group_data = {}
            for g in groups:
                group_data[g] = df[df[group_var] == g][measure_var].dropna().values
            
            # 执行 Dunn's test
            dunn_df = sp.posthoc_dunn(df, val_col=measure_var, group_col=group_var, p_adjust=method)
            
            # 转换为成对结果
            pairwise_results = []
            sig_pairs = []
            
            for i, group1 in enumerate(groups):
                for j, group2 in enumerate(groups):
                    if i >= j:
                        continue
                    
                    p_value = dunn_df.loc[group1, group2]
                    significant = p_value < alpha
                    
                    pairwise_result = {
                        'group1': str(group1),
                        'group2': str(group2),
                        'p_value': float(p_value),
                        'significant': significant
                    }
                    pairwise_results.append(pairwise_result)
                    
                    if significant:
                        sig_pairs.append((str(group1), str(group2)))
            
            result = {
                'test': f"Dunn's test ({method} corrected)",
                'pairwise_results': pairwise_results,
                'significant_pairs': sig_pairs,
                'total_pairs': len(pairwise_results),
                'alpha': alpha,
                'correction_method': method,
                'dunn_table': dunn_df.to_dict('records'),
                'error': None
            }
        else:
            # 使用 pingouin 的 pairwise_tests（如果可用）
            try:
                # pingouin 的 pairwise_tests 支持非参数检验
                dunn_df = pg.pairwise_tests(data=df, dv=measure_var, between=group_var,
                                           parametric=False, padjust=method)
                
                if not dunn_df.empty:
                    pairwise_results = []
                    sig_pairs = []
                    
                    for _, row in dunn_df.iterrows():
                        if row['Contrast'] != f'{group_var}':
                            continue
                            
                        group1 = row['A']
                        group2 = row['B']
                        p_value = float(row['p-unc'])
                        p_adj = float(row['p-corr']) if 'p-corr' in row else p_value
                        significant = p_adj < alpha
                        
                        pairwise_result = {
                            'group1': str(group1),
                            'group2': str(group2),
                            'p_value': float(p_value),
                            'p_adjusted': float(p_adj),
                            'significant': significant
                        }
                        pairwise_results.append(pairwise_result)
                        
                        if significant:
                            sig_pairs.append((str(group1), str(group2)))
                    
                    result = {
                        'test': f"Dunn's test ({method} corrected)",
                        'pairwise_results': pairwise_results,
                        'significant_pairs': sig_pairs,
                        'total_pairs': len(pairwise_results),
                        'alpha': alpha,
                        'correction_method': method,
                        'error': None
                    }
                else:
                    raise ValueError("No results from pingouin")
                    
            except Exception as e_pg:
                # 手动实现
                from itertools import combinations
                
                groups = df[group_var].unique()
                group_ranks = {}
                
                # 计算整体秩
                all_values = []
                all_groups = []
                for g in groups:
                    values = df[df[group_var] == g][measure_var].dropna().values
                    all_values.extend(values)
                    all_groups.extend([g] * len(values))
                
                # 计算秩
                ranks = stats.rankdata(all_values)
                
                # 计算每组平均秩
                group_avg_ranks = {}
                for g in groups:
                    mask = [gg == g for gg in all_groups]
                    group_ranks_g = [r for r, m in zip(ranks, mask) if m]
                    group_avg_ranks[g] = np.mean(group_ranks_g) if group_ranks_g else 0
                
                # 计算 Dunn 统计量
                N = len(all_values)
                pairwise_results = []
                sig_pairs = []
                
                for (g1, g2) in combinations(groups, 2):
                    n1 = sum(1 for gg in all_groups if gg == g1)
                    n2 = sum(1 for gg in all_groups if gg == g2)
                    
                    if n1 == 0 or n2 == 0:
                        continue
                    
                    # Dunn 统计量
                    z = (group_avg_ranks[g1] - group_avg_ranks[g2]) / np.sqrt(N*(N+1)/12 * (1/n1 + 1/n2))
                    
                    # P 值
                    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                    
                    # Bonferroni 校正
                    k = len(groups)
                    total_pairs = k*(k-1)/2
                    if method == 'bonferroni':
                        p_adj = min(p_value * total_pairs, 1.0)
                    else:
                        p_adj = p_value
                    
                    significant = p_adj < alpha
                    
                    pairwise_result = {
                        'group1': str(g1),
                        'group2': str(g2),
                        'z_stat': float(z),
                        'p_value': float(p_value),
                        'p_adjusted': float(p_adj),
                        'significant': significant
                    }
                    pairwise_results.append(pairwise_result)
                    
                    if significant:
                        sig_pairs.append((str(g1), str(g2)))
                
                result = {
                    'test': f"Dunn's test ({method} corrected, manual)",
                    'pairwise_results': pairwise_results,
                    'significant_pairs': sig_pairs,
                    'total_pairs': len(pairwise_results),
                    'alpha': alpha,
                    'correction_method': method,
                    'error': None
                }
                
    except Exception as e:
        result = {
            'test': "Dunn's test",
            'error': f"Dunn's test failed: {str(e)[:200]}",
            'pairwise_results': None,
            'significant_pairs': []
        }
    
    return result

def get_significance_matrix(posthoc_results: Dict, variable: str) -> pd.DataFrame:
    """
    获取显著性矩阵
    
    Parameters
    ----------
    posthoc_results : Dict
        事后检验结果
    variable : str
        变量名
    
    Returns
    -------
    pd.DataFrame
        显著性矩阵（布尔值）
    """
    if variable not in posthoc_results.get('by_variable', {}):
        return pd.DataFrame()
    
    var_results = posthoc_results['by_variable'][variable]
    if not var_results.get('pairwise_results'):
        return pd.DataFrame()
    
    # 获取所有组
    groups = set()
    for result in var_results['pairwise_results']:
        groups.add(result['group1'])
        groups.add(result['group2'])
    
    groups = sorted(groups)
    n = len(groups)
    
    # 创建矩阵
    matrix = pd.DataFrame(np.zeros((n, n)), index=groups, columns=groups)
    
    for result in var_results['pairwise_results']:
        i = groups.index(result['group1'])
        j = groups.index(result['group2'])
        significant = result['significant']
        
        matrix.iloc[i, j] = 1 if significant else 0
        matrix.iloc[j, i] = 1 if significant else 0
    
    # 对角线设为 0
    np.fill_diagonal(matrix.values, 0)
    
    return matrix

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
    
    print("Tukey HSD 测试")
    tukey_result = tukey_hsd(test_data, 'group', 'value1')
    print(f"显著对数量: {len(tukey_result.get('significant_pairs', []))}")
    
    print("\nGames-Howell 测试")
    gh_result = games_howell(test_data, 'group', 'value1')
    print(f"显著对数量: {len(gh_result.get('significant_pairs', []))}")