# 結果表示改修 進捗メモ（2025-09-08）

- Task 1: CSS 追記（pre-wrap） [x]
- Task 2-4: JS 関数追加・置換（formatMomentum / getUnitJapanese / displayResults） [x]
- Task 5: innerHTML 廃止／esc 削除／エラー表示統一 [x]
  - innerHTML 使用: 0件
  - 例外時メッセージ: `textContent` でプレーンテキストに統一
  - 未入力時エラーもプレーンテキストに変更
- Task 6: 動作確認テスト [pending]
  - 6.1 関数単体（ブラウザコンソール）: 手動実施が必要
  - 6.2 統合（月/週/日/エラー）: 手動実施が必要

対象ファイル:
- dual-momentum-mvp/static/index.html

補足:
- 出力は `resultsDiv.textContent` のみ使用。`\n` は CSS `white-space: pre-wrap;` で改行表示。
- 期間行は `期間: <N + 単位> (<past> → <current>)` 形式に整形。
