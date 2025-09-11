#!/bin/bash

echo "🚀 启动 Kronos 股票预测系统..."

# Activate pyenv kronos-env environment
echo "� 激活 pyenv kronos-env 环境..."
export PYENV_VERSION=kronos-env
eval "$(pyenv init -)"
pyenv shell kronos-env

# Install dependencies
echo "📥 安装依赖包..."
pip install -r requirements.txt

# Create prediction results directory
mkdir -p prediction_results

# Start the application
echo "🌐 启动Flask应用..."
echo "访问 http://localhost:5001 查看应用"
python app.py
