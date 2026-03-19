# imports
import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import pandas as pd
import re
import warnings


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
# =========================
# FIER GRONINGEN (DINNER)
# =========================
def scrape_fier_groningen_dinner():
    restaurant_name = "Fier Groningen"
    city_name = "Groningen"
    menu_type_default = "Dinner"

    url = "https://fiergroningen.nl"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    menu_items = []

    sections = soup.select("#food-menu h3")

    for section in sections:
        category = clean_text(section.get_text(strip=True))

        parent = section.find_parent("div", class_="mb-16")
        if not parent:
            continue

        dishes = parent.select(".border-b")
        for dish in dishes:
            name_tag = dish.find("h4")
            price_tag = dish.find("span")
            desc_tag = dish.find("p")

            dish_name = clean_text(name_tag.get_text(strip=True)) if name_tag else None
            description = clean_text(desc_tag.get_text(strip=True)) if desc_tag else None
            price_text = clean_text(price_tag.get_text(strip=True)) if price_tag else None

            price = None
            if price_text:
                match = re.search(r"(\d+[.,]?\d*)", price_text)
                if match:
                    price = float(match.group(1).replace(",", "."))

            tags = []
            if description and ("vega" in description.lower() or "vegetarisch" in description.lower()):
                tags.append("vegetarian")
            tags_str = ", ".join(tags) if tags else None

            if dish_name and price is not None:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": category,
                    "dish": dish_name,
                    "price": price,
                    "description": description,
                    "tags": tags_str
                })

    return pd.DataFrame(menu_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# DOKJARD (DINNER)
# =========================
def scrape_dokjard_dinner():
    restaurant_name = "Dokjard"
    city_name = "Groningen"
    menu_type_default = "Dinner"

    url = "https://dokjard.nl/menu/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    menu_items = []

    section = soup.find("section", id="bistro-menu")
    if not section:
        return []

    articles = section.find_all("article", class_="menu-item")

    current_category = None

    for art in articles:
        classes = art.get("class", [])
        title_tag = art.find("h2", class_="entry-title")
        if not title_tag:
            continue

        title = clean_text(title_tag.get_text(strip=True))
        price_tag = art.find("span", class_="menu-price")
        price_text = clean_text(price_tag.get_text(strip=True)) if price_tag else ""
        desc_div = art.find("div", class_="entry-content")
        description = clean_text(desc_div.get_text(" ", strip=True)) if desc_div else None

        is_label = "tk_menu_item_label-kop" in classes
        is_empty_price = (not price_text)
        is_empty_description = (not description)

        if is_label or (is_empty_price and is_empty_description):
            current_category = title
            continue

        prices = []
        if price_text:
            for part in re.split(r"[\/]", price_text):
                part = part.strip()
                if part:
                    m = re.search(r"(\d+[.,]?\d*)", part)
                    if m:
                        prices.append(float(m.group(1).replace(",", ".")))

        tags = []
        desc_lower = (description or "").lower()
        if any(word in desc_lower for word in ["vega", "vegetarisch", "vegan", "veganistisch"]):
            tags.append("vegetarian")
        tags_str = ", ".join(tags) if tags else None

        if not prices:
            menu_items.append({
                "restaurant": restaurant_name,
                "city": city_name,
                "menu_type": menu_type_default,
                "category": current_category,
                "dish": title,
                "price": None,
                "description": description,
                "tags": tags_str
            })
        else:
            for p in prices:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": current_category,
                    "dish": title,
                    "price": p,
                    "description": description,
                    "tags": tags_str
                })

    return pd.DataFrame(menu_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# DE DRIE GEZUSTERS (LUNCH + DINNER)
# =========================
def scrape_drie_gezusters():
    restaurant_name = "De Drie Gezusters"
    city_name = "Groningen"
    headers = {"User-Agent": "Mozilla/5.0"}

    menus = [
        {"url": "https://www.dedriegezusters.nl/nl/menu/diner/voorgerechten/voorgerechten", "type": "dinner"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/diner/hoofdgerechten", "type": "dinner"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/diner/nagerechten", "type": "dinner"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/borrel", "type": "borrel"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/ontbijt/gebak", "type": "borrel"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/ontbijt/stadshap", "type": "borrel"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/lunch", "type": "lunch"}
    ]

    all_items = []

    for menu in menus:
        url = menu["url"]
        menu_type = menu["type"]

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        sections = soup.select("div.menu")
        for section in sections:
            title_tag = section.select_one(".menu--title h2")
            category = clean_text(title_tag.get_text(strip=True)) if title_tag else "Unknown"

            if "en natuurlijk ook" in category.lower():
                category = "borrel"

            items_blocks = section.select(".menu--item")
            for block in items_blocks:
                cols = block.select("div.col-md-6")
                for col in cols:
                    h5_tags = col.find_all("h5")
                    for h5 in h5_tags:
                        dish_name = clean_text(h5.get_text(" ", strip=True))
                        if not dish_name:
                            continue

                        desc_segments = []
                        sib = h5.next_sibling
                        while sib and (sib.name not in ["h5"]):
                            if hasattr(sib, "get_text"):
                                txt = clean_text(sib.get_text(" ", strip=True))
                                if txt:
                                    desc_segments.append(txt)
                            sib = sib.next_sibling

                        combined_text = " ".join(desc_segments).strip()
                        price_match = re.search(r"(\d+[.,]?\d*)", combined_text)
                        price = float(price_match.group(1).replace(",", ".")) if price_match else None
                        description = combined_text
                        if price_match:
                            description = description.replace(price_match.group(1), "").strip()

                        tags = []
                        if "vega" in description.lower() or "vegetarisch" in description.lower():
                            tags.append("vegetarian")
                        tags_str = ", ".join(tags) if tags else None

                        if price is not None:
                            all_items.append({
                                "restaurant": restaurant_name,
                                "city": city_name,
                                "menu_type": menu_type,
                                "category": category,
                                "dish": dish_name,
                                "price": price,
                                "description": description,
                                "tags": tags_str
                            })

    return pd.DataFrame(all_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# BRASSERIE FLAIR (DINNER)
# =========================
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

def scrape_brasserie_flair():
    restaurant_name = "Brasserie Flair"
    city_name = "Groningen"
    menu_type_default = "Dinner"
    
    url = "https://www.brasserieflair.nl/menukaart"
    resp = requests.get(url)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    section = soup.find("section", class_="sections minmargin content")
    p = section.find("p") if section else None
    
    if not p:
        return []

    raw_html = str(p)
    parts = re.split(r'<br\s*/?>', raw_html, flags=re.IGNORECASE)
    
    lines = []
    for part in parts:
        cleaned = BeautifulSoup(part, "html.parser").get_text(" ", strip=True)
        cleaned = re.sub(r'[<>*/•]', '', cleaned).strip()
        if cleaned and len(cleaned) > 1:
            lines.append(cleaned)
    
    price_pattern = re.compile(r'€?\s*\d+[,.]\d{2}')
    menu_items = []
    current_category = "General"
    i = 0
    
    while i < len(lines):
        line = clean_text(lines[i]).strip()
        
        if line.endswith(":") and not price_pattern.search(line):
            current_category = line[:-1].strip()
            i += 1
            continue
        
        if price_pattern.search(line):
            matches = list(price_pattern.finditer(line))
            last_match = matches[-1]
            
            dish_name = clean_text(line[:last_match.start()]).strip()
            price_text = line[last_match.start():].strip()
            
            price_match = re.search(r'(\d+)[,.](\d{2})', price_text)
            price_numeric = None
            if price_match:
                whole, decimal = price_match.groups()
                price_numeric = float(f"{whole}.{decimal}")
            
            description = ""
            if i + 1 < len(lines):
                next_line = clean_text(lines[i + 1]).strip()
                if (not price_pattern.search(next_line) and 
                    not next_line.endswith(":") and 
                    len(next_line) > 10):
                    description = next_line
                    i += 1
            
            tags = ""
            if "(V)" in dish_name or "vega" in description.lower() or "vegetarisch" in description.lower():
                tags = "vegetarian"
            
            if price_numeric:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": current_category,
                    "dish": dish_name,
                    "price": price_numeric,
                    "description": description,
                    "tags": tags
                })
        
        i += 1
    
    return pd.DataFrame(menu_items).drop_duplicates().to_dict(orient="records")


