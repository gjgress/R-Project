import pandas as pd
 
pd.set_option('display.max_columns', 50)  # display columns
df = pd.read_json('arxiv-metadata-oai-snapshot.json',lines = True)
df.to_csv("arxiv-dataset.csv")
