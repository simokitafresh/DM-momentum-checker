# 結果表示改善実装タスクリスト（最終版）

## 前提条件
- 対象ファイル: `dual-momentum-mvp/static/index.html`
- 言語: JavaScript（HTML内の`<script>`タグ内）
- 既存コードを直接修正（バックアップ・コメントアウト不要）
- **コピペで即実装可能な最小差分を提供**

## 実装タスク

### Task 1: CSS追記（改行表示対応）
- [ ] **対象**: `static/index.html`の`<style>`タグ内
- [ ] **場所**: 既存の`#results`セレクタ
- [ ] **実装**: 以下の1行を追加
```css
#results {
  margin-top: 16px;
  white-space: pre-wrap; /* \nを改行として表示 */
}
```
- [ ] **成功基準**: CSSエラーなし、`\n`が改行として表示される

---

### Task 2-4: JavaScript関数の追加と置換
- [ ] **対象**: `static/index.html`の`<script>`タグ内
- [ ] **実装手順**:
  1. 既存の`displayResults`関数の**前**に以下2関数を追加
  2. 既存の`displayResults`関数を**全削除**
  3. 新しい`displayResults`関数を追加

#### 追加するコード（完全版）
```javascript
// --- formatMomentum関数（新規追加） ---
function formatMomentum(value) {
  // null/undefined チェック
  if (value === null || value === undefined) return 'N/A';

  // 数値変換と有限数チェック
  const num = Number(value);
  if (!Number.isFinite(num)) return 'N/A';

  // パーセント値に変換して2桁に丸める（-0.00%回避）
  const pct = Math.round(num * 10000) / 100;
  const normalized = Object.is(pct, -0) ? 0 : pct;

  // 符号判定（丸め後の値で判定）
  const sign = normalized > 0 ? '+' : (normalized < 0 ? '' : '+');

  // 絶対値文字列化
  const absStr = Math.abs(normalized).toFixed(2);

  // 最終フォーマット（ゼロは常に+0.00%）
  return (normalized < 0)
    ? `-${absStr}%`
    : `${sign}${absStr}%`;
}

// --- getUnitJapanese関数（新規追加） ---
function getUnitJapanese(unit, n) {
  const unitMap = {
    'month': 'ヶ月',
    'week': '週間',
    'day': '営業日'
  };
  const label = unitMap[unit];
  return `${n}${label ?? unit}`; // 未知単位はそのまま
}

// --- displayResults関数（既存を削除して置換） ---
function displayResults(data, request) {
  console.log('displayResults called with:', { data, request }); // デバッグ出力

  const lines = [];

  // モメンタム値の表示（入力順を保証）
  const tickers = Array.isArray(request?.tickers) ? request.tickers : [];
  for (let i = 0; i < tickers.length; i++) {
    const ticker = tickers[i];
    const result = data?.results?.[i]; // 欠損はundefined -> N/A
    lines.push(`${ticker}: ${formatMomentum(result)}`);
  }

  lines.push(''); // 空行

  // 期間の表示
  const unitJa = getUnitJapanese(request?.unit, request?.n);
  const past = data?.anchors?.past;
  const current = data?.anchors?.current;

  // アンカー存在チェック（null/undefined/空文字/'N/A'を除外）
  const hasAnchors = !!past && !!current && past !== 'N/A' && current !== 'N/A';

  if (hasAnchors) {
    lines.push(`期間: ${unitJa} (${past} → ${current})`);
  } else {
    lines.push(`期間: ${unitJa} (データ不足)`);
  }

  // 基準の表示
  lines.push(`基準: ${request?.as_of_period}`);

  // 安全に出力
  resultsDiv.textContent = lines.join('\n');
}
```

- [ ] **成功基準**: 
  - コンソールエラーなし
  - resultsDiv変数が定義済み（既存コード依存）

---

### Task 5: クリーンアップ（innerHTML廃止）
- [ ] **対象**: `static/index.html`の`<script>`タグ内全体
- [ ] **作業内容**:

#### 5.1 innerHTML使用箇所の置換
- [ ] 検索: `resultsDiv.innerHTML`
- [ ] すべて`resultsDiv.textContent`に置換
- [ ] 例:
  ```javascript
  // 変更前
  resultsDiv.innerHTML = '<span class="error">エラー: ' + esc(err) + '</span>';
  
  // 変更後
  resultsDiv.textContent = `エラー: ${err}`;
  ```

#### 5.2 esc関数の削除
- [ ] HTMLエスケープ用の`esc()`関数があれば削除
- [ ] `esc()`の呼び出し箇所も削除

#### 5.3 エラー表示の統一
- [ ] すべての`catch`節を以下に統一:
  ```javascript
  } catch (error) {
    const msg = (error && error.message) ? error.message : String(error);
    resultsDiv.textContent = `エラー: ${msg}`;
  }
  ```

