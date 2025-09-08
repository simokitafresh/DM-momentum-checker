# 進捗メモ（2025-09-08）

- PHASE 1: [x] 1.1 / [x] 1.2 / [x] 1.3 / [x] 1.4 / [x] 1.5
- PHASE 2: [x] 2.1
- PHASE 3: [x] 3.1 / [x] 3.2 / [x] 3.3
- PHASE 4: [x] 4.1 / [x] 4.2 / [x] 4.3 / [x] 4.4 / [x] 4.5 / [x] 4.6 / [x] 4.7 / [ ] 4.8（検証のみ保留）
- PHASE 5: [x] 5.1 / [x] 5.2 / [x] 5.3 / [x] 5.4 / [x] 5.5 / [ ] 5.6（検証のみ保留）
- PHASE 6: [x] 6.1 / [x] 6.2 / [x] 6.3 / [x] 6.4 / [x] 6.5 / [ ] 6.6（検証のみ保留）
- PHASE 7: [x] 7.1
- PHASE 8: [x] 8.1 / [x] 8.2 / [x] 8.3 / [x] 8.4
  - 8.1: venv 作成 + requirements インストール
  - 8.2: サーバ起動確認（ユーザ提供ログの 200 OK）
  - 8.3: Month/Week/Day の計算をモジュール/クライアントで確認
  - 8.4: INVALID_TICKER で None、アプリ継続（TestClient）

備考:
- 3.3 エラーログは `STOCK_API_BASE='http://dummy'` で確認（symbols/from/to 含む）
- `api_client.py` は配列/辞書の両レスポンス形式に対応済み
