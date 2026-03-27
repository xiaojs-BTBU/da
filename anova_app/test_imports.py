#!/usr/bin/env python3
"""
测试所有模块的导入
"""

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 测试导入
modules = [
    'modules.data_loader',
    'modules.variable_selector',
    'modules.stats_calculator',
    'modules.anova_executor',
    'modules.posthoc',
    'modules.visualizer',
    'modules.interactive_visualizer',
    'modules.report_generator',
    'modules.utils'
]

print("开始测试模块导入...")
for module_name in modules:
    try:
        __import__(module_name)
        print(f"[OK] {module_name} 导入成功")
    except Exception as e:
        print(f"[FAIL] {module_name} 导入失败: {e}")

print("\n测试 Streamlit 导入...")
try:
    import streamlit
    print("[OK] streamlit 导入成功")
except ImportError as e:
    print(f"[FAIL] streamlit 导入失败: {e}")

print("\n测试其他关键依赖...")
dependencies = [
    'pandas',
    'numpy',
    'scipy',
    'statsmodels',
    'pingouin',
    'matplotlib',
    'seaborn',
    'plotly',
    'altair',
    'reportlab'
]

for dep in dependencies:
    try:
        __import__(dep)
        print(f"[OK] {dep} 导入成功")
    except ImportError as e:
        print(f"[WARN] {dep} 导入失败: {e}")

print("\n导入测试完成！")