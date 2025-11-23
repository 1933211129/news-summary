# 新闻情报自动化抽取系统

基于 DSPy 框架和大型语言模型的新闻情报智能抽取系统，能够自动对新闻进行分类并提取结构化信息。

## 项目简介

本项目是一个新闻情报自动化处理系统，主要功能包括：

- **新闻分类**：自动判断新闻类型（研究前沿、产业应用、政策计划、其他）
- **信息抽取**：从新闻中提取标题、简短摘要和详细摘要
- **智能过滤**：仅处理目标类别的新闻（研究前沿、产业应用、政策计划），自动过滤其他类别
- **批量处理**：支持从 Excel/CSV 文件批量读取并处理新闻数据
- **结果输出**：以 JSON Lines（.jsonl）格式输出结构化结果，每条记录生成后立即写入磁盘

## 技术架构

### 核心技术栈

- **DSPy**：用于构建和优化 LLM 管道
- **LiteLLM**：作为 LLM 调用桥接层
- **DeepSeek V3.2**：通过 ChatAnywhere API 提供语言模型能力
- **Pandas**：处理 Excel/CSV 数据文件

### 核心组件

1. **NewsClassifier**：新闻分类器，使用 Chain-of-Thought 推理判断新闻类别
2. **IntelligenceExtractor**：情报抽取器，一次性生成标题和两层摘要
3. **NewsPipeline**：完整处理管道，串联分类与抽取流程

## 项目结构

```
extract/
├── main.py              # 生产环境入口脚本
├── model.py             # DSPy 模型定义（分类器、抽取器、管道）
├── config.py            # LLM 配置与实例化
├── utils.py             # 数据读取与结果写入工具
├── optimize.py          # Pipeline 优化脚本（BootstrapFewShot）
├── example.json         # 训练示例数据
├── best_pipeline.json   # 优化后的 Pipeline 配置（自动生成）
├── test_data.xls        # 测试数据文件
└── result_output.jsonl  # 输出结果文件（自动生成）
```

## 安装与配置

### 环境要求

- Python 3.12+
- Conda 环境（推荐）

### 安装步骤

1. **创建并激活 Conda 环境**

```bash
conda create -n ser python=3.12
conda activate ser
```

2. **安装依赖包**

```bash
pip install dspy-ai litellm pandas openpyxl
```

3. **配置 API Key**

编辑 `config.py` 文件，设置 ChatAnywhere API Key，或通过环境变量设置：

```bash
export CHATANYWHERE_API_KEY="your-api-key-here"
```

## 使用方法

### 1. 优化 Pipeline（可选）

首次使用或需要重新优化模型时，运行优化脚本：

```bash
python optimize.py
```

该脚本会：
- 从 `example.json` 加载训练示例
- 使用 BootstrapFewShot 优化 Pipeline
- 将优化后的配置保存到 `best_pipeline.json`

### 2. 处理新闻数据

使用主程序处理新闻文件：

```bash
python main.py --data-file test_data.xls --output-file result_output.jsonl
```

**参数说明**：
- `--data-file`：待处理的 Excel/CSV 文件路径（默认：`test_data.xls`）
- `--output-file`：结果输出 JSONL 文件路径（默认：`result_output.jsonl`，流式逐条写入）

### 3. 数据文件格式要求

输入文件（Excel/CSV）应包含以下列（支持多种列名别名）：

- **原文内容**：必需字段
  - 支持的列名：`原文内容`、`内容`、`新闻内容`、`正文`
- **发布时间**：可选字段
  - 支持的列名：`资源发布时间`、`发布时间`、`时间`
- **来源机构**：可选字段
  - 支持的列名：`资源来源机构`、`来源`、`机构`
- **URL**：可选字段
  - 支持的列名：`资源URL`、`资源url`、`链接`、`url`

## 输出格式

处理结果以 JSON Lines（每行一条 JSON 记录）形式输出，文件中的每一行都包含以下字段：

```json
{"category":"研究前沿","title":"新闻标题","short_summary":"本期看点，单段中文简介","detailed_summary":"本期概要，使用(1)(2)(3)编号的中文分点描述","raw_content":"原始新闻内容","release_time":"2024-08-29","source_institution":"来源机构","url":"https://example.com"}
{"category":"产业应用","title":"另一条新闻","short_summary":"第二条的简短摘要","detailed_summary":"第二条的详细摘要","raw_content":"原始新闻内容...","release_time":"2024-08-30","source_institution":"来源机构","url":"https://example.com/2"}
```

**字段说明**：
- `category`：新闻类别（研究前沿、产业应用、政策计划）
- `title`：提取的标题（不超过30个汉字）
- `short_summary`：简短摘要（不超过40个汉字，单段描述）
- `detailed_summary`：详细摘要（分点描述，使用编号格式）
- `raw_content`：原始新闻内容
- `release_time`：发布时间（如果输入文件包含）
- `source_institution`：来源机构（如果输入文件包含）
- `url`：新闻链接（如果输入文件包含）

**注意**：只有属于目标类别（研究前沿、产业应用、政策计划）的新闻才会被输出，其他类别的新闻会被自动过滤。写出过程为流式追加，程序中断时也能保留已完成的记录。

## 配置说明

### LLM 配置

在 `config.py` 中可以调整以下参数：

- `base_url`：API 服务地址
- `model`：使用的模型名称（当前：`deepseek-v3-2-exp`）
- `max_tokens`：最大生成 token 数（默认：1024）
- `temperature`：温度参数（默认：0.3）

### Pipeline 优化参数

在 `optimize.py` 中可以调整优化参数：

- `max_bootstrapped_demos`：最大引导示例数（默认：4）
- `max_labeled_demos`：最大标注示例数（默认：训练集大小）
- `metric`：评估指标函数

## 工作流程

1. **数据读取**：从 Excel/CSV 文件读取新闻数据，自动识别列名
2. **分类判断**：使用 NewsClassifier 对每条新闻进行分类
3. **类别过滤**：仅处理目标类别的新闻，其他类别直接跳过
4. **信息抽取**：对目标类别新闻，使用 IntelligenceExtractor 提取标题和摘要
5. **结果输出**：将结构化结果按 JSONL 流式写入文件，每条记录完成后立刻 flush

## 示例数据

项目包含示例数据文件 `example.json`，格式如下：

```json
[
  {
    "content": "新闻原文内容...",
    "category": "产业应用",
    "title": "新闻标题",
    "short_summary": "简短摘要",
    "detailed_summary": "详细摘要",
    "release_time": "2024-08-29",
    "source_institution": "来源机构",
    "url": "https://example.com"
  }
]
```

## 注意事项

1. **API 费用**：每次处理都会调用 LLM API，请注意 API 使用成本
2. **处理速度**：由于需要调用 LLM，批量处理可能需要较长时间
3. **数据质量**：输入数据的质量直接影响抽取结果的准确性
4. **模型优化**：建议定期使用新的示例数据重新优化 Pipeline 以提升效果

## 开发说明

### 添加新的训练示例

编辑 `example.json` 文件，添加新的示例数据，然后重新运行 `optimize.py` 进行优化。

### 修改目标类别

在 `model.py` 中修改 `TARGET_CATEGORIES` 列表：

```python
TARGET_CATEGORIES = ["研究前沿", "产业应用", "政策计划"]
```

### 自定义列名映射

在 `utils.py` 中修改 `DEFAULT_COLUMN_ALIASES` 字典以支持新的列名。

## 许可证

本项目仅供内部使用。

## 更新日志

- 项目正在稳步执行中，功能持续优化完善。

