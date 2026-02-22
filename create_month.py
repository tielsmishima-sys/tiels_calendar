#!/usr/bin/env python3
"""
月次カレンダー設定ファイル作成ツール

使い方:
  python3 create_month.py

対話的に営業スケジュールを入力し、config.json を生成して
カレンダー画像を自動生成します。
"""

import json
import calendar
import datetime
import os
import sys


# 日本の祝日データ（年ごとに更新してください）
JAPAN_HOLIDAYS = {
    2026: {
        1: [1, 12],        # 元日, 成人の日
        2: [11, 23],       # 建国記念の日, 天皇誕生日
        3: [20],           # 春分の日
        4: [29],           # 昭和の日
        5: [3, 4, 5, 6],   # 憲法記念日, みどりの日, こどもの日, 振替休日
        7: [20],           # 海の日
        8: [11],           # 山の日
        9: [21, 22, 23],   # 敬老の日, 国民の休日, 秋分の日
        10: [12],          # スポーツの日
        11: [3, 23],       # 文化の日, 勤労感謝の日
        12: [],
    },
    2027: {
        1: [1, 11],
        2: [11, 23],
        3: [21],           # 春分の日（2027年は21日）
        4: [29],
        5: [3, 4, 5],
        7: [19],
        8: [11],
        9: [20, 23],
        10: [11],
        11: [3, 23],
        12: [],
    }
}


def get_holidays(year, month):
    """指定月の祝日リストを取得"""
    if year in JAPAN_HOLIDAYS and month in JAPAN_HOLIDAYS[year]:
        return JAPAN_HOLIDAYS[year][month]
    return []


def print_calendar_preview(year, month):
    """カレンダーのプレビューを表示"""
    print(f"\n{'='*50}")
    print(f"  {year}年 {month}月")
    print(f"{'='*50}")

    first_dow, num_days = calendar.monthrange(year, month)
    holidays = get_holidays(year, month)

    print("  月   火   水   木   金   土   日")
    print("  " + "     " * first_dow, end="")

    for d in range(1, num_days + 1):
        dow = (first_dow + d - 1) % 7
        marker = "*" if d in holidays else " "
        if dow >= 5:  # 土日
            marker = "*"
        print(f" {d:2d}{marker} ", end="")
        if dow == 6:
            print()

    print()
    if holidays:
        print(f"  祝日: {', '.join(str(d) + '日' for d in holidays)}")
    print()


def parse_schedule_input(text):
    """
    スケジュール入力をパース。
    形式: "1 15-21, 2 17-21, ..." または "1  15-21\\n2  17-21\\n..."
    """
    schedule = {}
    # カンマまたは改行で分割
    entries = text.replace(',', '\n').strip().split('\n')
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split()
        if len(parts) >= 2:
            day = parts[0].strip()
            hours = parts[1].strip()
            schedule[day] = hours
    return schedule


