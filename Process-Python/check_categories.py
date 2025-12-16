import pandas as pd
try:
    df = pd.read_csv(r'09-QID-Crosscheck/02-Merged_Recheck_With_QID_Cleaned.csv')
    print("Unique Categories:")
    print(df['Refined_Category'].unique())
except Exception as e:
    print(e)
