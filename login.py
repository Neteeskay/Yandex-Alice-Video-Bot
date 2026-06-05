from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(r"D:\desktop\yandex_photo\yandex_alice_profile")
URL = "https://alice.yandex.ru/media/video"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        slow_mo=300,
    )

    page = context.new_page()
    page.goto(URL)

    print("Войди в Яндекс вручную в открывшемся браузере.")
    print("После успешного входа и открытия страницы Alice нажми Enter здесь.")

    input()

    context.close()

print("Сессия сохранена.")