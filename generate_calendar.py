#!/usr/bin/env python3
"""
Instagram カレンダー画像ジェネレーター
毎月の営業時間カレンダーをデータ入力だけで自動生成します。

使い方:
  python3 generate_calendar.py              → config.json を読み込んで生成
  python3 generate_calendar.py config.json  → 指定ファイルから生成
"""

import calendar
import datetime
import json
import sys
import os
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# デフォルト設定（config.json で上書き可能）
# ============================================================
DEFAULT_CONFIG = {
    "year": 2026,
    "month": 3,

    # 営業時間スケジュール: { "日": "時間" }
    # 記載のない日は定休日（"-"）として表示
    "schedule": {
        "1": "15-21", "2": "17-21", "6": "17-22", "7": "15-21",
        "8": "15-21", "9": "17-21", "13": "17-22", "14": "15-21",
        "15": "15-21", "16": "17-21", "20": "17-22", "21": "15-21",
        "22": "15-21", "23": "17-21", "27": "17-22", "28": "15-21",
        "29": "15-21", "30": "17-21"
    },

    # 前月の週末営業時間（カレンダー上に表示する分）
    "prev_month_schedule": {
        "28": "15-21"
    },

    # 翌月の週末営業時間（カレンダー上に表示する分）
    "next_month_schedule": {
        "4": "15-21",
        "5": "15-21"
    },

    # 祝日（対象月の日にちリスト）
    # 3月2026: 春分の日(20日)
    "holidays": [20],

    # 前月・翌月の祝日（カレンダー上に出る日にちのみ）
    "prev_month_holidays": [],
    "next_month_holidays": [],

    # フォントパス（システムに合わせて変更）
    # Avenir がある場合は latin_font を差し替えてください
    "latin_font": "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
    "latin_font_bold": "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "latin_font_medium": "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
    "japanese_font": "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",

    # 下部テキスト
    "bottom_text": "ご予約は 055-957-4500 / 070-8419-5489 にて承ります",

    # 出力ファイル名（空欄だと自動命名）
    "output_filename": ""
}


# ============================================================
# レイアウト定数（テンプレート準拠）
# ============================================================
IMG_W, IMG_H = 1080, 1350
BG_COLOR = (255, 255, 255)

# カラー
COLOR_DARK    = (42, 42, 42)       # 通常テキスト
COLOR_GRAY    = (120, 120, 120)    # 定休日「-」
COLOR_ORANGE  = (240, 112, 80)     # 土日・祝日 (#F07050)
COLOR_HEADER  = (100, 100, 100)    # 曜日ヘッダー

# カラム（7列: MON-SUN）
COL_X = [120, 260, 400, 540, 680, 820, 960]

# 縦方向の基準位置
Y_MONTH_NUM   = 130   # 月の数字の中心 Y
Y_YEAR        = 145   # 年テキストの中心 Y
Y_HEADERS     = 310   # 曜日ヘッダーの Y
Y_FIRST_ROW   = 400   # 最初の日付行の Y
Y_HOURS_OFFSET = 50   # 日付の下の営業時間オフセット
Y_BOTTOM_TEXT = 1220   # 下部テキストの Y

# フォントサイズ
SIZE_MONTH_NUM   = 100
SIZE_YEAR        = 36
SIZE_HEADER      = 22
SIZE_DATE        = 36
SIZE_MONTH_PREFIX = 18
SIZE_HOURS       = 22
SIZE_BOTTOM      = 24
SIZE_CLOSED      = 26
SIZE_EVENT       = 16

# イベントボックス
EVENT_BOX_GAP     = 8    # 営業時間とボックスの間
EVENT_BOX_PAD_H   = 12   # ボックス内の水平パディング
EVENT_BOX_PAD_V   = 6    # ボックス内の垂直パディング
EVENT_BORDER_W    = 0.75  # 枠線の太さ
EVENT_LINE_GAP    = 4    # 複数行テキストの行間

