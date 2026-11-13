# 阶段一：构建前端（React + Vite + Monaco）
FROM node:20-alpine AS front
WORKDIR /app
COPY web/package.json ./
RUN npm install
COPY web/ .
RUN npm run build

# 阶段二：编译后端（需要阶段一产出的 web/dist 供 go:embed）
FROM golang:1.25-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY --from=front /app/dist web/dist
COPY embed.go ./
COPY content content
COPY examples examples
COPY cmd cmd
COPY internal internal
RUN CGO_ENABLED=0 go build -o /out/bkcc-server ./cmd/server

# 阶段三：运行镜像
# 保留 Go toolchain（供进程内沙箱编译示例）+ Python/qiskit（供量子示例）。
# 注意用 bookworm(glibc) 而非 alpine(musl)：qiskit-aer 含 C++ 扩展，alpine 无可用 wheel。
FROM golang:1.25-bookworm
WORKDIR /app

COPY --from=build /out/bkcc-server /usr/local/bin/bkcc-server

# 安装 Python3 + qiskit（安装到 venv，并以非 root 运行；exec 沙箱用 PATH 中的 python3 解析到它）。
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
 && python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir qiskit qiskit-aer \
 && apt-get purge -y python3-pip \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/venv/bin:${PATH}"

# 以非 root 身份运行。
# 沙箱(exec)需要可写且可"执行"的工作区（注意：tmpfs/noexec 挂载点无法运行二进制），
# 因此统一放到 overlay 文件系统的 /workspace 下。
RUN groupadd -g 10001 appuser \
 && useradd -u 10001 -g appuser -m -s /usr/sbin/nologin appuser \
 && mkdir -p /workspace/tmp /workspace/gocache /workspace/gomodcache \
 && chown -R appuser:appuser /workspace
ENV HOME=/workspace \
    TMPDIR=/workspace/tmp \
    GOCACHE=/workspace/gocache \
    GOMODCACHE=/workspace/gomodcache \
    PIP_NO_CACHE_DIR=1

USER appuser
EXPOSE 8080
ENTRYPOINT ["bkcc-server"]
CMD ["-addr", ":8080"]