# PnP Dataset Processing Workflow & Results

本文档详细记录了 PnP 数据集的处理流程、使用的脚本工具以及最终产出的数据结果。整个工作流旨在将机器提取的索引数据（Index）与人工整理的数据（Manual）进行对比、清洗、标准化，并利用外部知识库（Wikidata/Getty）进行丰富。

---

## 📊 1. 工作流概览 (Workflow Overview)

整个数据处理过程分为四个主要阶段：

1.  **数据对比与审计 (Comparison & Audit)**: 识别 Index 与 Manual 数据集之间的差异，提取未匹配项。
2.  **深度清洗与标准化 (Deep Normalization)**: 针对历史人名、地名、作品名进行复杂的格式统一。
3.  **外部知识库链接 (External Enrichment)**: 利用 Wikidata API 自动匹配实体，获取 QID 和描述。
4.  **结果精炼 (Refinement)**: 自动采纳高置信度的模糊匹配结果。

---

## 🛠️ 2. 详细步骤与脚本 (Detailed Steps)

### 阶段一：数据对比与差异提取
**目标**: 生成全量对比矩阵，并分离出无法自动匹配的“问题数据”进行审计。

*   **核心脚本**:
    *   `10_Deduplicate_Matrix.py`: 生成去重后的全量对比矩阵。
    *   `12_Extract_Manual_Audit.py`: 从矩阵中提取未匹配的行（Unmatched Index + Unmatched Manual）。
*   **产出文件**:
    *   `06-Crosscheck/Full_Comparison_Matrix_Unique.csv`: 全量对比表。
    *   `06-Crosscheck/Audit_List_Combined.csv`: **审计列表 (1610 条)**，包含所有未匹配项。

### 阶段二：深度标准化 (Deep Normalization)
**目标**: 解决历史数据中名称格式不统一的问题（如倒装、头衔、昵称、拼写变体），以便于外部查询。

*   **核心脚本**: `14_Normalize_Audit_List_Full.py`
*   **主要逻辑**:
    *   **分类判定**: 严格区分 Person (E21), Place (E53), Work (E22/E28)。
    *   **人名清洗**: 去除头衔 (Cardinal, Marchese, Duke 等)，处理昵称 (Baciccio -> Giovanni Battista Gaulli)。
    *   **地名/作品清洗**: 统一建筑名称 (Palace -> Palazzo)，处理倒装标题 (Magi, Adoration of the -> Adoration of the Magi)。
    *   **重分类**: 自动修正被误标为 Object 的人名/地名。
*   **产出文件**:
    *   `06-Crosscheck/Audit_List_Normalized_Full.csv`: 包含清洗后的 `Formal_Full_Name` 字段。

### 阶段三：Wikidata 知识库链接
**目标**: 使用标准化后的名称查询 Wikidata，获取唯一标识符 (QID) 和描述信息。

*   **核心脚本**: `15_Query_Wikidata.py`
*   **功能**:
    *   调用 Wikidata API (`wbsearchentities`)。
    *   自动处理 API 速率限制和重试。
    *   记录精确匹配 (QID) 和候选列表 (Candidates)。
*   **产出文件**:
    *   `06-Crosscheck/Audit_List_Wikidata_Enriched.csv`: 初步匹配结果。

### 阶段四：结果分析与精炼
**目标**: 分析匹配质量，并自动采纳高可能性的疑似匹配。

*   **核心脚本**:
    *   `16_Analyze_Wikidata_Results.py`: 生成统计报告。
    *   `17_Refine_Wikidata_Matches.py`: 执行自动采纳逻辑。
*   **精炼规则**:
    *   字符串相似度 > 0.85。
    *   包含关系且长度差异小（处理拼写变体或全名补全）。
*   **产出文件**:
    *   `06-Crosscheck/Audit_List_Wikidata_Refined.csv`: **最终结果表**。

---

## 📈 3. 工作结果统计 (Results Summary)

截至 2025-12-14，针对 **1610 条** 审计数据的处理结果如下：

### 3.1 总体匹配率
| 状态 | 数量 | 占比 | 说明 |
| :--- | :--- | :--- | :--- |
| **成功匹配 (Matched)** | **731** | **45.4%** | 已获取 Wikidata QID |
| **未匹配 (Unmatched)** | 879 | 54.6% | 主要是描述性作品名或极冷门实体 |

### 3.2 分类匹配详情
*   **Person (人物)**: 匹配率 **~46%**。标准化效果显著，成功识别了大量带头衔或昵称的历史人物。
*   **Place (地点)**: 匹配率 **~40%**。著名学院 (Accademia) 和宫殿 (Palazzo) 匹配良好。
*   **Work (作品)**: 匹配率 **~40%**。由于作品名变体极多且 Wikidata 收录不全，匹配难度最大。

### 3.3 典型成功案例
*   **昵称识别**: `Baciccio` -> `Giovanni Battista Gaulli` (Q520573)
*   **拼写变体**: `Leonard Bramer` -> `Leonaert Bramer` (Q979381)
*   **机构识别**: `Accademia degli Umoristi` -> `Q3603986`

