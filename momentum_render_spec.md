# デュアル・モメンタム計算アプリ MVP実装仕様書（Renderデプロイ版・完全版）

## 0. MVP最終チェックリスト

### 0.1 コア価値の定義
**「正しく一貫してモメンタムを算出できること」**
- 最大5ティッカーのシンプルリターンを計算
- 共通アンカー日付で全銘柄を統一比較
- データ不足時は明示的にNone返却

### 0.2 スコープ境界
**やること**
- Unit/N/as_of_periodによるモメンタム計算
- 土曜丸め込み（Week時）
- 共通アンカー特定と表示
- 実行条件サマリー表示
- Renderへのシングルサービスデプロイ

**やらないこと**
- 入力バリデーション（API委譲）
- 詳細エラー分類
- UI装飾（絵文字、過剰なスタイル）
- 非同期処理
- キャッシュ
- render.yaml使用

## 1. プロジェクト構成（Renderデプロイ版MVP）

```
dual-momentum-mvp/
├── main.py               # FastAPIアプリケーション（静的配信含む）（150行想定）
├── config.py             # 環境変数管理（15行想定）
├── api_client.py         # 自作API通信（45行想定）
├── momentum.py           # モメンタム計算ロジック（120行想定）
├── static/
│   └── index.html        # 単一HTML（300行想定）
├── .env                  # 環境変数（Git除外）
├── .env.example          # 環境変数テンプレート
├── .gitignore            # Git除外設定
├── requirements.txt      # Python依存（5パッケージ）
└── README.md             # 仕様と起動方法（100行想定）
```

### 1.1 バージョン情報（2025年9月8日現在）
- Python: 3.13.7（Renderデフォルト）
- FastAPI: 最新版
- uvicorn: 0.35.0以上
- デプロイ先: Render Web Service

## 2. 詳細モジュール仕様

### 2.1 `main.py`

```python
"""
FastAPIアプリケーション本体
責務：エンドポイント定義、リクエスト/レスポンス処理、静的ファイル配信
"""

# インポート
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
import momentum
import config

# Pydanticモデル（2つのみ）
class ComputeRequest(BaseModel):
    """モメンタム計算リクエスト"""
    tickers: List[str] = Field(..., max_items=5, min_items=1)
    unit: Literal["month", "week", "day"]
    n: int = Field(..., ge=1)  # 1以上
    as_of_period: str  # YYYY-MM or YYYY-MM-DD

class ComputeResponse(BaseModel):
    """モメンタム計算レスポンス"""
    results: List[Optional[float]]  # None許容
    summary: Dict[str, Any]
    anchors: Dict[str, str]

# FastAPIインスタンス
app = FastAPI(title="Dual Momentum Calculator MVP", version="1.0.0")

# 静的ファイル配信（HTMLのみ）
app.mount("/static", StaticFiles(directory="static"), name="static")

# ルートアクセス時にindex.htmlを返す
@app.get("/")
async def read_index():
    """ルートアクセスでindex.htmlを返す"""
    return FileResponse('static/index.html')

# エンドポイント
@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "api_base": config.STOCK_API_BASE}

@app.post("/compute", response_model=ComputeResponse)
async def compute_momentum(request: ComputeRequest):
    """
    モメンタム計算エンドポイント
    
    処理フロー：
    1. リクエスト受信
    2. momentum.calculate()呼び出し
    3. 結果をレスポンス形式に整形
    4. 返却
    
    エラー時：
    - 個別ティッカーエラー → None
    - 全体エラー → HTTPException
    """
    try:
        # モメンタム計算実行
        results, anchors = momentum.calculate(
            tickers=request.tickers,
            unit=request.unit,
            n=request.n,
            as_of_period=request.as_of_period
        )
        
        # レスポンス構築
        return ComputeResponse(
            results=results,
            summary={
                "tickers": request.tickers,
                "unit": request.unit,
                "n": request.n,
                "as_of_period": request.as_of_period
            },
            anchors=anchors
        )
    except Exception as e:
        # 予期しないエラー
        raise HTTPException(status_code=500, detail=str(e))
```

