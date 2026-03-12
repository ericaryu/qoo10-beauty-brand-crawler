"""
Qoo10 JP カテゴリ 120000020 ブランド名クローラー
出力: ~/Downloads/qoo10_beauty_brands.csv  (A列: ブランド名)
"""
import csv, time, re, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.qoo10.jp/cat/120000020"
OUT = os.path.expanduser("~/Downloads/qoo10_beauty_brands.csv")

def get_driver():
    opts = Options()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=opts)

def clean(text):
    text = re.sub(r'[\[【].*?[\]】]', '', text).strip()
    return text if 1 < len(text) < 80 else ''

def collect(driver):
    # 기존 CSV에서 브랜드 불러오기 (이어 크롤링)
    brands = set()
    if os.path.exists(OUT):
        with open(OUT, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None)  # 헤더 스킵
            for row in reader:
                if row:
                    brands.add(row[0])
        print(f"기존 수집 브랜드 {len(brands)}개 로드 완료. 이어서 크롤링합니다.")
    else:
        # 파일 없으면 헤더만 초기화
        with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow(['ブランド名'])

    driver.get(URL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".txt_brand"))
    )
    time.sleep(3)

    while True:
        # 1. 현재 화면의 브랜드 추출
        elements = driver.find_elements(By.CSS_SELECTOR, ".txt_brand")
        current_batch = []
        new_count = 0

        for el in elements:
            b = clean(el.text)
            if b:
                if b not in brands:
                    brands.add(b)
                    current_batch.append(b)
                    new_count += 1

        # 2. 실시간 파일 저장 (추가 모드 'a')
        if current_batch:
            with open(OUT, 'a', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                for b in current_batch:
                    w.writerow([b])
            print(f"  새로 저장됨: {len(current_batch)}개 / 누적: {len(brands)}개")

        # 3. 1000개 도달 시 종료
        if len(brands) >= 1000:
            print(f"✅ 목표 1000개 달성. 크롤링을 종료합니다.")
            break

        # 4. 더보기 버튼 탐색
        more_btn = None
        for sel in ["a.btn_more", "button.btn_more", ".more_btn a",
                    "a[class*='more']", "button[class*='more']",
                    "//a[contains(text(),'もっと見る')]",
                    "//button[contains(text(),'もっと見る')]",
                    "//a[contains(text(),'more')]"]:
            try:
                by = By.XPATH if sel.startswith("//") else By.CSS_SELECTOR
                btn = driver.find_element(by, sel)
                if btn.is_displayed():
                    more_btn = btn
                    break
            except Exception:
                pass

        if more_btn:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", more_btn)
            time.sleep(0.5)
            try:
                more_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(2.5)
        else:
            # 버튼 없으면 스크롤로 무한로드 시도
            prev_h = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_h = driver.execute_script("return document.body.scrollHeight")
            if new_h == prev_h:
                print("⛔ 더 이상 로드할 데이터 없음")
                break

    return sorted(brands)

def main():
    driver = get_driver()
    try:
        print(f"🚀 크롤링 시작: {URL}")
        brands = collect(driver)
        print(f"\n✅ 완료: {len(brands)}개 브랜드 → {OUT}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
