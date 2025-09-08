# モメンタム計算結果表示改善仕様書（改訂版）

## 1. 概要
デュアル・モメンタム計算MVPの結果表示を、より読みやすく直感的な形式に改善する。

## 2. 基本方針
- **最小限情報の階層表示**を採用
- テキストベースでシンプルな出力を維持
- 装飾は避ける
- **堅牢性を重視**（エッジケース・異常値への対処）

## 3. 表示フォーマット仕様

### 3.1 正常時の表示形式

```
QQQ: +10.00%
GLD: +4.77%

期間: 3ヶ月 (2025-05-30 → 2025-08-29)
基準: 2025-09
```

※dayの場合の表示例：
```
AAPL: +2.35%
MSFT: -1.20%

期間: 20営業日 (2025-08-11 → 2025-09-08)
基準: 2025-09-08
```

### 3.2 表示要素の詳細

#### ティッカーとモメンタム値
- 形式: `{ティッカー}: {符号}{値}%`
- 小数点: 2桁固定
- 符号ルール: 
  - 正の値: `+` を明示的に表示
  - 負の値: `-` を表示
  - **ゼロ: 常に `+0.00%`**（-0.00%は出力しない）
  - 非数値（NaN/Infinity等）: `N/A`

#### 期間表示
- 形式: `期間: {n}{単位} ({過去日} → {現在日})`
- 日付順序: **過去 → 現在**（時系列順）
- 日付形式: `YYYY-MM-DD`
- **期間は両端を含む**

#### 基準表示
- 形式: `基準: {as_of_period}`
- monthの場合: `YYYY-MM`
- week/dayの場合: `YYYY-MM-DD`

## 4. 単位の日本語表記と定義

| unit | 日本語表記 | 定義 | 例 |
|------|----------|------|-----|
| month | ヶ月 | 暦月ベース | 3ヶ月 |
| week | 週間 | 7×n日 | 4週間（28日） |
| day | 日間 | 営業日ベース | 20日間 |

### 4.1 アンカー規則
- **current**: `as_of_period`を含む期間の最終取引日
  - monthの場合: 指定月の前月の最終取引日
  - weekの場合: 土曜を含む週の最終取引日
  - dayの場合: 指定日以前の直近取引日
- **past**: currentからn単位さかのぼった期間の取引日
- 取得できない場合: `(データ不足)`と表示

## 5. エラー・データ不足時の表示

### 5.1 一部データなし
```
QQQ: +10.00%
GLD: N/A
INVALID: N/A

期間: 3ヶ月 (2025-05-30 → 2025-08-29)
基準: 2025-09
```

### 5.2 全データなし（共通アンカー特定不可）
```
QQQ: N/A
GLD: N/A

期間: 3ヶ月 (データ不足)
基準: 2025-09
```

### 5.3 API接続エラー
```
エラー: HTTPエラー: 500
```

## 6. 実装詳細（堅牢化版）

### 6.1 数値フォーマット関数（改訂版）
```javascript
function formatMomentum(value) {
    // null/undefined チェック
    if (value === null || value === undefined) return 'N/A';
    
    // 数値変換と有限数チェック
    const num = Number(value);
    if (!Number.isFinite(num)) return 'N/A';

    // パーセント値に変換して2桁に丸める
    const pct = Math.round(num * 10000) / 100;
    
    // -0を+0に正規化
    const normalized = Object.is(pct, -0) ? 0 : pct;

    // 符号判定（丸め後の値で判定）
    const sign = normalized > 0 ? '+' : (normalized < 0 ? '' : '+');

    // 絶対値文字列化
    const absStr = Math.abs(normalized).toFixed(2);

    // 最終フォーマット
    return (normalized < 0) 
        ? `-${absStr}%`
        : `${sign}${absStr}%`;
}
```

### 6.2 単位変換関数（防御的実装）
```javascript
function getUnitJapanese(unit, n) {
    const unitMap = {
        'month': 'ヶ月',
        'week': '週間',
        'day': '日間'
    };
    const label = unitMap[unit];
    return `${n}${label ?? unit}`; // 未知単位はそのまま
}
```

### 6.3 表示生成関数（堅牢化版）
```javascript
function displayResults(data, request) {
    const lines = [];

    // モメンタム値の表示（入力順を保証）
    const tickers = Array.isArray(request?.tickers) ? request.tickers : [];
    for (let i = 0; i < tickers.length; i++) {
        const ticker = tickers[i];
        const result = data?.results?.[i];
        lines.push(`${ticker}: ${formatMomentum(result)}`);
    }

    lines.push(''); // 空行

    // 期間の表示
    const unitJa = getUnitJapanese(request?.unit, request?.n);
    const past = data?.anchors?.past;
    const current = data?.anchors?.current;
    
    // アンカー存在チェック（null/undefined/空文字/'N/A'）
    const hasAnchors = (
        !!past && !!current && 
        past !== 'N/A' && current !== 'N/A'
    );
    
    if (hasAnchors) {
        lines.push(`期間: ${unitJa} (${past} → ${current})`);
    } else {
        lines.push(`期間: ${unitJa} (データ不足)`);
    }

    // 基準の表示
    lines.push(`基準: ${request?.as_of_period}`);

    // textContentで安全に出力
    resultsDiv.textContent = lines.join('\n');
}
```

