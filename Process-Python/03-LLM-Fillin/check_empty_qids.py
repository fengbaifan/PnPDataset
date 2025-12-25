import pandas as pd
import os

file_path = r"c:\Users\001\Desktop\Github-Project\PnPDataset\09-MissingQID-LLM-Fillin\04-QID-Combine ORGfile\07-Requery_Filled_Combined.csv"

def check_empty():
    if not os.path.exists(file_path):
        print("File not found.")
        return

    df = pd.read_csv(file_path)
    total_rows = len(df)
    
    # Define what counts as "Empty" (NaN or whitespace)
    def is_empty(series):
        return series.isna() | (series.astype(str).str.strip() == '')

    empty_orig = is_empty(df['Original-QID'])
    empty_second = is_empty(df['Second-Query_QID'])
    empty_llm = is_empty(df['LLM-Fillin_QID'])
    
    # Count empty per column
    count_empty_orig = empty_orig.sum()
    count_empty_second = empty_second.sum()
    count_empty_llm = empty_llm.sum()
    
    # Count rows where ALL are empty
    all_empty = empty_orig & empty_second & empty_llm
    count_all_empty = all_empty.sum()
    
    # Check if secondary sources filled any gaps
    # i.e., Original is Empty BUT (Second is filled OR LLM is filled)
    gained_coverage = df[empty_orig & (~empty_second | ~empty_llm)]
    
    print(f"Total Rows: {total_rows}")
    print("-" * 30)
    print(f"Empty 'Original-QID': {count_empty_orig}")
    print(f"Empty 'Second-Query_QID': {count_empty_second}")
    print(f"Empty 'LLM-Fillin_QID': {count_empty_llm}")
    print("-" * 30)
    print(f"Rows with NO QID at all (All 3 empty): {count_all_empty}")
    print("-" * 30)
    print(f"Rows where Original was empty but filled by others: {len(gained_coverage)}")

if __name__ == "__main__":
    check_empty()
