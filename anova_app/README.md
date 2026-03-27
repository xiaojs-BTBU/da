# 自动化方差分析 (ANOVA) 与可视化工具

基于 Streamlit 的交互式方差分析工具，支持单因素、多因素 ANOVA、Welch's ANOVA、Kruskal-Wallis 检验，并提供丰富的统计可视化与报告导出功能。

## 功能特性

### 数据导入
- 支持 CSV、Excel 文件上传（.csv, .xls, .xlsx）
- 自动检测列类型和缺失值
- 数据预览与清洗

### 变量选择
- 分组变量（自变量）下拉选择
- 检测变量（因变量）多选
- 多因素 ANOVA 支持（可选）

### 统计分析
- **描述性统计**：均值、标准差、中位数、置信区间等
- **前提假设检验**：
  - 正态性检验（Shapiro-Wilk）
  - 方差齐性检验（Levene）
- **ANOVA 模型**：
  - 标准单因素 ANOVA（满足正态性且方差齐性）
  - Welch's ANOVA（方差不齐）
  - Kruskal-Wallis 检验（非正态数据）
  - 双因素 ANOVA（交互作用分析）
- **事后两两比较**：
  - Tukey HSD（方差齐）
  - Games-Howell（方差不齐）
  - Dunn's test（非参数）

### 可视化
- **箱线图**：显示数据分布和异常值
- **小提琴图**：结合核密度估计和箱线图
- **带散点的柱状图**：均值 ± 标准差/标准误，叠加原始数据点
- **显著性标注**：自动在图表中添加统计显著性标记（*p<0.05, **p<0.01, ***p<0.001）
- **交互式图表**：使用 Plotly 支持缩放、悬停查看数值

### 报告导出
- **CSV 报告**：完整统计结果表格
- **PDF 报告**：格式化专业报告，包含图表和结论

### 错误处理与用户反馈
- 友好的错误提示和验证信息
- 数据质量检查与警告
- 进度指示和状态反馈

## 安装部署

### 环境要求
- Python 3.8+
- 推荐使用虚拟环境（venv 或 conda）

### 快速开始

1. **克隆或下载项目**
   ```bash
   git clone <repository-url>
   cd anova_app
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行应用**
   ```bash
   streamlit run app.py
   ```

4. **在浏览器中打开**
   - 应用默认运行在 `http://localhost:8501`
   - 按照界面提示上传数据、选择变量、执行分析

### 详细安装步骤

#### 方法一：使用 pip 安装
```bash
# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 方法二：使用 conda 安装
```bash
# 创建 conda 环境
conda create -n anova_env python=3.9
conda activate anova_env

# 安装核心依赖
conda install -c conda-forge pandas numpy scipy statsmodels matplotlib seaborn

