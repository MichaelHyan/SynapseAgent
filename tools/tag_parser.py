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

TAGS = ["imageurl", "image", "audiourl", "audio", "videourl", "video"]
TAG_ALTERNATION = "|".join(TAGS)
PATTERN = re.compile(
    r"<(?P<tag>" + TAG_ALTERNATION + r")>(?P<data>.*?)</(?P=tag)>",
    re.DOTALL,
)
def parse_all(text):
    matches = []
    segments = []
    last_end = 0

    for m in PATTERN.finditer(text):
        matches.append({"tag": m.group("tag"), "data": m.group("data")})
        segments.append(text[last_end:m.start()])
        last_end = m.end()
    segments.append(text[last_end:])
    return {
        "matches": matches,
        "rest": "".join(segments),
    }