DAY_NAMES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def load_config(config_path=None):
    """設定を読み込む"""
    config = DEFAULT_CONFIG.copy()

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        config.update(user_config)
    elif os.path.exists("config.json"):
        with open("config.json", 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        config.update(user_config)

    return config


def load_fonts(config):
    """フォントを読み込む"""
    fonts = {}
    try:
        fonts['month_num'] = ImageFont.truetype(config['latin_font_bold'], SIZE_MONTH_NUM)
    except:
        fonts['month_num'] = ImageFont.truetype(config['latin_font'], SIZE_MONTH_NUM)

    fonts['year'] = ImageFont.truetype(config['latin_font'], SIZE_YEAR)

    try:
        fonts['header'] = ImageFont.truetype(config['latin_font_medium'], SIZE_HEADER)
    except:
        fonts['header'] = ImageFont.truetype(config['latin_font'], SIZE_HEADER)

    # 日付フォント（date_font が指定されていればそちらを優先）
    date_font_path = config.get('date_font', config['latin_font_bold'])
    try:
        fonts['date'] = ImageFont.truetype(date_font_path, SIZE_DATE)
    except:
        try:
            fonts['date'] = ImageFont.truetype(config['latin_font_bold'], SIZE_DATE)
        except:
            fonts['date'] = ImageFont.truetype(config['latin_font'], SIZE_DATE)

    fonts['date_regular'] = ImageFont.truetype(config['latin_font'], SIZE_DATE)
    fonts['month_prefix'] = ImageFont.truetype(config['latin_font'], SIZE_MONTH_PREFIX)
    fonts['hours'] = ImageFont.truetype(config['latin_font'], SIZE_HOURS)
    fonts['closed'] = ImageFont.truetype(config['latin_font'], SIZE_CLOSED)
    fonts['bottom_jp'] = ImageFont.truetype(config['japanese_font'], SIZE_BOTTOM)
    fonts['bottom_latin'] = ImageFont.truetype(config['latin_font'], SIZE_BOTTOM)
    fonts['event_jp'] = ImageFont.truetype(config['japanese_font'], SIZE_EVENT)
    fonts['event_latin'] = ImageFont.truetype(config['latin_font'], SIZE_EVENT)

    return fonts


def build_simple_calendar(year, month):
    """
    シンプルなカレンダーグリッド構築。
    返り値: weeks (各週は7要素のリスト、各要素は (day, month_offset))
    month_offset: -1=前月, 0=当月, 1=翌月
    """
    # 月の初日の曜日（0=月, 6=日）と日数
    first_dow, num_days = calendar.monthrange(year, month)

    # 前月の日数
    if month == 1:
        prev_days = calendar.monthrange(year - 1, 12)[1]
    else:
        prev_days = calendar.monthrange(year, month - 1)[1]

    # 全セルを生成（前月の端数 + 当月 + 翌月の端数）
    cells = []

    # 前月の端数
    for i in range(first_dow):
        d = prev_days - first_dow + 1 + i
        cells.append((d, -1))

    # 当月
    for d in range(1, num_days + 1):
        cells.append((d, 0))

    # 翌月の端数（7の倍数になるまで）
    next_d = 1
    while len(cells) % 7 != 0:
        cells.append((next_d, 1))
        next_d += 1

    # 週に分割
    weeks = []
    for i in range(0, len(cells), 7):
        weeks.append(cells[i:i+7])

    return weeks


def is_weekend(dow):
    """土曜(5)または日曜(6)かどうか"""
    return dow >= 5


def is_holiday(day, month_offset, config):
    """祝日かどうか"""
    if month_offset == 0:
        return day in config.get('holidays', [])
    elif month_offset == -1:
        return day in config.get('prev_month_holidays', [])
    elif month_offset == 1:
        return day in config.get('next_month_holidays', [])
    return False


def get_hours(day, month_offset, config):
    """営業時間を取得"""
    if month_offset == 0:
        return config['schedule'].get(str(day), None)
    elif month_offset == -1:
        return config.get('prev_month_schedule', {}).get(str(day), None)
    elif month_offset == 1:
        return config.get('next_month_schedule', {}).get(str(day), None)
    return None


def get_month_prefix(month_offset, year, month):
    """前月/翌月のプレフィックス番号"""
    if month_offset == -1:
        m = month - 1 if month > 1 else 12
        return str(m)
    elif month_offset == 1:
        m = month + 1 if month < 12 else 1
        return str(m)
    return ""


def draw_centered_text(draw, x, y, text, font, color):
    """中央揃えでテキストを描画"""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw / 2, y - th / 2), text, fill=color, font=font)


