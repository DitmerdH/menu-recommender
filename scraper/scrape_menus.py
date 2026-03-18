# imports
import requests
from bs4 import BeautifulSoup
import pandas as pd


# =========================
# HELPER FUNCTIONS
# DONT DUPLICATE
# =========================

def clean_text(text):
    if not text:
        return None

    text = " ".join(text.replace("\xa0", " ").split())

    replacements = {
        "Ã¨": "è", "Ã©": "é", "Ãª": "ê", "Ã«": "ë",
        "Ã¡": "á", "Ã ": "à", "Ã§": "ç",
        "Ã¶": "ö", "Ã¼": "ü",
        "Ã®": "î", "Ã¯": "ï",
        "Ã´": "ô", "Ã»": "û",
        "â": "–", "â": "—", "â": "’",
        "Â ": "", "&nbsp;": " ",
    }

    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    return text.strip()


def clean_price_whole_decimal(price_whole, price_decimal):
    whole = clean_text(price_whole) if price_whole else ""
    decimal = clean_text(price_decimal) if price_decimal else ""
    price = f"{whole}.{decimal}" if decimal else whole
    try:
        return float(price)
    except:
        return None

# =========================
# PIZZA BEPPE
# =========================
def scrape_pizza_beppe():
    url = "https://www.pizzabeppe.nl/menu"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    dishes = []
    current_category = None

    category_map = {
        "Pizza": "Pizza",
        "Starters to share": "Starters",
        "Dolci": "Desserts"
    }

    elements = soup.select("section.c-section.is--menu h2, section.c-section.is--menu div.menu_row")

    for el in elements:
        if el.name == "h2":
            heading = clean_text(el.get_text(" ", strip=True))
            current_category = category_map.get(heading)
            continue

        if "menu_row" in el.get("class", []):
            if not current_category:
                continue

            items = el.select("div.menu_item")

            for item in items:
                title_tag = item.select_one("h3.c-h3-small")
                desc_tag = item.select_one("p.menu_item-ingredients")
                price_whole_tag = item.select_one("div.c-menu-price-txt")
                price_decimal_tag = item.select_one("div.is--price-small")

                if not title_tag or not price_whole_tag:
                    continue

                dish = clean_text(title_tag.get_text(" ", strip=True))
                description = clean_text(desc_tag.get_text(" ", strip=True)) if desc_tag else None
                price = clean_price_whole_decimal(
                    price_whole_tag.get_text(" ", strip=True) if price_whole_tag else None,
                    price_decimal_tag.get_text(" ", strip=True) if price_decimal_tag else None
                )

                tag_list = []

                icon_urls = [
                    img.get("src", "").lower()
                    for img in item.select("img.c-icon, img.c-tip")
                ]

                if any("vegetarisch" in src for src in icon_urls):
                    tag_list.append("vegetarian")
                if any("vegan" in src for src in icon_urls):
                    tag_list.append("vegan")
                if any("tip" in src for src in icon_urls):
                    tag_list.append("tip")

                tags = ", ".join(tag_list) if tag_list else None

                dishes.append({
                    "restaurant": "Pizza Beppe",
                    "city": "Leeuwarden",
                    "menu_type": "Dinner",
                    "category": current_category,
                    "dish": dish,
                    "price": price,
                    "description": description,
                    "tags": tags
                })

    df = pd.DataFrame(dishes).drop_duplicates(
        subset=["restaurant", "city", "menu_type", "category", "dish", "price"]
    )

    return df.to_dict(orient="records")

# =========================
# BROODHUYS
# =========================
def scrape_broodhuys():
    url = "https://www.hetbroodhuys.nl/nl/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    dishes = []

    panes = soup.select("div.tab-pane")

    for pane in panes:
        category_tag = pane.find("h3")
        if not category_tag:
            continue

        category = category_tag.get_text(" ", strip=True)

        if category.lower() == "drinken":
            continue

        for p in pane.find_all("p"):
            price_tags = p.select("span.tab")

            if len(price_tags) != 1:
                continue

            price = price_tags[0].get_text(" ", strip=True)
            full_text = p.get_text(" ", strip=True)

            dish_text = full_text.replace(price, "").strip()

            if not dish_text:
                continue

            if dish_text.lower().startswith(("geserveerd op", "keuze uit", "met verrassing")):
                continue

            dishes.append({
                "restaurant": "Broodhuys",
                "city": "Leeuwarden",
                "menu_type": "Lunch",
                "category": category,
                "dish": dish_text,
                "price": price,
                "description": None,
                "tags": None
            })

    df = pd.DataFrame(dishes).drop_duplicates(
        subset=["restaurant", "city", "menu_type", "category", "dish", "price"]
    )

    return df.to_dict(orient="records")

