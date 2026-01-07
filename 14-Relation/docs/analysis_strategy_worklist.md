# 02-worklist 数据分析与三元组提取策略

## 1. 数据源概述
- **文件**: `02-worklist/01-Worklist-Plates-Matched-Original.csv`
- **主要字段**:
    - `Artist` (艺术家名称), `Artist_QID` (艺术家 Wikidata ID)
    - `Title_Description` (作品标题/描述), `Title_QID` (作品 Wikidata ID)
    - `Location` (收藏地/地点), `Location_QID` (地点 Wikidata ID)
- **数据特征**: 数据为半结构化表格。虽然有明确的列定义，但 `Title_Description` 包含自然语言描述，蕴含潜在的语义关系。

## 2. 知识图谱构建目标
目标是从表格中提取实体（Entities）和关系（Relations），构建三元组（Triples）。

### 预定义本体（Ontology）
建议采用以下核心关系：
1.  **创作关系** (`created_by` / `creator`): 连接 **作品** 与 **艺术家**。
2.  **收藏关系** (`located_at` / `collection`): 连接 **作品** 与 **地点**。
3.  **描绘关系** (`depicts` / `subject`): 连接 **作品** 与 **画中内容（人物/地点/寓意）**。

## 3. 提取策略

### 3.1 结构化提取（基于列映射）
这部分利用现有的表格结构直接提取，准确率高。

*   **规则 A (作品-艺术家)**:
    *   Subject: `Title_Description` (若有 Title_QID 则优先使用 ID)
    *   Predicate: `created_by`
    *   Object: `Artist` (若有 Artist_QID 则优先使用 ID)
    *   *条件*: Artist 字段非空。

*   **规则 B (作品-地点)**:
    *   Subject: `Title_Description`
    *   Predicate: `located_at`
    *   Object: `Location`
    *   *条件*: Location 字段非空。

### 3.2 语义分析提取（深度优化）
`Title_Description` 和 `Location` 字段包含丰富的隐含关系，需要更细致的解析。

#### A. 标题深度解析 (Title_Description)
1.  **嵌入式收藏地**:
    *   **模式**: `Title [Collection]` 或 `Title (Collection)`
    *   **示例**: "Three portraits of Doges [Private Collections)"
    *   **处理**: 提取括号内内容作为地点/收藏者。
    *   **三元组**: `Work --located_at--> Collection`
2.  **局部与整体关系 (Part-Whole)**:
    *   **模式**: `Title. Detail from Source` 或 `Title from Source`
    *   **示例**: "Romulus and Remus. Detail from ceiling of gallery in Bibliothèque Nationale"
    *   **处理**: 识别 "Detail from", "from" 等关键词。
    *   **三元组**: `Work --part_of--> Source` (这里的 Work 指 "Romulus and Remus")
3.  **描绘关系 (Depicts) - 增强**:
    *   **模式**: "Three portraits of X" -> `Work --depicts--> X`

#### B. 地点层级解析 (Location)
1.  **机构与城市**:
    *   **模式**: `Institution, City` (逗号分隔)
    *   **示例**: "Ufficio dell’Assessore Comunale alle Belle Arti, Rome"
    *   **处理**: 将地点字符串按逗号分割。通常最后一部分为城市/国家，前面为具体机构。
    *   **三元组**:
        *   `Work --located_at--> Institution`
        *   `Institution --located_at--> City`

## 4. 数据处理计划
1.  **清洗**: 统一空值处理（将 "nan", "", " " 统一为 None）。
2.  **转换**: 生成标准化的三元组表。
    *   格式: `Head_Entity | Head_QID | Relation | Tail_Entity | Tail_QID | Source_Column`
3.  **输出**: 保存为 `02-worklist/02-Worklist-Triples.csv`。

## 5. 待确认问题
- 对于没有 QID 的实体，是否仅保留文本名称？（建议：保留，作为文本节点）。
- 是否需要拆分 `Title_Description` 中的复杂描述？（建议：先进行简单拆分，如 "A as B"）。