### 2.2 `config.py`

```python
"""
環境変数と設定管理
責務：設定値の一元管理
"""

import os
from dotenv import load_dotenv

# .envファイル読み込み
load_dotenv()

# API設定
STOCK_API_BASE = os.getenv("STOCK_API_BASE", "https://stockdata-api-6xok.onrender.com/")
API_KEY = os.getenv("API_KEY", "")  # 将来用、現在は未使用

# 固定値
TIMEOUT = 30  # API通信タイムアウト（秒）
MAX_TICKERS = 5  # 最大ティッカー数
```

### 2.3 `api_client.py`

```python
"""
バムさん自作APIクライアント
責務：外部API通信、データ取得
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import config

def fetch_prices(
    symbols: List[str], 
    from_date: str, 
    to_date: str
) -> Dict[str, List[Dict]]:
    """
    株価データ取得
    
    Args:
        symbols: ティッカーリスト（例：["AAPL", "MSFT"]）
        from_date: 開始日（YYYY-MM-DD）
        to_date: 終了日（YYYY-MM-DD）
    
    Returns:
        {
            "AAPL": [
                {"date": "2025-09-01", "close": 181.5},
                {"date": "2025-09-02", "close": 182.0},
                ...
            ],
            "MSFT": [...],
            ...
        }
        エラー時は該当ティッカーが空リストまたは欠落
    
    実装詳細：
        - GET /v1/prices を1回呼び出し
        - symbolsはカンマ区切りで結合
        - タイムアウト30秒
        - エラー時は空辞書返却（エラー詳細は区別しない）
    """
    
    # URLとパラメータ構築
    url = f"{config.STOCK_API_BASE}v1/prices"
    params = {
        "symbols": ",".join(symbols),
        "from": from_date,
        "to": to_date
    }
    
    # APIキーが設定されている場合（将来用）
    headers = {}
    if config.API_KEY:
        headers["Authorization"] = f"Bearer {config.API_KEY}"
    
    try:
        # API呼び出し（同期）
        response = requests.get(
            url, 
            params=params, 
            headers=headers,
            timeout=config.TIMEOUT
        )
        
        # ステータスチェック
        if response.status_code != 200:
            print(f"API returned {response.status_code}")
            return {}
        
        # レスポンス解析
        data = response.json()
        
        # 必要なフィールドのみ抽出
        result = {}
        for ticker, prices in data.items():
            if prices:  # データが存在する場合
                result[ticker] = [
                    {"date": p["date"], "close": p["close"]} 
                    for p in prices
                ]
            else:
                result[ticker] = []
        
        return result
        
    except requests.Timeout:
        print(f"API timeout: symbols={symbols}, from={from_date}, to={to_date}")
        return {}
    except requests.RequestException as e:
        print(f"API request failed: {e}, symbols={symbols}")
        return {}
    except Exception as e:
        print(f"Unexpected error: {e}, symbols={symbols}")
        return {}
```

### 2.4 `momentum.py`

