import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
db = sqlite3.connect(ROOT / 'data' / 'bike.db')

df = pd.read_csv(ROOT / 'data' / 'daily_bike_weather.csv')
df.to_sql('daily', db, if_exists='replace', index=False)

print(db.execute('SELECT COUNT(*) FROM daily').fetchone())
db.close()