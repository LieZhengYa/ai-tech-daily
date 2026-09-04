from __future__ import annotations

import argparse
import base64
import datetime as dt
import email.utils
import hashlib
import hmac
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "sources.json"
PUBLIC_DIR = ROOT / "public"
TZ = dt.timezone(dt.timedelta(hours=8), name="Asia/Shanghai")
DEFAULT_MAX_ITEMS = int(os.getenv("MAX_ITEMS", "10"))


KEYWORD_WEIGHTS = {
    "大模型": 8,
    "基础模型": 7,
    "生成式 ai": 7,
    "生成式人工智能": 7,
    "人工智能": 4,
    "智能体": 7,
    "多模态": 7,
    "推理模型": 7,
    "开源模型": 7,
    "机器人": 5,
    "芯片": 5,
    "算力": 5,
    "自动驾驶": 5,
    "ar": 3,
    "vr": 3,
    "llm": 8,
    "large language model": 8,
    "foundation model": 7,
    "generative ai": 7,
    "agent": 6,
    "multimodal": 6,
    "reasoning model": 6,
    "open source model": 6,
    "robot": 5,
    "robotics": 5,
    "chip": 5,
    "gpu": 5,
    "accelerator": 4,
    "autonomous driving": 5,
    "self-driving": 5,
    "openai": 4,
    "anthropic": 4,
    "deepmind": 4,
    "hugging face": 4,
    "nvidia": 4,
    "meta ai": 4,
    "google ai": 4,
}


TAGS = [
    ("大模型", ["大模型", "llm", "large language model", "foundation model", "gpt", "claude"]),
    ("AI Agent", ["agent", "智能体", "代理"]),
    ("多模态", ["多模态", "multimodal", "vision-language", "video model"]),
    ("开源模型", ["开源", "open source", "hugging face"]),
    ("AI Infra", ["infra", "infrastructure", "算力", "gpu", "chip", "nvidia"]),
    ("机器人", ["机器人", "robot", "robotics"]),
    ("自动驾驶", ["自动驾驶", "autonomous driving", "self-driving"]),
    ("AR/VR", ["ar", "vr", "mixed reality", "spatial"]),
    ("行业动态", ["funding", "startup", "regulation", "policy", "融资", "监管"]),
]


