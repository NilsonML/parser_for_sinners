"""
sinners_parser.py — сбор открытых данных с сайта студии sinners.studio:
состав команды (страница About) и вакансии (страница Job).

Запуск:
    python sinners_parser.py            # обе страницы
    python sinners_parser.py --only jobs
"""

import argparse
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ABOUT_URL = "https://sinners.studio/ru/about/"
JOBS_URL = "https://sinners.studio/ru/job/"
HEADERS = {"User-Agent": "Mozilla/5.0 (educational scraper)"}
TIMEOUT_SECONDS = 15


def fetch(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_team(soup: BeautifulSoup) -> pd.DataFrame:
    """Карточки 'Имя — Должность'. partition вместо split: строка без
    разделителя не роняет скрипт IndexError, а даёт пустую должность."""
    rows = []
    for member in soup.find_all("li", class_="team-member"):
        caption = member.find("p")
        if caption is None:
            continue
        name, _, post = caption.get_text(strip=True).partition("—")
        rows.append({"name": name.strip(), "post": post.strip(), "img": member.get("data-src")})
    return pd.DataFrame(rows, columns=["name", "post", "img"])


def parse_jobs(soup: BeautifulSoup) -> pd.DataFrame:
    rows = []
    for article in soup.find_all("article"):
        title = article.find("h3")
        description = article.select_one("p.roobert-m.trim span.selection-fix")
        if title is None:
            continue
        rows.append({
            "job": title.get_text(strip=True),
            # \xa0 — неразрывный пробел из вёрстки, заменяем на обычный
            "about_job": description.get_text(" ", strip=True).replace("\xa0", " ") if description else None,
        })
    return pd.DataFrame(rows, columns=["job", "about_job"])


def save(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
    print(f"Сохранено {len(df)} строк в {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Парсер страниц sinners.studio")
    parser.add_argument("--only", choices=["team", "jobs"], help="собрать только одну страницу")
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.only in (None, "team"):
        save(parse_team(fetch(ABOUT_URL)), args.out_dir / "about_data.csv")
    if args.only in (None, "jobs"):
        save(parse_jobs(fetch(JOBS_URL)), args.out_dir / "job_data.csv")


if __name__ == "__main__":
    main()
