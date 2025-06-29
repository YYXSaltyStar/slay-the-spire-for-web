FROM python:3.9-slim

WORKDIR /app

# 先只复制requirements.txt文件进行依赖安装
# 这样当应用代码变更时，如果requirements.txt没变，这一层会使用缓存
COPY requirements.txt .
RUN pip install -r requirements.txt

# 创建数据目录
RUN mkdir -p data

# 复制其余应用代码（在依赖安装之后）
COPY . .

# 创建启动脚本
RUN echo '#!/bin/bash\n\
# 检查数据库文件是否存在\n\
if [ ! -f /app/data/slay_the_spire.db ]; then\n\
  echo "数据库文件不存在，开始初始化..."\n\
  # 初始化数据库\n\
  python -c "from src.db_init import init_database; init_database()"\n\
  echo "数据库已初始化: /app/data/slay_the_spire.db"\n\
else\n\
  echo "数据库文件已存在，跳过初始化。"\n\
fi\n\
\n\
# 启动应用\n\
exec gunicorn --worker-class eventlet -w 1 --timeout 120 --log-level debug --bind 0.0.0.0:${PORT:-14514} app:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# 暴露端口
EXPOSE 14514

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PORT=14514

# 启动应用
CMD ["/app/start.sh"] 