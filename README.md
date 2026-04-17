<div align="center">

# AI Vocab Coach · 沉浸式 AI 学习助手
# AI Vocab Coach · Immersive AI Learning Assistant

<p>
  <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/TailwindCSS-06B6D4?logo=tailwindcss" />
  <img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite" />
  <img src="https://img.shields.io/badge/OpenAI%20Compatible-412991?logo=openai" />
</p>

<p>
  <b>中文</b> | <a href="#english">English</a>
</p>

</div>

---

## 简介 / Introduction

**AI Vocab Coach** 是一个基于 **FastAPI + Vue3 + Tailwind CSS** 的沉浸式 AI 学习助手。支持多词库单词记忆（SM-2 算法）、番茄钟专注计时、任务管理、日历学习打卡、数据统计看板与智能 AI 答疑。所有学习数据本地存储，AI 配置安全隔离。

> 💡 灵感来自沉浸式学习体验，主打轻量、高效、有趣。我们甚至为界面注入了 **Comic Style（漫画风格）**，让背单词也能充满活力！

---

## ✨ 核心功能 / Core Features

| 功能 | 说明 |
|------|------|
| 📚 **多词库单词记忆** | CET4/6 等词库导入、SM-2 复习算法、认识/模糊/不认识 评分、练习模式（选择题 / 拼写） |
| 📖 **词库隔离管理** | 可切换当前词库，学习 / 练习 / 统计按词库独立计算 |
| ⏱️ **番茄钟专注** | 自定义专注时长、关联学习任务、白噪音背景（雨声 / 森林） |
| ✅ **任务管理** | 学习任务的增删改查、优先级、截止日期、状态筛选 |
| 📅 **日历打卡** | 每日学习行为自动打卡、日历视图、连续打卡天数统计 |
| 📊 **数据统计** | Dashboard 数据卡片、近 7 天复习 / 专注趋势图（ECharts） |
| 🤖 **AI 答疑** | 流式对话、每日激励语、单词记忆技巧生成、快捷指令 |

---

## 🖼️ 界面预览 / Preview

> 漫画风格界面，粗黑边框 + 硬边阴影 + 动态交互，学习也要 POW! BAM!

| Dashboard | Study | Focus | Chat |
|-----------|-------|-------|------|
| 数据卡片 + 趋势图 | SM-2 卡片评分 | 倒计时 + 白噪音 | 流式对话 |

---

## 🚀 快速开始 / Quick Start

### 1. 克隆仓库 / Clone

```bash
git clone https://github.com/haodehaode378/vocab-coach-ai.git
cd vocab-coach-ai
```

### 2. 安装后端依赖 / Backend Setup

```bash
cd apps/api
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 安装前端依赖 / Frontend Setup

```bash
cd ../web
npm install
```

### 4. 导入词库（可选）/ Import Vocab (Optional)

```bash
cd ../..
python scripts/import_words.py data/CET4luan_2.json data/CET6_1.json
```

### 5. 启动服务 / Run

**开发模式 / Dev Mode**

```bash
# Terminal 1: Backend
cd apps/api
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd apps/web
npm run dev
```

访问 / Open: **http://localhost:5173**

或一键启动（推荐）：

```bash
python run.py
```

可选：

```bash
python run.py --target api
python run.py --target web
python run.py --api-port 8000 --web-port 5173
```

**生产模式 / Production Mode**

```bash
cd apps/web && npm run build
cd ../api && uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问 / Open: **http://localhost:8000**

---

## 🏗️ 技术架构 / Tech Stack

- **Backend**: Python + FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vite + Vue 3 (Composition API) + Tailwind CSS + Pinia + Vue Router + ECharts
- **AI API**: OpenAI-compatible, supporting Kimi / DeepSeek / OpenAI / Azure etc.

### 项目结构 / Project Structure

```
ai-vocab-agent/
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/     # DB/models/services/AI config
│   │   │   ├── domains/  # learning/productivity/intelligence/system
│   │   │   ├── main.py
│   │   │   └── ...
│   │   └── requirements.txt
│   └── web/              # Vue3 frontend
│       ├── src/
│       │   ├── features/ # business feature pages
│       │   ├── app/      # router, app-level wiring
│       │   └── ...
│       └── package.json
├── packages/
│   └── shared/           # Shared types/constants/DTO
├── data/                 # SQLite DB + AI config + vocab files (gitignored)
├── scripts/              # Utility scripts
├── run.py                # One-command local startup
└── docs/                 # Documentation
```

---

## 🔐 AI 配置与隐私保护 / AI Config & Privacy

