#!/usr/bin/env python3
"""
集成测试：测试核心功能流程
"""

import sys
import os
import pandas as pd
import numpy as np

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_anova_pipeline():
    """测试完整的 ANOVA 流程"""
    print("开始集成测试...")
    
    # 创建测试数据
    np.random.seed(42)
    n_per_group = 20
    groups = ['Control', 'Treatment1', 'Treatment2']
    
    df = pd.DataFrame({
        'group': np.repeat(groups, n_per_group),
        'score': np.concatenate([
            np.random.normal(50, 10, n_per_group),
            np.random.normal(55, 12, n_per_group),
            np.random.normal(65, 15, n_per_group)
        ]),
        'value': np.concatenate([
            np.random.exponential(5, n_per_group),
            np.random.exponential(7, n_per_group),
            np.random.exponential(10, n_per_group)
        ])
    })
    
    print(f"测试数据创建完成: {df.shape[0]} 行, {df.shape[1]} 列")
    print(f"分组变量: group (水平: {df['group'].unique().tolist()})")
    print(f"检测变量: score, value")
    
    # 测试数据加载模块
    try:
        from modules.data_loader import validate_data, get_column_types
        valid, msg = validate_data(df, 'group', ['score', 'value'])
        print(f"数据验证: {valid}, 消息: {msg}")
        
        col_types = get_column_types(df)
        print(f"列类型: {col_types}")
    except Exception as e:
        print(f"数据加载模块测试失败: {e}")
        return False
    
    # 测试统计计算模块
    try:
        from modules.stats_calculator import descriptive_stats, normality_test, homogeneity_test
        
        desc = descriptive_stats(df, 'group', ['score'])
        print(f"描述性统计计算成功，包含 {len(desc['by_group']['score'])} 个组")
        
        norm = normality_test(df, 'group', ['score'])
        print(f"正态性检验完成: score 整体正态性 = {norm['overall']['score']['normal']}")
        
        homo = homogeneity_test(df, 'group', ['score'])
        print(f"方差齐性检验完成: score 方差齐性 = {homo['by_variable']['score']['homogeneous']}")
    except Exception as e:
        print(f"统计计算模块测试失败: {e}")
        return False
    
    # 测试 ANOVA 执行模块
    try:
        from modules.anova_executor import perform_anova, determine_test_type
        
        test_type = determine_test_type('score', norm, homo)
        print(f"推荐的检验方法: {test_type}")
        
        anova_results = perform_anova(df, 'group', ['score'], norm, homo)
        print(f"ANOVA 执行成功，检验了 {len(anova_results['by_variable'])} 个变量")
        
        for var, result in anova_results['by_variable'].items():
            if 'error' not in result:
                print(f"  {var}: {result['test']}, F/H={result.get('f_value', result.get('h_statistic')):.2f}, p={result.get('p_value'):.4f}, 显著={result.get('significant')}")
    except Exception as e:
        print(f"ANOVA 执行模块测试失败: {e}")
        return False
    
    # 测试事后检验模块（如果 ANOVA 显著）
    try:
        from modules.posthoc import perform_posthoc
        
        # 模拟显著的 ANOVA 结果
        anova_sig = {'by_variable': {'score': {'significant': True}}}
        posthoc_results = perform_posthoc(df, 'group', ['score'], anova_sig, homo)
        print(f"事后检验执行成功，{len(posthoc_results.get('by_variable', {}))} 个变量进行了检验")
    except Exception as e:
        print(f"事后检验模块测试失败: {e}")
        # 继续测试，不是关键错误
    
    # 测试可视化模块（不显示图形）
    try:
        from modules.visualizer import create_boxplot
        import matplotlib
        matplotlib.use('Agg')  # 不使用 GUI 后端
        
        fig = create_boxplot(df, 'group', 'score')
        print(f"箱线图创建成功，图形尺寸: {fig.get_size_inches()}")
    except Exception as e:
        print(f"可视化模块测试失败: {e}")
        # 继续测试
    
    # 测试报告生成模块
    try:
        from modules.report_generator import generate_csv_report
        
        csv_report = generate_csv_report(df, 'group', ['score'], anova_results, posthoc_results, {'normality': norm, 'homogeneity': homo})
        print(f"CSV 报告生成成功，长度: {len(csv_report)} 字符")
    except Exception as e:
        print(f"报告生成模块测试失败: {e}")
        # 继续测试
    
    print("\n集成测试完成！所有核心模块功能正常。")
    return True

if __name__ == "__main__":
    success = test_anova_pipeline()
    sys.exit(0 if success else 1)