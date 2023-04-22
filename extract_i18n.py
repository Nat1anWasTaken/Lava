import json
import re

regex = r"Localized\((\s*('[^']*'|\"(?:(?:(?<!\\\\)(\\\\)*\\\")|[^\"])*\")\s*,){1,2}\s*key\s*=\s*(('[^']*'|\"(?:(?:(?<!\\\\)(\\\\)*\\\")|[^\"])*\")\s*)\)"

with open('cogs/commands.py', 'r', encoding='utf-8') as f:
    test_str = f.read()

with open('cogs/events.py', 'r', encoding='utf-8') as f:
    test_str += f.read()

with open('core/sources/source.py', 'r', encoding='utf-8') as f:
    test_str += f.read()

with open('core/utils.py', 'r', encoding='utf-8') as f:
    test_str += f.read()

# Find all matches
matches = re.findall(regex, test_str)

result = {}

# Extract the first and second string values from each match
for match in matches:
    value = match[1].strip("'\"")
    key = match[3].strip("'\"")

    result[key] = value

with open('locale/zh_TW.json', mode='w', encoding='utf-8') as f:
    json.dump(result, f, indent=4, ensure_ascii=False)