def is_latin_char(ch):
    """ラテン文字・数字・記号かどうか"""
    cp = ord(ch)
    return cp < 0x3000 or (0xFF00 <= cp <= 0xFFEF)


def split_text_segments(text):
    """テキストを日本語/ラテンのセグメントに分割"""
    segments = []
    current = ""
    current_is_latin = None

    for ch in text:
        ch_latin = is_latin_char(ch)
        if current_is_latin is None:
            current_is_latin = ch_latin
        if ch_latin != current_is_latin:
            if current:
                segments.append((current, current_is_latin))
            current = ch
            current_is_latin = ch_latin
        else:
            current += ch

    if current:
        segments.append((current, current_is_latin))

    return segments


def draw_bottom_text(draw, y, text, fonts, color):
    """
    下部テキストを描画。日本語とラテン文字で別フォントを使用。
    ベースラインを揃えて描画する。
    """
    segments = split_text_segments(text)

    # 各セグメントの情報を収集（ascent/descentでベースライン揃え）
    total_w = 0
    seg_info = []
    for seg_text, is_latin in segments:
        font = fonts['bottom_latin'] if is_latin else fonts['bottom_jp']
        bbox = draw.textbbox((0, 0), seg_text, font=font)
        w = bbox[2] - bbox[0]
        ascent, descent = font.getmetrics()
        seg_info.append((seg_text, font, w, ascent, descent, bbox[1]))
        total_w += w

    # 最大のascentを基準にベースラインを揃える
    max_ascent = max(a for _, _, _, a, _, _ in seg_info)
    max_descent = max(d for _, _, _, _, d, _ in seg_info)
    total_h = max_ascent + max_descent

    x = (IMG_W - total_w) / 2
    baseline_y = y - total_h / 2 + max_ascent

    for seg_text, font, w, ascent, descent, top_offset in seg_info:
        # ベースラインから各フォントのascentを引いた位置に描画
        draw_y = baseline_y - ascent
        draw.text((x, draw_y), seg_text, fill=color, font=font)
        x += w


def should_show_adjacent_weekends(year, month):
    """
    前月・翌月の週末を表示すべきかどうかを判定する。

    ルール:
    - 前月の週末: 当月が日曜始まりの場合のみ（前の土曜を表示して週末を完成）
    - 翌月の週末: 当月の末日が金曜 or 土曜の場合のみ（翌週末を表示して完成）
      月末が日〜木の場合、翌月の週末は離れているため表示しない
    """
    first_dow, num_days = calendar.monthrange(year, month)
    last_dow = (first_dow + num_days - 1) % 7  # 末日の曜日 (0=月...6=日)

    show_prev = (first_dow == 6)       # 月初が日曜 → 前月土曜を表示
    show_next = (last_dow in (4, 5))   # 末日が金曜(4) or 土曜(5) → 翌月週末を表示

    return show_prev, show_next


def should_show_cell(dow, month_offset, show_prev_weekends, show_next_weekends):
    """
    セルを表示すべきかどうか。
    当月の日付はすべて表示。
    前月/翌月は週末のみ、かつ月境界が近い場合のみ表示。
    """
    if month_offset == 0:
        return True
    if not is_weekend(dow):
        return False
    if month_offset == -1:
        return show_prev_weekends
    if month_offset == 1:
        return show_next_weekends
    return False


