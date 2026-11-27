# 📡 Collect-IPTV（验真增强版）

采集多个公开聚合源 → 频道分类与台标 → **两阶段验真** → 每频道保留多条备用源 → 生成
`best_sorted.m3u` / `best_sorted.m3u8`，并由 GitHub Actions 每 4 小时自动跑一轮。

本项目把两套方案的优点合在了一起：

- **采集/分类/台标/网页**来自 [Collect-IPTV](https://github.com/zilong7728/Collect-IPTV) 这一支
- **验真/保护/重试**借鉴了 juhe-stream-checker 那套两阶段探测的做法

> ⚠️ **特别说明：** 因使用 GitHub 服务器，**不保证国内网络环境下的链接速度与可用性**。
> ⚠️ **部分节目源来自互联网公开资源，上游源可能自行添加广告、弹窗、二维码或“赞助”提示。此类内容由上游节目源提供，与本项目及项目作者本人无关，本项目未主动添加、推广或收取相关赞助。**
> ⚠️ 所有频道的完整性与有效性高度依赖上游网络资源；若上游频道源大面积失效，本轮会触发保护、保留上一版列表，而不是把列表清空。

---

## 🔬 验真流程（和原版的区别）

原版只判断「HTTP 返回 200」，于是会员过期页、欢迎页、错误页这些同样返回 200 的假活源会被当成好源放进列表。现在改成两阶段：

1. **第一阶段（快）**：带 `Range` 只读首包 4KB，UA 在 Chrome / VLC / mpv 之间轮换（不少源对 `python-requests` 默认 UA 直接 403），按内容类型和扩展名判断是不是 HLS。
2. **第二阶段（下钻）**：如果是 HLS，继续往下抓一层——`master` 列表 → 子列表 → 首个分片，任何一层拿不到就判死；不是 HLS 的（flv/mp4/ts）则要求真读到数据，返回网页的判死。
3. **多源备用**：每个频道按延迟排序，保留前 `MAX_PER_CHANNEL` 条（默认 3）。一条挂了播放器可以换下一条，不会整台消失。
4. **有效率保护**：本轮有效率低于 `MIN_RATIO`（默认 5%）或有效条目少于 `MIN_ITEMS`（默认 20），**不覆盖**上一版产物，避免上游抽风把列表清空。
5. **体积上限**：单次拉取超过 `MAX_BYTES`（默认 8MB）直接放弃，源站返回巨型错误页不会拖垮任务。
6. **推送重试**：生成物提交失败会先 `fetch` + 合并远端再重推，最多 3 次；冲突时保留本次生成物。

每轮会写一份 `check-report.json`：各源抓取情况、有效/失效数、失效率、失效原因 TOP、本轮参数。Actions 里也会作为 artifact 上传。

## ⚙️ 可调参数（环境变量）

都在 `.github/workflows/iptv.yml` 的 `env:` 里，删掉也能跑（有默认值）。

| 变量 | 默认 | 说明 |
|---|---|---|
| `WORKERS` | 40 | 第一阶段并发 |
| `DEEP_WORKERS` | 30 | 下钻并发 |
| `DEEP` | 1 | 1=下钻验真，0=只验主地址（快，但假活源会多） |
| `TIMEOUT` | 10 | 单次读取超时（秒） |
| `CONNECT_TIMEOUT` | 5 | 建连超时（秒） |
| `RETRIES` | 1 | 每个地址重试次数 |
| `FAST_BYTES` | 4096 | 首包读取字节数 |
| `MAX_BYTES` | 8MB | 单次拉取体积上限 |
| `MAX_PER_CHANNEL` | 3 | 每频道保留几条源 |
| `MIN_RATIO` | 0.05 | 有效率低于此值触发保护 |
| `MIN_ITEMS` | 20 | 有效条目少于此值触发保护 |
| `PROTECT_EXIT_CODE` | 0 | 保护时是否让 CI 标红 |
| `EXTRA_SOURCES` | 空 | 追加源，逗号分隔 |

手动 Run 时也可以在 `sources` 输入框里临时追加源。

## 📺 网页

https://pengcgg.github.io/collect-iptv-fu/

网页会自动识别当前仓库，fork 之后读的是自己仓库的数据，不会串到上游。

## ⏱️ Last Run Time

<!-- Last Run Time --> 2026-11-28 07:57:10 CST

## 🔗 Generated File Link

<!-- Generated File Link M3U --> [View M3U File](https://raw.githubusercontent.com/pengcgg/collect-iptv-fu/refs/heads/main/best_sorted.m3u)

<!-- Generated File Link M3U8 --> [View M3U8 File](https://raw.githubusercontent.com/pengcgg/collect-iptv-fu/refs/heads/main/best_sorted.m3u8)

## 💡 使用说明

1. 点上方链接获取最新播放列表
2. 导入支持 IPTV 的播放器（Kodi、PotPlayer、Perfect Player、TiviMate 等）
3. 每 4 小时自动更新，建议定期重新拉取
4. 同一频道会出现多条（最多 `MAX_PER_CHANNEL` 条），按顺序是从快到慢，播不动就换下一条

## 🧪 本地自测

```bash
pip install aiohttp

# 验真器单测：好源判活、死链/网页/404 判死
python3 tests/test_probe.py

# 端到端：需要先在 tests/fixtures 起一个静态服务
cd tests/fixtures && python3 -m http.server 8765 &
cd ../.. && python3 tests/test_pipeline.py
```

---

## 📢 免责声明（个人学习测试专用）

本项目仅用于**网络协议、爬虫技术、自动化脚本开发等个人学习与测试用途**，不用于任何商业、盈利及违规用途。

- 所有节目源均来自互联网公开可访问链接，项目本身不生产、不存储、不篡改任何媒体内容。
- **本项目仅对收集到的公开链接进行整理、去重、可用性检测及延迟筛选，不对上游链接所提供的内容负责。**
- 部分上游节目源可能包含广告、弹窗、二维码、赞助信息或其他推广内容，**这些内容由对应的上游源自行提供，与本项目及项目作者本人无关。**
- **本项目及项目作者不代表、不授权、也不参与任何上游节目源所显示的赞助、捐赠、广告或其他商业活动。**
- 如上游页面或播放源出现要求扫码赞助、捐赠、付费等提示，请使用者自行判断，**项目作者不会以任何方式要求用户进行上述操作。**
- 严禁将本项目及生成的播放列表用于商业传播、二次分发、公开分享等行为。
- 所有频道版权均归原版权方所有，使用前请确保符合当地法律法规。
- 因违规使用本项目产生的任何法律责任、版权纠纷，均由使用者自行承担。

详细免责声明请参阅 [`DISCLAIMER.md`](./DISCLAIMER.md)。

---

## ⭐️ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=pengcgg/collect-iptv-fu&type=Date)](https://star-history.com/#pengcgg/collect-iptv-fu&Date)
