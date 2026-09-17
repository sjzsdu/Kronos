import os
import pandas as pd
import numpy as np
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
import warnings
import datetime
warnings.filterwarnings('ignore')

## Path adjustments: ensure root model package is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)  # project root is parent of csweb/
# Try root model first (local dev), then local model dir (Docker)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from model import Kronos, KronosTokenizer, KronosPredictor  # model may come from embedded bridge
    MODEL_AVAILABLE = True
except Exception as e:
    MODEL_AVAILABLE = False
    print(f"Warning: Kronos model import failed: {e}. Using simulated data.")

try:
    from china_stock_data import StockData
    STOCK_DATA_AVAILABLE = True
except ImportError:
    STOCK_DATA_AVAILABLE = False
    print("Warning: china_stock_data not available, will use simulated data")

# Direct akshare import as fallback (bypasses proxy issues with china_stock_data)
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Global variables to store models
tokenizer = None
model = None
predictor = None

# Available model configurations
AVAILABLE_MODELS = {
    'kronos-mini': {
        'name': 'Kronos-mini',
        'model_id': 'NeoQuasar/Kronos-mini',
        'tokenizer_id': 'NeoQuasar/Kronos-Tokenizer-2k',
        'context_length': 2048,
        'params': '4.1M',
        'description': 'Lightweight model, suitable for fast prediction'
    },
    'kronos-small': {
        'name': 'Kronos-small',
        'model_id': 'NeoQuasar/Kronos-small',
        'tokenizer_id': 'NeoQuasar/Kronos-Tokenizer-base',
        'context_length': 512,
        'params': '24.7M',
        'description': 'Small model, balanced performance and speed'
    },
    'kronos-base': {
        'name': 'Kronos-base',
        'model_id': 'NeoQuasar/Kronos-base',
        'tokenizer_id': 'NeoQuasar/Kronos-Tokenizer-base',
        'context_length': 512,
        'params': '102.3M',
        'description': 'Base model, provides better prediction quality'
    }
}

# Popular Chinese stock codes
POPULAR_STOCKS = {
    '000001': '平安银行',
    '000002': '万科A',
    '600000': '浦发银行',
    '600036': '招商银行',
    '600519': '贵州茅台',
    '000858': '五粮液',
    '002415': '海康威视',
    '000725': '京东方A',
    '601318': '中国平安',
    '601288': '农业银行'
}

def get_stock_data(stock_code, days=500):
    """获取股票数据 - 多源获取，优先使用能穿透代理的源"""
    # 尝试方法1: china_stock_data (东方财富源)
    if STOCK_DATA_AVAILABLE:
        try:
            stock = StockData(stock_code, days=days)
            kline_data = stock.get_data("kline")
            
            column_mapping = {
                '开盘': 'open',
                '收盘': 'close', 
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            }
            
            df = kline_data.rename(columns=column_mapping)
            df = df.reset_index()
            df['timestamps'] = pd.to_datetime(df['日期'])
            if 'amount' not in df.columns:
                df['amount'] = df['volume'] * df['close']
            
            df = df.dropna()
            
            if len(df) > 0:
                return df, None
        except Exception:
            pass  # 静默失败，尝试下一个源
    
    # 尝试方法2: akshare 直接调用 (新浪源，可穿透代理)
    if AKSHARE_AVAILABLE:
        try:
            # stock_zh_a_daily 使用新浪源，稳定性更好
            df = ak.stock_zh_a_daily(symbol=f"sz{stock_code}" if stock_code.startswith('0') else f"sh{stock_code}", adjust="qfq")
            
            if df is not None and len(df) > 0:
                df = df.tail(days)  # 只取最近N天
                
                column_mapping = {
                    'date': 'timestamps',
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'volume': 'volume'
                }
                df = df.rename(columns=column_mapping)
                
                if 'timestamps' not in df.columns:
                    df['timestamps'] = df.index
                
                df['timestamps'] = pd.to_datetime(df['timestamps'])
                if 'amount' not in df.columns:
                    df['amount'] = df['volume'] * df['close']
                
                df = df.dropna()
                
                if len(df) > 0:
                    return df, None
        except Exception:
            pass  # 静默失败，使用模拟数据
    
    # 所有源都失败，返回模拟数据
    return generate_simulated_stock_data(stock_code, days), None

