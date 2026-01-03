# 07-Human-Merge 数据处理流程说明

本文件夹记录了将 LLM 补充的 QID 数据与人工校对数据进行融合、清洗和质量控制的完整流程。

## 数据处理步骤

### 1. 初始融合 (Initial Merge)
*   **文件**: `01-Requery_Filled_Human_Merged.csv`
*   **描述**: 将上一阶段（LLM 自动填充 QID）的结果与人工手动查找或校对的数据进行初步合并。

### 2. 去重 (Deduplication)
*   **文件**: `02-Requery_Filled_Human_Merged_Deduplicated.csv`
*   **描述**: 对合并后的数据进行去重处理。通常基于实体名称或 QID 进行唯一性检查，移除重复的条目，确保每个实体只出现一次。

### 3. 数据清洗 (Cleaning)
*   **文件**: `03-Requery_Filled_Human_Merged_Cleaned.csv`
*   **描述**: 对去重后的数据进行格式清洗。可能包括：
    *   移除空白行或无效列。
    *   标准化字段格式（如去除首尾空格）。
    *   统一 QID 格式。

### 4. 阶段性定稿 (Draft Final)
*   **文件**: `04-Requery_Filled_Human_Merged_Final.csv`
*   **描述**: 经过清洗后的阶段性完整数据集，准备进入质量检查环节。

### 5. 质量检查与异常识别 (Quality Control)
*   **文件**: `05-Potential_QID_Mismatches.csv`
*   **描述**: 这是一个中间分析文件，用于记录潜在的 QID 匹配错误。
    *   可能通过比对实体名称与 Wikidata 标签的相似度，或者检查同一 QID 是否对应了完全不同的实体名称来生成。
    *   该文件用于指导后续的人工修正。

### 6. 最终修正 (Final Correction)
*   **文件**: `06-Requery_Filled_Human_Merged_Corrected.csv`
*   **描述**: 基于步骤 5 发现的问题进行修正后的最终版本。
    *   修复了错误的 QID 映射。
    *   确认了存疑的条目。
    *   **这是当前阶段最高质量的参考数据集**，被用于后续的机构匹配（11-ORG）和最终数据集生成（12-Final-Dataset）。

## 总结
该流程通过“合并 -> 去重 -> 清洗 -> 质检 -> 修正”的闭环，确保了 QID 数据的准确性和一致性。