def find_event_position(event, weeks, year, month):
    """
    イベントがカレンダー上のどの行・列に位置するかを計算。
    返り値: (row_idx, start_col, end_col) のリスト（複数行にまたがる場合）
    """
    first_dow = calendar.monthrange(year, month)[0]
    start_day = event['start']
    end_day = event.get('end', start_day)

    positions = []
    for row_idx, week in enumerate(weeks):
        row_start_col = None
        row_end_col = None
        for col, (day, month_offset) in enumerate(week):
            if month_offset == 0 and start_day <= day <= end_day:
                if row_start_col is None:
                    row_start_col = col
                row_end_col = col
        if row_start_col is not None:
            positions.append((row_idx, row_start_col, row_end_col))

    return positions


def wrap_event_text(text, font, max_width, draw):
    """
    テキストをボックス幅に収まるよう折り返す。
    """
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw_event_box(draw, row_idx, start_col, end_col, text, fonts, y_first_row, row_height):
    """
    イベントボックスを描画する。
    営業時間の下に枠線付きのボックスでイベント名を表示。
    """
    y_hours = y_first_row + int(row_idx * row_height) + Y_HOURS_OFFSET
    y_box_top = y_hours + 18 + EVENT_BOX_GAP

    # ボックスの横幅（開始列〜終了列をカバー）
    col_half = 60  # 各列の半幅
    x_left = COL_X[start_col] - col_half
    x_right = COL_X[end_col] + col_half

    # テキスト折り返し
    font = fonts['event_jp']
    max_text_w = (x_right - x_left) - EVENT_BOX_PAD_H * 2
    lines = wrap_event_text(text, font, max_text_w, draw)

    # ボックスの高さを計算
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])

    total_text_h = sum(line_heights) + EVENT_LINE_GAP * (len(lines) - 1) if lines else 0
    box_h = total_text_h + EVENT_BOX_PAD_V * 2
    y_box_bottom = y_box_top + box_h

    # 枠線を描画（角丸風にrectangleで描画）
    draw.rectangle(
        [x_left, y_box_top, x_right, y_box_bottom],
        outline=COLOR_DARK,
        width=int(EVENT_BORDER_W + 0.5)
    )

    # テキストを描画（中央揃え）
    y_text = y_box_top + EVENT_BOX_PAD_V
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x_text = (x_left + x_right) / 2 - tw / 2
        draw.text((x_text, y_text), line, fill=COLOR_DARK, font=font)
        y_text += th + EVENT_LINE_GAP