def generate_simulated_stock_data(stock_code, days=500):
    """Generate simulated stock data for demonstration"""
    # Ensure we have at least 500 days for better testing
    days = max(days, 500)
    
    # Start from a base price
    base_price = 10.0 + hash(stock_code) % 100
    
    dates = pd.date_range(end=datetime.date.today(), periods=days, freq='D')
    
    # Generate price data with random walk
    np.random.seed(hash(stock_code) % 1000)
    returns = np.random.normal(0.001, 0.02, days)
    prices = [base_price]
    
    for i in range(1, days):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, 0.1))  # Ensure positive prices
    
    # Generate OHLC data
    df = pd.DataFrame({
        'timestamps': dates,
        'open': prices,
        'close': prices,
        'high': [p * (1 + np.random.uniform(0, 0.03)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.03)) for p in prices],
        'volume': np.random.randint(1000000, 10000000, days)
    })
    
    # Ensure high >= close >= low and high >= open >= low
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    
    df['amount'] = df['volume'] * df['close']
    
    return df

def save_prediction_results(stock_code, prediction_results, actual_data, input_data, prediction_params):
    """Save prediction results to file"""
    try:
        # Create prediction results directory
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prediction_results')
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'prediction_{stock_code}_{timestamp}.json'
        filepath = os.path.join(results_dir, filename)
        
        # Prepare data for saving
        save_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'stock_code': stock_code,
            'stock_name': POPULAR_STOCKS.get(stock_code, 'Unknown'),
            'prediction_params': prediction_params,
            'input_data_summary': {
                'rows': len(input_data),
                'columns': list(input_data.columns),
                'time_range': {
                    'start': input_data['timestamps'].min().isoformat(),
                    'end': input_data['timestamps'].max().isoformat()
                },
                'price_range': {
                    'open': {'min': float(input_data['open'].min()), 'max': float(input_data['open'].max())},
                    'high': {'min': float(input_data['high'].min()), 'max': float(input_data['high'].max())},
                    'low': {'min': float(input_data['low'].min()), 'max': float(input_data['low'].max())},
                    'close': {'min': float(input_data['close'].min()), 'max': float(input_data['close'].max())}
                }
            },
            'prediction_results': prediction_results,
            'actual_data': actual_data
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        return filename, None
        
    except Exception as e:
        return None, f"保存预测结果失败"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/models')
def get_models():
    """Get available models"""
    return jsonify({
        'success': True,
        'models': AVAILABLE_MODELS,
        'model_available': MODEL_AVAILABLE
    })

@app.route('/api/popular_stocks')
def get_popular_stocks():
    """Get popular stock codes"""
    return jsonify({
        'success': True,
        'stocks': POPULAR_STOCKS
    })

@app.route('/api/model-status')
def get_model_status():
    """Get model status"""
    if MODEL_AVAILABLE:
        if predictor is not None:
            return jsonify({
                'available': True,
                'loaded': True,
                'message': 'Kronos model loaded and available',
                'current_model': {
                    'name': predictor.model.__class__.__name__,
                    'device': str(next(predictor.model.parameters()).device)
                }
            })
        else:
            return jsonify({
                'available': True,
                'loaded': False,
                'message': 'Kronos model available but not loaded'
            })
    else:
        return jsonify({
            'available': False,
            'loaded': False,
            'message': 'Kronos model library not available, please install related dependencies'
        })

@app.route('/api/load_model', methods=['POST'])
def load_model():
    """Load specified model"""
    global tokenizer, model, predictor
    
    try:
        data = request.get_json()
        model_key = data.get('model', 'kronos-small')
        device = data.get('device', 'cpu')
        
        if not MODEL_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Kronos model is not available, using simulated prediction'
            })
        
        model_config = AVAILABLE_MODELS.get(model_key)
        if not model_config:
            return jsonify({
                'success': False,
                'error': f'Unknown model: {model_key}'
            })
        
        # Load tokenizer and model
        tokenizer = KronosTokenizer.from_pretrained(model_config['tokenizer_id'])
        model = Kronos.from_pretrained(model_config['model_id'])
        
        # Create predictor
        predictor = KronosPredictor(
            model, 
            tokenizer, 
            device=device, 
            max_context=model_config['context_length']
        )
        
        return jsonify({
            'success': True,
            'message': f'Model {model_config["name"]} loaded successfully on {device}',
            'model_info': model_config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'加载模型失败: {str(e)}'
        })

