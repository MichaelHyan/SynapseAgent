import re
def parse(text):
    tag_contents = []
    pattern = r'<tool_call>(.*?)</tool_call>'
    matches = re.finditer(pattern, text, re.DOTALL)
    for match in matches:
        tag_contents.append(match.group(1))
    plain_text = re.sub(pattern, '', text, flags=re.DOTALL)
    #plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    return tag_contents, plain_text