SAMPLE_ITEMS = [
    {
        "title": "OpenAI releases a new model update for enterprise AI workflows",
        "summary": "OpenAI 发布面向企业工作流的模型更新，重点提升工具调用、长上下文处理和复杂任务执行稳定性。",
        "source": "Sample Source",
        "url": "https://example.com/openai-model-update",
        "published_at": "2026-09-02T09:00:00+08:00",
        "score": 99,
        "tag": "大模型",
    },
    {
        "title": "国产开源大模型社区发布新一代 MoE 架构模型",
        "summary": "国内开源社区发布新一代 MoE 模型，强调推理成本控制、多语言能力和商用友好许可证。",
        "source": "Sample Source",
        "url": "https://example.com/china-open-model",
        "published_at": "2026-09-02T10:10:00+08:00",
        "score": 95,
        "tag": "开源模型",
    },
    {
        "title": "NVIDIA details next-generation AI inference chip roadmap",
        "summary": "NVIDIA 透露下一代 AI 推理芯片路线图，围绕低延迟、多模态推理和数据中心能耗优化展开。",
        "source": "Sample Source",
        "url": "https://example.com/nvidia-inference-chip",
        "published_at": "2026-09-02T11:30:00+08:00",
        "score": 92,
        "tag": "AI Infra",
    },
    {
        "title": "Google DeepMind showcases multimodal reasoning benchmark results",
        "summary": "Google DeepMind 展示多模态推理评测进展，关注图像、视频、文本混合任务中的可解释解题能力。",
        "source": "Sample Source",
        "url": "https://example.com/deepmind-multimodal",
        "published_at": "2026-09-02T12:40:00+08:00",
        "score": 90,
        "tag": "多模态",
    },
    {
        "title": "AI agent startup raises new funding for browser automation platform",
        "summary": "一家 AI Agent 初创公司完成新融资，产品聚焦浏览器自动化、企业知识库连接和跨应用任务执行。",
        "source": "Sample Source",
        "url": "https://example.com/agent-startup-funding",
        "published_at": "2026-09-02T13:00:00+08:00",
        "score": 86,
        "tag": "AI Agent",
    },
    {
        "title": "机器人公司发布面向仓储场景的通用操作模型",
        "summary": "机器人公司发布仓储操作模型，用视觉语言模型连接抓取、路径规划和异常处理能力。",
        "source": "Sample Source",
        "url": "https://example.com/robotics-vla",
        "published_at": "2026-09-02T14:20:00+08:00",
        "score": 84,
        "tag": "机器人",
    },
    {
        "title": "Autonomous driving company adds vision-language planner to fleet testing",
        "summary": "自动驾驶公司在车队测试中引入视觉语言规划器，用于复杂路口解释、长尾场景分析和安全复盘。",
        "source": "Sample Source",
        "url": "https://example.com/autonomous-vlm-planner",
        "published_at": "2026-09-02T15:40:00+08:00",
        "score": 81,
        "tag": "自动驾驶",
    },
    {
        "title": "AR glasses maker integrates on-device AI assistant",
        "summary": "AR 眼镜厂商集成本地 AI 助手，支持实时翻译、场景识别和低功耗语音交互。",
        "source": "Sample Source",
        "url": "https://example.com/ar-ai-assistant",
        "published_at": "2026-09-02T16:30:00+08:00",
        "score": 76,
        "tag": "AR/VR",
    },
    {
        "title": "Hugging Face community trends point to smaller reasoning models",
        "summary": "Hugging Face 社区趋势显示，小型推理模型和端侧部署工具链成为开发者关注重点。",
        "source": "Sample Source",
        "url": "https://example.com/hf-small-reasoning-models",
        "published_at": "2026-09-02T18:00:00+08:00",
        "score": 74,
        "tag": "大模型",
    },
    {
        "title": "AI regulation update focuses on model transparency and safety testing",
        "summary": "最新 AI 监管动向聚焦模型透明度、安全评测和高风险应用审计，对企业部署流程影响较大。",
        "source": "Sample Source",
        "url": "https://example.com/ai-regulation-safety",
        "published_at": "2026-09-02T19:00:00+08:00",
        "score": 72,
        "tag": "行业动态",
    },
]


def log(message: str) -> None:
    print(message, file=sys.stderr)


def now_local() -> dt.datetime:
    return dt.datetime.now(TZ)


