# 技术文档：Wikidata 知识图谱提取器

## 1. 架构设计

本系统采用模块化设计，主要包含以下组件：

### 1.1 核心类
- **`Config`**: 集中管理配置参数（API 端点、超时、重试策略等）。
- **`DataLoader`**: 负责读取 `01-Merged_Dataset.csv`，解析 QID，并支持数据切片。
- **`CheckpointManager`**: 实现断点续传功能，通过 JSON 文件持久化已处理的 QID 集合。
- **`SPARQLQueryBuilder`**: 动态构建 SPARQL 查询语句，使用 `VALUES` 子句实现批量查询。
- **`WikidataFetcher`**: 封装 HTTP 请求，实现 User-Agent 轮换、错误处理和指数退避算法。
- **`DataProcessor`**: 处理 SPARQL 返回的原始 JSON 结果，清洗数据、合并字段并转换为目标 schema。
- **`Main`**: 协调各模块工作流：加载 -> 过滤(断点) -> 批处理 -> 获取 -> 处理 -> 写入 -> 更新断点。

## 2. 数据模型

输出文件为 JSON Lines 格式，每行包含一个完整的实体对象。

### JSON 结构示例
```json
{
  "id": "Q1392936",
  "dataset_info": {
    "Refined_Formal_Name": "A Dance to the Music of Time (Poussin)",
    "Original-QID": "Q1392936"
  },
  "primary_label": "A Dance to the Music of Time",
  "labels": {
    "en": "A Dance to the Music of Time",
    "zh": "随时间之乐起舞"
  },
  "descriptions": {
    "en": "series of romans a clef by Anthony Powell"
  },
  "properties": {
    "P31": [
      {
        "value": "http://www.wikidata.org/entity/Q277759",
        "type": "uri",
        "label": "book series"
      }
    ],
    "P577": [
      {
        "value": "1951-01-01T00:00:00Z",
        "type": "literal"
      }
    ]
  },
  "metadata": {
    "extracted_at": "2026-01-03T15:10:21Z",
    "source": "Wikidata"
  }
}
```

## 3. 异常处理流程

1. **网络异常 (Network Error)**: 捕获 `requests.exceptions.RequestException`，记录错误日志，并按策略重试。
2. **限流 (HTTP 429)**: 触发指数退避（Exponential Backoff），等待时间随重试次数增加（例如 5s, 10s, 20s）。
3. **数据解析错误 (JSON Decode Error)**: 记录错误并跳过当前批次，避免程序崩溃。
4. **缺失数据**: 如果某个 QID 在 Wikidata 中已被删除或无数据，程序会记录警告但继续执行。

## 4. 性能优化

- **批量查询**: 使用 SPARQL `VALUES` 子句一次查询 50 个实体，显著减少 HTTP 请求次数。
- **并行处理**: 目前采用单线程同步模式以严格遵守 Wikidata API 速率限制（Rate Limit）。
- **内存管理**: 采用流式写入（JSONL），无需将所有结果保存在内存中，适合处理大规模数据。

## 5. 扩展建议

- **代理支持**: 可在 `Config` 中添加 `PROXIES` 配置，并在 `WikidataFetcher` 中传递给 `requests.Session`。
- **异步 IO**: 如果需要更高吞吐量（需注意 API 限制），可改用 `aiohttp` 实现异步并发请求。
