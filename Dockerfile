FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .

# Railway 通过 PORT 环境变量指定端口，默认 8000
EXPOSE 8000

# 启动 uvicorn，监听所有网卡
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