def parse_report_date(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return now_local().date()


def cover_window(report_date: dt.date) -> tuple[dt.datetime, dt.datetime]:
    start = dt.datetime.combine(report_date - dt.timedelta(days=1), dt.time.min, tzinfo=TZ)
    end = dt.datetime.combine(report_date, dt.time.min, tzinfo=TZ)
    return start, end


def load_sources() -> list[dict[str, Any]]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def fetch_text(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AI-Tech-Daily/1.0; +https://github.com/LieZhengYa/ai-tech-daily)"
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        charset = "utf-8"
        match = re.search(r"charset=([^;\s]+)", content_type, re.I)
        if match:
            charset = match.group(1).strip('"')
        return response.read().decode(charset, errors="replace")


def tag_name(raw_tag: str) -> str:
    if "}" in raw_tag:
        return raw_tag.rsplit("}", 1)[1].lower()
    return raw_tag.lower()


def first_child_text(element: ET.Element, names: set[str]) -> str:
    for child in list(element):
        if tag_name(child.tag) in names:
            return "".join(child.itertext()).strip()
    return ""


def first_atom_link(element: ET.Element) -> str:
    for child in list(element):
        if tag_name(child.tag) == "link":
            href = child.attrib.get("href", "").strip()
            rel = child.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                return href
    for child in list(element):
        if tag_name(child.tag) == "link":
            return child.attrib.get("href", "").strip() or "".join(child.itertext()).strip()
    return ""


def parse_datetime(value: str) -> dt.datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(TZ)


def strip_html(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_feed(xml_text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    root_tag = tag_name(root.tag)
    entries: list[ET.Element]
    is_atom = root_tag == "feed"
    if is_atom:
        entries = [child for child in list(root) if tag_name(child.tag) == "entry"]
    else:
        entries = root.findall(".//item")

    articles: list[dict[str, Any]] = []
    for entry in entries:
        title = first_child_text(entry, {"title"})
        link = first_atom_link(entry) if is_atom else first_child_text(entry, {"link"})
        summary = first_child_text(entry, {"summary", "description", "content", "encoded"})
        published_raw = first_child_text(entry, {"published", "updated", "pubdate", "date"})
        published_at = parse_datetime(published_raw)
        if not title or not link:
            continue
        articles.append(
            {
                "title": strip_html(title),
                "summary": strip_html(summary),
                "url": link.strip(),
                "source": source["name"],
                "source_language": source.get("language", ""),
                "source_weight": int(source.get("weight", 1)),
                "source_tags": source.get("tags", []),
                "published_at": published_at.isoformat() if published_at else "",
            }
        )
    return articles


def keyword_score(text: str) -> int:
    lowered = text.lower()
    score = 0
    for keyword, weight in KEYWORD_WEIGHTS.items():
        key = keyword.lower()
        if re.fullmatch(r"[a-z0-9]{1,3}", key):
            if re.search(rf"\b{re.escape(key)}\b", lowered):
                score += weight
        elif key in lowered:
            score += weight
    return score


def infer_tag(text: str) -> str:
    lowered = text.lower()
    for tag, keywords in TAGS:
        for keyword in keywords:
            key = keyword.lower()
            if re.fullmatch(r"[a-z0-9]{1,3}", key):
                if re.search(rf"\b{re.escape(key)}\b", lowered):
                    return tag
            elif key in lowered:
                return tag
    return "AI 科技"


def normalize_title(title: str) -> str:
    return re.sub(r"[\W_]+", "", title.lower())


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), "", ""))


def collect_candidates(report_date: dt.date) -> list[dict[str, Any]]:
    start, end = cover_window(report_date)
    sources = load_sources()
    by_key: dict[str, dict[str, Any]] = {}

    log(f"Collecting news from {len(sources)} sources for {start.date()}...")
    for source in sources:
        try:
            feed_text = fetch_text(source["url"])
            articles = parse_feed(feed_text, source)
            log(f"  {source['name']}: {len(articles)} articles")
        except Exception as exc:
            log(f"  {source['name']}: skipped ({exc})")
            continue

        for article in articles:
            published = parse_datetime(article.get("published_at", ""))
            if published and not (start <= published < end):
                continue
            search_text = " ".join(
                [
                    article.get("title", ""),
                    article.get("summary", ""),
                    article.get("source", ""),
                    " ".join(article.get("source_tags", [])),
                ]
            )
            score = keyword_score(search_text) + int(article.get("source_weight", 1))
            if score <= 2:
                continue
            article["score"] = score
            article["tag"] = infer_tag(search_text)

            key = normalize_url(article["url"]) or normalize_title(article["title"])
            title_key = normalize_title(article["title"])
            existing = by_key.get(key) or by_key.get(title_key)
            if not existing or article["score"] > existing.get("score", 0):
                by_key[key] = article
                by_key[title_key] = article

    unique = list({id(article): article for article in by_key.values()}.values())
    unique.sort(key=lambda item: (item.get("score", 0), item.get("published_at", "")), reverse=True)
    log(f"Collected {len(unique)} relevant candidates.")
    return unique


def likely_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def fallback_items(candidates: list[dict[str, Any]], max_items: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, article in enumerate(candidates[:max_items], start=1):
        title = article.get("title", "").strip()
        summary = article.get("summary", "").strip()
        short_summary = summary[:140] if summary else "该条资讯与 AI / 大模型科技相关，建议查看原文获取完整细节。"
        items.append(
            {
                "rank": index,
                "zh_title": title if likely_chinese(title) else title,
                "en_title": title if not likely_chinese(title) else "",
                "summary_zh": short_summary,
                "tag": article.get("tag") or infer_tag(title + " " + summary),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "published_at": article.get("published_at", ""),
                "importance": int(article.get("score", 0)),
            }
        )
    return items


def llm_endpoint() -> str:
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def call_llm(candidates: list[dict[str, Any]], max_items: int) -> list[dict[str, Any]] | None:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "deepseek-chat").strip()
    if not api_key:
        log("LLM_API_KEY is not set. Using fallback summaries.")
        return None

    compact_candidates = []
    for index, article in enumerate(candidates[:40], start=1):
        compact_candidates.append(
            {
                "id": index,
                "title": article.get("title", ""),
                "summary": article.get("summary", "")[:500],
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "published_at": article.get("published_at", ""),
                "score": article.get("score", 0),
                "tag_hint": article.get("tag", ""),
            }
        )

    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是严谨的科技日报编辑。只基于用户提供的候选新闻筛选，不编造链接、来源和事实。"
                    "输出必须是 JSON，不要包含 Markdown。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": (
                            f"从候选新闻里选出最值得关注的 {max_items} 条 AI / 大模型 / Agent / 多模态 / 机器人 / "
                            "芯片算力 / 自动驾驶 / ARVR 相关新闻。保留英文标题，补充中文标题。"
                            "每条摘要用 40 到 80 个中文字符，突出为什么重要。"
                        ),
                        "output_schema": {
                            "items": [
                                {
                                    "id": "候选新闻 id",
                                    "zh_title": "中文标题",
                                    "en_title": "英文标题，若原文为中文则翻译成英文",
                                    "summary_zh": "中文摘要",
                                    "tag": "大模型/AI Agent/多模态/开源模型/AI Infra/机器人/自动驾驶/AR/VR/行业动态",
                                    "importance": "1-100 整数",
                                }
                            ]
                        },
                        "candidates": compact_candidates,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }

    request = urllib.request.Request(
        llm_endpoint(),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(extract_json(content))
    except Exception as exc:
        log(f"LLM call failed. Using fallback summaries. ({exc})")
        return None

    articles_by_id = {index: article for index, article in enumerate(candidates[:40], start=1)}
    items: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for raw_item in parsed.get("items", []):
        try:
            candidate_id = int(raw_item.get("id"))
        except (TypeError, ValueError):
            continue
        if candidate_id in seen_ids or candidate_id not in articles_by_id:
            continue
        seen_ids.add(candidate_id)
        article = articles_by_id[candidate_id]
        items.append(
            {
                "rank": len(items) + 1,
                "zh_title": str(raw_item.get("zh_title") or article.get("title") or "").strip(),
                "en_title": str(raw_item.get("en_title") or article.get("title") or "").strip(),
                "summary_zh": str(raw_item.get("summary_zh") or article.get("summary") or "").strip(),
                "tag": str(raw_item.get("tag") or article.get("tag") or "AI 科技").strip(),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "published_at": article.get("published_at", ""),
                "importance": safe_int(raw_item.get("importance"), int(article.get("score", 0))),
            }
        )
        if len(items) >= max_items:
            break
    return items if items else None


def extract_json(value: str) -> str:
    value = value.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?", "", value, flags=re.I).strip()
        value = re.sub(r"```$", "", value).strip()
    start = value.find("{")
    end = value.rfind("}")
    if start >= 0 and end >= start:
        return value[start : end + 1]
    return value


def safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_report(report_date: dt.date, sample: bool, max_items: int) -> dict[str, Any]:
    if sample:
        candidates = SAMPLE_ITEMS
    else:
        candidates = collect_candidates(report_date)
    if not candidates:
        log("No candidates found. Falling back to sample data so the pipeline still produces a visible report.")
        candidates = SAMPLE_ITEMS

    items = None if sample else call_llm(candidates, max_items)
    if items is None:
        items = fallback_items(candidates, max_items)

    for index, item in enumerate(items, start=1):
        item["rank"] = index

    start, end = cover_window(report_date)
    return {
        "report_date": report_date.isoformat(),
        "cover_date": start.date().isoformat(),
        "cover_window": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timezone": "Asia/Shanghai",
        },
        "generated_at": now_local().isoformat(),
        "sample": sample,
        "candidate_count": len(candidates),
        "items": items,
        "paths": {
            "poster": f"daily/{report_date.isoformat()}/poster.png",
            "html": f"daily/{report_date.isoformat()}/index.html",
            "json": f"daily/{report_date.isoformat()}/report.json",
        },
    }


