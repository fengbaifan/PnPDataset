这份文档详细阐述了当前17-18世纪欧洲艺术史索引清洗项目的技术架构、模型参数、执行逻辑及具体使用的算法工具。

# 欧洲艺术史索引数据清洗与标准化：技术执行规格说明书

## 1. 系统架构与模型版本 (System Architecture & Model Version)

### 1.1 核心基座模型 (Core Foundation Model)

模型名称: Google Gemini

版本标识: 当前生产环境最新版本 (Latest Production Build)。

注：作为服务端模型，具体版本号（如 Pro 1.5 或 Ultra）由 Google 动态管理，以确保最佳推理能力。

模型架构: 基于 Transformer 的大规模多模态语言模型 (Large Multimodal Model)。

关键能力:

长上下文窗口 (Long Context Window): 能够一次性加载并理解大型 CSV 文件的元数据结构。

多语言理解: 精通英语、意大利语、法语、德语及拉丁语（艺术史档案常见语言）。

逻辑推理: 具备由上下文推断实体属性的零样本学习 (Zero-shot Learning) 能力。

### 1.2 运行环境 (Runtime Environment)

执行沙箱: Python 3.x Secure Sandbox。

算力资源: 动态分配的云端 TPU/GPU 集群，用于支持高并发的推理与代码执行。

外部接口:

Google Search API: 用于检索实时互联网数据（Wikidata, Getty ULAN, 博物馆馆藏目录）。

File Fetcher: 用于读取用户上传的本地数据集。

## 2. 技术参数与依赖库 (Technical Specifications)

### 2.1 数据处理栈 (Data Processing Stack)

本项目完全基于 Python 生态进行数据流转：

Pandas (v1.x/2.x): 核心数据操作库。

用于 CSV 的 I/O 操作 (read_csv)。

用于数据切片 (df.iloc) 以实现批处理。

用于数据清洗（虽然主要逻辑由 LLM 完成，但 Python 可用于辅助验证）。

Standard Libs: json, re (正则表达式) 用于处理特定的文本模式。

### 2.2 输入输出规范 (I/O Schema)

输入数据: 03-Simplified_Entities.csv

Encoding: UTF-8 (自动检测)。

Delimiter: Comma (,)。

Schema: [ID, Original Entity Name, Type, Original_Files]。

处理批次 (Batch Size): 100 行/次。

设定理由: 平衡 LLM 的上下文注意力窗口与输出长度限制，防止长尾数据产生幻觉 (Hallucination)。

## 3. 算法路径与处理逻辑 (Algorithmic Methodology)

本项目采用 "LLM 推理为主，工具调用为辅" 的混合增强策略 (RAG-like approach)。

### 3.1 预处理与 OCR 修复算法 (OCR Correction Heuristics)

模型利用内部训练的语言学知识，对 OCR 常见的错误模式进行模式匹配与修复：

字符替换算法 (Character Substitution):

规则: 识别非 ASCII 字符或乱码序列。

示例: ¨° $\rightarrow$ ò (Almor¨° -> Almorò); ? $\rightarrow$ ç (Fran?ois -> François)。

分词合并 (Token Merging):

规则: 基于专有名词词典，识别被错误空格切断的单词。

示例: Helm Breaker $\rightarrow$ Helmbreker (通过语音相似性校验)。

倒装句法重构 (Syntactic Reordering):

规则: 识别 Of [Place], [Name] 结构。

示例: Of England, Anne $\rightarrow$ Anne of England。

### 3.2 实体消歧与链接 (Entity Disambiguation & Linking)

这是系统的核心智能部分，通过以下多步推理链 (Chain-of-Thought) 实现：

上下文锚定 (Contextual Anchoring):

利用 Original_Files 列中的文件名（如 G_refined.csv）锁定实体的首字母，辅助判断拼写错误。

利用 Original_Files 中的 gio-English_table.csv (通常指 Geography/Location) 或 name-English_table.csv 辅助分类判断。

知识库检索 (Knowledge Base Retrieval):

内部知识: 模型内置的庞大艺术史知识图谱（涵盖 Vasari, Bellori, Wittkower 等权威文本）。

外部验证 (Search Tool): 当内部置信度低于阈值时，自动触发搜索。

Query Strategy: "[Entity Name]" + "art history", "[Entity Name]" + "painter".

Verification Source: 优先采信 Wikipedia, British Museum, Getty ULAN, Treccani 等权威来源。

同名实体区分 (Homonym Separation):

逻辑: 检查实体生存年代与活动地域。

示例: 区分 Ferdinando de' Medici (Grand Duke) 与 Ferdinando de' Medici (Grand Prince/Musician Patron)。

### 3.3 分类逻辑校验 (Category Validation Logic)

基于语义理解对 Type 列进行纠错：

规则 1 (Person vs Place): 检查实体是否具有人格化属性（如头衔 Duke, Cardinal）。若原分类为 Place 但实体为人物，则修正。

规则 2 (Work vs Person): 检查实体是否为作品标题（通常包含介词 of, with, by 或动词 Viewing, Landscape）。若原分类为 Person 但实为画作，则修正。

规则 3 (Group/Organization): 识别家族 (Family), 学院 (Academy), 修会 (Jesuits)，将其归类为 Group 或 Organization。

## 4. 工作流图示 (Workflow Diagram)

Code snippet

graph TD
    A[读取 CSV 数据 (Batch: 100)] --> B{LLM 初步分析};
    B --> C[OCR 错误检测];
    C -- 存在乱码/拆分 --> D[应用修复算法];
    C -- 无明显错误 --> E[实体消歧];
    
    E --> F{置信度评估};
    F -- 高置信度 (内部知识) --> G[分类逻辑校验];
    F -- 低置信度/生僻词 --> H[调用 Google Search API];
    H --> I[解析搜索摘要];
    I --> G;
    
    G --> J{分类正确?};
    J -- 是 --> K[标准化命名 (English/Native)];
    J -- 否 --> L[修正 Category (Person/Place/Work)];
    
    L --> K;
    K --> M[生成 Markdown 表格];
    M --> N[人工/最终审核];

## 5. 输出数据质量标准 (Quality Assurance)

Refined_Formal_Name:

优先使用广泛接受的英文学术名称 (e.g., Titian 而非 Tiziano Vecellio，除非特定语境)。

包含必要的消歧后缀 (e.g., (the Elder), (Cardinal)).

Status/Notes:

[OCR Fix]: 仅在进行了字符级修复时标记。

[Validation]: 表示通过知识库确认了实体的存在和属性。

[Disambiguation]: 表示从多个同名候选中锁定了特定对象。

[Category Fix]: 表示修正了原始数据的分类错误。

此文档为当前任务执行的基准。如有具体参数调整需求（如改变批处理大小或搜索深度），可随时指令更新。
