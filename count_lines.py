import os
from collections import defaultdict

# 需要统计的文件后缀
EXTENSIONS = {'.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp', '.html', '.css', '.md', '.json', '.txt', '.xml', '.yaml', '.yml', '.toml', '.cfg', '.ini', '.sh', '.bat', '.ps1', '.rs', '.go', '.ts', '.tsx', '.jsx', '.vue', '.svelte'}

# 跳过的目录
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', '.idea', 'dist', 'build', 'target', 'out', '.tox', '.eggs', '*.egg-info'}

def count_lines_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception:
        return 0

def count_lines(root_dir='.'):
    total_lines = 0
    total_files = 0
    lang_lines = defaultdict(int)
    lang_files = defaultdict(int)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in EXTENSIONS:
                filepath = os.path.join(dirpath, filename)
                lines = count_lines_in_file(filepath)
                total_lines += lines
                total_files += 1
                lang_lines[ext] += lines
                lang_files[ext] += 1
                print(f"{filepath}: {lines} lines")

    print("\n===== Summary =====")
    print(f"Total files: {total_files}")
    print(f"Total lines: {total_lines}\n")

    if total_lines == 0:
        return

    print("Language breakdown (by lines):")
    sorted_langs = sorted(lang_lines.items(), key=lambda x: x[1], reverse=True)
    for ext, lines in sorted_langs:
        files = lang_files[ext]
        percent = (lines / total_lines) * 100
        print(f"  {ext}: {lines} lines ({files} files), {percent:.2f}%")

if __name__ == '__main__':
    count_lines()