def font_candidates(kind: str) -> list[str]:
    if kind == "bold":
        return [
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    return [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]


def load_font(size: int, kind: str = "regular") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in font_candidates(kind):
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if text_width(draw, text, font) <= max_width:
        return text
    suffix = "..."
    while text and text_width(draw, text + suffix, font) > max_width:
        text = text[:-1]
    return text + suffix if text else suffix


def wrap_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current.strip())
            current = char
            if len(lines) == max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current.strip())
    if len(lines) == max_lines and text_width(draw, "".join(lines), font) < text_width(draw, text, font):
        lines[-1] = fit_text(draw, lines[-1], font, max_width)
    if len(lines) > 1 and re.fullmatch(r"[，。！？,.!?;；:：、]+", lines[-1]):
        candidate = lines[-2] + lines[-1]
        if text_width(draw, candidate, font) <= max_width:
            lines[-2] = candidate
        else:
            lines[-1] = ""
    return lines[:max_lines]


def draw_gradient_background(image: Image.Image) -> None:
    width, height = image.size
    pixels = image.load()
    for y in range(height):
        ratio = y / max(height - 1, 1)
        base = (
            int(18 + 10 * ratio),
            int(20 + 7 * ratio),
            int(24 + 5 * ratio),
        )
        for x in range(width):
            warm = int(10 * x / width)
            pixels[x, y] = (base[0] + warm, base[1] + int(warm / 2), base[2])


