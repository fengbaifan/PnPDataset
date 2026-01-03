# Wikidata 知识图谱数据提取工具开发计划

我将为您开发一个健壮的 Python 脚本，用于根据 `01-Merged_Dataset.csv` 中的 QID 从 Wikidata 提取详细的知识图谱数据。

## 1. 项目结构
我们将创建以下文件：
- `extract_wikidata.py`: 主程序脚本，包含所有核心逻辑。
- `requirements.txt`: 依赖库清单。
- `README.md`: 操作手册。
- `TECHNICAL_DOCS.md`: 技术文档。
- `logs/`: 存放日志文件的目录。
- `output/`: 存放结果文件和断点信息的目录。

## 2. 核心模块设计 (`extract_wikidata.py`)

脚本将采用面向对象设计，包含以下类：

### A. `Config` & `Utils`
- 管理配置（最大重试次数、超时时间、User-Agent 列表）。
- 提供随机等待和日志记录功能。

### B. `DataLoader`
- 读取 `01-Merged_Dataset.csv`。
- 验证字段（Refined_Formal_Name, Original-QID）。
- 支持 `--test` 模式（仅读取前 N 条数据）。

### C. `CheckpointManager`
- 管理断点续传。
- 记录已完成的 QID 到 `checkpoint.json`。
- 启动时加载断点，过滤已处理的 QID。

### D. `SPARQLQueryBuilder`
- 构建 SPARQL 查询。
- **策略**: 使用 `VALUES` 子句批量查询 QID（例如每批 50 个），获取其所有直接属性（P-values）和对应的标签。
- 查询内容包括：属性 ID、属性值、属性值标签（优先英文+中文）、限定词（如有必要）。

### E. `WikidataFetcher`
- 封装 `requests` 库。
- 实现 User-Agent 轮换。
- 实现指数退避算法（Exponential Backoff）处理 429/5xx 错误。
- 处理分页（如果单次批量查询结果过多）。

### F. `DataProcessor`
- 清洗数据：日期标准化 (ISO 8601)。
- 多语言处理：保留所有语言标签，提取优先语言。
- 格式化：将 SPARQL 结果转换为以实体为中心的 JSON 对象。
- 字段合并：将 CSV 中的原始字段 (`Refined_Formal_Name`, `Match_Method`) 合并到输出中。

### G. `JSONLWriter`
- 实时写入 `sponsor_painter_kg.jsonl`。
- 确保 UTF-8 编码。
- 写入文件头/元数据（如果 JSONL 格式允许，通常作为第一行或单独的元数据文件，这里我们将每行作为一个独立的数据记录，元数据可作为第一行特殊记录或单独文件）。

## 3. 执行步骤

1.  **环境准备**: 检查并安装 `requests` 库。
2.  **代码实现**: 编写完整的 Python 脚本。
3.  **小规模测试**: 使用前 5-10 条数据运行脚本，验证查询逻辑、数据格式和错误处理。
4.  **文档编写**: 生成操作手册和技术文档。

## 4. 输出示例
```json
{
  "id": "Q1392936",
  "dataset_info": {
    "Refined_Formal_Name": "A Dance to the Music of Time (Poussin)",
    "Match_Method": "..."
  },
  "labels": {"en": "A Dance to the Music of Time", "zh": "..."},
  "properties": {
    "P31": [{"value": "Q3305213", "label": "painting"}],
    "P170": [{"value": "Q42187", "label": "Nicolas Poussin"}]
  },
  "metadata": {"extracted_at": "2023-10-27T10:00:00Z"}
}
```

请确认是否开始执行此计划？