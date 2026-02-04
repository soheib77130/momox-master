import sqlite3
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------- DATABASE ----------
db = sqlite3.connect("mabase.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT,
    name TEXT,
    price TEXT,
    date TEXT
)
""")

date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
isbn = input("isbn ?: ").strip()


# ---------- SELENIUM ----------
driver = webdriver.Chrome()
driver.set_page_load_timeout(30)

try:
    driver.get("https://www.momox.fr/")

    wait = WebDriverWait(driver, 30)

    # champ recherche
    search = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "searchbox-input"))
    )
    search.clear()
    search.send_keys(isbn)

    # bouton rechercher
    wait.until(
        EC.element_to_be_clickable((By.ID, "buttonMediaSearchSubmit"))
    ).click()

    # résultats
    price = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "searchresult-price"))
    ).text

    title = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "product-title"))
    ).text

finally:
    driver.quit()


# ---------- SAVE ----------
cursor.execute(
    "INSERT INTO users(isbn, name, price, date) VALUES (?,?,?,?)",
    (isbn, title, price, date)
)
db.commit()


# ---------- DISPLAY ----------
print("Date :", date)
print("ISBN :", isbn)
print("Titre :", title)
print("Prix :", price)

cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

print("\nHistorique :")
for r in rows:
    print(r)

db.close()
print("\nfin")