def interactive_create():
    """対話的に設定ファイルを作成"""
    print("╔══════════════════════════════════════════╗")
    print("║  Instagram カレンダー画像 - 月次設定     ║")
    print("╚══════════════════════════════════════════╝")

    # 年月の入力
    today = datetime.date.today()
    default_year = today.year
    default_month = today.month + 1
    if default_month > 12:
        default_month = 1
        default_year += 1

    year_input = input(f"\n年 [{default_year}]: ").strip()
    year = int(year_input) if year_input else default_year

    month_input = input(f"月 [{default_month}]: ").strip()
    month = int(month_input) if month_input else default_month

    # カレンダープレビュー
    print_calendar_preview(year, month)

    # 営業スケジュール入力
    print("営業スケジュールを入力してください。")
    print("形式: 日 時間 （1行に1つ、空行で入力終了）")
    print("例:")
    print("  1  15-21")
    print("  2  17-21")
    print("  6  17-22")
    print()

    lines = []
    while True:
        line = input("  > ").strip()
        if not line:
            if lines:
                break
            continue
        lines.append(line)

    schedule = parse_schedule_input('\n'.join(lines))
    print(f"\n✓ {len(schedule)}日分の営業日を登録しました")

    # 祝日の確認
    holidays = get_holidays(year, month)
    if holidays:
        print(f"\n祝日（自動検出）: {', '.join(str(d) + '日' for d in holidays)}")
        confirm = input("この祝日で合っていますか？ [Y/n]: ").strip().lower()
        if confirm == 'n':
            holiday_input = input("祝日を入力 (カンマ区切り、例: 20,23): ").strip()
            if holiday_input:
                holidays = [int(d.strip()) for d in holiday_input.split(',')]
            else:
                holidays = []
    else:
        print(f"\n{year}年{month}月の祝日データがありません。")
        holiday_input = input("祝日を入力 (カンマ区切り、空欄でスキップ): ").strip()
        if holiday_input:
            holidays = [int(d.strip()) for d in holiday_input.split(',')]

    # 前月・翌月の週末スケジュール
    first_dow, num_days = calendar.monthrange(year, month)

    prev_schedule = {}
    next_schedule = {}

    # 前月の週末日（カレンダーに表示される分）
    if first_dow > 0:  # 月曜始まりでない場合
        if month == 1:
            prev_days = calendar.monthrange(year - 1, 12)[1]
        else:
            prev_days = calendar.monthrange(year, month - 1)[1]

        prev_weekend_days = []
        for i in range(first_dow):
            d = prev_days - first_dow + 1 + i
            dow = i  # 0=月, 1=火, ...
            if dow >= 5:
                prev_weekend_days.append(d)

        if prev_weekend_days:
            print(f"\n前月の週末日がカレンダーに表示されます: {prev_weekend_days}")
            for d in prev_weekend_days:
                hours = input(f"  前月 {d}日 の営業時間 [15-21]: ").strip()
                if not hours:
                    hours = "15-21"
                prev_schedule[str(d)] = hours

    # 翌月の週末日
    last_day_dow = (first_dow + num_days - 1) % 7
    if last_day_dow < 6:  # 日曜で終わらない場合
        remaining = 6 - last_day_dow
        next_weekend_days = []
        for i in range(1, remaining + 1):
            dow = (last_day_dow + i) % 7
            if dow >= 5:
                next_weekend_days.append(i)

        if next_weekend_days:
            print(f"\n翌月の週末日がカレンダーに表示されます: {next_weekend_days}")
            for d in next_weekend_days:
                hours = input(f"  翌月 {d}日 の営業時間 [15-21]: ").strip()
                if not hours:
                    hours = "15-21"
                next_schedule[str(d)] = hours

    # config.json 生成
    config = {
        "year": year,
        "month": month,
        "schedule": schedule,
        "prev_month_schedule": prev_schedule,
        "next_month_schedule": next_schedule,
        "holidays": holidays,
        "prev_month_holidays": [],
        "next_month_holidays": [],
        "bottom_text": "ご予約は 055-957-4500 / 070-8419-5489 にて承ります",
        "output_filename": f"calendar_{year}_{month:02d}.png"
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\n✓ config.json を更新しました")

    # 画像生成
    print("\nカレンダー画像を生成中...")
    import generate_calendar
    config = generate_calendar.load_config(config_path)
    output_path = generate_calendar.generate_calendar(config)

    print(f"\n{'='*50}")
    print(f"  完成！ {output_path}")
    print(f"{'='*50}")


def quick_create(year, month, schedule_text):
    """
    コマンドラインから直接生成（非対話モード）

    使用例:
      python3 create_month.py quick 2026 4 "1 15-21, 2 17-21, ..."
    """
    schedule = parse_schedule_input(schedule_text)
    holidays = get_holidays(year, month)

    config = {
        "year": year,
        "month": month,
        "schedule": schedule,
        "prev_month_schedule": {},
        "next_month_schedule": {},
        "holidays": holidays,
        "prev_month_holidays": [],
        "next_month_holidays": [],
        "bottom_text": "ご予約は 055-957-4500 / 070-8419-5489 にて承ります",
        "output_filename": f"calendar_{year}_{month:02d}.png"
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    import generate_calendar
    config = generate_calendar.load_config(config_path)
    generate_calendar.generate_calendar(config)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        if len(sys.argv) < 5:
            print("使い方: python3 create_month.py quick YEAR MONTH 'SCHEDULE'")
            print("例: python3 create_month.py quick 2026 4 '1 15-21, 2 17-21, 6 17-22'")
            sys.exit(1)
        quick_create(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    else:
        interactive_create()