# =========================
# JAVAANS EETCAFE GRONINGEN (DINNER)
# =========================
def scrape_javaans_eetcafe():
    restaurant_name = "Javaans Eetcafe Groningen"
    city_name = "Groningen"
    menu_type_default = "Dinner"

    URL = "https://javaanseetcafegroningen.nl/menukaart/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    menu_items = []

    price_lists = soup.select("div.elementor-widget-price-list")

    for pl in price_lists:
        section = pl.find_previous("h2")
        category = clean_text(section.get_text(strip=True)) if section else "Unknown"

        items = pl.select("li")

        for item in items:
            title_tag = item.select_one(".elementor-price-list-title")
            dish_name = clean_text(title_tag.get_text(strip=True)) if title_tag else category

            price_tag = item.select_one(".elementor-price-list-price")
            price_numeric = None
            if price_tag:
                price_text = clean_text(price_tag.get_text(strip=True))
                price_text_clean = price_text.replace("prijs p.p.", "").replace("€", "").replace(",", ".").strip()
                try:
                    price_numeric = float(price_text_clean)
                except:
                    price_numeric = None

            desc_tag = item.select_one(".elementor-price-list-description")
            description = clean_text(desc_tag.get_text(strip=True)) if desc_tag else ""

            tags = ""
            if "vega" in (description.lower() + dish_name.lower()) or "vegetarisch" in description.lower():
                tags = "vegetarian"

            if price_numeric is not None:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": category,
                    "dish": dish_name,
                    "price": price_numeric,
                    "description": description,
                    "tags": tags
                })

    df = pd.DataFrame(menu_items)
    df = df[~df["category"].str.contains("woordenboek", case=False, na=False)]

    return df.drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# MAHALO (LUNCH)