---

## 📂 4. 关键文件索引 (File Index)

所有中间文件和结果均位于 `06-Crosscheck/` 目录下：

1.  **`Audit_List_Combined.csv`**: 原始审计列表（未清洗）。
2.  **`Audit_List_Normalized_Full.csv`**: 标准化后的列表（含 `Formal_Full_Name`）。
3.  **`Audit_List_Wikidata_Refined.csv`**: **最终交付文件**，包含 QID 和匹配详情。

---

## 🚀 5. 后续建议

1.  **人工复核**: 重点检查 `Audit_List_Wikidata_Refined.csv` 中 `Match_Type` 为 "Auto-Refined" 的条目。
2.  **数据回填**: 将获得的 QID 合并回主数据库 (`04-Index-Enrich` 或 `05-Index-Handmade`)。
3.  **补充查询**: 对于未匹配的 Works，可考虑使用 Google Knowledge Graph API 或 Getty AAT 进行补充查询。

---

# PnP Dataset Processing Scripts (Old)

此文件夹包含用于处理、分析和丰富 PnP 数据集的所有 Python 脚本。脚本按功能分为三个主要阶段。

## 📂 01-Process (数据处理流水线)
此文件夹包含核心的数据清洗和转换脚本。建议按顺序运行。

| 脚本名 | 功能描述 |
| :--- | :--- |
| `01_Apply_Initial_CIDOC.py` | 初步应用 CIDOC CRM 类型分类 (E21, E53 等)。 |
| `02_Update_Specific_Unknowns.py` | 更新特定的未知类型条目。 |
| `03_Finalize_Unknown_Classification.py` | 完成剩余未知条目的分类。 |
| `04_Fix_Quoted_Terms.py` | 修复被错误引用的术语格式。 |
| `05_Fix_Type_Mismatches.py` | 修复类型不匹配的数据错误。 |
| `06_Rename_Columns.py` | 标准化列名 (如 Index_Main Entry)。 |
| `07_Preview_Location_Enrichment.py` | 预览地点数据的丰富效果。 |
| `08_Add_Location_Columns.py` | 添加地点相关的空列 (Proposed Location 等)。 |
| `09_Update_Location_Chinese_Notes.py` | 更新地点的中文备注信息。 |
| `10_Enrich_All_Locations.py` | 对所有文件执行地点丰富化操作。 |
| `11_Organize_Workspace.py` | (工具) 整理工作区文件夹结构。 |
| `12_Generate_Crosscheck_Files.py` | 生成用于与人工数据对比的中间文件 (`_crosscheck.csv`)。 |

## 📂 02-Analysis (统计与对比分析)
此文件夹包含用于生成报告和对比不同数据集的脚本。

| 脚本名 | 功能描述 |
| :--- | :--- |
| `01_Audit_Missing_Locations.py` | 审计缺失地点信息的条目。 |
| `02_Analyze_Missing.py` | 分析缺失数据的模式。 |
| `03_Analyze_Enriched_Data.py` | 对丰富后的数据进行统计分析。 |
| `04_Analyze_Content_Details.py` | 分析索引内容的详细信息。 |
| `05_Deep_Entity_Analysis.py` | 深度实体分析 (去重、频率统计)。 |
| `06_Compare_Datasets.py` | (基础) 对比索引数据(04)与人工数据(05)。 |
| `07_Normalize_and_Match.py` | (高级) 使用归一化策略进行深度匹配。 |
| `08_Generate_Consolidated_Report.py` | 生成简单的合并对比报告。 |
| `09_Generate_Full_Comparison_Report.py` | 生成完整的对比矩阵 (包含未匹配的人工数据)。 |

**生成的报告:**
- `Analysis_Report.md`: 总体数据分析报告。
- `Data_Comparison_Report.md`: 基础对比报告。
- `Advanced_Comparison_Report.md`: 高级归一化对比报告。

## 📂 03-Getty-Integration (Getty 数据集成)
此文件夹包含用于查询本地 Getty Vocabularies (ULAN, TGN, AAT) 的工具。

| 脚本名 | 功能描述 |
| :--- | :--- |
| `01_Query_Local_Getty_ULAN.py` | 扫描本地 ULAN `.nt` 文件以查找匹配项。 |
| `02_Get_Hogarth_Details.py` | (示例) 获取特定艺术家 (Hogarth) 的详细信息。 |
| `03_Get_ScopeNote.py` | 从 RDF 数据中提取 ScopeNote (传记/描述)。 |
| `04_Query_Getty_B_Full.py` | 对 `B_refined.csv` 执行完整的 Getty 查询 (ULAN/TGN/AAT)。 |
| `05_Query_Getty_B_Sample.py` | 对 `B_refined.csv` 执行小样本测试查询。 |

## 📂 Archive (归档)
包含旧的 `StepX` 系列脚本和失败的 API 尝试脚本。仅供参考。
