"""
日本コスメブランド 公式サイト検索ツール
Brand name → official website URL

Usage:
  # デフォルト (~/Downloads/qoo10_beauty_brands.csv を入出力)
  python3 brand_website_finder.py

  # 入力ファイル指定
  python3 brand_website_finder.py --input path/to/brands.csv

  # 入出力ファイルを別々に指定
  python3 brand_website_finder.py --input brands.csv --output result.csv

  # A列ヘッダー名を指定 (デフォルト: 先頭列を使用)
  python3 brand_website_finder.py --brand-col ブランド名

CSV形式:
  - A列: ブランド名
  - B列: 公式ウェブサイト URL (空なら検索して埋める、既存値はスキップ)
"""

import argparse
import csv
import os
import re
import time

from ddgs import DDGS

# ────────────────────────────────────────────
# 公式サイトと見なさないドメインキーワード
# ────────────────────────────────────────────
EXCLUDE_DOMAINS = [
    # EC / 通販
    "qoo10", "amazon.", "rakuten.", "yahoo.co.jp", "store.shopping.yahoo",
    "mercari", "zozotown", "lohaco", "askul", "itoyokado", "bellemaison",
    "yodobashi", "biccamera", "bic-camera", "nitori", "cosme-de.com",
    "esty.com", "shopping.naver", "aliexpress", "taobao", "jd.com",
    # 口コミ・比較・美容メディア
    "@cosme", "cosme.net", "cosme.com", "lips.beauty", "lipscosme.com",
    "hotpepper", "beauty.hotpepper", "minpaku",
    "prtimes.jp", "mynavi", "oricon", "allabout.co.jp",
    "beautyexpert", "beautyreview", "stylecraze",
    "byrdie", "elle.", "vogue.", "cosmopolitan.",
    "locokau.com", "bihadashop.jp", "maquia.hpplus",
    # ニュース・まとめ・PR
    "matome", "buzzfeed", "huffpost", "news.",
    "nikkei.", "asahi.", "mainichi.", "yomiuri.", "sankei.",
    "prtimes", "prwire", "dreamnews",
    # SNS
    "twitter.com", "x.com", "instagram.com", "facebook.com",
    "tiktok.com", "youtube.com", "pinterest.com", "line.me", "threads.net",
    # ブログ・CMS・個人サイト
    "note.com", "ameblo.jp", "livedoor", "goo.ne.jp",
    "excite.co.jp", "biglobe.ne.jp", "fc2.com", "blog.",
    "wordpress.com", "wix.com", "weebly.com", "jugem.jp",
    "hatena.ne.jp", "seesaa.net",
    # 辞典・百科事典
    "wikipedia.org", "wikimedia.org", "wikidata.org",
    # 検索エンジン・ポータル
    "google.com", "bing.com", "duckduckgo.com", "search.yahoo",
    # DDGSレート制限時のリダイレクト先 (偽陽性除去)
    "hermes.com",
    # 業販・卸・第三者ショップ
    "forcise.jp", "andhabit.com", "hikota.com",
    "a-round-match.shop", "album-hair.com",
    "lullhair.com", "vicrea", "azzurro-shop",
    "hairbeauty", "haircosme", "beautypark",
    "hamee.co.jp", "m-kirei.com", "wacul.co.jp",
    # 無関係ドメイン
    "investor.vanguard", ".gov", ".edu", "dormy-hotels",
    "be-story.jp", "naokogushima.com",
]

# タイトルに含まれると「公式らしい」キーワード
OFFICIAL_TITLE_KEYWORDS = ["公式", "official", "オフィシャル"]


def clean_brand_name(name: str) -> str:
    """「公式」などのプレフィックスを除去してブランド名を返す"""
    name = re.sub(r"^公式\s*", "", name).strip()
    return name


def score_result(url: str, title: str) -> int:
    """
    検索結果のスコアを返す (高いほど公式サイトらしい)
      -99 : 除外ドメインにヒット → 採用しない
        0 : 除外なし・手がかりなし
       +1 : .jp ドメイン
       +2 : タイトル or URL に 公式/official が含まれる
    """
    if not url:
        return -99
    url_lower = url.lower()
    for domain in EXCLUDE_DOMAINS:
        if domain in url_lower:
            return -99

    score = 0
    title_lower = (title or "").lower()
    for kw in OFFICIAL_TITLE_KEYWORDS:
        if kw in title_lower or kw in url_lower:
            score += 2
            break
    if re.search(r"\.jp(/|$)", url_lower):
        score += 1
    return score


