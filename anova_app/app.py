"""
Streamlit ANOVA 与可视化工具
主应用入口
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import sys
import os

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# 设置页面配置
st.set_page_config(
    page_title="自动化方差分析 (ANOVA) 与可视化工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏警告
warnings.filterwarnings('ignore')

# 设置 matplotlib 中文字体（解决中文乱码问题）
def set_chinese_font():
    import matplotlib
    import os
    # 中文字体备选路径
    font_paths = [
        "static/SimHei.ttf",  # 项目内字体
        "C:/Windows/Fonts/simhei.ttf",  # Windows 系统字体
        "C:/Windows/Fonts/msyh.ttc",    # Microsoft YaHei
        "C:/Windows/Fonts/msyh.ttf",    # Microsoft YaHei (另一种格式)
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
    ]
    font_added = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                matplotlib.font_manager.fontManager.addfont(font_path)
                font_name = matplotlib.font_manager.FontProperties(fname=font_path).get_name()
                matplotlib.rcParams['font.sans-serif'] = [font_name]
                matplotlib.rcParams['axes.unicode_minus'] = False
                font_added = True
                break
            except:
                continue
    if not font_added:
        # 尝试使用系统已注册的中文字体名称
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'DejaVu Sans']
        for font_name in chinese_fonts:
            if font_name in matplotlib.font_manager.fontManager.ttflist:
                matplotlib.rcParams['font.sans-serif'] = [font_name]
                matplotlib.rcParams['axes.unicode_minus'] = False
                font_added = True
                break
    if not font_added:
        # 最终回退
        matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

set_chinese_font()

# 导入自定义模块
try:
    from data_loader import load_data, validate_data
    from variable_selector import select_variables
    from stats_calculator import descriptive_stats, normality_test, homogeneity_test
    from anova_executor import perform_anova
    from posthoc import perform_posthoc
    from visualizer import create_boxplot, create_violinplot, create_barplot_with_scatter
    from interactive_visualizer import create_interactive_boxplot, create_interactive_violinplot
    from report_generator import generate_csv_report, generate_pdf_report
    from utils import display_error, display_warning
except ImportError as e:
    st.error(f"模块导入失败: {e}")
    st.info("请确保所有模块文件都存在。如果这是第一次运行，请先创建模块文件。")

# 应用标题
st.title("📊 自动化方差分析 (ANOVA) 与可视化工具")
st.markdown("""
    本工具用于执行方差分析 (ANOVA) 并生成可视化图表。支持单因素、多因素 ANOVA、Welch's ANOVA、Kruskal-Wallis 检验，
    并提供丰富的统计图表和交互式可视化。