**API Key 不会上传到 GitHub，也不保存在前端 localStorage。**

1. 点击页面右上角「设置」，填写 **Base URL**、**API Key**、**Model**。  
2. 在设置面板中可直接点击「**测试 AI 连接**」，验证模型是否可用。  
3. 保存后：
   - `Base URL` 和 `Model` 仅缓存在浏览器内存中；
   - `API Key` 通过加密通道发送到后端，写入 `data/ai_config.json`。
4. 前端设置面板**不会回显**已保存的 API Key，再次打开时 API Key 输入框为空，留空即保留原值。

> 🛡️ `data/ai_config.json` 与 `data/app.db` 均已加入 `.gitignore`，确保不会进入 Git 仓库。  
> Environment variables are also supported: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.

---

## 📡 API 文档 / API Overview

### Core APIs
- `GET /healthz`
- `GET /api/stats/overview`
- `GET /api/stats/dashboard`
- `GET /api/vocab/list`
- `POST /api/vocab/import-json-files`
- `GET /api/study/today`
- `POST /api/study/grade`
- `POST /api/study/test/generate`
- `POST /api/practice/generate`
- `POST /api/practice/submit`

### Books & Settings
| Endpoint | Description |
|----------|-------------|
| `GET /api/study/books` | List user's vocab books |
| `POST /api/study/current-book` | Set current active book |
| `GET /api/study/settings` | Get study settings |
| `POST /api/study/settings` | Update study settings |

### Other Modules
| Module | Endpoints |
|--------|-----------|
| Focus | `POST /api/focus/start` · `POST /api/focus/end` · `GET /api/focus/history` |
| Tasks | `GET /api/tasks` · `POST /api/tasks` · `PUT /api/tasks/{id}` · `DELETE /api/tasks/{id}` |
| Checkin | `GET /api/checkin/calendar` · `GET /api/checkin/streak` |
| AI | `POST /api/ai/chat` (SSE) · `POST /api/ai/generate-memory-tip` · `POST /api/ai/daily-motivation` |
| System | `GET /api/system/ai-config` · `POST /api/system/ai-config` |

---

## 🤝 贡献 / Contributing

欢迎 Issue 和 PR！如果你有任何建议或发现了 Bug，请随时提交。

Contributions, issues and feature requests are welcome!

---

## 📄 许可证 / License

[MIT](LICENSE) © 2026

---

> 🌸 每一天的进步，都是未来的伏笔。  
> Every step forward today is a伏笔 for the future.

---

<div align="center">

<a name="english"></a>

# English

</div>

## What is AI Vocab Coach?

**AI Vocab Coach** is an immersive AI-powered learning assistant built with **FastAPI + Vue 3 + Tailwind CSS**. It supports multi-book vocabulary memorization (SM-2 algorithm), Pomodoro focus timer, task management, daily check-in calendar, learning statistics dashboard, and intelligent AI Q&A. All learning data is stored locally, and AI configuration is securely isolated.

> 💡 Inspired by immersive learning platforms, it is lightweight, efficient, and fun. We even injected a **Comic Style** into the UI to make vocabulary learning energetic!

## Features

- 📚 **Multi-book Vocabulary** — Import CET4/6 and more. SM-2 review algorithm with Know/Vague/Forget ratings. Practice modes (MCQ / Spelling).
- 📖 **Book Isolation** — Switch current book. Study, practice, and stats are calculated independently per book.
- ⏱️ **Pomodoro Focus** — Custom duration, task linking, white noise (Rain / Forest).
- ✅ **Task Management** — CRUD tasks with priority, due date, and status filters.
- 📅 **Calendar Check-in** — Auto check-in, calendar view, streak counter.
- 📊 **Statistics** — Dashboard cards + 7-day review / focus trend charts (ECharts).
- 🤖 **AI Chat** — Streaming conversation, daily motivation, memory tips, quick shortcuts.

## Quick Start

See the [Quick Start](#快速开始--quick-start) section above for installation and run instructions.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vite, Vue 3 (Composition API), Tailwind CSS, Pinia, Vue Router, ECharts
- **AI**: OpenAI-compatible API (Kimi, DeepSeek, OpenAI, Azure, etc.)

## Privacy

Your API Key is **never** uploaded to GitHub or stored in browser localStorage. It is sent securely to the backend and saved in a local file (`data/ai_config.json`), which is `.gitignore` protected.

## API

See the [API 文档 / API Overview](#api-文档--api-overview) section above.

## License

[MIT](LICENSE) © 2026
