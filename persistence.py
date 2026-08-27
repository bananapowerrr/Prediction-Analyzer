import sqlite3
from typing import Dict, List

class PersistenceManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                data TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def save_event(self, event_type: str, data: Dict):
        self.cursor.execute('INSERT INTO reports (report_type, data) VALUES (?, ?)', (event_type, str(data)))
        self.conn.commit()

    def get_events(self, event_type: str = None) -> List[Dict]:
        query = 'SELECT data FROM reports'
        if event_type:
            query += f' WHERE report_type = ?'
            self.cursor.execute(query, (event_type,))
        else:
            self.cursor.execute(query)
        results = self.cursor.fetchall()
        return [dict(row) for row in results]

    def save_report(self, report_type: str, data: Dict):
        self.cursor.execute('INSERT INTO reports (report_type, data) VALUES (?, ?)', (report_type, str(data)))
        self.conn.commit()

    def get_report(self, report_type: str) -> Dict:
        self.cursor.execute('SELECT data FROM reports WHERE report_type = ?', (report_type,))
        result = self.cursor.fetchone()
        if result:
            return dict(result)
        return None

    def get_all_reports(self) -> List[Dict]:
        self.cursor.execute('SELECT * FROM reports')
        results = self.cursor.fetchall()
        return [dict(row) for row in results]