# =========================
def scrape_mahalo():
    restaurant_name = "Mahalo"
    city_name = "Groningen"
    menu_type_default = "Lunch"

    URL = "https://mahalo.nu/menu/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    menu_items = []

    sections = soup.select("div.elementor-widget-price-list")

    for section in sections:
        section_title = section.find_previous("div", class_="elementor-widget-text-editor")
        category = clean_text(section_title.get_text(strip=True)) if section_title else "Unknown"

        items = section.select("li.elementor-price-list-item")

        for item in items:
            title_tag = item.select_one(".elementor-price-list-title")
            dish_name = clean_text(title_tag.get_text(strip=True)) if title_tag else category

            price_tag = item.select_one(".elementor-price-list-price")
            price_numeric = None
            if price_tag:
                try:
                    price_numeric = float(clean_text(price_tag.get_text(strip=True)).replace(",", "."))
                except:
                    price_numeric = None

            desc_tag = item.select_one(".elementor-price-list-description")
            description = clean_text(desc_tag.get_text(strip=True)) if desc_tag else ""

            tags = ""
            if "vega" in (description.lower() + dish_name.lower()) or "vegetarisch" in description.lower():
                tags = "vegetarian"

            if price_numeric is not None:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": category,
                    "dish": dish_name,
                    "price": price_numeric,
                    "description": description,
                    "tags": tags
                })

    return pd.DataFrame(menu_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# MR DAM BANH MI (LUNCH)
# =========================
def scrape_mr_dam_banh_mi():
    restaurant_name = "Mr. Dam Banh Mi"
    city_name = "Groningen"
    menu_type_default = "Lunch"

    URL = "http://mrdambanhmi.com/nl/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    menu_items = []

    menu_div = soup.find("div", id="menu")

    categories = menu_div.find_all("h3") if menu_div else []

    for cat in categories:
        category_name = clean_text(cat.get_text(strip=True))

        dl = cat.find_next("dl")
        if not dl:
            continue

        dts = dl.find_all("dt")
        dds = dl.find_all("dd")

        for dt, dd in zip(dts, dds):
            dish_name = clean_text(dt.get_text(strip=True))

            if not dish_name:
                continue

            price_tag = dd.find("strong")
            price_numeric = None

            if price_tag:
                price_text = clean_text(price_tag.get_text(strip=True))
                price_text_clean = price_text.replace("€", "").replace(",", ".").strip()
                price_text_clean = re.sub(r"[^\d\.]", "", price_text_clean)

                try:
                    price_numeric = float(price_text_clean)
                except:
                    price_numeric = None

            description = ""

            combined_text = dish_name.lower()
            tags = ""
            if any(word in combined_text for word in ["vega", "vegetarisch", "vegan"]):
                tags = "vegetarian"

            if price_numeric is not None:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": category_name,
                    "dish": dish_name,
                    "price": price_numeric,
                    "description": description,
                    "tags": tags
                })

    return pd.DataFrame(menu_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# UGLY DUCK (LUNCH + DINNER)
# =========================
def scrape_ugly_duck():
    restaurant_name = "Ugly Duck"
    city_name = "Groningen"
    headers = {"User-Agent": "Mozilla/5.0"}

    URL = "https://www.uglyduck.nl/menukaart/"
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    menu_items = []
    current_menu_type = None

    elements = soup.find_all(["h1", "h2", "div"])

    for el in elements:
        if el.name == "h1":
            text = clean_text(el.get_text(strip=True)).lower()
            if "lunch" in text:
                current_menu_type = "lunch"
            elif "diner" in text or "nagerechten" in text:
                current_menu_type = "dinner"

        if el.name == "h2":
            category = clean_text(el.get_text(strip=True))

            next_pl = el.find_next("div", class_="elementor-widget-price-list")
            if not next_pl:
                continue

            items = next_pl.select("li")

            for item in items:
                title_tag = item.select_one(".elementor-price-list-title")
                dish_name = clean_text(title_tag.get_text(strip=True)) if title_tag else category

                price_tag = item.select_one(".elementor-price-list-price")
                price_numeric = None

                if price_tag:
                    price_text = clean_text(price_tag.get_text(strip=True))
                    price_text_clean = price_text.lower()
                    price_text_clean = price_text_clean.replace("€", "").replace(",", ".")
                    price_text_clean = re.sub(r"[^\d\.]", "", price_text_clean)

                    try:
                        price_numeric = float(price_text_clean)
                    except:
                        price_numeric = None

                desc_tag = item.select_one(".elementor-price-list-description")
                description = clean_text(desc_tag.get_text(" ", strip=True)) if desc_tag else ""

                combined_text = (dish_name + " " + description).lower()
                tags = ""
                if any(word in combined_text for word in ["vega", "vegetarisch", "vegan", " v"]):
                    tags = "vegetarian"

                if price_numeric is not None and current_menu_type:
                    menu_items.append({
                        "restaurant": restaurant_name,
                        "city": city_name,
                        "menu_type": current_menu_type,
                        "category": category,
                        "dish": dish_name,
                        "price": price_numeric,
                        "description": description,
                        "tags": tags
                    })

    df = pd.DataFrame(menu_items)
    df = df.dropna(subset=["menu_type"])

    return df.drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# XO GRONINGEN (LUNCH)
# =========================
def scrape_xo_groningen_lunch():
    restaurant_name = "XO Groningen"
    city_name = "Groningen"
    menu_type = "Lunch"

    url = "https://xo-groningen.nl/menu/#lunch"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html_content = response.text

    soup = BeautifulSoup(html_content, "html.parser")

    all_items = []

    for section in soup.select("div.menu-list"):
        category_tag = section.select_one("h2.menu-list__title")
        if not category_tag:
            continue
        category = clean_text(category_tag.get_text(strip=True))
        
        for li in section.select("ul.menu-list__items > li.menu-list__item"):
            dish_tag = li.select_one("h4.menu-list__item-title")
            desc_tag = li.select_one("p.menu-list__item-desc span.desc__content")
            
            if not dish_tag:
                continue
            
            dish_text = clean_text(dish_tag.get_text(strip=True))
            description = clean_text(desc_tag.get_text(strip=True)) if desc_tag else ""
            
            price_match = re.search(r'€\s*\d+[,\.]?\d*', dish_text)
            if not price_match:
                price_span = li.select_one("span.menu-list__item-price")
                price = clean_text(price_span.get_text(strip=True)) if price_span else None
            else:
                price = price_match.group(0)
                dish_text = dish_text.replace(price, "").strip()
            
            veg_keywords = ["Vega", "vegetarisch", "geitenkaas"]
            tags = "Vegetarian" if any(k.lower() in dish_text.lower() or k.lower() in description.lower() for k in veg_keywords) else ""
            
            if price:
                all_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type,
                    "category": category,
                    "dish": dish_text,
                    "price": price,
                    "description": description,
                    "tags": tags
                })

    return pd.DataFrame(all_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")
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
    print("Fier Groningen:", len(scrape_fier_groningen_dinner()))
    print("Dokjard:", len(scrape_dokjard_dinner()))
    print("Drie Gezusters:", len(scrape_drie_gezusters()))
    print("Brasserie Flair:", len(scrape_brasserie_flair()))
    print("Javaans Eetcafe:", len(scrape_javaans_eetcafe()))
    print("Mahalo:", len(scrape_mahalo()))
    print("Mr Dam Banh Mi:", len(scrape_mr_dam_banh_mi()))
    print("Ugly Duck:", len(scrape_ugly_duck()))
    print("XO Groningen:", len(scrape_xo_groningen_lunch()))

    all_data.extend(scrape_jack_and_jackys())
    all_data.extend(scrape_roast_lunch())
    all_data.extend(scrape_roast_dinner())
    all_data.extend(scrape_baylings())
    all_data.extend(scrape_dikke_van_dale_lunch())
    all_data.extend(scrape_dikke_van_dale_dinner())
    all_data.extend(scrape_fier_groningen_dinner())
    all_data.extend(scrape_dokjard_dinner())
    all_data.extend(scrape_drie_gezusters())
    all_data.extend(scrape_brasserie_flair())
    all_data.extend(scrape_javaans_eetcafe())
    all_data.extend(scrape_mahalo())
    all_data.extend(scrape_mr_dam_banh_mi())
    all_data.extend(scrape_ugly_duck())
    all_data.extend(scrape_xo_groningen_lunch())

    return pd.DataFrame(all_data)

# running file manually
if __name__ == "__main__":
    df = scrape_all_menus()
    print(df.head())

df = scrape_all_menus()

df.to_csv("data/menus_raw.csv", index=False, encoding="utf-8-sig")

print("Saved raw dataset")