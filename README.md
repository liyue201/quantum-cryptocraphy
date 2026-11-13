# quantum-cryptography

一本**零基础也能看懂**的《量子密码学在线交互书》——不只"读"，更"边读边动手"：每个知识点都配有可在浏览器里查看、修改、运行的 **Python 示例**（基于 Qiskit）。内容面向**没有量子物理基础的普通程序员**，从叠加态讲起，逐步走向量子威胁、后量子密码与 QKD。

> 无数据库 · 无登录 · 完全免费开放 · 单 Go 二进制即可部署（沙箱内置 Python/Qiskit 环境）

---

## ✨ 核心特色

- **通俗易懂**：用生活比喻切入叠加、坍缩、纠缠等概念，把量子力学讲成人话。
- **可运行示例**：每个知识点配套 Python + Qiskit 程序，在浏览器内直接运行，亲自观察测量坍缩与纠缠。
- **真·沙箱执行**：前端是编辑器 + 展示层，代码由后端沙箱运行，输出实时返回。
- **单二进制部署**：前端静态资源、教材正文、示例代码全部 `go:embed` 打进一个二进制，对外只需暴露 **一个端口**。
- **免费开放**：全文开放、示例免费运行，无任何访问门槛。
- **契合代码人先验**：把"它听起来像玄学"的量子现象，拆成你能一眼看懂的可运行代码。

---

## 🗺️ 内容全景

> 书处于**持续写作中**，当前已完成前两篇。整体大纲：

### 第 0 篇 量子威胁：为什么今天的密码会失效
1. 为什么量子会颠覆今天的密码（全景视角）

### 第 1 篇 量子计算地基：叠加、测量与纠缠
1. 叠加、测量坍缩与纠缠：量子的三张底牌

### 后续篇（规划中）
- 量子攻击武器：Grover 搜索与 Shor 分解（对 RSA/ECC 的威胁）
- 后量子密码：哈希签名、格密码、McEliece
- 量子密钥分发 QKD：BB84 协议
- 综合实战：搭建一个"抗量子"迷你体系

---

## 🧱 技术栈

| 模块 | 技术 |
|---|---|
| 前端框架 | React + TypeScript + Vite |
| 代码编辑器 | Monaco Editor（VS Code 内核） |
| 样式 | Tailwind CSS |
| 后端 | Go（标准库 net/http，单二进制） |
| 量子示例 | Python + Qiskit + Qiskit Aer（模拟器） |
| 教材/前端托管 | `go:embed` 内嵌进二进制 |
| 数据库 | 无（内容走文件 + go:embed，状态存内存） |
| 沙箱执行 | 进程内 Python/Go 执行器（默认）/ Docker 容器后端（可选，`SANDBOX_BACKEND=docker`） |
| 认证 | 匿名访问、无登录，靠 IP 令牌桶限流防滥用 |

---

## 📁 项目结构

```
quantum-cryptography/
├── cmd/server/            # 主服务入口（唯一入口，-addr :8080）
├── internal/
│   ├── server/            # HTTP 服务：路由 + 静态托管 + 限流中间件
│   ├── handler/           # HTTP handlers（运行接口）
│   ├── service/           # 章节/内容业务（加载 go:embed 教材）
│   └── sandbox/           # 沙箱执行器（exec / Docker 双后端 + 多语言分派）
├── content/               # 教材正文（Markdown + YAML front matter）
├── examples/              # 示例 Python 程序（按篇编号）
├── web/                   # 前端源码 (React+TS+Vite+Monaco)
│   └── dist/              # build 产物（由 go:embed 打包）
├── Dockerfile             # 多阶段构建（前端→编译→运行镜像，内置 Python/Qiskit）
├── docker-compose.yml     # 单服务编排
├── requirements.txt       # Python 量子示例依赖
├── DESIGN.md              # 详细设计文档
└── go.mod                 # Go 模块
```

### 章节与示例编号约定
- `content/part-N/MM-<topic>/chapter.md`（front matter 的 `example` 字段引用示例 id）
- `examples/NM-<topic>/main.py`（量子章节为 Python 示例，后端会自动按语言分派）

---

## 🚀 本地运行

### 方式一：直接跑 Go（需要已构建前端 `web/dist`）

```bash
# 构建前端
cd web && npm install && npm run build && cd ..

# 启动服务（默认 :8080，exec 沙箱）
go run ./cmd/server -addr :8080
```

> exec 沙箱运行 Python 示例时使用系统中可用的 `python3`；如需指定解释器，设 `PYTHON_BIN` 环境变量（如本地装有 Qiskit 的 venv `PYTHON_BIN=/path/to/.venv/bin/python3`）。