def generate_calendar(config):
    """カレンダー画像を生成"""
    year = config['year']
    month = config['month']

    # フォント読み込み
    fonts = load_fonts(config)

    # カレンダーグリッド構築
    weeks = build_simple_calendar(year, month)
    show_prev_weekends, show_next_weekends = should_show_adjacent_weekends(year, month)
    num_weeks = len(weeks)

    # 行間を動的に計算（5行 or 6行に対応）
    available_height = Y_BOTTOM_TEXT - Y_FIRST_ROW - 100
    row_height = available_height / (num_weeks - 1) if num_weeks > 1 else 150
    row_height = min(row_height, 155)  # 最大155px

    # 画像作成
    img = Image.new('RGB', (IMG_W, IMG_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- 月の数字 ---
    month_str = str(month)
    draw_centered_text(draw, IMG_W // 2, Y_MONTH_NUM, month_str,
                       fonts['month_num'], COLOR_DARK)

    # --- 年 ---
    year_str = str(year)
    year_bbox = draw.textbbox((0, 0), year_str, font=fonts['year'])
    year_x = 830
    draw.text((year_x, Y_YEAR - (year_bbox[3] - year_bbox[1]) / 2),
              year_str, fill=COLOR_DARK, font=fonts['year'])

    # --- 曜日ヘッダー ---
    for dow, name in enumerate(DAY_NAMES):
        color = COLOR_ORANGE if dow >= 5 else COLOR_HEADER
        draw_centered_text(draw, COL_X[dow], Y_HEADERS, name,
                          fonts['header'], color)

    # --- カレンダーグリッド ---
    for row_idx, week in enumerate(weeks):
        y_date = Y_FIRST_ROW + int(row_idx * row_height)
        y_hours = y_date + Y_HOURS_OFFSET

        for dow, (day, month_offset) in enumerate(week):
            # 前月/翌月の非表示セルはスキップ
            if not should_show_cell(dow, month_offset, show_prev_weekends, show_next_weekends):
                continue

            x = COL_X[dow]

            # 色を決定
            colored = is_weekend(dow) or is_holiday(day, month_offset, config)
            date_color = COLOR_ORANGE if colored else COLOR_DARK

            # 月プレフィックスを付けるかどうか判定
            # 前月/翌月の日付は常にプレフィックス付き
            # 当月でも、同じ行に前月日付がある場合はプレフィックスを付ける
            needs_prefix = False
            prefix = ""
            if month_offset != 0:
                needs_prefix = True
                prefix = get_month_prefix(month_offset, year, month)
            elif row_idx == 0 and show_prev_weekends:
                # 最初の行に前月の週末がある → 当月日付にも月名を付ける
                needs_prefix = True
                prefix = str(month)

            # 日付描画
            day_str = str(day)
            if needs_prefix:
                prefix_text = prefix + "/"
                prefix_bbox = draw.textbbox((0, 0), prefix_text, font=fonts['month_prefix'])
                day_bbox = draw.textbbox((0, 0), day_str, font=fonts['date'])

                prefix_w = prefix_bbox[2] - prefix_bbox[0]
                day_w = day_bbox[2] - day_bbox[0]
                total_w = prefix_w + day_w

                start_x = x - total_w / 2

                # プレフィックス（小さく、上寄り）
                day_h = day_bbox[3] - day_bbox[1]
                prefix_y = y_date - day_h / 2 - 4
                draw.text((start_x, prefix_y), prefix_text,
                         fill=date_color, font=fonts['month_prefix'])

                # 日付
                day_x = start_x + prefix_w
                day_y = y_date - day_h / 2
                draw.text((day_x, day_y), day_str,
                         fill=date_color, font=fonts['date'])
            else:
                # プレフィックスなし
                draw_centered_text(draw, x, y_date, day_str,
                                  fonts['date'], date_color)

            # 営業時間描画
            hours = get_hours(day, month_offset, config)
            if hours is not None:
                draw_centered_text(draw, x, y_hours, hours,
                                  fonts['hours'], COLOR_DARK)
            elif month_offset == 0:
                # 当月で営業時間がない = 定休日
                draw_centered_text(draw, x, y_hours, "-",
                                  fonts['closed'], COLOR_GRAY)

    # --- イベントボックス ---
    events = config.get('events', [])
    for event in events:
        positions = find_event_position(event, weeks, year, month)
        for row_idx, start_col, end_col in positions:
            draw_event_box(draw, row_idx, start_col, end_col,
                          event['name'], fonts, Y_FIRST_ROW, row_height)

    # --- 下部テキスト ---
    bottom_text = config.get('bottom_text', '')
    if bottom_text:
        # 最終行の営業時間の下に十分な余白を確保
        last_row_bottom = Y_FIRST_ROW + int((num_weeks - 1) * row_height) + Y_HOURS_OFFSET + 30
        actual_bottom_y = max(Y_BOTTOM_TEXT, last_row_bottom + 60)
        draw_bottom_text(draw, actual_bottom_y, bottom_text, fonts, COLOR_DARK)

    # --- 保存 ---
    output = config.get('output_filename', '')
    if not output:
        output = f"calendar_{year}_{month:02d}.png"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output)

    img.save(output_path, 'PNG', quality=95)
    print(f"✓ カレンダー画像を生成しました: {output_path}")
    print(f"  {year}年{month}月 / {IMG_W}x{IMG_H}px / {num_weeks}週")

    return output_path


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(config_path)
    generate_calendar(config)


if __name__ == '__main__':
    main()