def draw_poster(report: dict[str, Any], out_path: Path) -> None:
    width, height = 1080, 1920
    image = Image.new("RGB", (width, height), "#111318")
    draw_gradient_background(image)
    draw = ImageDraw.Draw(image)

    title_font = load_font(58, "bold")
    subtitle_font = load_font(25)
    meta_font = load_font(21)
    rank_font = load_font(36, "bold")
    zh_font = load_font(27, "bold")
    en_font = load_font(18)
    summary_font = load_font(20)
    tag_font = load_font(18, "bold")
    footer_font = load_font(18)

    draw.rectangle((0, 0, width, 16), fill="#46d9b6")
    draw.rectangle((0, 16, width, 24), fill="#ffbf69")
    draw.text((62, 58), "大模型科技日报", font=title_font, fill="#f7f7f2")
    draw.text((66, 130), "AI / Agent / Robotics / Chips / Mobility / ARVR", font=subtitle_font, fill="#c6c8ce")

    cover_date = report.get("cover_date", "")
    report_date = report.get("report_date", "")
    meta = f"推送日 {report_date} | 覆盖昨日 {cover_date} | Top {len(report.get('items', []))}"
    if report.get("sample"):
        meta += " | SAMPLE"
    draw.rounded_rectangle((62, 164, 1018, 213), radius=18, fill="#20242c", outline="#343946", width=1)
    draw.text((86, 176), meta, font=meta_font, fill="#e3e3db")

    palette = ["#46d9b6", "#ffbf69", "#e76fbc", "#8ecae6", "#f28482"]
    top = 242
    card_h = 150
    gap = 12
    for idx, item in enumerate(report.get("items", [])[:10]):
        y = top + idx * (card_h + gap)
        accent = palette[idx % len(palette)]
        draw.rounded_rectangle((50, y, 1030, y + card_h), radius=22, fill="#191c22", outline="#30343d", width=1)
        draw.rounded_rectangle((50, y, 66, y + card_h), radius=8, fill=accent)
        draw.text((88, y + 48), f"{idx + 1:02d}", font=rank_font, fill=accent)

        tag = fit_text(draw, str(item.get("tag", "AI 科技")), tag_font, 150)
        tag_w = text_width(draw, tag, tag_font) + 32
        draw.rounded_rectangle((850, y + 18, 850 + tag_w, y + 50), radius=16, fill="#272b34", outline=accent, width=1)
        draw.text((866, y + 22), tag, font=tag_font, fill=accent)

        x = 154
        max_text_w = 670
        zh_title = fit_text(draw, str(item.get("zh_title", "")), zh_font, max_text_w)
        en_title = fit_text(draw, str(item.get("en_title", "")), en_font, max_text_w)
        summary = wrap_lines(draw, str(item.get("summary_zh", "")), summary_font, 810, 2)
        source = fit_text(draw, f"{item.get('source', '')}", footer_font, 250)

        draw.text((x, y + 16), zh_title, font=zh_font, fill="#f5f4ef")
        if en_title and en_title != zh_title:
            draw.text((x, y + 52), en_title, font=en_font, fill="#aeb4bf")
        for line_index, line in enumerate(summary):
            draw.text((x, y + 80 + line_index * 26), line, font=summary_font, fill="#d7d7d2")
        draw.text((850, y + 108), source, font=footer_font, fill="#9299a6")

    footer = "Generated automatically from public web sources. Links are available on the web report."
    draw.text((62, 1878), fit_text(draw, footer, footer_font, 956), font=footer_font, fill="#888e98")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, quality=95)


