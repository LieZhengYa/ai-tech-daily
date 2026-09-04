# AI Tech Daily

每天东八区早上 8 点自动整理昨日 AI / 大模型 / 机器人 / 芯片 / 自动驾驶 / AR/VR 科技资讯，生成资讯海报，并推送到钉钉群。

## 第一版能力

- 抓取公开 RSS / 新闻源。
- 筛选昨日相关新闻，默认选 10 条。
- 用大模型生成中文摘要，并保留中英文标题和原文链接。
- 生成 `1080 x 1920` 资讯海报 PNG。
- 生成公开 HTML 页面和 JSON 归档。
- 通过钉钉自定义机器人推送 Markdown 消息。

## 本地先跑一个样例

```powershell
pip install -r requirements.txt
python scripts/daily_news.py --sample --generate
```

生成结果会在：

```text
public/daily/YYYY-MM-DD/
```

## 本地测试钉钉推送

钉钉机器人只能展示公网图片，所以正式推送建议放到 GitHub Pages 后再跑。若只想测试文字链路，可以先设置环境变量：

```powershell
$env:DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=xxx"
$env:DINGTALK_SECRET="SECxxx"
$env:PUBLIC_BASE_URL="https://你的用户名.github.io/ai-tech-daily/"
python scripts/daily_news.py --send
```

不要把 Webhook、Secret、API Key 写进代码或提交到仓库。

## GitHub Secrets

仓库网络恢复后，在仓库的 `Settings -> Secrets and variables -> Actions` 添加：

```text
DINGTALK_WEBHOOK
DINGTALK_SECRET
LLM_API_KEY
```

可选项：

```text
LLM_BASE_URL
LLM_MODEL
```

DeepSeek 默认配置：

```text
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

OpenAI 示例：

```text
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5-mini
```

## GitHub Pages

在仓库 `Settings -> Pages` 里，把构建来源设置为 `GitHub Actions`。之后可以在 `Actions` 页面手动运行 `Daily AI Tech Briefing`，验证成功后它会每天自动运行。

GitHub Actions 的定时任务使用 UTC 时间，所以工作流里的：

```text
0 0 * * *
```

对应东八区每天早上 8 点。

## 调整资讯源

编辑：

```text
config/sources.json
```

可以增加、删除或调整 RSS 源。脚本会跳过暂时访问失败的来源，不会因为单个来源故障而中断日报。
