import cv2, os, random

VIDEO = r"D:\git\SynapseAgent\1e689989a8bbbca9ae47eff063cab8d7.mp4"
OUT_DIR = os.path.dirname(VIDEO)
N = 5

cap = cv2.VideoCapture(VIDEO)
if not cap.isOpened():
    raise SystemExit(f"无法打开视频: {VIDEO}")

total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
dur = total / fps if fps else 0
print(f"总帧数={total}, fps={fps:.3f}, 分辨率={w}x{h}, 时长={dur:.2f}s")

if total < N:
    raise SystemExit("帧数不足 5 帧")

idxs = sorted(random.sample(range(total), N))
print("随机帧号:", idxs)

saved = []
for i, idx in enumerate(idxs, 1):
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, frame = cap.read()
    if not ok:
        print(f"  第{idx}帧读取失败，跳过")
        continue
    t = idx / fps if fps else 0
    name = f"frame_{i}_idx{idx}_t{t:.2f}s.png"
    path = os.path.join(OUT_DIR, name)
    cv2.imwrite(path, frame)
    saved.append(path)
    print("已保存:", path)

cap.release()
print(f"完成，共保存 {len(saved)} 帧")