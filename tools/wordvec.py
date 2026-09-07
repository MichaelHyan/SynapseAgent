import numpy as np
import json

VECTOR_PATH = "database/vector.txt"
VECTOR_BINARY = False

def load_wv(path, binary=False):
    """加载词向量，返回 (word2idx, vectors)。"""
    if binary:
        return _load_binary(path)
    return _load_text(path)


def _load_text(path):
    """加载 word2vec 文本格式。"""
    word2idx = {}
    with open(path, "r", encoding="utf-8") as f:
        first = f.readline().strip().split()
        vocab_size, dim = int(first[0]), int(first[1])
        vectors = np.zeros((vocab_size, dim), dtype=np.float32)
        idx = 0
        for line in f:
            parts = line.split()
            if len(parts) < dim + 1:
                continue
            word = parts[0]
            vectors[idx] = np.array(parts[1:1 + dim], dtype=np.float32)
            word2idx[word] = idx
            idx += 1
    return word2idx, vectors[:idx]


def _load_binary(path):
    """加载 word2vec 二进制格式。"""
    word2idx = {}
    with open(path, "rb") as f:
        first = f.readline().decode("utf-8").strip().split()
        vocab_size, dim = int(first[0]), int(first[1])
        vectors = np.zeros((vocab_size, dim), dtype=np.float32)
        for idx in range(vocab_size):
            word_bytes = b""
            while True:
                ch = f.read(1)
                if ch == b" " or ch == b"":
                    break
                word_bytes += ch
            word = word_bytes.decode("utf-8", errors="ignore")
            vec = np.fromfile(f, dtype=np.float32, count=dim)
            if vec.shape[0] != dim:
                break
            vectors[idx] = vec
            word2idx[word] = idx
    return word2idx, vectors[:idx]


def cosine_sim(a, b):
    """单对向量的余弦相似度（备用）。"""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def edit_distance(a, b):
    """计算两个字符串的编辑距离。"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            insert = curr[j - 1] + 1
            delete = prev[j] + 1
            replace = prev[j - 1] + (ca != cb)
            curr.append(min(insert, delete, replace))
        prev = curr
    return prev[-1]


def get_word_vector(wv, word):
    """获取词向量；整词不存在时直接遍历词库，按编辑距离找最相近的词。"""
    word2idx, vectors = wv
    if word in word2idx:
        return vectors[word2idx[word]]

    if not word2idx:
        return None

    best_word = None
    best_dist = None
    for vocab_word in word2idx:
        dist = edit_distance(word, vocab_word)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_word = vocab_word

    if best_word is not None:
        return vectors[word2idx[best_word]]
    return None


def match(target_word,candidate_words,matchs=1):
    global wv
    target_vector = get_word_vector(wv, target_word)

    valid_words = []
    cand_vectors = []
    for cand in candidate_words:
        cand_vector = get_word_vector(wv, cand)
        valid_words.append(cand)
        cand_vectors.append(cand_vector)

    target_vector = np.asarray(target_vector, dtype=np.float32)
    target_norm = target_vector / np.linalg.norm(target_vector)

    cand_matrix = np.stack(cand_vectors).astype(np.float32)
    cand_norms = np.linalg.norm(cand_matrix, axis=1)
    denom = cand_norms * np.linalg.norm(target_vector)
    scores = np.zeros(len(valid_words), dtype=np.float32)
    mask = denom > 0
    scores[mask] = (cand_matrix[mask] @ target_norm) / cand_norms[mask]

    results = sorted(zip(valid_words, scores), key=lambda x: x[1], reverse=True)
    best_words = results[:matchs]
    result = []
    for i in best_words:
        result.append(i[0])
    return result

def target(target):
    with open('database/mem.json','r',encoding='utf-8') as f:
        dat = json.load(f)
        candidate_words = []
        for k,v in dat.items():
            candidate_words.append(k)
    result = []
    for word in target:
        compare = match(word,candidate_words)
        for c in compare:
            if c not in result:
                result.append(c)
    return result

wv = load_wv(VECTOR_PATH, VECTOR_BINARY)