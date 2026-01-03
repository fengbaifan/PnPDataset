# 11-ORG 文件夹说明文档

## 概述
本文件夹包含从项目原始数据源（图版列表和索引）中提取的机构（博物馆、美术馆、档案馆、教堂、宫殿等）清单，并已尝试与 Wikidata QID 进行匹配。

## 数据处理流程

### 1. 机构提取 (Extraction)
*   **执行时间**: 2026年1月3日
*   **数据源**:
    *   `02-Markdown/00_05_List_of_Plates.md` (List of Plates)
    *   `03-Index/03-2-Index-CSV/*.csv` (Index CSV files)
*   **提取逻辑**:
    *   使用 Python 脚本遍历源文件。
    *   基于关键词匹配提取潜在的机构名称。
    *   **关键词列表**: Museum, Museo, Gallery, Galleria, Library, Biblioteca, Archive, Archivio, Institute, Istituto, Academy, Accademia, University, Universita, College, Collegio, Collection, Collezione, Palace, Palazzo, Villa, Church, Chiesa, Cathedral, Duomo, Basilica, Chapel, Cappella, Oratory, Oratorio, San, Santa, Hospital, Ospedale, Foundation, Fondazione, Louvre, Vatican, Uffizi, Prado, Pitti, Hermitage, National Gallery, Royal Collection, Pinacoteca.
    *   **排除词**: Peace of, Treaty of, Battle of, Council of, Diet of, Edict of, League of, Sanctity, Saint, Saints.
*   **中间产物**: `organizations_list.csv` (包含 Name, Source, Context)

### 2. QID 匹配 (QID Matching)
*   **执行时间**: 2026年1月3日
*   **参考数据集**: `09-MissingQID-LLM-Fillin/07-Human-Merge/06-Requery_Filled_Human_Merged_Corrected.csv`
*   **匹配逻辑**:
    *   **精确匹配 (Exact Match)**: 名称完全一致。
    *   **替换匹配 (Substitution Match)**: 处理常见缩写和同义词（如 `S.` -> `San`, `Palace` <-> `Palazzo`）。
    *   **子串匹配 (Substring Match)**: 检查机构名称中是否包含参考数据集中的已知实体。
*   **产物**: `organizations_list_with_qid.csv`

### 3. 数据清洗与结构调整 (Refinement)
*   **列重排**: 将 `QID` 列移动到 `Name` 之后。
    *   最终列结构: `Name`, `QID`, `Source`, `Context`, `Match_Method`
*   **行删除**: 移除了泛指的条目：
    *   `Churches`
    *   `Churches of religious orders`

## 文件列表

*   **organizations_list.csv**: 原始提取的机构清单（未匹配 QID）。
*   **organizations_list_with_qid.csv**: 最终处理后的机构清单，包含 QID 和匹配方法说明。

## 统计信息
*   **总提取条目数**: 75 (初始) -> 73 (清洗后)
*   **成功匹配 QID 数**: 48 (截至 2026-01-03)

## 注意事项
*   部分机构可能因名称拼写差异或不在参考数据集中而未匹配到 QID。
*   "Santa Maria Maggiore" 等条目虽然存在于全量数据 (`05-EntityMerge`) 中，但因未被提取规则选中，目前不在本清单中。如需添加需手动处理或调整提取规则。
