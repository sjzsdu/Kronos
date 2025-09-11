# Kronos 股票预测系统

基于Kronos AI模型的中国股票价格预测系统，支持实时获取股票数据并进行未来价格预测。

## 快速开始

### 前置条件
- 确保已安装 pyenv 和 kronos-env 环境
- 项目会自动使用 kronos-env 环境（通过 .python-version 文件）

### 启动应用

```bash
cd /Users/juzhongsun/Codes/projects/Kronos/csweb
./start.sh
```

或者手动启动：

```bash
cd /Users/juzhongsun/Codes/projects/Kronos/csweb

# 环境会自动激活（通过 .python-version）
pip install -r requirements.txt
python app.py
```

访问 http://localhost:5001 使用应用。

## 环境配置说明

项目已配置为自动使用 `kronos-env` 环境：

1. **根目录**: `/Users/juzhongsun/Codes/projects/Kronos/.python-version` 设置了 kronos-env
2. **csweb目录**: `/Users/juzhongsun/Codes/projects/Kronos/csweb/.python-version` 也设置了 kronos-env
3. **启动脚本**: `start.sh` 会确保使用正确的环境

这意味着：
- 当你 `cd` 到项目目录时，pyenv 会自动切换到 kronos-env
- 无需手动激活虚拟环境
- 所有 Python 命令都会使用 kronos-env 中的包

## 使用说明

1. **启动应用**: 运行启动脚本后，访问 http://localhost:5001
2. **加载模型**: 选择Kronos模型和运行设备，点击"加载模型"
3. **选择股票**: 点击热门股票按钮或手动输入股票代码
4. **获取数据**: 点击"获取股票数据"按钮加载历史数据
5. **调整参数**: 设置预测天数、温度等参数
6. **开始预测**: 点击"开始预测"按钮进行AI预测
7. **查看结果**: 在图表和表格中查看预测结果

## 预测参数说明

- **历史窗口大小**: 固定为400个数据点，用于模型输入
- **预测天数**: 预测未来的交易日数量（1-30天）
- **预测温度**: 控制预测的随机性
  - 数值越低（0.1-0.5）：预测越保守，变化平稳
  - 数值越高（1.5-2.0）：预测越多样化，波动较大
  - 建议值：1.0

## 技术架构

- **后端**: Flask + Python
- **前端**: HTML + CSS + JavaScript + Plotly.js
- **AI模型**: Kronos (HuggingFace)
- **数据源**: china_stock_data + akshare
- **图表**: Plotly.js 交互式图表

## 注意事项

⚠️ **重要提示**: 本系统的预测结果仅供参考，不构成投资建议。股市有风险，投资需谨慎！

- 预测结果基于历史数据和AI模型，不能保证准确性
- 股票市场受多种因素影响，包括政策、经济、突发事件等
- 请结合多种分析方法和专业意见做出投资决策
- 建议仅将此工具作为辅助分析手段

## 目录结构

```
csweb/
├── app.py                 # Flask应用主程序
├── templates/
│   └── index.html        # 前端页面
├── requirements.txt      # Python依赖包
├── start.sh             # 启动脚本
├── README.md            # 说明文档
└── prediction_results/  # 预测结果保存目录
```

## 故障排除

### 模型加载失败
- 确保网络连接正常，能够访问HuggingFace
- 检查是否有足够的磁盘空间下载模型
- 首次运行时模型下载可能需要较长时间

### 股票数据获取失败
- 检查网络连接
- 确认股票代码格式正确（6位数字）
- 某些股票可能暂停交易或代码不存在

### 依赖安装失败
- 确保使用Python 3.8+版本
- 更新pip: `pip install --upgrade pip`
- 如果网络问题，可使用国内镜像源

## 许可证

本项目基于开源许可证，具体见项目根目录的LICENSE文件。
