import re

# ---- tool_call 标签：单趟状态机消费 ----
_TAG = 'tool_call'

_TOKEN_RE = re.compile(
    r'<\s*(/?)\s*' + re.escape(_TAG) + r'\s*>',
    re.IGNORECASE,
)


def strip_tags(text):
    if not isinstance(text, str):
        return text
    return _TOKEN_RE.sub('', text)


def parse(text):
    if not isinstance(text, str) or not text:
        return [], ''
    calls, plain, buf = [], [], []
    in_cmd, pos = False, 0
    for m in _TOKEN_RE.finditer(text):
        seg = text[pos:m.start()]
        (buf if in_cmd else plain).append(seg)
        if m.group(1) != '/':
            if not in_cmd:
                in_cmd, buf = True, []
        else:
            if in_cmd:
                calls.append(''.join(buf))
                buf, in_cmd = [], False
        pos = m.end()
    tail = text[pos:]
    if in_cmd:
        plain.append(''.join(buf))
        plain.append(tail)
    else:
        plain.append(tail)
    return calls, ''.join(plain)


TAGS = ["agent_imageurl", "agent_image", "agent_audiourl", "agent_audio", "agent_videourl", "agent_video"]
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