## 7. 改修対象ファイル

- `static/index.html` - displayResults関数および関連ヘルパー関数の修正

## 8. テストケース

### 8.1 正常系（月次）
**入力:**
- Tickers: QQQ, GLD
- Unit: month
- N: 3
- as_of_period: 2025-09

**期待出力:**
```
QQQ: +10.00%
GLD: +4.77%

期間: 3ヶ月 (2025-05-30 → 2025-08-29)
基準: 2025-09
```

### 8.2 正常系（週次・負の値含む）
**入力:**
- Tickers: AAPL, MSFT, GOOGL
- Unit: week
- N: 4
- as_of_period: 2025-09-06

**期待出力:**
```
AAPL: +3.45%
MSFT: -2.13%
GOOGL: +0.00%

期間: 4週間 (2025-08-08 → 2025-09-05)
基準: 2025-09-06
```

### 8.3 ゼロ境界テスト
**入力値と期待出力:**
- `value = 0` → `+0.00%`
- `value = -0.0000001` → `+0.00%`（丸め後ゼロ）
- `value = 0.0000001` → `+0.00%`
- `value = -0.00001` → `+0.00%`

### 8.4 非数値・異常値テスト
**入力値と期待出力:**
- `value = null` → `N/A`
- `value = undefined` → `N/A`
- `value = NaN` → `N/A`
- `value = Infinity` → `N/A`
- `value = "12%"` → `N/A`

### 8.5 異常系（一部データなし）
**入力:**
- Tickers: VALID, INVALID
- Unit: day
- N: 20
- as_of_period: 2025-09-08

**期待出力:**
```
VALID: +5.23%
INVALID: N/A

期間: 20日間 (2025-08-10 → 2025-09-05)
基準: 2025-09-08
```

### 8.6 異常系（全データなし）
**入力:**
- Tickers: INVALID1, INVALID2
- Unit: month
- N: 3
- as_of_period: 2025-09

**期待出力:**
```
INVALID1: N/A
INVALID2: N/A

期間: 3ヶ月 (データ不足)
基準: 2025-09
```

### 8.7 結果配列の長さズレ
**入力:**
- tickers: ['A', 'B', 'C']
- results: [0.1]（要素不足）

**期待出力:**
```
A: +10.00%
B: N/A
C: N/A

期間: ...
基準: ...
```

## 9. 技術的要件

### 9.1 必須要件
- [ ] ゼロ表記が常に **`+0.00%`** になる（-0.00%を出力しない）
- [ ] `NaN`/`Infinity`/未定義は **N/A** として表示
- [ ] **入力順表示**が保証される（request.tickersの順序を維持）
- [ ] アンカーの存在判定でnull/undefined/空文字/'N/A'を考慮
- [ ] HTMLエスケープ不要（textContent使用）

### 9.2 データ整合性
- 表示順序は入力順（request.tickersの順）を正とする
- data.resultsとrequest.tickersのインデックスが対応
- 配列長の不一致時は不足分をN/Aとして扱う

## 10. 注意事項

- 改行は`\n`を使用
- フォント等のスタイルは既存のCSSを維持
- エラー表示は既存の`.error`クラスを活用可能

## 11. チェックリスト

- [ ] ゼロ表記が常に **`+0.00%`** になる
- [ ] 極小の負値が丸めでゼロになっても **`+0.00%`** 
- [ ] `NaN`/`Infinity`/未定義は **N/A**
- [ ] **入力順表示**が保証される
- [ ] アンカーの**定義と取得規則**が明文化済み
- [ ] 週・月の**算出規則**が明文化済み
- [ ] 例示出力と実装出力が**完全一致**（空行・改行含む）
- [ ] 非数値の混入に対して堅牢
- [ ] アンカー判定が防御的実装

## 12. 承認事項

- [x] 最小限情報の階層表示を採用
- [x] 期間表示は「過去 → 現在」の順序
- [x] パーセント表示は小数点2桁固定
- [x] 正の値には`+`記号を明示
- [x] ゼロは常に`+0.00%`（-0.00%は禁止）
- [x] データなし時は`N/A`表示
- [x] 単位は日本語表記
- [x] 非数値・異常値への堅牢な対処
- [x] アンカー規則の明文化