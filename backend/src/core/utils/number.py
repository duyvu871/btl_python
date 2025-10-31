import re


def extract_number(text):
    if not text:
        return None
    match = re.search(r'\d+', str(text)) # Tìm số đầu tiên
    if match:
        return int(match.group(0))
    return None

