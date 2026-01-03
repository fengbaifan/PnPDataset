# Wikidata JSON-LD 知识图谱构建计划

根据您的要求，我将重新设计脚本以直接输出 **JSON-LD** 格式的知识图谱，并确保包含**实体**和**关系**的标签，使其具备良好的可读性和展示性。

## 1. 目标与格式
- **输出格式**: JSON-LD (`.jsonld`)。
- **核心要求**:
  - 符合 Linked Data 标准。
  - 包含 CSV 中的原始 QID 和名称。
  - **显式包含标签**: 不仅包含 `QID`，还直接在数据中包含实体标签（Subject & Object）和属性标签（Predicate）。

## 2. 核心架构设计

### A. 数据模型设计 (JSON-LD)
我们将构建一个包含 `@context` 和 `@graph` 的单一 JSON 对象。

**结构示例**:
```json
{
  "@context": {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "wd": "http://www.wikidata.org/entity/",
    "wdt": "http://www.wikidata.org/prop/direct/",
    "schema": "http://schema.org/",
    "ex": "http://example.org/ontology/",
    "dataset_name": "ex:originalName"
  },
  "@graph": [
    {
      "@id": "wd:Q1392936",
      "@type": "wd:Q3305213", 
      "rdfs:label": {"en": "A Dance to the Music of Time", "zh": "..."},
      "dataset_name": "A Dance to the Music of Time (Poussin)",
      "wdt:P577": { 
          "@value": "1951-01-01T00:00:00Z", 
          "@type": "xsd:dateTime" 
      },
      "wdt:P50": {
          "@id": "wd:Q573813",
          "rdfs:label": "Anthony Powell"
      }
    },
    {
      "@id": "wdt:P50",
      "rdfs:label": {"en": "author", "zh": "作者"},
      "@type": "rdf:Property"
    }
  ]
}
```

### B. 脚本重构 (`extract_kg_jsonld.py`)

1.  **两阶段查询策略**:
    *   **阶段一 (Entity Data)**: 批量查询目标 QID 的所有直接声明 (`wdt:?p ?o`)。
        *   同时获取 `?itemLabel` (主体标签) 和 `?oLabel` (客体值标签)。
        *   *优化*: 在构建 JSON 结构时，将 `?oLabel` 直接嵌入到对象节点中，满足"显示实体标签"的需求。
    *   **阶段二 (Property Metadata)**: 收集阶段一中出现的所有属性 ID (如 `P31`, `P50`)。
        *   单独执行一次 SPARQL 查询，获取这些属性的标签 (English/Chinese)。
        *   将这些属性定义添加到 `@graph` 中，满足"显示关系标签"的需求。

2.  **处理逻辑**:
    *   **Config**: 保留之前的重试、反封禁配置。
    *   **Buffer**: 由于需要收集所有属性后才能生成完整的图，我们将数据暂存在内存中（考虑到数据集约 1000 条，内存足以容纳），最后一次性写入文件。
    *   **Context 生成**: 自动生成标准 Wikidata Prefix。

## 3. 执行步骤

1.  **创建新脚本**: `extract_kg_jsonld.py`。
2.  **实现 SPARQL 查询生成器**:
    *   Query 1: `VALUES ?item { ... } ?item ?p ?o . ...` (获取数据)
    *   Query 2: `VALUES ?prop { ... } ?prop rdfs:label ?label ...` (获取属性元数据)
3.  **实现 JSON-LD 构建器**: 组装节点和上下文。
4.  **测试**: 使用 `--test` 参数运行前 5-10 条数据，检查生成的 JSON-LD 结构是否正确。

请确认是否采用此 JSON-LD 方案进行开发？