"""端到端自测：本地源 -> 抓取 -> 去重 -> 验真 -> 多源选优 -> 输出 m3u

跑法：
  1) 在 tests/fixtures 起一个静态服务（python3 -m http.server 8765）
  2) python3 tests/test_pipeline.py
"""
import asyncio
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# 测试用小阈值：否则 MIN_ITEMS=20 会让 5 条样本直接触发保护
os.environ.setdefault("MIN_ITEMS", "1")
os.environ.setdefault("MIN_RATIO", "0.01")
os.environ.setdefault("MAX_PER_CHANNEL", "2")
os.environ.setdefault("REPORT", "check-report.test.json")

spec = importlib.util.spec_from_file_location(
    "iptv", os.path.join(ROOT, ".github", "workflows", "iptv.py")
)
iptv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iptv)

SRC = "http://127.0.0.1:8765/list.txt"
CCTV_FILE = ".github/workflows/IPTV/CCTV.txt"
PROVINCE_FILES = [
    ".github/workflows/IPTV/浙江频道.txt",
]


def parse_m3u(path):
    entries = []
    name = None
    group = None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("#EXTINF:"):
            name = line.split(",", 1)[-1]
            group = "未分组"
            for part in line.split(",")[0].split():
                if part.startswith("group-title="):
                    group = part.split("=", 1)[1].strip('"')
        elif line.startswith("http"):
            entries.append((name, group, line))
    return entries


async def run():
    fails = 0

    # --- 正常路径 ---
    code = await iptv.main([SRC], CCTV_FILE, PROVINCE_FILES)
    out = "best_sorted.m3u"
    if code != 0:
        print("FAIL: 退出码应为 0，实际", code)
        fails += 1
    if not os.path.exists(out):
        print("FAIL: 没有生成输出文件")
        return 1

    entries = parse_m3u(out)
    names = [e[0] for e in entries]

    # 每频道最多 2 条（fixture 里频道A 有 3 条，其中 1 条死的）
    a_count = names.count("测试频道A")
    expect_a = iptv.PROBE["max_per_channel"] if iptv.PROBE["max_per_channel"] <= 2 else 2
    if a_count != expect_a:
        print("FAIL: 测试频道A 应有 %d 条，实际 %d" % (expect_a, a_count))
        fails += 1
    else:
        print("PASS: 多源备用生效，测试频道A = %d 条" % a_count)

    # 死链必须被剔除
    if any("127.0.0.1:9" in e[2] for e in entries):
        print("FAIL: 死链没有被剔除")
        fails += 1
    else:
        print("PASS: 死链已剔除")

    # CCTV1 归到央视频道
    cctv = [e for e in entries if e[0] == "CCTV1"]
    if not cctv or cctv[0][1] != "央视频道":
        print("FAIL: CCTV1 分类错误 ->", cctv)
        fails += 1
    else:
        print("PASS: CCTV1 归入央视频道")

    # 浙江钱江 归到浙江
    zj = [e for e in entries if e[0] == "浙江钱江"]
    if not zj or not zj[0][1].startswith("浙江"):
        print("FAIL: 浙江钱江 分类错误 ->", zj)
        fails += 1
    else:
        print("PASS: 浙江钱江 归入浙江")

    # 台标字段存在
    if "tvg-logo=" not in open(out, encoding="utf-8").read():
        print("FAIL: 缺少 tvg-logo")
        fails += 1
    else:
        print("PASS: 台标字段保留")

    # --- 保护路径：全部死链时不该覆盖旧文件 ---
    before = open(out, encoding="utf-8").read()
    bad_src = "http://127.0.0.1:8765/all-dead.txt"
    code = await iptv.main([bad_src], CCTV_FILE, PROVINCE_FILES)
    after = open(out, encoding="utf-8").read()
    if code != iptv.PROBE["protect_exit_code"]:
        print("FAIL: 保护时退出码应为 %d，实际 %d" % (iptv.PROBE["protect_exit_code"], code))
        fails += 1
    elif before != after:
        print("FAIL: 触发保护时旧产物被覆盖了")
        fails += 1
    else:
        print("PASS: 触发保护时保留旧产物、CI 不标红")

    print("\nRESULT:", "ALL PASS" if fails == 0 else "%d FAILED" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
