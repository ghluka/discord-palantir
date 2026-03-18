import os
import sys

import psycopg

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL


class Database:
    def __init__(self):
        self.conn = psycopg.connect(DATABASE_URL)
        self.conn.autocommit = True

    def execute(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)

    def fetchone(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetchall(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
            cur.execute(query, params)
            return cur.fetchall()
