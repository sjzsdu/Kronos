import pandas as pd
import matplotlib.pyplot as plt
import sys
from china_stock_data import StockData
sys.path.append("../")
from model import Kronos, KronosTokenizer, KronosPredictor


def plot_prediction(kline_df, pred_df):
    pred_df.index = kline_df.index[-pred_df.shape[0]:]
    sr_close = kline_df['close']
    sr_pred_close = pred_df['close']
    sr_close.name = 'Ground Truth'
    sr_pred_close.name = "Prediction"

    sr_volume = kline_df['volume']
    sr_pred_volume = pred_df['volume']
    sr_volume.name = 'Ground Truth'
    sr_pred_volume.name = "Prediction"

    close_df = pd.concat([sr_close, sr_pred_close], axis=1)
    volume_df = pd.concat([sr_volume, sr_pred_volume], axis=1)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    ax1.plot(close_df['Ground Truth'], label='Ground Truth', color='blue', linewidth=1.5)
    ax1.plot(close_df['Prediction'], label='Prediction', color='red', linewidth=1.5)
    ax1.set_ylabel('Close Price', fontsize=14)
    ax1.legend(loc='lower left', fontsize=12)
    ax1.grid(True)

    ax2.plot(volume_df['Ground Truth'], label='Ground Truth', color='blue', linewidth=1.5)
    ax2.plot(volume_df['Prediction'], label='Prediction', color='red', linewidth=1.5)
    ax2.set_ylabel('Volume', fontsize=14)
    ax2.legend(loc='upper left', fontsize=12)
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


# 1. Load Model and Tokenizer
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")

# 2. Instantiate Predictor
predictor = KronosPredictor(model, tokenizer, device="cpu", max_context=512)

# 3. Get stock data using china_stock_data
# 601688 可能不在 akshare 支持的股票代码列表中，我们使用 000001（平安银行）作为示例
try:
    stock = StockData("000001", days=500)  # 平安银行
    kline_data = stock.get_data("kline")
    print(f"成功获取股票 000001 的数据")
except Exception as e:
    print(f"获取股票数据失败: {e}")
    print("请尝试其他股票代码，如 000001, 600000, 000858 等")
    exit(1)

# Convert Chinese column names to English
column_mapping = {
    '开盘': 'open',
    '收盘': 'close', 
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume'
}

df = kline_data.rename(columns=column_mapping)

# Add timestamps and amount columns
df = df.reset_index()
df['timestamps'] = pd.to_datetime(df['日期'])
if 'amount' not in df.columns:
    df['amount'] = df['volume'] * df['close']

print(f"获取到 {len(df)} 天的股票数据")
print("数据列名:", df.columns.tolist())
print("数据预览:")
print(df[['timestamps', 'open', 'high', 'low', 'close', 'volume']].head())

lookback = 400
pred_len = 5  # 预测未来5天

if len(df) < lookback + pred_len:
    lookback = min(200, len(df) - pred_len - 1)
    print(f"数据不足，调整lookback为: {lookback}")

x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
x_timestamp = df.loc[:lookback-1, 'timestamps']

# 生成从今天开始的未来5个交易日时间戳
import datetime
today = datetime.date(2025, 9, 10)  # 今天是9月10日
future_dates = []
current_date = today
for _ in range(pred_len):
    current_date += datetime.timedelta(days=1)
    # 跳过周末（周六日）
    while current_date.weekday() >= 5:
        current_date += datetime.timedelta(days=1)
    future_dates.append(pd.Timestamp(current_date))

y_timestamp = pd.Series(future_dates)

# 4. Make Prediction
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,
    top_p=0.9,
    sample_count=1,
    verbose=True
)

# 5. Visualize Results
print("\n" + "="*50)
print("📈 平安银行(000001)未来5天股价预测 📈")
print("="*50)
print(f"预测基准日期: {df['timestamps'].iloc[-1].strftime('%Y-%m-%d')}")
print(f"最新收盘价: {df['close'].iloc[-1]:.2f} 元")
print("-"*50)

# 打印详细的预测结果
for i, (date, row) in enumerate(pred_df.iterrows(), 1):
    print(f"第{i}天 ({date.strftime('%Y-%m-%d %A')}):")
    print(f"  开盘价: {row['open']:.2f} 元")
    print(f"  最高价: {row['high']:.2f} 元") 
    print(f"  最低价: {row['low']:.2f} 元")
    print(f"  收盘价: {row['close']:.2f} 元")
    print(f"  成交量: {row['volume']:,.0f} 股")
    
    # 计算涨跌幅
    if i == 1:
        prev_close = df['close'].iloc[-1]
    else:
        prev_close = pred_df.iloc[i-2]['close']
    
    change_pct = (row['close'] - prev_close) / prev_close * 100
    change_symbol = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
    print(f"  涨跌幅: {change_symbol} {change_pct:+.2f}%")
    print("-"*30)

print("="*50)
total_change = (pred_df['close'].iloc[-1] - df['close'].iloc[-1]) / df['close'].iloc[-1] * 100
print(f"5天总涨跌幅: {total_change:+.2f}%")
print(f"目标价位: {pred_df['close'].iloc[-1]:.2f} 元")
print("="*50)
print("⚠️  以上预测仅供参考，投资有风险，入市需谨慎！")

# Combine historical and forecasted data for plotting
kline_df = df.loc[:lookback+pred_len-1]

# visualize
plot_prediction(kline_df, pred_df)

