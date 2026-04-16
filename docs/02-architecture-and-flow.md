# AI Agent 记单词项目｜02 系统架构与数据流

## 分层架构
- 客户端层：Web App（Next.js）
- 业务层：词库模块、复习模块、练习模块、统计模块
- Agent 层：AI Coach + Tool 调用（search_vocab、get_due_words、make_quiz）
- 数据层：Prisma + SQLite/Postgres

## 数据流
- 导入词条 -> AI 丰富卡片 -> 加入学习计划
- 学习新词 -> 练习答题 -> 复习评分
- 评分结果 -> SM-2 更新 next_review_at
- 统计模块聚合行为 -> Dashboard 展示

## 核心表
- vocab_items
- review_logs
- practice_sessions
- ai_generation_cache
