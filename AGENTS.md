# AI Mail Client - Agent Instructions

本项目是个人轻量邮箱客户端，目标部署环境非常受限：**2C2G / 5GB SSD 数据盘**。所有实现必须优先考虑低资源占用、可维护性和后续平滑扩展。

## 核心约束

- 不引入重型服务：不要添加 Elasticsearch、OpenSearch、Meilisearch、MinIO、本地 LLM、Next.js SSR。
- 不默认全量同步邮箱历史。
- 不默认下载和长期保存所有附件。
- 不做全量邮件自动 AI 处理。
- AI 必须通过外部 API 按需调用。
- 单机部署优先，Docker Compose 只包含必要服务。
- 代码要 API-first，后续移动端会复用 API。

## 技术选择

Backend:

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x async 或 sync 均可，但保持简单。
- Alembic
- PostgreSQL 为生产目标；开发测试可用 SQLite。
- pytest
- Pydantic v2

Frontend:

- React + Vite + TypeScript
- Tailwind CSS
- TanStack Query
- 静态构建，不使用 Next.js SSR。

Worker:

- 第一版优先使用 APScheduler 或应用内轻量 worker。
- 不要强制依赖 Redis/Celery，除非明确需要。

## 邮件同步策略

默认限制：

```text
MAX_INITIAL_DAYS = 30
MAX_INITIAL_MESSAGES = 1000
MAX_BODY_CACHE_MB = 1024
MAX_ATTACHMENT_CACHE_MB = 700
DISK_PAUSE_THRESHOLD = 85%
```

实现同步时遵守：

- 首次同步只拉 envelope / headers / flags / snippet。
- 打开邮件详情时才按需拉正文。
- 附件只保存元信息；用户下载时临时缓存。
- 缓存清理任务必须从一开始预留。
- 数据库里保存 IMAP UID、UIDVALIDITY、Message-ID，避免重复同步。

## 数据安全

- 邮箱密码、OAuth token 必须加密后保存。
- 日志禁止打印邮箱密码、OAuth token、完整邮件正文。
- HTML 邮件展示前必须 sanitize。
- 远程图片加载要预留代理/禁用策略。
- 附件下载要走后端受控接口。

## 数据模型方向

至少预留这些实体：

- User
- MailAccount
- MailFolder
- MailMessage
- MailRecipient
- MailBody
- MailAttachment
- MailSyncJob
- AiSummary
- AiReplyDraft

## 开发原则

- 先写可运行骨架和测试，不要一次性实现过多业务。
- 优先小步提交，保持 git diff 可审查。
- 每个新模块都要有最小测试。
- 不要硬编码用户机器路径。
- 使用 `.env.example` 说明配置，不提交真实密钥。
- 所有外部服务调用都要有超时和错误处理。

## 当前任务

请搭建基础工程结构，不要实现完整邮箱同步业务。目标：

1. 创建 backend FastAPI 项目结构。
2. 创建 SQLAlchemy 模型文件和数据库 session 配置。
3. 配置 Alembic。
4. 添加 `/health` 接口。
5. 添加基础 pytest。
6. 创建 frontend React/Vite/Tailwind 项目结构。
7. 添加简单三栏邮箱 UI skeleton。
8. 创建 deploy/docker-compose.yml 和 Caddyfile skeleton。
9. 确保 backend 测试可运行。
10. 不要提交真实账号、密码、API key。

## 验证命令

优先让以下命令可运行：

```bash
cd backend
uv sync
uv run pytest

cd ../frontend
npm install
npm run build
```
