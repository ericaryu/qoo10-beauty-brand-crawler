# Qoo10 Beauty Brand Crawler

日本コスメブランドに関する2つのツールを提供します。

---

## ツール一覧

| ファイル | 役割 |
|---|---|
| `qoo10_beauty_brands.py` | Qoo10JPからブランド名を収集してCSVに保存 |
| `brand_website_finder.py` | CSVのブランド名から公式サイトURLを検索して追記 |

---

## 1. Qoo10 ブランド名クローラー (`qoo10_beauty_brands.py`)

Qoo10 JP の美容カテゴリ (`/cat/120000020`) からブランド名を自動収集します。

### 使い方

```bash
python qoo10_beauty_brands.py
```

- 出力: `~/Downloads/qoo10_beauty_brands.csv`（A列: ブランド名）
- 1000件に達するまで収集。途中中断→再実行で続きから再開可能。

### 必要環境

- Google Chrome + ChromeDriver
- `pip install selenium`

---

## 2. 公式サイト検索ツール (`brand_website_finder.py`)

CSVのA列に記載されたブランド名を読み取り、DuckDuckGoで公式サイトを検索してB列に追記します。

**ヘアケアに限らず、日本コスメブランド全般に使用可能です。**

### 使い方

```bash
# デフォルト (~/Downloads/qoo10_beauty_brands.csv を使用)
python brand_website_finder.py

# 入力ファイルを指定
python brand_website_finder.py --input path/to/brands.csv

# 入出力ファイルを別々に指定
python brand_website_finder.py --input brands.csv --output result.csv

# ブランド名の列ヘッダーを指定 (デフォルトは0列目)
python brand_website_finder.py --brand-col ブランド名
```

### CSV フォーマット

| A列 (ブランド名) | B列 (ウェブサイト) |
|---|---|
| ミルボン | https://www.milbon.co.jp/ |
| BOTANIST | https://botanist.jp/ |
| … | … |

- B列がすでに埋まっている行はスキップされます（途中再開対応）
- 「公式」プレフィックス付きのブランド名も自動で除去して検索

### 必要環境

```bash
pip install duckduckgo-search
```

---

## セットアップ

```bash
git clone https://github.com/ericaryu/qoo10-beauty-brand-crawler.git
cd qoo10-beauty-brand-crawler
pip install -r requirements.txt
```