```python
"""
モメンタム計算ロジック
責務：共通アンカー特定、モメンタム値算出
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional, Tuple
import api_client

def calculate(
    tickers: List[str],
    unit: str,
    n: int,
    as_of_period: str
) -> Tuple[List[Optional[float]], Dict[str, str]]:
    """
    モメンタム計算メイン関数
    
    Args:
        tickers: ティッカーリスト
        unit: "month" | "week" | "day"
        n: 期間数
        as_of_period: 基準期（YYYY-MM or YYYY-MM-DD）
    
    Returns:
        (
            [0.034, None, -0.021, ...],  # 各ティッカーのモメンタム
            {"current": "2025-09-05", "past": "2025-08-08"}  # アンカー日付
        )
    
    アルゴリズム：
        1. 日付レンジ計算（最小限）
        2. API経由でデータ取得
        3. 共通アンカー特定
        4. 各ティッカーのモメンタム計算
    """
    
    # Step 1: 日付レンジ計算
    from_date, to_date = calculate_date_range(unit, n, as_of_period)
    
    # Step 2: データ取得
    price_data = api_client.fetch_prices(tickers, from_date, to_date)
    
    # Step 3: 共通アンカー特定
    current_anchor, past_anchor = find_common_anchors(
        price_data, unit, n, as_of_period
    )
    
    # アンカーが特定できない場合
    if not current_anchor or not past_anchor:
        return [None] * len(tickers), {"current": "N/A", "past": "N/A"}
    
    # Step 4: モメンタム計算
    results = []
    for ticker in tickers:
        if ticker not in price_data or not price_data[ticker]:
            results.append(None)
            continue
        
        # 該当日の価格を探す
        current_price = find_price_on_date(price_data[ticker], current_anchor)
        past_price = find_price_on_date(price_data[ticker], past_anchor)
        
        if current_price and past_price:
            momentum = (current_price / past_price) - 1
            results.append(momentum)
        else:
            results.append(None)
    
    return results, {"current": current_anchor, "past": past_anchor}


def calculate_date_range(unit: str, n: int, as_of_period: str) -> Tuple[str, str]:
    """
    データ取得用の日付レンジ計算（最小限）
    
    Args:
        unit: "month" | "week" | "day"
        n: 期間数
        as_of_period: 基準期
    
    Returns:
        (from_date, to_date) 形式：YYYY-MM-DD
    
    ロジック：
        - Month: N+1ヶ月分
        - Week: N+1週分
        - Day: N+20営業日分（バッファ込み）
    """
    
    # as_of_periodを日付として解釈
    if unit == "month":
        # YYYY-MM形式 → 月末日
        year, month = map(int, as_of_period.split("-"))
        to_date = datetime(year, month, 1) + relativedelta(months=1) - timedelta(days=1)
        from_date = to_date - relativedelta(months=n+1)
    else:
        # YYYY-MM-DD形式
        to_date = datetime.strptime(as_of_period, "%Y-%m-%d")
        
        if unit == "week":
            # 土曜に丸め込み
            to_date = round_to_saturday(to_date)
            from_date = to_date - timedelta(weeks=n+1)
        else:  # day
            from_date = to_date - timedelta(days=(n+20)*2)  # 営業日考慮のバッファ
    
    return from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")


def round_to_saturday(date: datetime) -> datetime:
    """
    指定日を含む週の土曜日に丸め込み
    
    Args:
        date: 任意の日付
    
    Returns:
        その週の土曜日
    
    例：
        2025-09-03（水） → 2025-09-06（土）
        2025-09-07（日） → 2025-09-13（土）※次週の土曜
    """
    days_until_saturday = (5 - date.weekday()) % 7
    if days_until_saturday == 0 and date.weekday() != 5:
        days_until_saturday = 7  # 日曜〜金曜は次の土曜へ
    return date + timedelta(days=days_until_saturday)


def find_common_anchors(
    price_data: Dict[str, List[Dict]],
    unit: str,
    n: int,
    as_of_period: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    共通アンカー日付の特定
    
    Args:
        price_data: {ticker: [{"date": "YYYY-MM-DD", "close": float}, ...]}
        unit: "month" | "week" | "day"
        n: 期間数
        as_of_period: 基準期
    
    Returns:
        (current_anchor, past_anchor) or (None, None)
    
    アルゴリズム：
        1. 全ティッカーの日付集合の交差を取る
        2. Unit別ルールで現在アンカーを特定
        3. N期前の過去アンカーを特定
    """
    
    # Step 1: 共通日付の抽出
    if not price_data:
        return None, None
    
    # 各ティッカーの日付集合を作成
    date_sets = []
    for ticker, prices in price_data.items():
        if prices:
            dates = {p["date"] for p in prices}
            date_sets.append(dates)
    
    if not date_sets:
        return None, None
    
    # 交差を取る
    common_dates = sorted(set.intersection(*date_sets))
    if not common_dates:
        return None, None
    
    # Step 2: 現在アンカーの特定
    current_anchor = None
    
    if unit == "month":
        # as_of_periodの直前月の最終取引日
        year, month = map(int, as_of_period.split("-"))
        target_month = datetime(year, month, 1) - timedelta(days=1)  # 前月末
        target_str = target_month.strftime("%Y-%m")
        
        # 該当月の最後の共通日付
        for date in reversed(common_dates):
            if date.startswith(target_str):
                current_anchor = date
                break
                
    elif unit == "week":
        # as_of_periodを土曜に丸めて、その週の最終取引日
        base_date = datetime.strptime(as_of_period, "%Y-%m-%d")
        saturday = round_to_saturday(base_date)
        week_start = saturday - timedelta(days=6)  # 日曜
        week_end = saturday
        
        # 該当週の最後の共通日付
        for date in reversed(common_dates):
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            if week_start <= date_obj <= week_end:
                current_anchor = date
                break
                
    else:  # day
        # as_of_periodの直前の取引日
        base_date = as_of_period
        for date in reversed(common_dates):
            if date <= base_date:
                current_anchor = date
                break
    
    if not current_anchor:
        return None, None
    
    # Step 3: 過去アンカーの特定
    current_idx = common_dates.index(current_anchor)
    
    if unit == "month":
        # N月前の最終取引日
        current_date = datetime.strptime(current_anchor, "%Y-%m-%d")
        target_date = current_date - relativedelta(months=n)
        target_str = target_date.strftime("%Y-%m")
        
        past_anchor = None
        for date in reversed(common_dates[:current_idx]):
            if date.startswith(target_str):
                past_anchor = date
                break
                
    elif unit == "week":
        # N週前の最終取引日
        current_date = datetime.strptime(current_anchor, "%Y-%m-%d")
        target_saturday = current_date - timedelta(weeks=n)
        # 最も近い金曜を探す
        target_friday = target_saturday - timedelta(days=1)
        
        past_anchor = None
        min_diff = float('inf')
        for date in common_dates[:current_idx]:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            diff = abs((date_obj - target_friday).days)
            if diff < min_diff and diff <= 7:  # 1週間以内
                min_diff = diff
                past_anchor = date
                
    else:  # day
        # N営業日前
        if current_idx >= n:
            past_anchor = common_dates[current_idx - n]
        else:
            past_anchor = None
    
    return current_anchor, past_anchor


def find_price_on_date(prices: List[Dict], target_date: str) -> Optional[float]:
    """
    指定日の価格を取得
    
    Args:
        prices: [{"date": "YYYY-MM-DD", "close": float}, ...]
        target_date: 検索対象日
    
    Returns:
        該当日の終値 or None
    """
    for price in prices:
        if price["date"] == target_date:
            return price["close"]
    return None
```