# 安装其他依赖
pip install streamlit pingouin statannotations plotly altair reportlab openpyxl xlrd python-docx Pillow
```

#### 方法三：Docker 部署
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

构建并运行：
```bash
docker build -t anova-app .
docker run -p 8501:8501 anova-app
```

## 使用指南

### 1. 数据准备
- 数据文件应为表格格式，每列代表一个变量，每行代表一个观测
- 确保分组变量为类别型（字符串或整数），检测变量为数值型
- 缺失值会自动处理，但建议提前清理

### 2. 操作流程
1. **上传数据**：在侧边栏点击"上传数据文件"，选择 CSV 或 Excel 文件
2. **选择变量**：
   - 分组变量：选择用于分组的类别变量
   - 检测变量：选择一个或多个数值变量进行分析
3. **执行分析**：点击"方差分析"按钮，系统将自动：
   - 计算描述性统计
   - 执行前提假设检验
   - 根据检验结果选择适当的 ANOVA 方法
   - 如果结果显著，执行事后两两比较
4. **查看结果**：
   - 上方区域显示统计结果表格
   - 下方区域显示可视化图表
5. **生成图表**：点击相应按钮生成箱线图、小提琴图或柱状图
6. **导出报告**：点击 CSV 或 PDF 按钮下载完整报告

### 3. 结果解读

#### 前提假设检验
- **正态性检验**：p > 0.05 表示数据服从正态分布
- **方差齐性检验**：p > 0.05 表示各组方差相等

#### ANOVA 结果
- **F 值/H 值**：检验统计量，值越大表示组间差异越大
- **P 值**：显著性水平，p < 0.05 表示存在显著差异
- **效应量**（η²/ε²）：表示差异的大小（小: <0.01, 中: 0.01-0.06, 大: >0.14）

#### 事后比较
- **均值差**：两组均值之间的差异
- **显著性**：标记为"显著"的组对存在统计显著差异
- **置信区间**：95% 置信区间不包含 0 表示差异显著

### 4. 高级功能

#### 多因素 ANOVA
在变量选择界面，可以选择多个分组变量进行多因素方差分析，分析主效应和交互作用。

#### 交互式可视化
勾选"启用交互式图表"后，图表将支持：
- 鼠标悬停查看数值
- 缩放和平移
- 图表下载（PNG 格式）

#### 自定义分析参数
在代码中可以调整的参数：
- 显著性水平（默认 α=0.05）
- 置信区间（默认 95%）
- 多重比较校正方法（默认 Bonferroni）

## 项目结构

```
anova_app/
├── app.py                    # 主 Streamlit 应用
├── requirements.txt          # Python 依赖包列表
├── README.md                # 项目文档
├── modules/                 # 核心模块
│   ├── data_loader.py       # 数据加载与清洗
│   ├── variable_selector.py # 变量选择界面
│   ├── stats_calculator.py  # 描述性统计与假设检验
│   ├── anova_executor.py    # ANOVA 核心算法
│   ├── posthoc.py          # 事后检验模块
│   ├── visualizer.py       # 静态可视化
│   ├── interactive_visualizer.py # 交互式可视化
│   ├── report_generator.py # 报告生成
│   └── utils.py            # 工具函数与错误处理
├── static/                  # 静态资源
├── templates/               # 报告模板
├── output/                  # 输出文件目录
└── tests/                   # 测试文件
```

## 模块说明

### data_loader.py
- 文件上传与解析
- 数据清洗与验证
- 列类型自动识别

### variable_selector.py
- Streamlit 小部件创建
- 变量分类与推荐
- 输入验证

### stats_calculator.py
- 描述性统计计算
- 正态性检验（Shapiro-Wilk, Kolmogorov-Smirnov）
- 方差齐性检验（Levene, Bartlett）

### anova_executor.py
- 标准单因素 ANOVA
- Welch's ANOVA
- Kruskal-Wallis H 检验
- 双因素 ANOVA

### posthoc.py
- Tukey's HSD
- Games-Howell
- Dunn's test
- 多重比较校正

### visualizer.py
- Matplotlib/Seaborn 图表生成
- 显著性标注集成
- 学术风格图表配置

### interactive_visualizer.py
- Plotly 交互式图表
- Altair 可视化支持
- 图表交互功能

### report_generator.py
- CSV 报告生成
- PDF 报告生成（使用 ReportLab）
- 报告模板管理

### utils.py
- 错误处理装饰器
- 用户反馈函数
- 会话状态管理

## 配置与自定义

### 修改默认参数
在 `app.py` 中可以修改：
```python
# 显著性水平
ALPHA = 0.05

# 图表尺寸
FIG_SIZE = (10, 6)

# 调色板
PALETTE = "Set2"
```

### 添加新功能
1. **新的统计方法**：在 `anova_executor.py` 中添加函数
2. **新的可视化**：在 `visualizer.py` 中添加函数
3. **新的报告格式**：在 `report_generator.py` 中添加函数

### 国际化支持
应用支持中文显示，如需其他语言：
1. 修改 `visualizer.py` 中的 `set_chinese_font()` 函数
2. 更新界面文本为对应语言

## 常见问题

### Q1: 上传文件失败
- 检查文件格式是否支持（CSV, Excel）
- 检查文件大小是否超过限制（默认 200MB）
- 检查文件编码（推荐 UTF-8）

### Q2: 分析结果不显示
- 确保选择了分组变量和检测变量
- 检查数据中是否有足够的观测值（每组至少 2 个）
- 查看控制台错误信息

### Q3: 图表显示异常
- 确保安装了所有依赖包
- 检查 matplotlib 字体配置
- 尝试重启应用

### Q4: 报告生成失败
- 确保安装了 reportlab（PDF 报告）
- 检查输出目录权限
- 查看磁盘空间

## 性能优化

### 大数据集处理
- 使用数据采样（侧边栏选项）
- 关闭交互式图表（减少内存使用）
- 分批处理多个检测变量

### 内存管理
- 及时清理 session state
- 使用 `gc.collect()` 手动垃圾回收
- 避免在内存中保存大型图表对象

## 扩展开发

### 添加新的统计检验
1. 在 `stats_calculator.py` 中添加检验函数
2. 在 `anova_executor.py` 中集成检验选择逻辑
3. 在 `app.py` 中添加对应的界面元素

### 集成机器学习功能
- 聚类分析用于自动分组
- 特征重要性排序
- 预测模型构建

### 云端部署
- Streamlit Sharing
- Heroku
- AWS EC2
- Docker + Kubernetes

## 版本历史

### v1.0.0 (2026-03-27)
- 初始版本发布
- 基础 ANOVA 功能
- 三种可视化图表
- CSV/PDF 报告导出

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

- 项目仓库：<repository-url>
- 问题反馈：<issues-url>
- 作者：Streamlit ANOVA 工具开发团队

## 致谢

- Streamlit 团队提供了优秀的前端框架
- SciPy、Statsmodels、Pingouin 等统计库
- Matplotlib、Seaborn、Plotly 等可视化库
- 所有贡献者和用户

---

**开始使用**：运行 `streamlit run app.py` 体验强大的方差分析工具！