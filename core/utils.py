import re


def convert_duration(duration):
    units = {'d': '天', 'h': '小時', 'm': '分鐘', 's': '秒'}
    matches = re.findall(r'(\d+)([dhms])', duration)

    return " ".join(f"{num} {units[unit]}" for num, unit in matches)