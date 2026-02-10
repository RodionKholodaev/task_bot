import re

class message_service():
    @staticmethod
    def extract_task_id(text: str) -> int | None:
        match = re.search(r"ID задачи:\s*(\d+)", text)
        if match:
            return int(match.group(1))
        return None