### 方式二：Docker Compose（推荐，一键起全套，内含 Python/Qiskit 环境）

```bash
docker compose up -d --build
```

之后浏览器打开 **http://localhost:8080**。

> 运行镜像保留 Go toolchain（用于 Go 示例沙箱编译）并内置 `/opt/venv` 的 Python + Qiskit 用于量子示例；非 root 运行，工作区位于 `/workspace`。

---

## 🔌 核心 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/meta` | 书的元信息（书名、篇名，来自 `content/book.json`） |
| GET | `/api/v1/chapters` | 章节列表（含篇分组、示例映射） |
| GET | `/api/v1/chapters/:id` | 章节正文 |
| POST | `/api/v1/run` | 提交代码到沙箱运行（支持语言 `lang` 分派） |
| GET | `/api/v1/health` | 健康检查 |
| GET | `/*` | 托管 go:embed 的前端静态资源（SPA） |

---

## 📖 把它改造成另一本书（模板化）

本项目是一个**内容驱动的书籍骨架**：书的所有"差异内容"都放在 `content/` 与 `examples/` 两个目录，**前端与后端代码无需改动**，替换这两处即可变成别的书。

### 1. 书名与篇名 → `content/book.json`

```json
{
  "title_zh": "你的书名",
  "title_en": "Your Book Title",
  "subtitle_zh": "在线交互书",
  "subtitle_en": "Interactive Book",
  "parts": {
    "-1": { "zh": "前言", "en": "Preface" },
    "0": { "zh": "第一篇名", "en": "Part 1" }
  }
}
```

- 前端侧栏标题、浏览器标签页标题都会跟随它切换中英文。
- `parts` 以篇号（`part`）为键，可自由增删。

### 2. 每章正文 → `content/part-N/NN-slug/chapter.md`

每个目录一章，目录名形如 `part-0/01-intro/`。正文为 Markdown + 简单 front matter：

```markdown
---
id: part-0-01        # 全局唯一 id（也是分组的 key）
title: 章节标题        # 中文标题
title_en: Chapter Title  # 英文标题（可选，缺省回退中文）
part: 0             # 属于哪一篇（对应 book.json 的 parts 键）
sort: 1             # 篇内排序
example: 01-intro   # 可选：关联 examples 下的示例源码
---

# 正文（Markdown）
```

- 同一目录可提供英文版 `chapter.en.md`，供浏览器切换英文时展示。

### 3. 可运行示例 → `examples/NN-slug/main.py`（或 `main.go`）

任意 `example:` 字段引用的示例源码，存放到 `examples/<id>/main.py`（Python 量子示例，推荐）。系统会根据文件名自动识别语言并选择对应的沙箱执行器；前端章节页会自动展示编辑器并支持在沙箱中运行。

### 4. 重新构建

```bash
cd web && npm run build      # 重新打包前端（若改了前端）
go build ./...               # 把新 content/examples 打进二进制
```

之后运行单二进制即可，页面自动呈现你的新书内容。

---

## ⚙️ 配置

| 环境变量 | 说明 |
|---|---|
| `SANDBOX_BACKEND` | 沙箱后端：空 = 进程内 `exec`（默认）；`docker` = Docker 容器后端 |
| `PYTHON_BIN` | Python 解释器路径（exec 沙箱运行量子示例用），缺省为 `python3` |
| `-addr`（flag） | 监听地址，默认 `:8080` |

### Python 依赖

Python 量子示例依赖见 [requirements.txt](./requirements.txt)（`qiskit` + `qiskit-aer`）。Docker 镜像已预装；本地运行请：

```bash
python3 -m venv .venv-qc && source .venv-qc/bin/activate
pip install -r requirements.txt
```

---

## 🛡️ 沙箱与安全

- **MVP（exec）**：用户代码写入临时 `main.py` / `main.go` → 按语言分派运行/编译 → 限时，捕获 stdout/stderr；有超时、内存、输出截断与 IP 限流。
- **生产（docker）**：非 root、只读根文件系统、禁用网络、限额（memory/cpu/pids）、收缩 capabilities + seccomp；Python 示例在 `python:3.12-slim` 容器运行，Go 在带 toolchain 的镜像运行。

---

## 📄 其他

- 详细设计见 [DESIGN.md](./DESIGN.md)
- 主题边界：本书只讲量子相关的密码学；共识、区块链等与量子无关的系统知识不展开。

**安全来自可验证的数学，而非相信谁。**