# Vocab Coach AI · 沉浸式 AI 学习助手

<p align="center">
  <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/ElementPlus-409EFF" />
  <img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite" />
  <img src="https://img.shields.io/badge/OpenAI%20Compatible-412991?logo=openai" />
</p>

一个基于 **FastAPI + Vue3 + Element Plus** 的沉浸式 AI 学习助手。支持四六级单词记忆（SM-2 算法）、番茄钟专注计时、任务管理、日历学习打卡、数据统计看板与智能 AI 答疑，所有学习数据本地存储，AI 配置安全隔离。

> 💡 灵感来自「Zest·Sleep」沉浸式学习平台，主打轻量、高效、温暖的学习体验。

---

## ✨ 核心功能

| 模块 | 说明 |
|------|------|
| 📚 **单词记忆** | CET4/6 词库导入、SM-2 复习算法、Again/Hard/Good/Easy 评分、练习模式（选择题 / 拼写） |
| ⏱️ **番茄钟专注** | 自定义专注时长、循环计数、关联学习任务、白噪音背景（雨声 / 森林） |
| ✅ **任务管理** | 学习任务的增删改查、优先级、截止日期、状态筛选 |
| 📅 **日历打卡** | 每日学习行为自动打卡、日历视图、连续打卡天数统计 |
| 📊 **数据统计** | Dashboard 数据卡片、近 7 天复习 / 专注趋势图（ECharts） |
| 🤖 **AI 答疑** | 流式对话、每日激励语、单词记忆技巧生成、快捷指令 |

---

## 🏗️ 技术架构

- **后端**：Python + FastAPI + SQLAlchemy + SQLite
- **前端**：Vite + Vue 3（组合式 API）+ Element Plus + Pinia + Vue Router + ECharts
- **AI 接口**：OpenAI 兼容格式，支持 Kimi / DeepSeek / OpenAI / Azure 等

```
ai-vocab-agent/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routers/      # API 路由（按模块拆分）
│   │   ├── ai_client.py  # AI 客户端封装
│   │   └── ...
│   ├── data/             # SQLite 数据库 + AI 配置（.gitignore 保护）
│   └── requirements.txt
├── frontend/             # Vue3 前端
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── api/          # Axios 封装
│   │   ├── router/
│   │   ├── stores/
│   │   └── ...
│   └── package.json
└── docs/                 # 项目文档
```

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/haodehaode378/vocab-coach-ai.git
cd vocab-coach-ai
```

### 2. 安装后端依赖

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd ../frontend
npm install
```

### 4. 导入词库（可选）

```bash
cd ../backend
python scripts/import_words.py CET4luan_2.json CET6_1.json
```

### 5. 启动服务

**方式一：开发模式（推荐）**

```bash
# 终端 1：启动后端
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端 2：启动前端
cd frontend
npm run dev
```

打开浏览器访问：**http://localhost:5173**

**方式二：生产模式**

前端已构建为 `frontend/dist/`，直接启动后端即可：

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问：**http://localhost:8000**

---

## 🔐 AI 配置与隐私保护

**API Key 不会上传到 GitHub，也不保存在前端 localStorage。**

1. 点击页面右上角「设置」，填写 **Base URL**、**API Key**、**Model**。  
2. 保存后：
   - `Base URL` 和 `Model` 仅缓存在浏览器内存中；
   - `API Key` 通过加密通道发送到后端，写入 `backend/data/ai_config.json`。
3. 前端设置面板**不会回显**已保存的 API Key，再次打开时 API Key 输入框为空，留空即保留原值。

> 🛡️ `backend/data/ai_config.json` 与 `backend/data/app.db` 均已加入 `.gitignore`，确保不会进入 Git 仓库。  
> 也支持通过环境变量覆盖文件配置：`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`。

---

## 📡 API 一览

### 原有 API
- `GET /healthz`
- `GET /api/stats/overview`
- `GET /api/stats/dashboard`
- `GET /api/vocab/list`
- `POST /api/vocab/import-json-files`
- `GET /api/review/today`
- `POST /api/review/grade`
- `POST /api/practice/generate`
- `POST /api/practice/submit`

### 新增 API
| 模块 | 接口 |
|------|------|
| 番茄钟 | `POST /api/focus/start` · `POST /api/focus/end` · `GET /api/focus/history` |
| 任务管理 | `GET /api/tasks` · `POST /api/tasks` · `PUT /api/tasks/{id}` · `DELETE /api/tasks/{id}` |
| 日历打卡 | `GET /api/checkin/calendar` · `GET /api/checkin/streak` |
| AI 服务 | `POST /api/ai/chat`（支持 SSE 流式）· `POST /api/ai/generate-memory-tip` · `POST /api/ai/daily-motivation` |
| 系统配置 | `GET /api/system/ai-config` · `POST /api/system/ai-config` |

---

## 🖼️ 页面截图（可选补充）

| Dashboard | 今日复习 | 番茄钟 | AI 答疑 |
|-----------|---------|--------|---------|
| 数据卡片 + 趋势图 | SM-2 卡片评分 | 倒计时 + 白噪音 | 流式对话 |

---

## 📄 License

MIT License © 2026

---

> 🌸 每一天的进步，都是未来的伏笔。