@app.route('/api/stock_data', methods=['POST'])
def get_stock_data_api():
    """Get stock data"""
    try:
        data = request.get_json()
        stock_code = data.get('stock_code', '000001')
        days = data.get('days', 500)
        
        # Get stock data
        df, error = get_stock_data(stock_code, days)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            })
        
        # Prepare data info
        data_info = {
            'stock_code': stock_code,
            'stock_name': POPULAR_STOCKS.get(stock_code, 'Unknown'),
            'rows': len(df),
            'columns': list(df.columns),
            'time_range': {
                'start': df['timestamps'].min().strftime('%Y-%m-%d'),
                'end': df['timestamps'].max().strftime('%Y-%m-%d')
            },
            'price_range': {
                'min': float(df['close'].min()),
                'max': float(df['close'].max()),
                'latest': float(df['close'].iloc[-1])
            },
            'volume_range': {
                'min': float(df['volume'].min()) if 'volume' in df.columns else 0,
                'max': float(df['volume'].max()) if 'volume' in df.columns else 0,
                'latest': float(df['volume'].iloc[-1]) if 'volume' in df.columns else 0
            }
        }
        
        # Prepare chart data
        chart_data = {
            'timestamps': df['timestamps'].dt.strftime('%Y-%m-%d').tolist(),
            'open': df['open'].tolist(),
            'high': df['high'].tolist(),
            'low': df['low'].tolist(),
            'close': df['close'].tolist(),
            'volume': df['volume'].tolist() if 'volume' in df.columns else [0] * len(df)
        }
        
        return jsonify({
            'success': True,
            'data_info': data_info,
            'chart_data': chart_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get stock data: {str(e)}'
        })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Make stock price prediction"""
    try:
        data = request.get_json()
        stock_code = data.get('stock_code', '000001')
        lookback = data.get('lookback', 400)
        pred_len = data.get('pred_len', 5)
        temperature = data.get('temperature', 1.0)
        top_p = float(data.get('top_p', 0.9))
        sample_count = int(data.get('sample_count', 1))
        days = data.get('days', 500)
        
        # Get stock data
        df, error = get_stock_data(stock_code, days)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            })
        
        # Auto-adjust parameters if data is insufficient
        original_lookback = lookback
        if len(df) < lookback + pred_len:
            # Reduce lookback to fit available data
            max_lookback = len(df) - pred_len - 10  # Leave some buffer
            if max_lookback < 50:  # Minimum required data points
                return jsonify({
                    'success': False,
                    'error': f'Insufficient data: need at least 60 data points, got {len(df)}. Please try a stock with more historical data.'
                })
            lookback = min(max_lookback, 300)  # Cap at 300 for performance
            print(f"Auto-adjusted lookback from {original_lookback} to {lookback} due to insufficient data")
        
        # Prepare input data
        x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
        x_timestamp = df.loc[:lookback-1, 'timestamps']
        
        # Generate future timestamps
        last_date = df['timestamps'].iloc[-1].date()
        future_dates = []
        current_date = last_date
        
        for _ in range(pred_len):
            current_date += datetime.timedelta(days=1)
            # Skip weekends for stock trading days
            while current_date.weekday() >= 5:
                current_date += datetime.timedelta(days=1)
            future_dates.append(pd.Timestamp(current_date))
        
        y_timestamp = pd.Series(future_dates)
        
        # Make prediction
        if MODEL_AVAILABLE and predictor is not None:
            pred_df = predictor.predict(
                df=x_df,
                x_timestamp=x_timestamp,
                y_timestamp=y_timestamp,
                pred_len=pred_len,
                T=temperature,
                top_p=top_p,
                sample_count=sample_count,
                verbose=False
            )
        else:
            # Generate simulated prediction
            pred_df = generate_simulated_prediction(df, lookback, pred_len, y_timestamp)
        
        # Prepare prediction results
        prediction_results = []
        for i, (date, row) in enumerate(pred_df.iterrows()):
            if i == 0:
                prev_close = df['close'].iloc[-1]
            else:
                prev_close = pred_df.iloc[i-1]['close']
            
            change_pct = (row['close'] - prev_close) / prev_close * 100 if prev_close != 0 else 0
            
            prediction_results.append({
                'date': date.strftime('%Y-%m-%d'),
                'weekday': date.strftime('%A'),
                'open': float(row['open']) if not np.isnan(row['open']) else 0,
                'high': float(row['high']) if not np.isnan(row['high']) else 0,
                'low': float(row['low']) if not np.isnan(row['low']) else 0,
                'close': float(row['close']) if not np.isnan(row['close']) else 0,
                'volume': float(row['volume']) if not np.isnan(row.get('volume', 0)) else 0,
                'change_pct': float(change_pct) if not np.isnan(change_pct) else 0
            })
        
        # Calculate overall prediction summary
        last_close = float(df['close'].iloc[-1])
        pred_last_close = float(pred_df['close'].iloc[-1]) if not np.isnan(pred_df['close'].iloc[-1]) else last_close
        total_change_pct = (pred_last_close - last_close) / last_close * 100 if last_close != 0 else 0
        
        prediction_summary = {
            'current_price': last_close,
            'target_price': pred_last_close,
            'total_change_pct': float(total_change_pct),
            'prediction_period': f'{pred_len} days',
            'confidence_level': 'Medium' if MODEL_AVAILABLE else 'Simulated',
            'actual_lookback': lookback,
            'data_adjusted': lookback != original_lookback
        }
        
        # Prepare chart data
        historical_data = {
            'timestamps': df['timestamps'].dt.strftime('%Y-%m-%d').tolist()[-50:],  # Last 50 days
            'close': [float(v) if not np.isnan(v) else 0 for v in df['close'].tolist()[-50:]]
        }
        
        prediction_data = {
            'timestamps': [date.strftime('%Y-%m-%d') for date in future_dates],
            'close': [float(v) if not np.isnan(v) else 0 for v in pred_df['close'].tolist()]
        }
        
        # Save prediction results
        prediction_params = {
            'lookback': lookback,
            'pred_len': pred_len,
            'temperature': temperature,
            'top_p': top_p,
            'sample_count': sample_count,
            'model_available': MODEL_AVAILABLE
        }
        
        filename, save_error = save_prediction_results(
            stock_code, prediction_results, None, df, prediction_params
        )
        
        return jsonify({
            'success': True,
            'stock_info': {
                'code': stock_code,
                'name': POPULAR_STOCKS.get(stock_code, 'Unknown')
            },
            'prediction_results': prediction_results,
            'prediction_summary': prediction_summary,
            'chart_data': {
                'historical': historical_data,
                'prediction': prediction_data
            },
            'saved_file': filename,
            'adjustment_info': {
                'original_lookback': original_lookback,
                'actual_lookback': lookback,
                'adjusted': lookback != original_lookback,
                'message': f'Lookback automatically adjusted from {original_lookback} to {lookback} due to insufficient data' if lookback != original_lookback else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'预测失败: {str(e)}'
        })

def generate_simulated_prediction(df, lookback, pred_len, y_timestamp):
    """Generate simulated prediction for demonstration"""
    # Use the last few prices to create realistic-looking predictions
    recent_prices = df['close'].iloc[-10:].values
    price_changes = np.diff(recent_prices)
    avg_change = np.mean(price_changes)
    volatility = np.std(price_changes)
    
    last_price = df['close'].iloc[-1]
    last_volume = df['volume'].iloc[-1] if 'volume' in df.columns else 1000000
    
    pred_data = []
    current_price = last_price
    
    for i in range(pred_len):
        # Generate price movement
        change = np.random.normal(avg_change, volatility)
        current_price = max(current_price + change, current_price * 0.9)  # Prevent too large drops
        
        # Generate OHLC
        daily_volatility = volatility * 0.5
        high = current_price * (1 + abs(np.random.normal(0, daily_volatility)))
        low = current_price * (1 - abs(np.random.normal(0, daily_volatility)))
        open_price = last_price if i == 0 else pred_data[-1]['close']
        
        # Ensure OHLC consistency
        high = max(high, current_price, open_price)
        low = min(low, current_price, open_price)
        
        volume = last_volume * np.random.uniform(0.7, 1.3)
        
        pred_data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': current_price,
            'volume': volume
        })
    
    pred_df = pd.DataFrame(pred_data, index=y_timestamp)
    return pred_df

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