# =========================
# JACK AND JACKY'S
# =========================

def scrape_jack_and_jackys():
    url = "https://jackandjackys.nl/menu-leeuwarden/"
    headers = {"User-Agent": "Mozilla/5.0"}

    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    dishes = []
    current_category = None

    allowed_categories = {
        "BOWLS", "PANCAKES", "SANDWICHES",
        "SALADS", "BAKERY", "KIDS FOOD"
    }

    elements = soup.select("h2.elementor-heading-title, div.menu-row")

    for el in elements:
        if el.name == "h2":
            current_category = el.get_text(" ", strip=True)
            continue

        if "menu-row" in el.get("class", []):
            if current_category not in allowed_categories:
                continue

            name_tag = el.select_one("span.name")
            price_tag = el.select_one("span.price")
            extra_tag = el.select_one("span.extra")

            if extra_tag or not name_tag or not price_tag:
                continue

            i_tag = name_tag.find("i")
            description = clean_text(i_tag.get_text()) if i_tag else None

            dish_parts = [
                str(c).strip()
                for c in name_tag.contents
                if getattr(c, "name", None) not in ["i", "br"] and str(c).strip()
            ]

            dish = clean_text(" ".join(dish_parts))

            dishes.append({
                "restaurant": "Jack and Jacky's",
                "city": "Leeuwarden",
                "menu_type": "Lunch",
                "category": current_category,
                "dish": dish,
                "price": clean_text(price_tag.get_text()),
                "description": description,
                "tags": None
            })

    df = pd.DataFrame(dishes).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    )

    return df.to_dict(orient="records")


# =========================
# ROAST (LUNCH + DINNER)
# =========================

def scrape_roast_lunch():
    url = "https://roastleeuwarden.nl/menukaarten/lunchkaart/"
    headers = {"User-Agent": "Mozilla/5.0"}

    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    dishes = []
    current_category = None

    elements = soup.select("span.elementor-heading-title, div.elementor-widget-price-list")

    for el in elements:
        if el.name == "span":
            current_category = clean_text(el.get_text())
            continue

        if "elementor-widget-price-list" in el.get("class", []):
            for item in el.select("li.elementor-price-list-item"):
                title = item.select_one("span.elementor-price-list-title")
                price = item.select_one("span.elementor-price-list-price")
                desc = item.select_one("p.elementor-price-list-description")

                if not title or not price:
                    continue

                dishes.append({
                    "restaurant": "Roast",
                    "city": "Leeuwarden",
                    "menu_type": "Lunch",
                    "category": current_category,
                    "dish": clean_text(title.get_text()),
                    "price": clean_text(price.get_text()),
                    "description": clean_text(desc.get_text()) if desc else None,
                    "tags": None
                })

    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")


def scrape_roast_dinner():
    url = "https://roastleeuwarden.nl/menukaarten/dinerkaart/"
    headers = {"User-Agent": "Mozilla/5.0"}

    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    dishes = []
    current_category = None

    elements = soup.select("span.elementor-heading-title, div.elementor-widget-price-list")

    for el in elements:
        if el.name == "span":
            current_category = clean_text(el.get_text())
            continue

        if "elementor-widget-price-list" in el.get("class", []):
            for item in el.select("li.elementor-price-list-item"):
                title = item.select_one("span.elementor-price-list-title")
                price = item.select_one("span.elementor-price-list-price")
                desc = item.select_one("p.elementor-price-list-description")

                if not title or not price:
                    continue

                dishes.append({
                    "restaurant": "Roast",
                    "city": "Leeuwarden",
                    "menu_type": "Dinner",
                    "category": current_category,
                    "dish": clean_text(title.get_text()),
                    "price": clean_text(price.get_text()),
                    "description": clean_text(desc.get_text()) if desc else None,
                    "tags": None
                })

    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")


# =========================
# BAYLINGS
# =========================

