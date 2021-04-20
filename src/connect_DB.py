from psycopg2.extras import RealDictCursor
import psycopg2
import dotenv
import os

dotenv_dict = dotenv.dotenv_values()


print(dotenv_dict["POSTGRESS_URI"])

db_conn = psycopg2.connect(uri)
c = db_conn.cursor(cursor_factory=RealDictCursor)

c.execute("SELECT 1 = 1")
result = c.fetchone()