""")

# 初始化 session state 变量
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

# 侧边栏 - 控制面板
with st.sidebar:
    st.header("📁 数据导入")
    
    # 文件上传器
    uploaded_file = st.file_uploader(
        "上传数据文件 (CSV, Excel)",
        type=['csv', 'xls', 'xlsx'],
        help="支持 CSV、Excel 格式。文件大小不超过 200MB。"
    )
    
    if uploaded_file is not None:
        try:
            df = load_data(uploaded_file)
            st.session_state.df = df
            st.success(f"数据加载成功！共 {df.shape[0]} 行, {df.shape[1]} 列")
            
            # 显示数据预览
            with st.expander("数据预览"):
                st.dataframe(df.head(), use_container_width=True)
                
        except Exception as e:
            display_error(f"数据加载失败: {e}")
    
    # 变量选择（仅在数据加载后显示）
    if st.session_state.df is not None:
        st.header("🎯 变量选择")
        
        group_var, measure_vars = select_variables(st.session_state.df)
        
        if group_var:
            st.session_state.group_var = group_var
        if measure_vars:
            st.session_state.measure_vars = measure_vars
        
        # 显示选择结果
        if st.session_state.group_var:
            st.info(f"**分组变量**: {st.session_state.group_var}")
        if st.session_state.measure_vars:
            st.info(f"**检测变量**: {', '.join(st.session_state.measure_vars)}")
    
    # 操作按钮
    st.header("⚙️ 分析操作")
    
    col1, col2 = st.columns(2)
    with col1:
        btn_anova = st.button("📈 方差分析", use_container_width=True, type="primary")
    with col2:
        btn_reset = st.button("🔄 重置", use_container_width=True)
    
    if btn_reset:
        st.session_state.df = None
        st.session_state.group_var = None
        st.session_state.measure_vars = []
        st.session_state.anova_results = None
        st.session_state.posthoc_results = None
        st.session_state.assumption_results = None
        st.rerun()
    
    # 可视化按钮
    st.header("📊 可视化")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        btn_boxplot = st.button("📦 箱线图", use_container_width=True)
    with col2:
        btn_violin = st.button("🎻 小提琴图", use_container_width=True)
    with col3:
        btn_bar = st.button("📊 柱状图", use_container_width=True)
    
    # 交互式可视化切换
    interactive_mode = st.checkbox("启用交互式图表", value=False)
    
    # 报告导出
    st.header("📤 报告导出")
    
    col1, col2 = st.columns(2)
    with col1:
        btn_csv = st.button("📄 CSV 报告", use_container_width=True)
    with col2:
        btn_pdf = st.button("📘 PDF 报告", use_container_width=True)

# 主界面 - 结果展示
if btn_anova and st.session_state.df is not None and st.session_state.group_var and st.session_state.measure_vars:
    st.header("📈 方差分析结果")
    
    with st.spinner("正在执行统计分析..."):
        try:
            # 描述性统计
            desc_stats = descriptive_stats(
                st.session_state.df, 
                st.session_state.group_var, 
                st.session_state.measure_vars
            )
            
            # 前提假设检验
            normality_results = normality_test(
                st.session_state.df, 
                st.session_state.group_var, 
                st.session_state.measure_vars
            )
            
            homogeneity_results = homogeneity_test(
                st.session_state.df, 
                st.session_state.group_var, 
                st.session_state.measure_vars
            )
            
            st.session_state.assumption_results = {
                'normality': normality_results,
                'homogeneity': homogeneity_results
            }
            
            # ANOVA
            anova_results = perform_anova(
                st.session_state.df,
                st.session_state.group_var,
                st.session_state.measure_vars,
                normality_results,
                homogeneity_results
            )
            st.session_state.anova_results = anova_results
            
            # 事后检验
            if anova_results['significant']:
                posthoc_results = perform_posthoc(
                    st.session_state.df,
                    st.session_state.group_var,
                    st.session_state.measure_vars,
                    anova_results,
                    homogeneity_results
                )
                st.session_state.posthoc_results = posthoc_results
            else:
                st.session_state.posthoc_results = None
            
        except Exception as e:
            display_error(f"分析过程中出现错误: {e}")
    
    # 显示结果
    if st.session_state.anova_results:
        from utils import display_anova_results
        display_anova_results(
            st.session_state.anova_results,
            st.session_state.assumption_results,
            st.session_state.posthoc_results
        )

# 可视化显示
if btn_boxplot and st.session_state.df is not None and st.session_state.group_var and st.session_state.measure_vars:
    st.header("📦 箱线图")
    
    for measure_var in st.session_state.measure_vars:
        st.subheader(f"变量: {measure_var}")
        
        if interactive_mode:
            fig = create_interactive_boxplot(
                st.session_state.df,
                st.session_state.group_var,
                measure_var,
                st.session_state.posthoc_results
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig = create_boxplot(
                st.session_state.df,
                st.session_state.group_var,
                measure_var,
                st.session_state.posthoc_results
            )
            st.pyplot(fig)
            plt.close()

if btn_violin and st.session_state.df is not None and st.session_state.group_var and st.session_state.measure_vars:
    st.header("🎻 小提琴图")
    
    for measure_var in st.session_state.measure_vars:
        st.subheader(f"变量: {measure_var}")
        
        if interactive_mode:
            fig = create_interactive_violinplot(
                st.session_state.df,
                st.session_state.group_var,
                measure_var,
                st.session_state.posthoc_results
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig = create_violinplot(
                st.session_state.df,
                st.session_state.group_var,
                measure_var,
                st.session_state.posthoc_results
            )
            st.pyplot(fig)
            plt.close()

if btn_bar and st.session_state.df is not None and st.session_state.group_var and st.session_state.measure_vars:
    st.header("📊 带散点的柱状图")
    
    for measure_var in st.session_state.measure_vars:
        st.subheader(f"变量: {measure_var}")
        
        fig = create_barplot_with_scatter(
            st.session_state.df,
            st.session_state.group_var,
            measure_var,
            st.session_state.posthoc_results
        )
        st.pyplot(fig)
        plt.close()

# 报告导出
if btn_csv and st.session_state.df is not None and st.session_state.group_var and st.session_state.measure_vars:
    with st.spinner("正在生成 CSV 报告..."):
        try:
            csv_data = generate_csv_report(
                st.session_state.df,
                st.session_state.group_var,
                st.session_state.measure_vars,
                st.session_state.anova_results,
                st.session_state.posthoc_results,
                st.session_state.assumption_results
            )
            st.download_button(
                label="下载 CSV 报告",
                data=csv_data,
                file_name="anova_report.csv",
                mime="text/csv"
            )
            st.success("CSV 报告生成成功！")
        except Exception as e:
            display_error(f"CSV 报告生成失败: {e}")

if btn_pdf and st.session_state.df is not None and st.session_state.group_var and st.session_state.measure_vars:
    with st.spinner("正在生成 PDF 报告..."):
        try:
            pdf_data = generate_pdf_report(
                st.session_state.df,
                st.session_state.group_var,
                st.session_state.measure_vars,
                st.session_state.anova_results,
                st.session_state.posthoc_results,
                st.session_state.assumption_results
            )
            st.download_button(
                label="下载 PDF 报告",
                data=pdf_data,
                file_name="anova_report.pdf",
                mime="application/pdf"
            )
            st.success("PDF 报告生成成功！")
        except Exception as e:
            display_error(f"PDF 报告生成失败: {e}")

# 底部信息
st.markdown("---")
st.caption("""
    **自动化方差分析工具** © 2026 | 使用 Streamlit 构建 | 
    统计方法：SciPy, Statsmodels, Pingouin | 可视化：Matplotlib, Seaborn, Plotly
""")