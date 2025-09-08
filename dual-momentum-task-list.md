# デュアル・モメンタムMVP - エンジニアリング実装タスクリスト

## 実装順序と依存関係
- 各タスクは番号順に実装
- [ ] チェックボックスで進捗管理
- 各タスクは**1つのファイル作成**または**1つの関数実装**に限定
- **全33タスク**で構成

---

## PHASE 1: プロジェクト基盤構築（5タスク）

### タスク 1.1: プロジェクトディレクトリ構造作成
- [ ] 完了
- **作成物**: ディレクトリ構造
- **コマンド実行**:
```bash
mkdir -p dual-momentum-mvp/static
cd dual-momentum-mvp
```
- **検証**: `ls -la` でディレクトリ確認

### タスク 1.2: .gitignoreファイル作成
- [ ] 完了
- **作成物**: `.gitignore`
- **内容**: Python、環境変数、IDE、OS関連の除外設定
- **検証**: ファイル存在確認

### タスク 1.3: requirements.txt（ピン止め版）作成
- [ ] 完了
- **作成物**: `requirements.txt`
- **内容**: 5つの依存パッケージ（マイナーバージョンまで固定）
```
fastapi==0.115.*
uvicorn[standard]==0.32.*
requests==2.32.*
python-dateutil==2.9.*
python-dotenv==1.0.*
```
- **検証**: `cat requirements.txt` で内容確認

### タスク 1.4: .env.exampleファイル作成
- [ ] 完了
- **作成物**: `.env.example`
- **内容**: 環境変数テンプレート（2項目）
```
STOCK_API_BASE=https://stockdata-api-6xok.onrender.com/
API_KEY=
```
- **検証**: ファイル存在確認

### タスク 1.5: .envファイル作成（.env.exampleコピー）
- [ ] 完了
- **作成物**: `.env`
- **前提**: タスク1.4完了
- **内容**: `.env.example`と同じ内容
- **検証**: ファイル存在確認

---

## PHASE 2: 設定モジュール実装（1タスク）

### タスク 2.1: config.pyファイル作成
- [ ] 完了
- **作成物**: `config.py`
- **実装内容**:
  - 環境変数読み込み（dotenv使用）
  - STOCK_API_BASE定義（デフォルト値付き）
  - API_KEY定義（空文字デフォルト）
  - TIMEOUT定数（30秒）
  - MAX_TICKERS定数（5）
- **検証**: `python -c "import config; print(config.STOCK_API_BASE)"`

---

## PHASE 3: APIクライアント実装（3タスク）

### タスク 3.1: api_client.py基本構造作成
- [ ] 完了
- **作成物**: `api_client.py`
- **前提**: タスク2.1完了
- **実装内容**: インポート文とモジュールdocstring
- **検証**: `python -c "import api_client"`

### タスク 3.2: fetch_prices関数実装
- [ ] 完了
- **更新対象**: `api_client.py`
- **前提**: タスク3.1完了
- **実装内容**:
  - fetch_prices関数（完全実装）
  - パラメータ: symbols, from_date, to_date
  - 戻り値: Dict[str, List[Dict]]
  - エラーハンドリング（timeout, request例外）
  - **ログ出力にsymbols/from/to含める**
  - Google形式docstring
- **検証**: `python -c "from api_client import fetch_prices; print(fetch_prices.__doc__)"`

### タスク 3.3: api_client.pyのエラーログ検証
- [ ] 完了
- **更新対象**: なし（検証のみ）
- **前提**: タスク3.2完了
- **検証内容**:
  - STOCK_API_BASEを一時的にダミー値に変更
  - fetch_prices呼び出し
  - エラーログにsymbols/from_date/to_dateが含まれることを確認
- **検証**: `python -c "import api_client; api_client.STOCK_API_BASE='http://dummy'; api_client.fetch_prices(['AAPL'], '2025-09-01', '2025-09-08')"`

---

## PHASE 4: モメンタム計算ロジック実装（8タスク）

### タスク 4.1: momentum.py基本構造作成
- [ ] 完了
- **作成物**: `momentum.py`
- **前提**: タスク3.2完了
- **実装内容**: インポート文とモジュールdocstring
- **検証**: `python -c "import momentum"`

### タスク 4.2: calculate関数（スケルトン）実装
- [ ] 完了
- **更新対象**: `momentum.py`
- **前提**: タスク4.1完了
- **実装内容**:
  - calculate関数シグネチャ
  - docstring
  - 仮実装（return [None] * len(tickers), {"current": "N/A", "past": "N/A"}）
- **検証**: `python -c "from momentum import calculate; print(calculate.__doc__)"`

