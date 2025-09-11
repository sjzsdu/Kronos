# Kronos 股票预测系统 - 环境配置总结

## ✅ 已完成的配置

### 1. 自动环境切换
- 创建了 `/Users/juzhongsun/Codes/projects/Kronos/.python-version` - 项目根目录自动使用 kronos-env
- 创建了 `/Users/juzhongsun/Codes/projects/Kronos/csweb/.python-version` - csweb 目录自动使用 kronos-env

### 2. 应用结构
```
csweb/
├── .python-version          # 自动激活 kronos-env
├── app.py                   # Flask 主应用
├── templates/
│   └── index.html          # 前端界面
├── requirements.txt        # 依赖包列表
├── start.sh               # 启动脚本（已更新支持 pyenv）
├── README.md              # 使用说明
└── prediction_results/    # 预测结果保存目录
```

### 3. 功能特点
- 🎯 基于 Kronos AI 模型进行股票预测
- 📊 支持中国股票实时数据获取
- 📈 交互式图表展示预测结果
- 🔧 可调节预测参数
- 💾 自动保存预测结果

## 🚀 使用方法

### 启动应用
```bash
cd /Users/juzhongsun/Codes/projects/Kronos/csweb
./start.sh
```

或者直接运行：
```bash
cd /Users/juzhongsun/Codes/projects/Kronos/csweb
python app.py
```

### 访问应用
打开浏览器访问：http://localhost:5001

## 📋 使用流程

1. **选择模型**: 在控制面板选择 Kronos 模型和运行设备
2. **加载模型**: 点击"加载模型"按钮
3. **选择股票**: 点击热门股票或输入股票代码
4. **获取数据**: 点击"获取股票数据"加载历史数据
5. **调整参数**: 设置预测天数、温度等参数
6. **开始预测**: 点击"开始预测"按钮
7. **查看结果**: 在图表和表格中查看预测结果

## 🎯 支持的热门股票
- 000001 - 平安银行
- 000002 - 万科A
- 600000 - 浦发银行
- 600036 - 招商银行
- 600519 - 贵州茅台
- 000858 - 五粮液
- 002415 - 海康威视
- 等等...

## ⚠️ 重要提示
本系统的预测结果仅供参考，不构成投资建议。股市有风险，投资需谨慎！

## 🔧 环境说明
- 自动使用 pyenv 的 kronos-env 环境
- 无需手动激活虚拟环境
- 进入项目目录自动切换到正确的 Python 环境