- [ ] **成功基準**: 
  - `innerHTML`の使用が0件
  - エラー時にHTMLタグが文字列として表示されない

---

### Task 6: 動作確認テスト

#### テスト6.1: 関数単体テスト（ブラウザコンソール）
- [ ] ブラウザコンソールで以下を実行:
```javascript
// formatMomentumテスト
formatMomentum(0)              // 期待値: '+0.00%'
formatMomentum(-0.0000001)     // 期待値: '+0.00%'
formatMomentum(0.1234)         // 期待値: '+12.34%'
formatMomentum(-0.0567)        // 期待値: '-5.67%'
formatMomentum(null)           // 期待値: 'N/A'
formatMomentum(NaN)            // 期待値: 'N/A'

// getUnitJapaneseテスト
getUnitJapanese('month', 3)    // 期待値: '3ヶ月'
getUnitJapanese('week', 4)     // 期待値: '4週間'
getUnitJapanese('day', 20)     // 期待値: '20営業日'
getUnitJapanese('unknown', 5)  // 期待値: '5unknown'
```

#### テスト6.2: 統合テスト（画面操作）
- [ ] `http://localhost:8000`を開く

##### 月次テスト
- [ ] 入力:
  - Tickers: QQQ, GLD
  - Unit: month
  - N: 3
  - as_of_period: 2025-09
- [ ] 期待表示形式:
  ```
  QQQ: +XX.XX%
  GLD: +XX.XX%
  
  期間: 3ヶ月 (YYYY-MM-DD → YYYY-MM-DD)
  基準: 2025-09
  ```

##### 週次テスト
- [ ] 入力:
  - Tickers: AAPL
  - Unit: week
  - N: 4
  - as_of_period: 土曜日を選択
- [ ] 期待表示形式:
  ```
  AAPL: +XX.XX%
  
  期間: 4週間 (YYYY-MM-DD → YYYY-MM-DD)
  基準: YYYY-MM-DD
  ```

##### 日次テスト
- [ ] 入力:
  - Tickers: MSFT
  - Unit: day
  - N: 20
  - as_of_period: 任意の平日
- [ ] 期待表示形式:
  ```
  MSFT: +XX.XX%
  
  期間: 20営業日 (YYYY-MM-DD → YYYY-MM-DD)
  基準: YYYY-MM-DD
  ```

##### エラーテスト
- [ ] 入力:
  - Tickers: INVALID_TICKER
  - その他: 任意
- [ ] 期待表示:
  ```
  INVALID_TICKER: N/A
  
  期間: XXX (データ不足)
  基準: YYYY-MM-DD
  ```

---

## 完了チェックリスト

### 必須確認項目
- [ ] CSS: `white-space: pre-wrap;`追加済み
- [ ] JS: `formatMomentum`関数追加済み
- [ ] JS: `getUnitJapanese`関数追加済み
- [ ] JS: `displayResults`関数置換済み
- [ ] `innerHTML`使用箇所: 0件
- [ ] `textContent`のみ使用
- [ ] ゼロ値: `+0.00%`と表示
- [ ] day単位: 「営業日」と表示
- [ ] 改行: 正しく表示される
- [ ] エラー表示: HTMLタグが見えない
- [ ] コンソール: エラーなし
- [ ] デバッグ出力: 動作確認

### 表示確認項目
- [ ] ティッカー順序: 入力順を維持
- [ ] 空行: ティッカーと期間の間に存在
- [ ] 矢印: 「→」が正しく表示
- [ ] データ不足: 「(データ不足)」表示
- [ ] 符号: 正の値に`+`表示

---

## 実装順序（推奨）
1. Task 1: CSS追記（1分）
2. Task 2-4: JavaScript関数追加・置換（5分）
3. Task 5: クリーンアップ（3分）
4. Task 6: 動作確認テスト（5分）

**合計作業時間目安: 約15分**

---

## トラブルシューティング

### 改行が表示されない場合
→ CSS の `white-space: pre-wrap;` が適用されているか確認

### formatMomentumが未定義エラー
→ 関数の追加位置が`displayResults`より前か確認

### resultsDiv未定義エラー
→ 既存コードで`const resultsDiv = document.getElementById('results');`が定義されているか確認

### 古い表示が残る場合
→ ブラウザキャッシュをクリア（Ctrl+Shift+R）

---

## 注意事項
- **バックエンドコードは一切変更しない**
- **HTMLの`<form>`構造は変更しない**
- **追加ライブラリは使用しない**
- **コメントアウトやバックアップコードは残さない**
- **すべてのコードは提供されたものをそのままコピペ可能**