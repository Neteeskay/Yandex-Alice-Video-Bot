import random
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError

INPUT_DIR = Path(r"D:\desktop\yandex_photo\photos")
OUTPUT_DIR = Path(r"D:\desktop\yandex_photo\videos")
PROFILE_DIR = Path(r"D:\desktop\yandex_photo\yandex_alice_profile")

URL = "https://alice.yandex.ru/media/video"
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

PLOTS = [
    "В кадре сцены только персона или персоны с оригинального снимка, больше никого в",
    "В кадре сцены только человек или люди с оригинального снимка, больше никого в ка",
    "Камера приближается на нос и неожиданно собака оказывается в праздничном колпаке",
    "Девочки за партой дают друг другу пять руками",
    "Девочки в школе дают друг другу пять. Атмосфера дружелюбная, радостная",
    "Дети улыбаются и машут в кадре",
    "Дружно танцуют в кадре",
    "Дети радостно прыгают",
    "Женщина машет рукой",
    "Оживи это старое детское фото так, будто оператор с VHS",
]


def wait_click(page, locator, timeout=30000):
    locator.wait_for(state="visible", timeout=timeout)
    locator.click()


def process_photo(page, photo_path: Path):
    print(f"\nОбрабатываю: {photo_path.name}")

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Если есть кнопка создания нового видео
    try:
        page.get_by_test_id("generate-video-create-new").click(timeout=5000)
        page.wait_for_timeout(1000)
    except TimeoutError:
        pass

    # Загрузка фото
    page.get_by_test_id("generate-video-file-label").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_test_id("generate-video-file-label").click()

    file_chooser = fc_info.value
    file_chooser.set_files(str(photo_path))
    page.wait_for_timeout(5000)

    # Выбор случайного сюжета
    plot = random.choice(PLOTS)
    print(f"Сюжет: {plot}")

    try:
        page.get_by_role("button", name=plot).click(timeout=15000)
    except TimeoutError:
        # Если Playwright не нашёл полное имя, пробуем по первым словам
        short_plot = plot[:45]
        page.get_by_role("button", name=re.compile(short_plot)).click(timeout=15000)

    page.wait_for_timeout(1000)

    # Старт
    page.get_by_test_id("generate-video-submit").click()

    # Ожидание кнопки Скачать
    print("Жду генерацию...")

    download_button = page.get_by_role("button", name="Скачать", exact=True)

    for _ in range(180):  # примерно до 30 минут
        try:
            if download_button.is_visible(timeout=3000):
                break
        except TimeoutError:
            pass
        time.sleep(10)
    else:
        raise RuntimeError("Не дождался кнопки Скачать")

    # Скачивание
    with page.expect_download(timeout=120000) as download_info:
        download_button.click()

    download = download_info.value
    output_file = OUTPUT_DIR / f"{photo_path.stem}.mp4"
    download.save_as(str(output_file))

    print(f"Готово: {output_file}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    photos = sorted(
        p for p in INPUT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in PHOTO_EXTS
    )

    if not photos:
        print("Фото не найдены")
        return

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            accept_downloads=True,
            slow_mo=300,
        )

        page = context.new_page()

        print("Если Яндекс попросит вход — войди вручную один раз.")
        print("После входа скрипт продолжит работу с сохранённой сессией.")

        for photo in photos:
            try:
                process_photo(page, photo)
            except Exception as e:
                print(f"Ошибка с {photo.name}: {e}")

        context.close()


if __name__ == "__main__":
    import re
    main()