def scrape_baylings():
    url = "https://baylings.nl/menu/"
    headers = {"User-Agent": "Mozilla/5.0"}

    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    dishes = []
    current_menu_type = None
    current_category = None

    elements = soup.select("h6.pt-title, div.pt-food-menu-item")

    for el in elements:
        if el.name == "h6":
            title = clean_text(el.get_text()).upper()

            if title == "LUNCH":
                current_menu_type = "Lunch"
                current_category = None
            elif title in ["STARTERS", "MAIN"]:
                current_menu_type = "Dinner"
                current_category = None
            elif title == "DESSERTS":
                current_menu_type = "Dinner"
                current_category = "Dessert"
            else:
                current_category = title.title()
            continue

        if "pt-food-menu-item" in el.get("class", []):
            title_tag = el.select_one("span.title-wrap")
            price_tag = el.select_one("span.pt-food-menu-price")
            desc_tag = el.select_one("p.pt-food-menu-details")

            if not title_tag or not price_tag:
                continue

            dishes.append({
                "restaurant": "Baylings",
                "city": "Leeuwarden",
                "menu_type": current_menu_type,
                "category": current_category or current_menu_type,
                "dish": clean_text(title_tag.get_text()),
                "price": clean_text(price_tag.get_text()),
                "description": clean_text(desc_tag.get_text()) if desc_tag else None,
                "tags": None
            })

    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")


# =========================
# DIKKE VAN DALE (LUNCH + DINNER)
# =========================

def scrape_dikke_van_dale_lunch():
    url = "https://www.dedikkevandale.nl/lekker-lunchen"
    headers = {"User-Agent": "Mozilla/5.0"}

    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    dishes = []
    current_category = None

    allowed_categories = {
        "Soepen","Salades","Tosti's","Koude Broodjes",
        "Twaalfuurtjes","Warme Broodjes","Eiergerechten","Plates"
    }

    elements = soup.select("h5.framer-text, div[class*='container']")

    for el in elements:
        if el.name == "h5":
            cat = clean_text(el.get_text()).title()
            if cat in allowed_categories:
                current_category = cat
            else:
                current_category = None
            continue

        if not current_category:
            continue

        text_tag = el.select_one("p.framer-text")
        price_tag = el.select_one("div.framer-uf3a4z p")

        if not text_tag or not price_tag:
            continue

        text = clean_text(text_tag.get_text())
        price = clean_text(price_tag.get_text())

        if " - " in text:
            dish, description = text.split(" - ", 1)
        else:
            dish, description = text, None

        dishes.append({
            "restaurant": "De Dikke van Dale",
            "city": "Leeuwarden",
            "menu_type": "Lunch",
            "category": current_category,
            "dish": clean_text(dish),
            "price": price,
            "description": clean_text(description) if description else None,
            "tags": None
        })

    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")


def scrape_dikke_van_dale_dinner():
    url = "https://www.dedikkevandale.nl/sfeervol-dineren"
    headers = {"User-Agent": "Mozilla/5.0"}

    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    dishes = []
    current_category = None

    elements = soup.select("h5.framer-text, p.framer-text")

    for el in elements:
        if el.name == "h5":
            current_category = clean_text(el.get_text()).title()
            continue

        if not current_category or not el.find("strong"):
            continue

        text = clean_text(el.get_text())
        dish = clean_text(el.find("strong").get_text())
        description = text.replace(dish, "").strip(" -–—")

        parent = el.find_parent("div")
        price_tag = parent.find_next("div", class_="framer-uf3a4z") if parent else None

        if not price_tag:
            continue

        dishes.append({
            "restaurant": "De Dikke van Dale",
            "city": "Leeuwarden",
            "menu_type": "Dinner",
            "category": current_category,
            "dish": dish,
            "price": clean_text(price_tag.get_text()),
            "description": clean_text(description) if description else None,
            "tags": None
        })

    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")

# =========================
# ADD YOUR SCRAPE FUNCTIONS HERE
# =========================

# =========================
# COLLECTOR (ADD YOUR SCRAPES HERE)
# =========================
def scrape_all_menus():
    all_data = []

    print("Jack and Jacky's:", len(scrape_jack_and_jackys()))
    print("Roast lunch:", len(scrape_roast_lunch()))
    print("Roast dinner:", len(scrape_roast_dinner()))
    print("Baylings:", len(scrape_baylings()))
    print("DVD lunch:", len(scrape_dikke_van_dale_lunch()))
    print("DVD dinner:", len(scrape_dikke_van_dale_dinner()))

    all_data.extend(scrape_jack_and_jackys())
    all_data.extend(scrape_roast_lunch())
    all_data.extend(scrape_roast_dinner())
    all_data.extend(scrape_baylings())
    all_data.extend(scrape_dikke_van_dale_lunch())
    all_data.extend(scrape_dikke_van_dale_dinner())

    return pd.DataFrame(all_data)

# running file manually
if __name__ == "__main__":
    df = scrape_all_menus()
    print(df.head())