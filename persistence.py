import json
import os
from typing import Dict, List, Optional

class PersistenceManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({}, f)

    def save_event(self, event_type: str, data: Dict):
        with open(self.db_path, 'r') as f:
            data_dict = json.load(f)
        if event_type not in data_dict:
            data_dict[event_type] = []
        data_dict[event_type].append(data)
        with open(self.db_path, 'w') as f:
            json.dump(data_dict, f, indent=4)

    def get_events(self, event_type: str = None) -> List[Dict]:
        with open(self.db_path, 'r') as f:
            data_dict = json.load(f)
        if event_type:
            return data_dict.get(event_type, [])
        return data_dict

    def close(self):
        pass
