# 多阶段构建
FROM python:3.10-slim as builder

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 生产镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p logs cache knowledge_base web/report

# 暴露端口
EXPOSE 8000 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 启动命令
CMD ["python", "main.py"]