def html_page(report: dict[str, Any]) -> str:
    items_html = []
    for item in report.get("items", []):
        url = html.escape(str(item.get("url", "")))
        zh_title = html.escape(str(item.get("zh_title", "")))
        en_title = html.escape(str(item.get("en_title", "")))
        summary = html.escape(str(item.get("summary_zh", "")))
        source = html.escape(str(item.get("source", "")))
        tag = html.escape(str(item.get("tag", "")))
        items_html.append(
            f"""
            <article class="item">
              <div class="rank">{int(item.get("rank", 0)):02d}</div>
              <div class="content">
                <div class="tag">{tag}</div>
                <h2>{zh_title}</h2>
                <p class="en">{en_title}</p>
                <p>{summary}</p>
                <a href="{url}" target="_blank" rel="noopener noreferrer">{source} - 原文链接</a>
              </div>
            </article>
            """
        )
    sample_note = "<p class=\"sample\">当前页面使用样例数据。</p>" if report.get("sample") else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>大模型科技日报 {html.escape(report.get("report_date", ""))}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #111318;
      --panel: #191c22;
      --text: #f5f4ef;
      --muted: #aeb4bf;
      --line: #30343d;
      --green: #46d9b6;
      --amber: #ffbf69;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.65;
    }}
    main {{
      width: min(960px, calc(100% - 32px));
      margin: 0 auto;
      padding: 40px 0 72px;
    }}
    header {{
      border-top: 10px solid var(--green);
      padding-top: 28px;
      margin-bottom: 28px;
    }}
    h1 {{ margin: 0 0 8px; font-size: clamp(32px, 5vw, 56px); }}
    .meta, .en, .sample {{ color: var(--muted); }}
    .poster {{
      display: block;
      width: min(420px, 100%);
      border: 1px solid var(--line);
      margin: 24px 0 36px;
    }}
    .item {{
      display: grid;
      grid-template-columns: 64px 1fr;
      gap: 18px;
      padding: 22px 0;
      border-top: 1px solid var(--line);
    }}
    .rank {{ color: var(--green); font-size: 30px; font-weight: 800; }}
    .tag {{
      display: inline-block;
      color: var(--amber);
      border: 1px solid rgba(255, 191, 105, .45);
      padding: 2px 10px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
    }}
    h2 {{ margin: 10px 0 4px; font-size: 22px; line-height: 1.35; }}
    p {{ margin: 8px 0; }}
    a {{ color: var(--green); }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>大模型科技日报</h1>
      <div class="meta">推送日 {html.escape(report.get("report_date", ""))} / 覆盖昨日 {html.escape(report.get("cover_date", ""))}</div>
      {sample_note}
    </header>
    <img class="poster" src="./poster.png" alt="大模型科技日报海报">
    {''.join(items_html)}
  </main>
</body>
</html>
"""


def index_page(report: dict[str, Any]) -> str:
    date_slug = html.escape(report["report_date"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Tech Daily</title>
  <style>
    body {{ margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #111318; color: #f5f4ef; }}
    main {{ width: min(860px, calc(100% - 32px)); margin: 0 auto; padding: 56px 0; }}
    a {{ color: #46d9b6; }}
  </style>
</head>
<body>
  <main>
    <h1>AI Tech Daily</h1>
    <p>Latest briefing: <a href="./daily/{date_slug}/">大模型科技日报 {date_slug}</a></p>
  </main>
</body>
</html>
"""


def write_report(report: dict[str, Any]) -> None:
    date_slug = report["report_date"]
    out_dir = PUBLIC_DIR / "daily" / date_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    report["paths"] = {
        "poster": f"daily/{date_slug}/poster.png",
        "html": f"daily/{date_slug}/index.html",
        "json": f"daily/{date_slug}/report.json",
    }
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "index.html").write_text(html_page(report), encoding="utf-8")
    (PUBLIC_DIR / "index.html").write_text(index_page(report), encoding="utf-8")
    draw_poster(report, out_dir / "poster.png")
    log(f"Wrote report to {out_dir}")


