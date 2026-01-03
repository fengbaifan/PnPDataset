# 11-ORG 文件夹说明文档

## 概述
本文件夹包含从项目原始数据源（图版列表和索引）中提取的机构（博物馆、美术馆、档案馆、教堂、宫殿等）清单，并已尝试与 Wikidata QID 进行匹配，最后融合了人工校对的数据。

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
*   **产物**: `01-Organizations_Extracted.csv` (原名 `organizations_list.csv`)

### 2. QID 匹配 (QID Matching)
*   **执行时间**: 2026年1月3日
*   **参考数据集**: `09-MissingQID-LLM-Fillin/07-Human-Merge/06-Requery_Filled_Human_Merged_Corrected.csv`
*   **匹配逻辑**:
    *   **精确匹配 (Exact Match)**: 名称完全一致。
    *   **替换匹配 (Substitution Match)**: 处理常见缩写和同义词（如 `S.` -> `San`, `Palace` <-> `Palazzo`）。
    *   **子串匹配 (Substring Match)**: 检查机构名称中是否包含参考数据集中的已知实体。
*   **数据清洗**:
    *   列重排: `Name`, `QID`, `Source`, `Context`, `Match_Method`
    *   移除泛指条目 (`Churches`, `Churches of religious orders`)
*   **产物**: `02-Organizations_With_QID_Auto.csv` (原名 `organizations_list_with_qid.csv`)

### 3. 未匹配数据提取与人工校对
*   **提取未匹配项**: 将 `02-Organizations_With_QID_Auto.csv` 中无 QID 的条目提取出来。
    *   **产物**: `03-Organizations_Missing_QID.csv` (原名 `organizations_missing_qid.csv`)
*   **人工校对**: 对提取出的未匹配项进行人工查询和补充 QID。
    *   **产物**: `04-Organizations_Missing_QID_Human_Corrected.csv` (原名 `human-organizations_missing_qid.csv`)

### 4. 数据融合 (Final Merge)
*   **执行时间**: 2026年1月3日
*   **输入**:
    *   `02-Organizations_With_QID_Auto.csv` (自动匹配成功的条目)
    *   `04-Organizations_Missing_QID_Human_Corrected.csv` (人工校对补充的条目)
*   **逻辑**:
    *   读取自动匹配文件中已有 QID 的行。
    *   读取人工校对文件中补充了 QID 的行。
    *   合并并去重（本例中互补）。
*   **产物**: `05-Organizations_Final_Merged.csv` (原名 `organizations_list_final.csv`)

## 文件列表

1.  **01-Organizations_Extracted.csv**: 原始提取的机构清单。
2.  **02-Organizations_With_QID_Auto.csv**: 自动匹配 QID 后的清单（包含未匹配项）。
3.  **03-Organizations_Missing_QID.csv**: 提取出的未匹配 QID 的机构清单。
4.  **04-Organizations_Missing_QID_Human_Corrected.csv**: 经过人工校对和补充 QID 的清单。
5.  **05-Organizations_Final_Merged.csv**: 最终融合的、仅包含有效 QID 的机构清单。

## 统计信息
*   **总提取条目数**: 75 (初始) -> 73 (清洗后)
*   **自动匹配成功数**: 46
*   **人工补充数**: 19
*   **最终有效条目数**: 65

## 注意事项
*   "Santa Maria Maggiore" 等条目虽然存在于全量数据 (`05-EntityMerge`) 中，但因未被提取规则选中，目前不在本清单中。
