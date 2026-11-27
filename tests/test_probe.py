"""验真器自测：用几个确定好/确定坏的地址，检查判定是否符合预期。

跑法：python3 tests/test_probe.py
"""
import asyncio
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

spec = importlib.util.spec_from_file_location(
    "iptv", os.path.join(ROOT, ".github", "workflows", "iptv.py")
)
iptv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iptv)
aiohttp = iptv.aiohttp

CASES = [
    # (地址, 期望状态, 说明)
    (
        "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8",
        "ok",
        "真实 HLS(master 多码率)",
    ),
    (
        "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "ok",
        "真实 HLS(media 列表)",
    ),
    ("https://raw.githubusercontent.com/pengcgg/backup-repo/main/README.md", "dead", "网页不是流"),
    ("https://raw.githubusercontent.com/pengcgg/backup-repo/main/nope-404.m3u", "dead", "404"),
    ("http://127.0.0.1:9/live.m3u8", "dead", "连不上"),
    ("rtmp://example.com/live/stream", "skip", "非 http 协议"),
]


async def run():
    sem = asyncio.Semaphore(8)
    connector = aiohttp.TCPConnector(limit=16, ssl=iptv._SSL_CTX)
    timeout = iptv.make_timeout(iptv.PROBE["sec_cap"])
    fails = 0
    async with aiohttp.ClientSession(cookie_jar=None, timeout=timeout, connector=connector, trust_env=True) as s:
        for url, expect, label in CASES:
            status, latency, reason = await iptv.test_stream(s, sem, url)
            ok = status == expect
            if not ok:
                fails += 1
            lat = "%.2fs" % latency if latency is not None else "-"
            print("[%s] %-8s 期望=%-5s 实际=%-5s 延迟=%-6s 原因=%s  (%s)"
                  % ("PASS" if ok else "FAIL", label, expect, status, lat, reason, url))
    print("\nRESULT:", "ALL PASS" if fails == 0 else "%d FAILED" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
