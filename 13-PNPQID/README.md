# Wikidata 知识图谱提取工具 (JSON-LD)

本工具用于从 Wikidata 批量提取知识图谱数据，直接输出为 **JSON-LD** 格式，包含完整的实体标签和属性（关系）标签。

## 1. 核心特性

- **JSON-LD 输出**: 符合 Linked Data 标准，支持直接导入图数据库或可视化工具。
- **全标签支持**: 
  - 实体 (Subject) 标签
  - 属性 (Predicate/Relation) 标签
  - 值 (Object) 标签
- **智能提取**: 自动合并 CSV 中的原始元数据。
- **鲁棒性**: 内置重试机制、反封禁策略（随机 User-Agent 和延迟）。

## 2. 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行测试
提取前 5 条数据，检查输出格式：
```bash
python extract_kg_jsonld.py --test
```
结果将生成在 `output/sponsor_painter_kg.jsonld`。

### 执行完整提取
```bash
python extract_kg_jsonld.py
```
> **注意**: 完整运行可能需要较长时间（取决于数据量），脚本会实时打印进度。

## 3. 输出格式说明

输出文件 `output/sponsor_painter_kg.jsonld` 是一个标准的 JSON-LD 文档。

### 结构示例
```json
{
  "@context": {
    "wd": "http://www.wikidata.org/entity/",
    "wdt": "http://www.wikidata.org/prop/direct/",
    ...
  },
  "@graph": [
    {
      "@id": "wd:Q709195",
      "@type": "wd:Item",
      "rdfs:label": "Arthur E. Popham",
      "wdt:P19": {
        "@id": "wd:Q43382",
        "rdfs:label": "Plymouth"
      }
    },
    {
      "@id": "wdt:P19",
      "@type": "rdf:Property",
      "rdfs:label": "place of birth"
    }
  ]
}
```
- **实体节点**: 包含 `@id` (QID), `rdfs:label`, 以及所有属性。
- **属性节点**: 单独列出所有用到的属性（如 `wdt:P19`）及其标签，方便可视化工具显示关系名称。

## 4. 配置
可在 `extract_kg_jsonld.py` 顶部的 `Config` 类中修改：
- `BATCH_SIZE`: 批处理大小（默认 50）
- `MIN_DELAY` / `MAX_DELAY`: 请求间隔
- `TIMEOUT`: 超时时间
