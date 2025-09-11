# Kronos Stock Prediction App - Docker部署

## 概述

这是一个基于AI的中国股票预测应用，使用Kronos模型进行股票价格预测。

## Docker镜像信息

- **镜像名称**: `sjzsdu/kronos-china-stock`
- **默认端口**: 5001
- **数据目录**: `/app/prediction_results`, `/app/cache`

## 快速部署

### 1. 拉取镜像

```bash
docker pull sjzsdu/kronos-china-stock:latest
```

### 2. 创建数据目录

```bash
mkdir -p prediction_results cache
```

### 3. 运行容器

```bash
docker run -d \
  --name kronos-stock-app \
  -p 5001:5001 \
  -v $(pwd)/prediction_results:/app/prediction_results \
  -v $(pwd)/cache:/app/cache \
  --restart unless-stopped \
  sjzsdu/kronos-china-stock:latest
```

### 4. 访问应用

- 应用地址: http://localhost:5001
- API文档: http://localhost:5001/api/models

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `FLASK_ENV` | Flask运行环境 | `production` |
| `PORT` | 应用端口 | `5001` |

## 数据卷

| 容器路径 | 描述 |
|----------|------|
| `/app/prediction_results` | 预测结果存储目录 |
| `/app/cache` | 数据缓存目录 |

## 与Traefik集成

如果你使用Traefik作为反向代理，可以添加以下标签：

```bash
docker run -d \
  --name kronos-stock-app \
  --network traefik \
  -v $(pwd)/prediction_results:/app/prediction_results \
  -v $(pwd)/cache:/app/cache \
  --restart unless-stopped \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.kronos-app.rule=Host(\`stock.your-domain.com\`)" \
  --label "traefik.http.routers.kronos-app.entrypoints=web" \
  --label "traefik.http.services.kronos-app.loadbalancer.server.port=5001" \
  sjzsdu/kronos-china-stock:latest
```

## 健康检查

容器内置健康检查，检查API端点的可用性：

```bash
# 手动健康检查
curl -f http://localhost:5001/api/models || echo "Service unhealthy"
```

## 日志查看

```bash
# 查看实时日志
docker logs -f kronos-stock-app

# 查看最近的日志
docker logs --tail 100 kronos-stock-app
```

## 更新应用

```bash
# 停止旧容器
docker stop kronos-stock-app
docker rm kronos-stock-app

# 拉取新镜像
docker pull sjzsdu/kronos-china-stock:latest

# 启动新容器
docker run -d \
  --name kronos-stock-app \
  -p 5001:5001 \
  -v $(pwd)/prediction_results:/app/prediction_results \
  -v $(pwd)/cache:/app/cache \
  --restart unless-stopped \
  sjzsdu/kronos-china-stock:latest
```

## 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 使用不同端口
   docker run -p 5002:5001 sjzsdu/kronos-china-stock:latest
   ```

2. **权限问题**
   ```bash
   # 确保数据目录权限
   sudo chown -R $(id -u):$(id -g) prediction_results cache
   ```

3. **内存不足**
   ```bash
   # 限制内存使用
   docker run --memory=2g sjzsdu/kronos-china-stock:latest
   ```

### 调试命令

```bash
# 进入容器
docker exec -it kronos-stock-app bash

# 检查应用状态
docker exec kronos-stock-app curl -f http://localhost:5001/api/models

# 查看容器信息
docker inspect kronos-stock-app
```

## API使用示例

### 获取可用模型
```bash
curl http://localhost:5001/api/models
```

### 获取热门股票
```bash
curl http://localhost:5001/api/popular_stocks
```

### 股票预测
```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "lookback": 300,
    "pred_len": 5,
    "temperature": 1.0
  }'
```

## 技术栈

- **后端**: Flask + Python 3.9
- **AI模型**: Kronos (Transformer-based)
- **数据源**: china_stock_data
- **前端**: HTML + JavaScript + Plotly.js
- **容器**: Docker