### 2.5 `.env.example`

```bash
# バムさん自作API
STOCK_API_BASE=https://stockdata-api-6xok.onrender.com/

# APIキー（将来用、現在は空）
API_KEY=
```

### 2.6 `requirements.txt`

```
fastapi
uvicorn[standard]
requests
python-dateutil
python-dotenv
```

### 2.7 `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment variables
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### 2.8 `static/index.html`

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>デュアル・モメンタム計算（MVP）</title>
    <style>
        /* 最小限のスタイル */
        body {
            font-family: monospace;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        label {
            display: inline-block;
            width: 150px;
        }
        
        input, select {
            width: 200px;
            padding: 5px;
            font-family: monospace;
        }
        
        .ticker-input {
            display: block;
            margin-bottom: 5px;
        }
        
        button {
            padding: 10px 30px;
            margin-top: 20px;
            font-size: 16px;
        }
        
        #results {
            margin-top: 30px;
            padding: 15px;
            background-color: #f5f5f5;
            white-space: pre-wrap;
            font-family: monospace;
        }
        
        .anchors {
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .error {
            color: red;
        }
    </style>
</head>
<body>
    <h1>デュアル・モメンタム計算（MVP）</h1>
    
    <form id="momentum-form">
        <!-- ティッカー入力 -->
        <div class="input-group">
            <label>ティッカー（最大5個）:</label>
            <div>
                <input type="text" class="ticker-input" placeholder="例: AAPL" maxlength="10">
                <input type="text" class="ticker-input" placeholder="例: MSFT" maxlength="10">
                <input type="text" class="ticker-input" placeholder="例: GOOGL" maxlength="10">
                <input type="text" class="ticker-input" placeholder="例: AMZN" maxlength="10">
                <input type="text" class="ticker-input" placeholder="例: TSLA" maxlength="10">
            </div>
        </div>
        
        <!-- Unit選択 -->
        <div class="input-group">
            <label for="unit">Unit:</label>
            <select id="unit" required>
                <option value="">選択してください</option>
                <option value="month">Month</option>
                <option value="week">Week</option>
                <option value="day">Day</option>
            </select>
        </div>
        
        <!-- N入力 -->
        <div class="input-group">
            <label for="n">N（期間数）:</label>
            <input type="number" id="n" min="1" required>
        </div>
        
        <!-- as_of_period入力 -->
        <div class="input-group">
            <label for="as_of_period">基準期:</label>
            <input type="text" id="as_of_period" placeholder="形式はUnitに依存" required>
            <span id="period-hint"></span>
        </div>
        
        <button type="submit">計算</button>
    </form>
    
    <!-- 結果表示エリア -->
    <div id="results"></div>
    
    <script>
        // フォーム要素
        const form = document.getElementById('momentum-form');
        const unitSelect = document.getElementById('unit');
        const periodInput = document.getElementById('as_of_period');
        const periodHint = document.getElementById('period-hint');
        const resultsDiv = document.getElementById('results');
        
        // Unit変更時の処理
        unitSelect.addEventListener('change', function() {
            const unit = this.value;
            
            // 入力形式のヒント更新
            if (unit === 'month') {
                periodInput.placeholder = 'YYYY-MM';
                periodHint.textContent = '（例: 2025-09）';
                periodInput.type = 'month';
            } else if (unit === 'week') {
                periodInput.placeholder = 'YYYY-MM-DD';
                periodHint.textContent = '（土曜日のみ選択可能）';
                periodInput.type = 'date';
                periodInput.step = '7';
            } else if (unit === 'day') {
                periodInput.placeholder = 'YYYY-MM-DD';
                periodHint.textContent = '（例: 2025-09-08）';
                periodInput.type = 'date';
                periodInput.step = '1';
            } else {
                periodInput.placeholder = '形式はUnitに依存';
                periodHint.textContent = '';
                periodInput.type = 'text';
            }
        });
        
        // 日付選択時の処理（Week時に土曜日に自動調整）
        periodInput.addEventListener('change', function() {
            if (unitSelect.value === 'week' && this.value) {
                const selectedDate = new Date(this.value);
                const dayOfWeek = selectedDate.getDay();
                
                // 土曜日でない場合は、次の土曜日に調整
                if (dayOfWeek !== 6) {
                    const daysUntilSaturday = (6 - dayOfWeek + 7) % 7 || 7;
                    selectedDate.setDate(selectedDate.getDate() + daysUntilSaturday);
                    
                    // YYYY-MM-DD形式に変換
                    const year = selectedDate.getFullYear();
                    const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
                    const day = String(selectedDate.getDate()).padStart(2, '0');
                    this.value = `${year}-${month}-${day}`;
                    
                    // ユーザーに通知
                    periodHint.textContent = '（土曜日に自動調整されました）';
                    periodHint.style.color = 'blue';
                    setTimeout(() => {
                        periodHint.textContent = '（土曜日のみ選択可能）';
                        periodHint.style.color = '';
                    }, 2000);
                }
            }
        });
        
        // フォーム送信処理
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // ティッカー収集（空欄除外）
            const tickerInputs = document.querySelectorAll('.ticker-input');
            const tickers = [];
            tickerInputs.forEach(input => {
                if (input.value.trim()) {
                    tickers.push(input.value.trim().toUpperCase());
                }
            });
            
            // 入力チェック
            if (tickers.length === 0) {
                resultsDiv.innerHTML = '<span class="error">エラー: ティッカーを1つ以上入力してください</span>';
                return;
            }
            
            // リクエスト構築
            const requestData = {
                tickers: tickers,
                unit: unitSelect.value,
                n: parseInt(document.getElementById('n').value),
                as_of_period: periodInput.value
            };
            
            // as_of_periodの形式調整（monthの場合）
            if (requestData.unit === 'month' && requestData.as_of_period.length === 7) {
                // month inputは YYYY-MM 形式で返す
                // そのまま使用
            }
            
            resultsDiv.innerHTML = '計算中...';
            
            try {
                // API呼び出し（相対パス）
                const response = await fetch('/compute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTPエラー: ${response.status}`);
                }
                
                const data = await response.json();
                
                // 結果表示
                displayResults(data, requestData);
                
            } catch (error) {
                resultsDiv.innerHTML = `<span class="error">エラー: ${error.message}</span>`;
            }
        });
        
        // 結果表示関数
        function displayResults(data, request) {
            let html = '';
            
            // 実行条件サマリー
            html += '=== 実行条件 ===\\n';
            html += `Unit: ${request.unit}\\n`;
            html += `N: ${request.n}\\n`;
            html += `基準期: ${request.as_of_period}\\n`;
            html += `ティッカー: ${request.tickers.join(', ')}\\n`;
            html += '\\n';
            
            // 計算結果
            html += '=== 計算結果 ===\\n';
            for (let i = 0; i < request.tickers.length; i++) {
                const ticker = request.tickers[i];
                const result = data.results[i];
                
                if (result === null) {
                    html += `${ticker}: None\\n`;
                } else {
                    // 小数点そのまま表示（丸めなし）
                    html += `${ticker}: ${result}\\n`;
                }
            }
            
            // 共通アンカー日付
            html += '\\n<span class="anchors">';
            html += '=== 共通アンカー ===\\n';
            html += `現在: ${data.anchors.current}\\n`;
            html += `過去: ${data.anchors.past}\\n';
            html += '</span>';
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>
```

## 3. Renderデプロイ手順書

### 3.1 GitHub準備

```bash
# リポジトリ作成
git init dual-momentum-mvp
cd dual-momentum-mvp

# ファイル配置
# 上記の構成通りにファイルを作成

# Git管理
git add .
git commit -m "Initial commit: Dual Momentum MVP"

# GitHubにプッシュ
git remote add origin https://github.com/[your-username]/dual-momentum-mvp.git
git push -u origin main
```

### 3.2 Renderデプロイ設定

1. **Renderダッシュボードアクセス**
   - https://dashboard.render.com にログイン

2. **新規Web Service作成**
   - 「New +」→「Web Service」を選択
   - GitHubリポジトリを接続

3. **設定入力**
   ```yaml
   Name: dual-momentum-mvp
   Region: Oregon (US West)
   Branch: main
   Root Directory: （空欄）
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **環境変数設定**
   - Key: `STOCK_API_BASE`
   - Value: `https://stockdata-api-6xok.onrender.com/`

5. **プラン選択**
   - Free（MVP用）

6. **デプロイ実行**
   - 「Create Web Service」クリック

### 3.3 デプロイ確認

```bash
# デプロイ完了後のURL
https://dual-momentum-mvp.onrender.com

# ヘルスチェック
curl https://dual-momentum-mvp.onrender.com/health

# ブラウザアクセス
# https://dual-momentum-mvp.onrender.com で画面表示確認
```

## 4. 実装手順書（ローカル開発）

### 4.1 環境構築

```bash
# プロジェクトディレクトリ作成
mkdir dual-momentum-mvp
cd dual-momentum-mvp

# Python仮想環境（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt

# .envファイル作成
cp .env.example .env
```

### 4.2 ローカル起動

```bash
# バックエンド起動
uvicorn main:app --reload --port 8000

# ブラウザアクセス
# http://localhost:8000 で画面表示
# http://localhost:8000/health でヘルスチェック
```

## 5. 動作確認手順

### 5.1 正常系テスト（Month）

```
入力:
- Tickers: AAPL, MSFT
- Unit: month
- N: 3
- as_of_period: 2025-09

期待結果:
- 2025年8月末と2025年5月末の価格でモメンタム計算
- 共通アンカー日付が表示される
```

### 5.2 正常系テスト（Week）

```
入力:
- Tickers: GOOGL
- Unit: week
- N: 4
- as_of_period: 2025-09-03（水曜→土曜に自動調整）

期待結果:
- 2025-09-06の週と4週前でモメンタム計算
- UI上で土曜日への自動調整が実行される
- 共通アンカー日付が表示される

**補足**：`as_of_period` が**土曜そのもの**の場合は、その土曜を含む**当週**を用いる（＝当週の最終取引日が現在アンカー）
```

### 5.3 正常系テスト（Day）

```
入力:
- Tickers: AMZN, TSLA
- Unit: day
- N: 20
- as_of_period: 2025-09-08

期待結果:
- 20営業日前との比較
- 共通アンカーで統一比較
```

### 5.4 異常系テスト

```
入力:
- Tickers: INVALID_TICKER
- その他は任意

期待結果:
- 該当ティッカーのみ None
- アプリケーションは停止しない
```

## 6. エラーケース一覧

### 6.1 個別ティッカーレベル（→ None）
- 不正なティッカーコード
- 履歴不足（上場から日が浅い）
- API側でデータ欠損
- 共通アンカー日にデータなし

### 6.2 全体レベル（→ エラーレスポンス）
- API接続失敗
- タイムアウト
- 不正なリクエスト形式

### 6.3 MVP統一ポリシー
**すべて None で返却、理由は区別しない**

## 7. 受け入れ基準（Definition of Done）

### 7.1 機能要件
- [ ] 5ティッカーまでの同時計算が動作
- [ ] Month/Week/Day の3Unit対応
- [ ] 土曜丸め込み（Week時）が正しく動作
- [ ] Week選択時にUIで土曜日自動調整
- [ ] 共通アンカー日付の表示
- [ ] 実行条件サマリーの表示
- [ ] 単一URLでアプリケーション動作

### 7.2 非機能要件
- [ ] APIタイムアウト時もアプリが停止しない
- [ ] データ不足時は None 返却
- [ ] 素のHTMLで動作（外部ライブラリ不使用）
- [ ] Renderへのデプロイ成功
- [ ] CORS設定不要（同一オリジン）

### 7.3 確認項目
- [ ] README.mdに起動手順記載
- [ ] .env.example が存在
- [ ] requirements.txt で依存解決
- [ ] .gitignore でenv除外

## 8. API仕様詳細

### 8.1 POST /compute

#### リクエスト
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "unit": "week",
  "n": 4,
  "as_of_period": "2025-09-06"
}
```

#### レスポンス（正常）
```json
{
  "results": [0.0345678901234567, null, -0.0213456789012345],
  "summary": {
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "unit": "week",
    "n": 4,
    "as_of_period": "2025-09-06"
  },
  "anchors": {
    "current": "2025-09-05",
    "past": "2025-08-08"
  }
}
```

#### レスポンス（エラー）
```json
{
  "detail": "エラーメッセージ"
}
```

### 8.2 GET /health

#### レスポンス
```json
{
  "status": "healthy",
  "api_base": "https://stockdata-api-6xok.onrender.com/"
}
```

### 8.3 GET /

#### レスポンス
- Content-Type: text/html
- static/index.html の内容を返却

## 9. 将来拡張ポイント（MVP対象外）

### 9.1 Phase 2候補
- 詳細エラー分類とメッセージ
- 非同期処理による高速化
- キャッシュ機構
- バッチ処理対応
- 複数の基準期同時計算

### 9.2 Phase 3候補
- UIの美装（CSS framework）
- グラフ表示
- 履歴保存機能
- エクスポート機能
- API認証機能

### 9.3 インフラ候補
- カスタムドメイン設定
- CI/CD設定（GitHub Actions）
- 監視・アラート（Sentry）
- ログ集約（Logtail）
- パフォーマンスモニタリング

## 10. リスクと対処

### 10.1 想定リスク
| リスク | 影響 | MVP対処 |
|--------|------|----------|
| API障害 | 全機能停止 | Noneで返却、エラー表示 |
| レート制限 | 一部取得失敗 | 該当分のみNone |
| データ不整合 | 誤った計算 | 共通アンカーで統一 |
| 未来日入力 | エラー | APIが空データ返却→None |
| Render無料プランの制限 | 応答遅延 | MVP許容範囲内 |

### 10.2 制約事項
- 市場カレンダーはAPI依存
- 調整済み株価はAPI依存
- タイムゾーン考慮なし（API準拠）
- Render無料プランは15分非アクティブでスリープ

## 11. 技術仕様詳細

### 11.1 パッケージバージョン（2025年9月8日現在）
- Python: 3.13.7（Renderデフォルト）
- FastAPI: 最新版
- uvicorn[standard]: 0.35.0以上
- requests: 最新版
- python-dateutil: 最新版
- python-dotenv: 最新版

### 11.2 Render設定詳細
```yaml
Service Type: Web Service
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
Auto-Deploy: Yes（GitHub連携）
```

### 11.3 セキュリティ考慮事項
- 環境変数で機密情報管理
- .gitignoreで.env除外
- 入力値サイズ制限（最大5ティッカー）
- タイムアウト設定（30秒）

## 12. README.md内容

```markdown
# デュアル・モメンタム計算 MVP

