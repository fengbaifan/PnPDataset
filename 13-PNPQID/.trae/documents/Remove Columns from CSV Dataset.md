I will remove the `Second-Query_Label`, `Source`, and `Context` columns from `01-Merged_Dataset.csv`.

**Implementation Steps:**
1.  **Read the CSV file**: Load `01-Merged_Dataset.csv` using Python's `csv` module (or pandas if available, but standard library is safer if dependencies are unknown).
2.  **Filter Columns**: Identify the indices of the columns to be removed and keep only the remaining columns (`Refined_Formal_Name`, `Original-QID`, `Match_Method`).
3.  **Write Changes**: Overwrite `01-Merged_Dataset.csv` with the modified data.

**Verification:**
- I will verify the header of the file after the operation to ensure the columns are gone and the data is intact.
