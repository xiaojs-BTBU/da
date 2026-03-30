"""
报告生成模块
生成 CSV 和 PDF 报告
"""

import pandas as pd
import numpy as np
import io
import base64
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import warnings

warnings.filterwarnings('ignore')

# 尝试导入 reportlab 用于 PDF 生成
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics import renderPDF
    from reportlab.lib.colors import HexColor
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    warnings.warn("ReportLab not installed. PDF reports will not be available.")

def generate_csv_report(df: pd.DataFrame,
                        group_var: str,
                        measure_vars: List[str],
                        anova_results: Optional[Dict] = None,
                        posthoc_results: Optional[Dict] = None,
                        assumption_results: Optional[Dict] = None) -> str:
    """
    生成 CSV 格式的报告
    
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
    posthoc_results : Dict, optional
        事后检验结果
    assumption_results : Dict, optional
        假设检验结果
    
    Returns
    -------
    str
        CSV 字符串
    """
    output = io.StringIO()
    
    # 写入 UTF-8 BOM 以便 Excel 正确识别编码
    output.write('\ufeff')
    
    # 写入报告头
    output.write("方差分析 (ANOVA) 报告\n")
    output.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write(f"数据形状: {df.shape[0]} 行, {df.shape[1]} 列\n")
    output.write(f"分组变量: {group_var}\n")
    output.write(f"检测变量: {', '.join(measure_vars)}\n")
    output.write("\n")
    
    # 描述性统计
    output.write("描述性统计\n")
    desc_data = []
    for var in measure_vars:
        if var not in df.columns:
            continue
        for group in df[group_var].unique():
            group_data = df[df[group_var] == group][var].dropna()
            if len(group_data) > 0:
                desc_data.append({
                    'Variable': var,
                    'Group': group,
                    'N': len(group_data),
                    'Mean': group_data.mean(),
                    'Std': group_data.std(),
                    'Median': group_data.median(),
                    'Min': group_data.min(),
                    'Max': group_data.max()
                })
    
    if desc_data:
        desc_df = pd.DataFrame(desc_data)
        desc_df.to_csv(output, index=False, mode='a', header=True)
        output.write("\n")
    
    # 假设检验结果
    if assumption_results:
        output.write("前提假设检验\n")
        
        # 正态性检验
        if 'normality' in assumption_results:
            output.write("正态性检验 (Shapiro-Wilk)\n")
            norm_data = []
            for var in measure_vars:
                if var in assumption_results['normality'].get('overall', {}):
                    norm_result = assumption_results['normality']['overall'][var]
                    norm_data.append({
                        'Variable': var,
                        'Statistic': norm_result.get('statistic'),
                        'P Value': norm_result.get('p_value'),
                        'Normal': norm_result.get('normal'),
                        'Test': norm_result.get('test')
                    })
            
            if norm_data:
                norm_df = pd.DataFrame(norm_data)
                norm_df.to_csv(output, index=False, mode='a', header=True)
                output.write("\n")
        
        # 方差齐性检验
        if 'homogeneity' in assumption_results:
            output.write("方差齐性检验 (Levene)\n")
            homo_data = []
            for var in measure_vars:
                if var in assumption_results['homogeneity'].get('by_variable', {}):
                    homo_result = assumption_results['homogeneity']['by_variable'][var]
                    homo_data.append({
                        'Variable': var,
                        'Statistic': homo_result.get('statistic'),
                        'P Value': homo_result.get('p_value'),
                        'Homogeneous': homo_result.get('homogeneous'),
                        'Test': homo_result.get('test')
                    })
            
            if homo_data:
                homo_df = pd.DataFrame(homo_data)
                homo_df.to_csv(output, index=False, mode='a', header=True)
                output.write("\n")
    
    # ANOVA 结果
    if anova_results:
        output.write("方差分析 (ANOVA) 结果\n")
        anova_data = []
        for var in measure_vars:
            if var in anova_results.get('by_variable', {}):
                anova_result = anova_results['by_variable'][var]
                if 'error' in anova_result:
                    continue
                
                anova_data.append({
                    'Variable': var,
                    'Test': anova_result.get('test', ''),
                    'F/H Statistic': anova_result.get('f_value', anova_result.get('h_statistic')),
                    'P Value': anova_result.get('p_value'),
                    'Significant': anova_result.get('significant', False),
                    'Effect Size': anova_result.get('eta_squared', anova_result.get('epsilon_squared')),
                    'DF Between': anova_result.get('df_between'),
                    'DF Within': anova_result.get('df_within')
                })
        
        if anova_data:
            anova_df = pd.DataFrame(anova_data)
            anova_df.to_csv(output, index=False, mode='a', header=True)
            output.write("\n")
    
    # 事后检验结果
    if posthoc_results:
        output.write("事后两两比较结果\n")
        for var in measure_vars:
            if var in posthoc_results.get('by_variable', {}):
                var_results = posthoc_results['by_variable'][var]
                if not var_results.get('pairwise_results'):
                    continue
                
                output.write(f"\n变量: {var}\n")
                posthoc_data = []
                for result in var_results['pairwise_results']:
                    posthoc_data.append({
                        'Group1': result['group1'],
                        'Group2': result['group2'],
                        'Mean Difference': result.get('mean_diff'),
                        'P Value': result.get('p_value'),
                        'Significant': result.get('significant', False),
                        'CI Lower': result.get('ci_lower'),
                        'CI Upper': result.get('ci_upper')
                    })
                
                if posthoc_data:
                    posthoc_df = pd.DataFrame(posthoc_data)
                    posthoc_df.to_csv(output, index=False, mode='a', header=True)
    
    return output.getvalue()