### タスク 4.3: calculate_date_range関数実装
- [ ] 完了
- **更新対象**: `momentum.py`
- **前提**: タスク4.2完了
- **実装内容**:
  - calculate_date_range関数（完全実装）
  - Month/Week/Day別のロジック
  - 戻り値: (from_date, to_date)のタプル
- **検証**: `python -c "from momentum import calculate_date_range; print(calculate_date_range('month', 3, '2025-09'))"`

### タスク 4.4: round_to_saturday関数実装
- [ ] 完了
- **更新対象**: `momentum.py`
- **前提**: タスク4.3完了
- **実装内容**:
  - round_to_saturday関数（完全実装）
  - 任意の日付を土曜日に丸め込み
- **検証**: `python -c "from datetime import datetime; from momentum import round_to_saturday; print(round_to_saturday(datetime(2025, 9, 3)))"`
- **期待値**: 2025-09-06（土）

### タスク 4.5: find_price_on_date関数実装
- [ ] 完了
- **更新対象**: `momentum.py`
- **前提**: タスク4.4完了
- **実装内容**:
  - find_price_on_date関数（完全実装）
  - 指定日の価格を取得
- **検証**: `python -c "from momentum import find_price_on_date; print(find_price_on_date([{'date': '2025-09-01', 'close': 100}], '2025-09-01'))"`
- **期待値**: 100

### タスク 4.6: find_common_anchors関数実装
- [ ] 完了
- **更新対象**: `momentum.py`
- **前提**: タスク4.5完了
- **実装内容**:
  - find_common_anchors関数（完全実装）
  - 共通日付の交差取得
  - Unit別の現在アンカー特定
  - N期前の過去アンカー特定
- **検証**: 関数定義の確認

### タスク 4.7: calculate関数（完全実装）
- [ ] 完了
- **更新対象**: `momentum.py`
- **前提**: タスク4.6完了
- **実装内容**:
  - calculate関数の仮実装を完全実装に置き換え
  - 4ステップのアルゴリズム実装
- **検証**: 関数の動作確認

### タスク 4.8: モメンタム計算アンカー日付検証
- [ ] 完了
- **更新対象**: なし（検証のみ）
- **前提**: タスク4.7完了
- **検証内容**:
  - **Month**: 2025-09 → 現在アンカー=2025-08月末、過去アンカー=N月前の月末
  - **Week**: 2025-09-03（水）→ 土曜丸め=2025-09-06、N週前の金曜付近
  - **Day**: 2025-09-08 → 直前営業日、N営業日前
- **検証**: 各Unitでアンカー日付が期待通りか目視確認

---

## PHASE 5: FastAPIアプリケーション実装（6タスク）

### タスク 5.1: main.py基本構造作成
- [ ] 完了
- **作成物**: `main.py`
- **前提**: タスク4.7完了
- **実装内容**:
  - インポート文
  - FastAPIインスタンス生成
  - 静的ファイルマウント設定（`/static`）
- **検証**: `python -c "from main import app; print(app.title)"`

### タスク 5.2: Pydanticモデル定義
- [ ] 完了
- **更新対象**: `main.py`
- **前提**: タスク5.1完了
- **実装内容**:
  - ComputeRequestモデル
  - ComputeResponseモデル
- **検証**: `python -c "from main import ComputeRequest, ComputeResponse"`

### タスク 5.3: ルートエンドポイント実装
- [ ] 完了
- **更新対象**: `main.py`
- **前提**: タスク5.2完了
- **実装内容**:
  - GET / エンドポイント
  - FileResponseでindex.html返却
- **検証**: 
  - エンドポイント定義確認
  - **`/` アクセスで200/HTML返却確認**

### タスク 5.4: ヘルスチェックエンドポイント実装
- [ ] 完了
- **更新対象**: `main.py`
- **前提**: タスク5.3完了
- **実装内容**:
  - GET /health エンドポイント
  - status と api_base を返却
- **検証**: `uvicorn main:app --reload` 起動後 `/health` アクセス

### タスク 5.5: computeエンドポイント実装
- [ ] 完了
- **更新対象**: `main.py`
- **前提**: タスク5.4完了
- **実装内容**:
  - POST /compute エンドポイント
  - momentum.calculate呼び出し
  - レスポンス構築
  - エラーハンドリング
- **検証**: エンドポイント定義確認

### タスク 5.6: Swagger UI動作確認
- [ ] 完了
- **更新対象**: なし（検証のみ）
- **前提**: タスク5.5完了
- **検証内容**:
  - `/docs` にアクセス
  - Swagger UIが表示される
  - 各エンドポイントが表示される
- **検証**: ブラウザで `http://localhost:8000/docs` アクセス

---

## PHASE 6: フロントエンド実装（6タスク）

