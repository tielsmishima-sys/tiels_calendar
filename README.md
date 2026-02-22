# Tiels Calendar

Instagram投稿用の月次営業カレンダー画像を自動生成するツールです。

## 機能

- `config.json` にスケジュールを記入するだけで、1080x1350px のカレンダー画像を生成
- 営業時間・定休日・祝日を自動で色分け表示
- 前月・翌月の週末も表示対応
- イベントボックスの表示に対応
- 対話モードでスケジュール入力 → 画像生成まで一括実行

## 必要環境

- Python 3
- Pillow (`pip install Pillow`)

## 使い方

### カレンダー画像を生成

```bash
python3 generate_calendar.py
```

`config.json` を読み込んでカレンダー画像を生成します。

### 対話モードで設定ファイルを作成 → 生成

```bash
python3 create_month.py
```

年月・営業スケジュール・祝日を対話的に入力し、`config.json` の更新とカレンダー画像の生成を一括で行います。

### クイックモード（非対話）

```bash
python3 create_month.py quick 2026 4 "1 15-21, 2 17-21, 6 17-22"
```

## config.json の設定項目

| 項目 | 説明 |
|------|------|
| `year`, `month` | 対象の年月 |
| `schedule` | 営業日と営業時間（例: `{"1": "15-21", "2": "17-21"}`） |
| `prev_month_schedule` | 前月の表示分の営業時間 |
| `next_month_schedule` | 翌月の表示分の営業時間 |
| `holidays` | 祝日の日にちリスト |
| `events` | イベント情報（`[{"name": "イベント名", "start": 1, "end": 3}]`） |
| `bottom_text` | カレンダー下部に表示するテキスト |
| `output_filename` | 出力ファイル名 |