def generate_pdf_report(df: pd.DataFrame,
                        group_var: str,
                        measure_vars: List[str],
                        anova_results: Optional[Dict] = None,
                        posthoc_results: Optional[Dict] = None,
                        assumption_results: Optional[Dict] = None,
                        figures: Optional[List] = None) -> bytes:
    """
    生成 PDF 格式的报告
    
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
    posthoc_results : Dict, optional
        事后检验结果
    assumption_results : Dict, optional
        假设检验结果
    figures : List, optional
        图形对象列表
    
    Returns
    -------
    bytes
        PDF 文件的字节数据
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is not installed. Please install reportlab to generate PDF reports.")
    
    # 创建 PDF 文档
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    # 获取样式
    styles = getSampleStyleSheet()
    
    # 注册中文字体
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        font_paths = [
            "static/SimHei.ttf",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyh.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]
        font_registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    # 注册字体族，确保粗体、斜体变体
                    pdfmetrics.registerFontFamily('ChineseFont',
                                                  normal='ChineseFont',
                                                  bold='ChineseFont',
                                                  italic='ChineseFont',
                                                  boldItalic='ChineseFont')
                    font_registered = True
                    break
                except Exception as e:
                    print(f"字体注册失败 {font_path}: {e}")
                    continue
        if not font_registered:
            # 尝试使用系统已注册字体名称
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', 'SimHei'))
                pdfmetrics.registerFontFamily('ChineseFont',
                                              normal='ChineseFont',
                                              bold='ChineseFont',
                                              italic='ChineseFont',
                                              boldItalic='ChineseFont')
                font_registered = True
            except Exception as e:
                print(f"系统字体注册失败: {e}")
        
        if font_registered:
            # 设置所有样式使用该字体
            for style_name in ['Normal', 'Heading1', 'Heading2', 'Heading3', 'Title', 'Heading4']:
                if style_name in styles:
                    styles[style_name].fontName = 'ChineseFont'
            print("中文字体注册并应用到样式。")
        else:
            warnings.warn("无法注册任何中文字体，PDF 中文可能显示为乱码。")
    except Exception as e:
        warnings.warn(f"无法注册中文字体: {e}")
    
    # 创建自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # 居中
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20
    )
    
    normal_style = styles['Normal']
    
    # 构建内容
    story = []
    
    # 标题
    story.append(Paragraph("方差分析 (ANOVA) 报告", title_style))
    story.append(Spacer(1, 12))
    
    # 基本信息
    story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Paragraph(f"数据形状: {df.shape[0]} 行, {df.shape[1]} 列", normal_style))
    story.append(Paragraph(f"分组变量: {group_var}", normal_style))
    story.append(Paragraph(f"检测变量: {', '.join(measure_vars)}", normal_style))
    story.append(Spacer(1, 20))
    
    # 描述性统计表格
    story.append(Paragraph("描述性统计", heading_style))
    
    desc_data = []
    for var in measure_vars[:3]:  # 限制前3个变量以避免表格过大
        if var not in df.columns:
            continue
        for group in sorted(df[group_var].unique()):
            group_data = df[df[group_var] == group][var].dropna()
            if len(group_data) > 0:
                desc_data.append([
                    var, group, str(len(group_data)),
                    f"{group_data.mean():.2f}", f"{group_data.std():.2f}",
                    f"{group_data.median():.2f}", f"{group_data.min():.2f}",
                    f"{group_data.max():.2f}"
                ])
    
    if desc_data:
        # 添加表头
        desc_header = ['变量', '组别', '样本量', '均值', '标准差', '中位数', '最小值', '最大值']
        table_data = [desc_header] + desc_data
        
        desc_table = Table(table_data, colWidths=[0.8*inch, 0.8*inch, 0.8*inch, 
                                                  0.8*inch, 0.8*inch, 0.8*inch, 
                                                  0.8*inch, 0.8*inch])
        desc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(desc_table)
        story.append(Spacer(1, 20))
    
    # 假设检验结果
    if assumption_results:
        story.append(Paragraph("前提假设检验", heading_style))
        
        # 正态性检验
        if 'normality' in assumption_results:
            story.append(Paragraph("正态性检验 (Shapiro-Wilk)", styles['Heading3']))
            
            norm_data = []
            for var in measure_vars[:3]:
                if var in assumption_results['normality'].get('overall', {}):
                    norm_result = assumption_results['normality']['overall'][var]
                    p_value = norm_result.get('p_value')
                    if p_value is not None:
                        norm_data.append([
                            var, 
                            f"{norm_result.get('statistic', 'N/A'):.3f}" if norm_result.get('statistic') is not None else 'N/A',
                            f"{p_value:.4f}",
                            "满足" if norm_result.get('normal') else "不满足" if norm_result.get('normal') is not None else "N/A"
                        ])
            
            if norm_data:
                norm_header = ['变量', '统计量', 'P 值', '正态性']
                norm_table_data = [norm_header] + norm_data
                
                norm_table = Table(norm_table_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
                norm_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(norm_table)
                story.append(Spacer(1, 10))
        
        # 方差齐性检验
        if 'homogeneity' in assumption_results:
            story.append(Paragraph("方差齐性检验 (Levene)", styles['Heading3']))
            
            homo_data = []
            for var in measure_vars[:3]:
                if var in assumption_results['homogeneity'].get('by_variable', {}):
                    homo_result = assumption_results['homogeneity']['by_variable'][var]
                    p_value = homo_result.get('p_value')
                    if p_value is not None:
                        homo_data.append([
                            var,
                            f"{homo_result.get('statistic', 'N/A'):.3f}" if homo_result.get('statistic') is not None else 'N/A',
                            f"{p_value:.4f}",
                            "齐性" if homo_result.get('homogeneous') else "不齐性" if homo_result.get('homogeneous') is not None else "N/A"
                        ])
            
            if homo_data:
                homo_header = ['变量', '统计量', 'P 值', '方差齐性']
                homo_table_data = [homo_header] + homo_data
                
                homo_table = Table(homo_table_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
                homo_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(homo_table)
                story.append(Spacer(1, 20))
    
    # ANOVA 结果
    if anova_results:
        story.append(Paragraph("方差分析 (ANOVA) 结果", heading_style))
        
        anova_data = []
        for var in measure_vars[:3]:
            if var in anova_results.get('by_variable', {}):
                anova_result = anova_results['by_variable'][var]
                if 'error' in anova_result:
                    continue
                
                f_value = anova_result.get('f_value', anova_result.get('h_statistic'))
                p_value = anova_result.get('p_value')
                
                if p_value is not None:
                    significance = "显著" if anova_result.get('significant') else "不显著"
                    
                    anova_data.append([
                        var,
                        anova_result.get('test', ''),
                        f"{f_value:.3f}" if f_value is not None else 'N/A',
                        f"{p_value:.4f}",
                        significance,
                        f"{anova_result.get('eta_squared', anova_result.get('epsilon_squared', 'N/A')):.3f}" if anova_result.get('eta_squared') is not None else 'N/A'
                    ])
        
        if anova_data:
            anova_header = ['变量', '检验方法', 'F/H 统计量', 'P 值', '显著性', '效应量']
            anova_table_data = [anova_header] + anova_data
            
            anova_table = Table(anova_table_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            anova_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(anova_table)
            story.append(Spacer(1, 20))
    
    # 事后检验结果
    if posthoc_results:
        story.append(Paragraph("事后两两比较结果", heading_style))
        
        for var in measure_vars[:2]:  # 限制前2个变量
            if var in posthoc_results.get('by_variable', {}):
                var_results = posthoc_results['by_variable'][var]
                if not var_results.get('pairwise_results'):
                    continue
                
                story.append(Paragraph(f"变量: {var}", styles['Heading3']))
                
                posthoc_data = []
                for result in var_results['pairwise_results'][:10]:  # 限制前10对
                    p_value = result.get('p_value')
                    if p_value is None:
                        continue
                    
                    significance = "显著" if result.get('significant') else "不显著"
                    
                    posthoc_data.append([
                        result['group1'],
                        result['group2'],
                        f"{result.get('mean_diff', 'N/A'):.3f}" if result.get('mean_diff') is not None else 'N/A',
                        f"{p_value:.4f}",
                        significance
                    ])
                
                if posthoc_data:
                    posthoc_header = ['组1', '组2', '均值差', 'P 值', '显著性']
                    posthoc_table_data = [posthoc_header] + posthoc_data
                    
                    posthoc_table = Table(posthoc_table_data, colWidths=[0.8*inch, 0.8*inch, 1*inch, 1*inch, 0.8*inch])
                    posthoc_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    story.append(posthoc_table)
                    story.append(Spacer(1, 10))
    
    # 结论
    story.append(Paragraph("结论与建议", heading_style))
    
    conclusions = []
    for var in measure_vars[:3]:
        if assumption_results and anova_results:
            # 获取检验结果
            normal = None
            homogeneous = None
            anova_sig = None
            
            if 'normality' in assumption_results and var in assumption_results['normality'].get('conclusion', {}):
                normal = assumption_results['normality']['conclusion'][var].get('data_normal')
            
            if 'homogeneity' in assumption_results and var in assumption_results['homogeneity'].get('conclusion', {}):
                homogeneous = assumption_results['homogeneity']['conclusion'][var].get('homogeneous')
            
            if var in anova_results.get('by_variable', {}):
                anova_sig = anova_results['by_variable'][var].get('significant')
            
            # 生成结论
            conclusion = f"{var}: "
            if normal is None or homogeneous is None:
                conclusion += "数据质量需要检查。"
            elif normal and homogeneous:
                conclusion += "数据满足正态性和方差齐性假设。"
                if anova_sig:
                    conclusion += "方差分析结果显著，存在组间差异。"
                else:
                    conclusion += "方差分析结果不显著，无足够证据表明存在组间差异。"
            elif normal and not homogeneous:
                conclusion += "数据满足正态性但方差不齐。"
                if anova_sig:
                    conclusion += "Welch方差分析结果显著，存在组间差异。"
                else:
                    conclusion += "Welch方差分析结果不显著。"
            elif not normal and homogeneous:
                conclusion += "数据不满足正态性但方差齐性。"
                if anova_sig:
                    conclusion += "Kruskal-Wallis检验结果显著，存在组间差异。"
                else:
                    conclusion += "Kruskal-Wallis检验结果不显著。"
            else:
                conclusion += "数据不满足正态性且方差不齐。"
                if anova_sig:
                    conclusion += "Kruskal-Wallis检验结果显著，存在组间差异。"
                else:
                    conclusion += "Kruskal-Wallis检验结果不显著。"
            
            conclusions.append(conclusion)
    
    for conclusion in conclusions:
        story.append(Paragraph(conclusion, normal_style))
        story.append(Spacer(1, 5))
    
    # 页脚
    story.append(Spacer(1, 30))
    story.append(Paragraph("--- 报告结束 ---", 
                          ParagraphStyle('Footer', parent=normal_style, alignment=1, fontSize=10)))
    
    # 构建 PDF
    doc.build(story)
    
    # 获取字节数据
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def save_report_to_file(report_content: Union[str, bytes],
                       filename: str,
                       report_type: str = 'csv') -> str:
    """
    将报告保存到文件
    
    Parameters
    ----------
    report_content : Union[str, bytes]
        报告内容
    filename : str
        文件名
    report_type : str, optional
        报告类型，'csv' 或 'pdf'，默认 'csv'
    
    Returns
    -------
    str
        保存的文件路径
    """
    import os
    
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 添加扩展名
    if not filename.lower().endswith(f'.{report_type}'):
        filename = f'{filename}.{report_type}'
    
    filepath = os.path.join('output', filename)
    
    # 写入文件
    if report_type == 'csv' and isinstance(report_content, str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
    elif report_type == 'pdf' and isinstance(report_content, bytes):
        with open(filepath, 'wb') as f:
            f.write(report_content)
    else:
        raise ValueError(f"不支持的报告类型或内容格式: {report_type}")
    
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
    
    print("生成 CSV 报告测试")
    csv_report = generate_csv_report(test_data, 'group', ['value1'])
    print(f"CSV 报告长度: {len(csv_report)} 字符")
    
    if REPORTLAB_AVAILABLE:
        print("\n生成 PDF 报告测试")
        try:
            pdf_report = generate_pdf_report(test_data, 'group', ['value1'])
            print(f"PDF 报告大小: {len(pdf_report)} 字节")
        except Exception as e:
            print(f"PDF 报告生成失败: {e}")