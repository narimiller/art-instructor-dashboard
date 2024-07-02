import sqlite3
import pandas as pd
import os


def read_csv_files_from_directory(directory):
    tables = {}
    for file_name in os.listdir(directory):
        if file_name in ['uploads.csv', 'cohorts.csv']:
            file_path = os.path.join(directory, file_name)
            table_name = os.path.splitext(file_name)[0]
            tables[table_name] = pd.read_csv(file_path)
    return tables

directory = 'data'

tables = read_csv_files_from_directory(directory)

# Cleaning/ deal with dtypes
for table in list(tables.keys()):
    tables[table].rename(columns=lambda x: x.replace(' ','_').lower(), inplace=True)

# Convert datetime to SQLite-compatible format
tables['uploads']['datetime'] = pd.to_datetime(tables['uploads']['datetime'], format='%Y/%m/%d %H:%M:%S')
tables['uploads']['datetime'] = pd.to_datetime(tables['uploads']['datetime']).dt.strftime('%Y-%m-%d %H:%M:%S')

date_columns = ['launch_start', 'term_start', 'term_end']
for col in date_columns:
    tables['cohorts'][col] = pd.to_datetime(tables['cohorts'][col], format='%b %d, %Y')
    tables['cohorts'][col] = tables['cohorts'][col].dt.strftime('%Y-%m-%d')

# Create/connect to SQLite database
connection = sqlite3.connect('data.db')

# Upload dataframes as db tables
for table in list(tables.keys()):
    tables[table].to_sql(table, connection, if_exists='replace', index=False)

print(tables['uploads'].head())

# Close connection
connection.close()