## 概要
株式のモメンタム（価格変化率）を計算するWebアプリケーション。
最大5つのティッカーに対して、指定期間のモメンタムを一括計算。

## 機能
- 月次/週次/日次のモメンタム計算
- 最大5ティッカーの同時処理
- 共通アンカー日付による統一比較
- Week選択時の土曜日自動調整

## 技術スタック
- Backend: FastAPI (Python 3.13+)
- Frontend: 純粋なHTML/JavaScript
- Deploy: Render

## ローカル開発

### セットアップ
```bash
# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
```

### 起動
```bash
uvicorn main:app --reload --port 8000
```

ブラウザで http://localhost:8000 にアクセス

## デプロイ

### Render
1. GitHubにpush
2. Renderでリポジトリ接続
3. 環境変数設定（STOCK_API_BASE）
4. デプロイ実行

## API仕様

### POST /compute
モメンタム計算

### GET /health
ヘルスチェック

### GET /
Webインターフェース

## ライセンス
MIT
```

## 13. 最終チェックリスト

### 13.1 実装前確認
- [x] 環境変数設定（STOCK_API_BASE）
- [x] APIエンドポイント確認（/v1/prices）
- [x] 依存パッケージ確認
- [x] ディレクトリ構造確認
- [x] Renderアカウント準備

### 13.2 実装後確認
- [ ] 3Unit（Month/Week/Day）での動作
- [ ] 5ティッカー同時処理
- [ ] None返却の確認
- [ ] 土曜丸め込みの動作（フロント/バック整合）
- [ ] Week選択時のUI自動調整
- [ ] 共通アンカー表示
- [ ] HTMLクォート記述の正常動作
- [ ] /docsでSwagger UI表示
- [ ] /healthでヘルスチェック動作
- [ ] Renderデプロイ成功
- [ ] 本番URL動作確認（コールドスタート含む）

### 13.3 納品物
- [ ] ソースコード（全ファイル）
- [ ] README.md
- [ ] 動作確認済み環境情報
- [ ] Render本番URL

---

**Renderデプロイ版MVP実装の全仕様が確定しました。**