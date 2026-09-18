import os,base64,shutil
import tools.lang as lang
import json,re
with open('./config/config.json',encoding='utf-8') as f:
    config = json.load(f)

SIZE_LIMIT = 1

def dir(path:str):
    if not path:
        path = config['base_path']
    try:
        all_items = os.listdir(path)
        dirs = []
        files = []
        r = ''
        for item in all_items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                dirs.append(item)
            elif os.path.isfile(full_path):
                files.append(item)        
        for d in dirs:
            r += f"[DIR]{d}\n"
        for f in files:
            r += f"[FILE]{f}\n"
        return r
    except Exception as e:
        return str(e)

def read(path:str):
    if len(path.split(maxsplit=2)) == 1:
        path,p0,p1 = path,0,0
    else:
        p0,p1,path = path.split(maxsplit=2)
        p0 = int(p0)
        p1 = int(p1)
    try:
        file_size = os.path.getsize(path)
        if file_size > SIZE_LIMIT * 1024 * 1024:
            return f'{lang.lang['bot.tool.fileunreadable']}{file_size}/{SIZE_LIMIT} bytes'
        with open(path, 'r', encoding = 'utf-8') as f:
            lines = f.readlines()
        if p0 == 0:
            p0 = 1
        if p1 == 0 or p1 < p0:
            p1 = len(lines)
        return ''.join(lines[p0-1:p1])
    except Exception as e:
        return str(e)

def write(path, content):
    try:
        '''
        content_size = len(content.encode('utf-8'))
        if content_size > SIZE_LIMIT * 1024 * 1024:
            return f'[A] 内容过大 ({content_size} bytes)，超过{SIZE_LIMIT}MB限制，无法写入'
        '''
        with open(path, 'w', encoding = 'utf-8') as f:
            f.write(content)
        return lang.lang['bot.tool.filewritedone']
    except Exception as e:
        return str(e)

