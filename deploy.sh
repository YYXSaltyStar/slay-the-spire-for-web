#!/bin/bash

echo "===== 杀戮尖塔网页版部署脚本 ====="

# 确保脚本在错误时停止
set -e

# 检查Docker是否已安装
echo "检查依赖..."
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 设置应用名称和端口
APP_NAME="slay-the-spire-web"
PORT=14514

# 创建必要的目录
echo "创建必要目录..."
mkdir -p data

# 停止并移除旧容器（如果存在）
echo "停止旧容器（如果存在）..."
docker stop $APP_NAME 2>/dev/null || true
docker rm $APP_NAME 2>/dev/null || true

# 构建镜像
echo "构建Docker镜像..."
docker build -t $APP_NAME .

# 启动容器
echo "启动容器..."
docker run -d \
  --name $APP_NAME \
  -p $PORT:$PORT \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=MReRne27pp4nXeMvBF4hojUlqwyoUYHW \
  -e PORT=$PORT \
  --restart unless-stopped \
  $APP_NAME

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查服务是否正常运行
if docker ps | grep -q "$APP_NAME"; then
    echo "服务已成功启动!"
    echo "访问 http://10.64.198.145:$PORT 开始游戏"
else
    echo "错误: 服务启动失败，请检查日志: docker logs $APP_NAME"
    exit 1
fi

echo "===== 部署完成 =====" 