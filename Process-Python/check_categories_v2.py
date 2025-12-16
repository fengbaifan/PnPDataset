import pandas as pd
import sys

try:
    df = pd.read_csv(r'09-QID-Crosscheck/02-Merged_Recheck_With_QID_Cleaned.csv')
    cats = df['Refined_Category'].unique()
    with open('categories_list.txt', 'w', encoding='utf-8') as f:
        for c in cats:
            f.write(str(c) + '\n')
    print("Done")
except Exception as e:
    print(e)