def delete(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        elif os.path.isfile(path):
            os.remove(path)
        return lang.lang['bot.tool.filedeletedone']
    except Exception as e:
        return str(e)

def encode(path,prex):
    with open(path, "rb") as file:
        return f'<{prex}>{base64.b64encode(file.read()).decode("utf-8")}</{prex}>'

def backup(src_dir, dst_dir='./bak/'):
    if not os.path.exists(src_dir):
        return False
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    try:
        for item in os.listdir(src_dir):
            src_path = os.path.join(src_dir, item)
            dst_path = os.path.join(dst_dir, item)
            if os.path.isdir(src_path):
                print(f"copying: {src_path} -> {dst_path}")
                if os.path.exists(dst_path):
                    backup(src_path, dst_path)
                else:
                    shutil.copytree(src_path, dst_path)
            else:
                print(f"copying: {src_path} -> {dst_path}")
                shutil.copy2(src_path, dst_path)
        return 'copy complete'
    except Exception as e:
        return str(e)
import os

def list_dir(path):
    if not path:
        path = config['base_path']
    response = ''
    response += f"[DIR] {path}\n"
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                response += f" - [DIR] {entry.name}" if entry.is_dir() else f" - [FILE] {entry.name}\n"
    except PermissionError:
        pass
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath == path:
            continue
        response += f"[DIR] {dirpath}"
        for dirname in dirnames:
            response += f" - [FILE] {dirname}"
        for filename in filenames:
            response += f" - [FILE] {filename}"
    return response

CASE_SENSITIVE = False
USE_REGEX = False
EXCLUDE_DIRS = [
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "dist",
    "build",
]

EXCLUDE_EXTS = [
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    ".zip", ".rar", ".7z", ".gz", ".tar", ".jar",
    ".pyc", ".pyo", ".pyd", ".pdb",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".avi", ".mov", ".wav", ".flv",
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ".sqlite", ".db",
]
ENCODINGS = ["utf-8", "utf-8-sig", "gbk", "latin-1"]
FOLLOW_SYMLINKS = False
MAX_LINE_PREVIEW = 200
SKIP_HIDDEN = False

def _build_matcher(patterns, use_regex, case_sensitive):
    errors = []
    compiled = []

    for p in patterns:
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled.append(("regex", re.compile(p, flags)))
            except re.error as e:
                errors.append((p, str(e)))
                compiled.append(("regex", None))  # 占位，保持下标对齐
        else:
            compiled.append(("text", p if case_sensitive else p.lower()))

    def match_func(line):
        hits = []
        haystack = line if case_sensitive else line.lower()
        for idx, (kind, obj) in enumerate(compiled):
            if kind == "regex":
                if obj is not None and obj.search(line):
                    hits.append(idx)
            else:
                if obj and obj in haystack:
                    hits.append(idx)
        return hits

    return match_func, errors


def _iter_files(root, exclude_dirs, exclude_exts, skip_hidden, follow_symlinks):
    exclude_dirs_set = set(exclude_dirs)
    exclude_exts_set = set(e.lower() for e in exclude_exts)

    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        dirnames[:] = [
            d for d in dirnames
            if d not in exclude_dirs_set and not (skip_hidden and d.startswith("."))
        ]

        for name in filenames:
            if skip_hidden and name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in exclude_exts_set:
                continue
            yield os.path.join(dirpath, name)


def _read_text_lines(path, encodings):
    last_err = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return f.read().splitlines(), enc, None
        except (UnicodeDecodeError, LookupError) as e:
            last_err = e
            continue
        except OSError as e:
            return None, None, e

    try:
        fallback_enc = encodings[0] if encodings else "utf-8"
        with open(path, "r", encoding=fallback_enc, errors="ignore") as f:
            return f.read().splitlines(), fallback_enc + "(ignore)", None
    except OSError as e:
        return None, None, e if last_err is None else last_err


def _truncate_line(line, limit):
    if limit and len(line) > limit:
        return line[:limit] + " ... "
    return line

def search_string(root,patterns):
    root = os.path.abspath(root)
    match_func, regex_errors = _build_matcher(patterns, USE_REGEX, CASE_SENSITIVE)
    search_result = ''
    max_size_bytes = 300 * 1024 * 1024
    results = []
    stats = {
        "scanned": 0,
        "skipped_big": 0,
        "skipped_unreadable": 0,
        "files": 0,
        "lines": 0,
        "per_pattern": {},
    }
    for p in patterns:
        stats["per_pattern"][p] = 0

    for filepath in _iter_files(root, EXCLUDE_DIRS, EXCLUDE_EXTS, SKIP_HIDDEN, FOLLOW_SYMLINKS):
        # 文件名匹配：文件名也可作为目标字符的命中项
        filename = os.path.basename(filepath)
        name_matched = match_func(filename)

        file_hits = []
        skip_content = False
        try:
            if max_size_bytes > 0 and os.path.getsize(filepath) > max_size_bytes:
                stats["skipped_big"] += 1
                skip_content = True
        except OSError:
            stats["skipped_unreadable"] += 1
            skip_content = True

        if not skip_content:
            lines, encoding, error = _read_text_lines(filepath, ENCODINGS)
            if lines is None:
                stats["skipped_unreadable"] += 1
            else:
                stats["scanned"] += 1
                for lineno, line in enumerate(lines, start=1):
                    matched = match_func(line)
                    if matched:
                        file_hits.append((lineno, matched, _truncate_line(line.strip(), MAX_LINE_PREVIEW)))
                        stats["lines"] += 1
                        for i in matched:
                            stats["per_pattern"][patterns[i]] += 1

        # 文件名命中或内容命中，均将该文件计入统计
        if name_matched or file_hits:
            stats["files"] += 1
            for i in name_matched:
                stats["per_pattern"][patterns[i]] += 1
            results.append((filepath, name_matched, file_hits))

    if not results:
        return 'None'
    else:
        for filepath, name_matched, hits in results:
            search_result += "file:%s" % filepath
            search_result += '\n'
            if name_matched:
                search_result += "  [name] %s" % os.path.basename(filepath)
                search_result += '\n'
            for lineno, matched, text in hits:
                search_result += "  [line %d] %s" % (lineno, text)
                search_result += '\n'
    return search_result