def search_brand_website(brand_name: str) -> str:
    """
    DuckDuckGo でブランドの公式サイトを検索して URL を返す。
    見つからない場合は空文字列を返す。
    """
    clean_name = clean_brand_name(brand_name)
    if not clean_name:
        return ""

    queries = [
        f"{clean_name} 公式サイト",
        f"{clean_name} 化粧品 OR ヘアケア 公式",
        f"{clean_name} official website cosmetics",
    ]

    best_url = ""
    best_score = -1

    for query in queries:
        try:
            # DDGS インスタンスをクエリごとに作成 (レート制限対策)
            with DDGS() as ddgs:
                results = ddgs.text(query, region="jp-jp", max_results=8)
            if not results:
                time.sleep(2)
                continue
            for r in results:
                url = r.get("href", "")
                title = r.get("title", "")
                s = score_result(url, title)
                if s > best_score:
                    best_score = s
                    best_url = url
                # 高スコア (公式キーワードあり) ならすぐ採用
                if s >= 2:
                    return best_url
            time.sleep(2.0)  # クエリ間のウェイト
        except Exception as e:
            print(f"\n    [warn] Search error for '{clean_name}': {e}")
            time.sleep(8.0)

    # score 0 以上 (除外なし) の結果のみ返す
    return best_url if best_score >= 0 else ""


def load_csv(filepath: str) -> list:
    """CSV を読み込み rows リストを返す"""
    with open(filepath, "r", newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def save_csv(filepath: str, rows: list) -> None:
    """CSV を上書き保存"""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="日本コスメブランドの公式サイトURLをCSVに追記するツール"
    )
    parser.add_argument(
        "--input",
        default=os.path.expanduser("~/Downloads/qoo10_beauty_brands.csv"),
        help="入力CSVパス (A列=ブランド名, B列=URL). デフォルト: ~/Downloads/qoo10_beauty_brands.csv",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="出力CSVパス. 省略時は --input と同じファイルを上書き",
    )
    parser.add_argument(
        "--brand-col",
        default=None,
        help="ブランド名が入っている列のヘッダー名. 省略時は0列目を使用",
    )
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output or args.input

    if not os.path.exists(input_file):
        print(f"[error] Input file not found: {input_file}")
        return

    rows = load_csv(input_file)
    if not rows:
        print("[error] CSV is empty")
        return

    header = rows[0]

    # ブランド列のインデックスを特定
    brand_col_idx = 0
    if args.brand_col and args.brand_col in header:
        brand_col_idx = header.index(args.brand_col)

    # URL列のヘッダーがなければ追加
    url_col_idx = brand_col_idx + 1
    if len(header) <= url_col_idx:
        header.append("ウェブサイト")

    data_rows = rows[1:]
    total = len(data_rows)
    found = 0
    skipped = 0

    print(f"[info] Input : {input_file}")
    print(f"[info] Output: {output_file}")
    print(f"[info] Total brands: {total}\n")

    for i, row in enumerate(data_rows, 1):
        # 列が足りなければ空文字でパディング
        while len(row) <= url_col_idx:
            row.append("")

        brand_name = row[brand_col_idx].strip()
        existing_url = row[url_col_idx].strip()

        if not brand_name:
            continue

        if existing_url:
            print(f"[{i:>4}/{total}] SKIP   {brand_name[:30]:<30} → {existing_url}")
            skipped += 1
            continue

        print(f"[{i:>4}/{total}] SEARCH {brand_name[:30]:<30}", end=" ... ", flush=True)
        url = search_brand_website(brand_name)
        row[url_col_idx] = url

        if url:
            found += 1
            print(f"✓ {url}")
        else:
            print("✗ not found")

        # 1件ごとに上書き保存 (途中中断しても進捗を保持)
        save_csv(output_file, rows)
        time.sleep(1.0)  # ブランド間のウェイト

    print(f"\n✅ 完了: {found} 件取得 / {skipped} 件スキップ / {total - found - skipped} 件未取得")
    print(f"   保存先: {output_file}")


if __name__ == "__main__":
    main()