### タスク 6.1: index.html基本構造作成
- [ ] 完了
- **作成物**: `static/index.html`
- **実装内容**:
  - HTMLヘッダー（meta, title）
  - 基本CSS（monospacフォント、レイアウト）
  - bodyタグとタイトル
- **検証**: ブラウザで表示確認

### タスク 6.2: 入力フォーム実装
- [ ] 完了
- **更新対象**: `static/index.html`
- **前提**: タスク6.1完了
- **実装内容**:
  - ティッカー入力欄（5個）
  - Unit選択（select）
  - N入力（number）
  - as_of_period入力
  - 送信ボタン
- **検証**: フォーム要素の表示確認

### タスク 6.3: Unit変更時の動的処理実装
- [ ] 完了
- **更新対象**: `static/index.html`
- **前提**: タスク6.2完了
- **実装内容**:
  - Unit変更イベントリスナー
  - placeholderとヒントの動的更新
  - input typeの切り替え
- **検証**: Unit変更時の動作確認

### タスク 6.4: Week選択時の土曜日自動調整実装
- [ ] 完了
- **更新対象**: `static/index.html`
- **前提**: タスク6.3完了
- **実装内容**:
  - 日付選択時のイベントリスナー
  - 土曜日への自動調整ロジック
  - ユーザー通知表示
- **検証**: Week選択時の土曜日調整動作

### タスク 6.5: フォーム送信とAPI通信実装
- [ ] 完了
- **更新対象**: `static/index.html`
- **前提**: タスク6.4完了
- **実装内容**:
  - フォーム送信イベントリスナー
  - ティッカー収集ロジック
  - fetch APIでPOST送信（相対パス`/compute`）
  - 結果表示関数（displayResults）
  - **エスケープ文字（`\\n`）の正しい記述**
  - エラーハンドリング
- **検証**: 
  - 計算実行と結果表示
  - **DevTools ConsoleにJavaScriptエラーなし**

### タスク 6.6: フロントエンドConsole無エラー確認
- [ ] 完了
- **更新対象**: なし（検証のみ）
- **前提**: タスク6.5完了
- **検証内容**:
  - フォーム送信前後
  - 結果表示中
  - Unit切り替え時
- **検証**: **ブラウザDevTools ConsoleにErrorが0件**

---

## PHASE 7: README作成（1タスク）

### タスク 7.1: README.md作成
- [ ] 完了
- **作成物**: `README.md`
- **実装内容**:
  - プロジェクト概要
  - 機能説明
  - 技術スタック
  - ローカル開発手順
  - デプロイ手順
  - API仕様
  - **Render環境変数メモ（PYTHON_VERSION推奨）**
- **検証**: Markdown構文確認

---

## PHASE 8: ローカル動作確認（4タスク）

### タスク 8.1: 依存パッケージインストール
- [ ] 完了
- **前提**: 全ファイル作成完了
- **実行内容**: `pip install -r requirements.txt`
- **検証**: インストール成功確認

### タスク 8.2: アプリケーション起動
- [ ] 完了
- **前提**: タスク8.1完了
- **実行内容**: `uvicorn main:app --reload --port 8000`
- **検証**: 起動ログ確認

### タスク 8.3: 基本動作テスト（Month/Week/Day）
- [ ] 完了
- **前提**: タスク8.2完了
- **テスト内容**:
  - http://localhost:8000 アクセス
  - /health エンドポイント確認
  - **Month**: AAPL, N=3, 2025-09
  - **Week**: MSFT, N=4, 2025-09-03（水→土曜補正）
  - **Day**: GOOGL, N=20, 2025-09-08
- **検証**: 
  - 各Unitで正常な結果表示
  - アンカー日付が妥当

### タスク 8.4: エラーケース動作確認
- [ ] 完了
- **前提**: タスク8.3完了
- **テスト内容**:
  - 不正ティッカー（INVALID_TICKER）
  - 結果がNoneになること
  - アプリが停止しないこと
- **検証**: エラー時もアプリケーション継続動作

---

## 完了基準
- **全33タスク**が完了
- ローカルで正常動作確認
- エラーなくデプロイ可能な状態
- DevTools Consoleエラー0件

## 注意事項（エンジニアリングLLM向け）
1. **コードのみ実装**: 設計や調査は不要、純粋なコード作成のみ
2. **完全なコード**: 省略なし、全関数を完全実装
3. **PEP8準拠**: Pythonコードは全てPEP8に準拠
4. **Google形式docstring**: 全関数にGoogle形式のdocstring
5. **バックアップ不要**: コメントアウトや未使用コードは残さない
6. **型ヒント使用**: Pythonでは可能な限り型ヒントを使用
7. **改行文字の使い分け**: 
   - 実際に改行させる場合：`\n`（バックスラッシュ1個）
   - 文字列として`\n`を表示する場合：`\\n`（バックスラッシュ2個）