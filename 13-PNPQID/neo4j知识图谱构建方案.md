## 一、总体目标与设计原则

### 1.1 目标

构建一个从 Wikidata 原始实体 JSON 出发，经过语义保持与结构重构，最终形成**可读、可分析、可扩展**的 Neo4j 知识图谱系统，用于复杂网络分析与艺术史研究。方案力求完整具体、工程可实施、科研可复现、论文可直接描述。

### 1.2 核心原则


| 原则     | 说明                                                  |
| -------- | ----------------------------------------------------- |
| 数据保真 | 使用 Wikidata 原始实体 JSON，避免 SPARQL 信息丢失     |
| 语义可读 | 实体 label 与关系 type 均语义化                       |
| 分析友好 | 消除 statement 中间节点，将 qualifiers 转换为关系属性 |
| 可扩展   | API ↔ dump 无缝切换                                  |
| 可复现   | 流水线模块化、可重复执行                              |

## 二、系统架构

```
QID Seeds
   ↓
Wikidata Entity API / Dump
   ↓
Raw Entity Store
   ↓
Claim Parser
   ↓
Canonical Statement Model
   ↓
Semantic Graph Mapping Engine
   ↓
Neo4j Knowledge Graph
   ↓
Analysis & Visualization
```

## 三、数据获取层（Acquisition）

### 当前阶段：在线 API

```
https://www.wikidata.org/wiki/Special:EntityData/Q1|Q2|Q3.json
```

### 后期扩展：Dump

* `wikidata-YYYYMMDD-all.json.gz`

**接口统一返回原始实体 JSON，结构一致。**

## 四、数据解析与标准化

### 4.1 解析实体

抽取：

* labels / descriptions
* claims → statements
* 每个 statement 的：
  * property (Pxx)
  * object
  * qualifiers
  * rank
  * references

### 4.2 Canonical Statement Model

```
Statement(
    subject, property, object,
    qualifiers, rank, references
)
```

该模型是系统语义核心，所有来源统一归一到此结构。

## 五、语义化图谱映射设计

### 5.1 实体标签体系（基于 P31 instance of）


| Wikidata | Neo4j Label  |
| -------- | ------------ |
| Q5       | Person       |
| Q838948  | Artwork      |
| Q43229   | Organization |
| Q215627  | Location     |
| ...      | ...          |

多标签机制支持复合身份。

### 5.2 关系语义映射


| Wikidata Property | Neo4j Relation  |
| ----------------- | --------------- |
| P39               | HELD\_OFFICE    |
| P106              | HAS\_OCCUPATION |
| P69               | EDUCATED\_AT    |
| P463              | MEMBER\_OF      |
| P1412             | SPEAKS          |
| ...               | ...             |

未知属性 → `RELATED_TO`（保留原始 Pxx 作为属性）。

### 5.3 标签映射获取策略

**重要说明：** 标签映射不应硬编码，而应从 Wikidata API 动态获取。


| 标签类型                       | 来源         | 缓存策略                                          |
| ------------------------------ | ------------ | ------------------------------------------------- |
| **实体类型** (P31 instance of) | Wikidata API | 按需获取，缓存至`data/cache/entity_labels.json`   |
| **属性标签** (Pxxx)            | Wikidata API | 按需获取，缓存至`data/cache/property_labels.json` |
| **值标签** (Qxxx)              | Wikidata API | 可选获取，用于关联实体名称补全                    |

缓存格式示例 (`property_labels.json`):

```json
{
  "P31": "instance of",
  "P170": "creator",
  "P195": "collection",
  ...
}
```

动态获取流程：

```
1. 检查缓存是否存在对应标签
2. 如不存在，调用 Wikidata API:
   https://www.wikidata.org/w/api.php?action=wbgetentities&ids=P31|P170|...&props=labels&languages=en
3. 解析返回结果，提取英文标签
4. 更新缓存
5. 返回标签
```

## 六、Qualifier 转换策略

Wikidata qualifiers → Neo4j 关系属性：

```
(:Person)-[:HELD_OFFICE {
    start_time,
    end_time,
    rank,
    sources
}]->(:Office)
```

* qualifiers 结构扁平化
* rank / references 保留

## 七、Neo4j 写入规范（核心模板）

```cypher
MERGE (s:Entity {qid:$s})
SET s.name=$s_name, s.type=$s_type

MERGE (o:Entity {qid:$o})
SET o.name=$o_name, o.type=$o_type

MERGE (s)-[r:HELD_OFFICE]->(o)
SET r += $qualifiers,
    r.rank = $rank,
    r.source = "Wikidata"
```

## 八、工程模块划分

```
 project/
├─ data/                      # 实体清单
├─ output/                    # 结果数据可直接导入到图数据库中
├─ acquisition/
│   ├─ wikidata_api.py        # 在线获取
│   └─ wikidata_dump.py       # 未来扩展
│
├─ parser/
│   ├─ entity_parser.py       # claims → statements
│   └─ qualifier_parser.py
│
├─ model/
│   └─ statement.py           # Canonical Statement
│
├─ graph/
│   ├─ neo4j_schema.py
│   └─ neo4j_writer.py
│
└─ pipeline.py

```

支持 API / dump 切换。

## 九、分析与可视化

* Neo4j GDS：网络分析
* NetworkX：算法验证
* yFiles / Cytoscape：交互可视化
* Jupyter：实验环境

## 十、质量控制与学术合规


| 维度       | 措施                                      |
| ---------- | ----------------------------------------- |
| 信息完整性 | 原始 JSON 数据源                          |
| 可复现性   | 固定 QID seeds / dump 版本 + 缓存版本记录 |
| 可解释性   | 语义化标签与关系                          |
| 可扩展性   | Schema + 映射表驱动                       |
| 标签质量   | 从 Wikidata API 动态获取，按需缓存        |

## 十一、方法描述

> 构建了一套面向 Wikidata 原始实体数据的知识图谱转换框架，通过对原始 JSON 数据的解析与语义结构重构，将 Wikidata 的 statement–qualifier 模型映射为属性图模型，并进一步构建语义化、分析友好的 Neo4j 知识图谱。