def load_report(report_date: dt.date) -> dict[str, Any]:
    path = PUBLIC_DIR / "daily" / report_date.isoformat() / "report.json"
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def public_url(relative_path: str) -> str:
    base = os.getenv("PUBLIC_BASE_URL", "").strip()
    if not base:
        repository = os.getenv("GITHUB_REPOSITORY", "").strip()
        if repository and "/" in repository:
            owner, repo = repository.split("/", 1)
            base = f"https://{owner}.github.io/{repo}/"
    if not base:
        raise RuntimeError("PUBLIC_BASE_URL is required before sending DingTalk image links.")
    return urllib.parse.urljoin(base.rstrip("/") + "/", relative_path)


def signed_dingtalk_url(webhook: str, secret: str) -> str:
    if not secret:
        return webhook
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), string_to_sign, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(digest).decode("utf-8"))
    separator = "&" if "?" in webhook else "?"
    return f"{webhook}{separator}timestamp={timestamp}&sign={sign}"


def send_dingtalk(report: dict[str, Any]) -> None:
    webhook = os.getenv("DINGTALK_WEBHOOK", "").strip()
    secret = os.getenv("DINGTALK_SECRET", "").strip()
    if not webhook:
        raise RuntimeError("DINGTALK_WEBHOOK is not set.")

    poster_url = public_url(report["paths"]["poster"])
    html_url = public_url(report["paths"]["html"])
    lines = [
        f"## 大模型科技日报 | {report['report_date']}",
        "",
        f"> 覆盖昨日 {report['cover_date']}，精选 {len(report.get('items', []))} 条 AI 科技要闻。",
        "",
        f"![日报海报]({poster_url})",
        "",
        f"[查看网页版日报]({html_url})",
        "",
        "### 今日要闻",
    ]
    for item in report.get("items", [])[:10]:
        title = item.get("zh_title") or item.get("en_title") or "Untitled"
        url = item.get("url", "")
        tag = item.get("tag", "AI 科技")
        lines.append(f"{int(item.get('rank', 0))}. [{title}]({url}) - {tag}")

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"大模型科技日报 {report['report_date']}",
            "text": "\n".join(lines),
        },
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        signed_dingtalk_url(webhook, secret),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8", errors="replace"))
    if result.get("errcode") != 0:
        raise RuntimeError(f"DingTalk send failed: {result}")
    log("DingTalk message sent.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and send AI tech daily briefing.")
    parser.add_argument("--generate", action="store_true", help="Generate report files under public/.")
    parser.add_argument("--send", action="store_true", help="Send DingTalk message for the report date.")
    parser.add_argument("--sample", action="store_true", help="Use built-in sample data instead of live feeds.")
    parser.add_argument("--date", help="Report date in YYYY-MM-DD. Defaults to current Asia/Shanghai date.")
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS, help="Number of items to include.")
    args = parser.parse_args()

    if not args.generate and not args.send:
        args.generate = True

    report_date = parse_report_date(args.date)
    if args.generate:
        report = build_report(report_date=report_date, sample=args.sample, max_items=args.max_items)
        write_report(report)
    if args.send:
        report = load_report(report_date)
        send_dingtalk(report)


if __name__ == "__main__":
    main()
