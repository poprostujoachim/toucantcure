'''
creates the database in sql from excel
'''


import sqlite3

import pandas as pd

# Opening the Excel files takes long
coverage = pd.read_excel("data/raw/coverage-data.xlsx", sheet_name="Data")
cases = pd.read_excel("data/raw/reported-cases-data.xlsx", sheet_name="Data")

db = sqlite3.connect("data/who_data.db")

# Each Excel sheet becomes a table in the database
coverage.to_sql("coverage", db, if_exists="replace", index=False)
cases.to_sql("cases", db, if_exists="replace", index=False)

# Our own small table: which vaccine protects against which disease
db.executescript("""
    DROP TABLE IF EXISTS vaccine_for;
    CREATE TABLE vaccine_for (DISEASE TEXT, ANTIGEN TEXT);
    INSERT INTO vaccine_for VALUES
        ('MEASLES', 'MCV1'),
        ('RUBELLA', 'RCV1'),
        ('PERTUSSIS', 'DTPCV3'),
        ('DIPHTHERIA', 'DTPCV3');
""")

db.commit()
db.close()
print("Saved data/who_data.db")