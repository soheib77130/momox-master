from __future__ import annotations

import argparse
import datetime
import re
import sqlite3
import sys
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen


MOMOX_SEARCH_URL = "https://www.momox.fr/search?query={isbn}"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class MomoxResult:
    isbn: str
    title: str
    price: str
    fetched_at: str
    error: str | None = None


def fetch_html(isbn: str, timeout: int = 20) -> str:
    url = MOMOX_SEARCH_URL.format(isbn=isbn)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _extract_text(html: str, class_name: str) -> str | None:
    pattern = (
        rf"class=\"[^\"]*{re.escape(class_name)}[^\"]*\"[^>]*>"
        r"\s*([^<]+)"
    )
    match = re.search(pattern, html, re.IGNORECASE)
    if not match:
        return None
    return unescape(match.group(1)).strip()


def parse_momox_page(html: str) -> tuple[str | None, str | None]:
    title = _extract_text(html, "product-title")
    price = _extract_text(html, "searchresult-price")
    return title, price


def fetch_momox_result(isbn: str) -> MomoxResult:
    fetched_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        html = fetch_html(isbn)
        title, price = parse_momox_page(html)
        if not title:
            return MomoxResult(isbn, "", "", fetched_at, "Titre introuvable")
        if not price:
            return MomoxResult(isbn, title, "", fetched_at, "Prix introuvable")
        return MomoxResult(isbn, title, price, fetched_at)
    except URLError as exc:
        return MomoxResult(isbn, "", "", fetched_at, f"Erreur réseau: {exc}")


def init_db(db_path: str) -> sqlite3.Connection:
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT,
            name TEXT,
            price TEXT,
            date TEXT,
            error TEXT
        )
        """
    )
    db.commit()
    ensure_error_column(db)
    return db


def ensure_error_column(db: sqlite3.Connection) -> None:
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}
    if "error" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN error TEXT")
        db.commit()


def save_result(db: sqlite3.Connection, result: MomoxResult) -> None:
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users(isbn, name, price, date, error) VALUES (?,?,?,?,?)",
        (result.isbn, result.title, result.price, result.fetched_at, result.error),
    )
    db.commit()


def load_isbns(args: argparse.Namespace) -> list[str]:
    isbns: list[str] = []
    if args.isbn:
        isbns.extend(args.isbn)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            for line in handle:
                value = line.strip()
                if value:
                    isbns.append(value)
    if not isbns:
        value = input("ISBN (ou liste séparée par des virgules) ?: ").strip()
        if value:
            isbns.extend([item.strip() for item in value.split(",") if item.strip()])
    return isbns


def print_results(results: Iterable[MomoxResult]) -> None:
    for result in results:
        print("\nISBN :", result.isbn)
        if result.error:
            print("Erreur :", result.error)
            continue
        print("Titre :", result.title)
        print("Prix  :", result.price)
        print("Date  :", result.fetched_at)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Récupère les prix Momox pour une liste d'ISBN."
    )
    parser.add_argument(
        "--isbn",
        action="append",
        help="ISBN individuel (peut être répété).",
    )
    parser.add_argument("--file", help="Fichier contenant un ISBN par ligne.")
    parser.add_argument("--db", default="mabase.db", help="Chemin du fichier SQLite.")
    args = parser.parse_args()

    isbns = load_isbns(args)
    if not isbns:
        print("Aucun ISBN fourni.")
        return 1

    db = init_db(args.db)
    results: list[MomoxResult] = []
    try:
        for isbn in isbns:
            result = fetch_momox_result(isbn)
            save_result(db, result)
            results.append(result)
    finally:
        db.close()

    print_results(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
