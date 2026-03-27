"""
数据加载模块
处理文件上传、数据解析和验证
"""

import pandas as pd
import numpy as np
import io
import warnings
from typing import Union, Tuple, Optional

warnings.filterwarnings('ignore')

def load_data(uploaded_file) -> pd.DataFrame:
    """
    加载上传的文件（CSV 或 Excel）并返回 DataFrame
    
    Parameters
    ----------
    uploaded_file : streamlit.UploadedFile
        上传的文件对象
    
    Returns
    -------
    pd.DataFrame
        加载的数据框
    
    Raises
    ------
    ValueError
        如果文件格式不支持或数据加载失败
    """
    try:
        # 根据文件扩展名选择加载方式
        file_name = uploaded_file.name.lower()
        
        if file_name.endswith('.csv'):
            # 尝试自动检测分隔符
            content = uploaded_file.read().decode('utf-8')
            # 回退到文件开头
            uploaded_file.seek(0)
            
            # 尝试常见分隔符
            for sep in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(io.StringIO(content), sep=sep, engine='python')
                    if df.shape[1] > 1:
                        return df
                except:
                    continue
            
            # 如果都不成功，使用默认逗号
            df = pd.read_csv(uploaded_file)
            
        elif file_name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            raise ValueError(f"不支持的文件格式: {file_name}")
        
        # 基本数据清洗
        df = clean_data(df)
        
        return df
        
    except Exception as e:
        raise ValueError(f"数据加载失败: {e}")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    数据清洗：处理缺失值、去除全空列等
    
    Parameters
    ----------
    df : pd.DataFrame
        原始数据框
    
    Returns
    -------
    pd.DataFrame
        清洗后的数据框
    """
    # 创建副本避免修改原数据
    df_clean = df.copy()
    
    # 去除全为空的列
    df_clean = df_clean.dropna(axis=1, how='all')
    
    # 去除全为空的列名
    df_clean.columns = [str(col).strip() for col in df_clean.columns]
    
    # 去除重复的列名（保留第一个）
    seen = {}
    new_columns = []
    for col in df_clean.columns:
        if col not in seen:
            seen[col] = 1
            new_columns.append(col)
        else:
            seen[col] += 1
            new_columns.append(f"{col}_{seen[col]}")
    df_clean.columns = new_columns
    
    # 将 object 类型列尝试转换为数值类型
    for col in df_clean.select_dtypes(include=['object']).columns:
        try:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='ignore')
        except:
            pass
    
    return df_clean

def validate_data(df: pd.DataFrame, 
                  group_var: Optional[str] = None, 
                  measure_vars: Optional[list] = None) -> Tuple[bool, str]:
    """
    验证数据是否满足分析要求
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    group_var : str, optional
        分组变量名
    measure_vars : list, optional
        检测变量名列表
    
    Returns
    -------
    Tuple[bool, str]
        (是否有效, 错误消息)
    """
    # 检查数据框是否为空
    if df.empty:
        return False, "数据框为空"
    
    # 检查列名是否有效
    if df.columns.duplicated().any():
        return False, "存在重复的列名"
    
    # 如果提供了分组变量，检查其是否存在
    if group_var is not None:
        if group_var not in df.columns:
            return False, f"分组变量 '{group_var}' 不存在于数据中"
        
        # 检查分组变量是否至少有两个水平
        unique_groups = df[group_var].nunique()
        if unique_groups < 2:
            return False, f"分组变量 '{group_var}' 只有 {unique_groups} 个水平，至少需要 2 个水平"
    
    # 如果提供了检测变量，检查它们是否存在且为数值类型
    if measure_vars is not None:
        for var in measure_vars:
            if var not in df.columns:
                return False, f"检测变量 '{var}' 不存在于数据中"
            
            # 检查是否为数值类型
            if not pd.api.types.is_numeric_dtype(df[var]):
                return False, f"检测变量 '{var}' 不是数值类型"
            
            # 检查是否有足够的非缺失值
            non_missing = df[var].notna().sum()
            if non_missing < 3:
                return False, f"检测变量 '{var}' 的有效数据点太少（{non_missing} 个），至少需要 3 个"
    
    return True, "数据验证通过"

def get_column_types(df: pd.DataFrame) -> dict:
    """
    获取列的数据类型分类
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    
    Returns
    -------
    dict
        包含分类的字典：
        - 'numeric': 数值型列名列表
        - 'categorical': 类别型列名列表
        - 'datetime': 日期时间型列名列表
        - 'other': 其他类型列名列表
    """
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []
    other_cols = []
    
    for col in df.columns:
        dtype = df[col].dtype
        
        if pd.api.types.is_numeric_dtype(dtype):
            numeric_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            datetime_cols.append(col)
        elif pd.api.types.is_categorical_dtype(dtype) or df[col].nunique() < 20:
            categorical_cols.append(col)
        else:
            other_cols.append(col)
    
    return {
        'numeric': numeric_cols,
        'categorical': categorical_cols,
        'datetime': datetime_cols,
        'other': other_cols
    }

def get_data_info(df: pd.DataFrame) -> dict:
    """
    获取数据的基本信息
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框
    
    Returns
    -------
    dict
        包含数据信息的字典
    """
    info = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'missing_values': df.isnull().sum().to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
        'column_types': get_column_types(df)
    }
    
    return info

if __name__ == "__main__":
    # 模块测试
    import sys
    sys.path.append('..')
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'group': ['A', 'A', 'B', 'B', 'C', 'C'],
        'value1': [1.2, 2.3, 3.4, 4.5, 5.6, 6.7],
        'value2': [10, 20, 30, 40, 50, 60]
    })
    
    print("列类型:", get_column_types(test_data))
    print("数据信息:", get_data_info(test_data))
    
    valid, msg = validate_data(test_data, 'group', ['value1', 'value2'])
    print(f"验证结果: {valid}, 消息: {msg}")