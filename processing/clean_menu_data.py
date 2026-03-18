import pandas as pd

from scraper.scrape_menus import scrape_all_menus


def clean_text(text):
    if pd.isna(text) or text is None:
        return None

    text = str(text)

    replacements = {
        "\xa0": " ",
        "Ã¨": "è",
        "Ã©": "é",
        "Ãª": "ê",
        "Ã«": "ë",
        "Ã¡": "á",
        "Ã ": "à",
        "Ã§": "ç",
        "Ã¶": "ö",
        "Ã¼": "ü",
        "Ã®": "î",
        "Ã¯": "ï",
        "Ã´": "ô",
        "Ã»": "û",
        "â": "–",
        "â": "—",
        "â": "’",
        "â": "‘",
        "â€œ": '"',
        "â€": '"',
        "Â ": "",
        "&nbsp;": " ",
    }

    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    text = " ".join(text.split()).strip()

    return text if text else None


def clean_price(price):
    if pd.isna(price) or price is None:
        return None

    price = str(price).strip().lower()

    replacements = {
        "€": "",
        ",": ".",
        "p.p.": "",
        "ps": "",
        "p.s.": "",
        "vanaf": "",
    }

    for wrong, right in replacements.items():
        price = price.replace(wrong, right)

    price = " ".join(price.split()).strip()

    import re
    match = re.search(r"\d+(\.\d+)?", price)
    if not match:
        return None

    try:
        return float(match.group())
    except ValueError:
        return None


def standardize_menu_type(menu_type):
    if pd.isna(menu_type) or menu_type is None:
        return None

    text = clean_text(menu_type).lower()

    mapping = {
        "lunch": "Lunch",
        "dinner": "Dinner",
        "dessert": "Dessert",
        "desserts": "Dessert",
    }

    return mapping.get(text, clean_text(menu_type).title())


def standardize_category(category, menu_type):
    if pd.isna(category) or category is None:
        return None

    category = clean_text(category)
    menu_type = standardize_menu_type(menu_type)

    lunch_map = {
        "bowls": "Bowls",
        "pancakes": "Pancakes",
        "sandwiches": "Sandwiches",
        "salads": "Salads",
        "bakery": "Bakery",
        "kids food": "Kids Food",
        "soepen": "Soup",
        "soup": "Soup",
        "tosti's": "Toasties",
        "tostis": "Toasties",
        "koude broodjes": "Cold Sandwiches",
        "warme broodjes": "Hot Sandwiches",
        "eiergerechten": "Egg Dishes",
        "twaalfuurtjes": "Lunch Specials",
        "plates": "Plates",
        "broodjes": "Sandwiches",
        "wraps": "Wraps",
        "classics": "Classics",
        "salade": "Salads",
        "salades": "Salads",
        "maaltijdsalade": "Salads",
        "zuurdesem brood": "Sandwiches",
        "croissant bun": "Sandwiches",
        "roast eggs": "Egg Dishes",
        "burgers & buns": "Burgers",
        "burgers and buns": "Burgers",
        "lunchplank": "Lunch Specials",
    }

    dinner_map = {
        "soepen": "Soup",
        "soup": "Soup",
        "salades": "Salads",
        "salade": "Salads",
        "voorgerechten": "Starters",
        "starters": "Starters",
        "starters to share": "Starters",
        "aperitivo": "Starters",
        "primi": "Starters",
        "bijgerechten": "Sides",
        "side dishes": "Sides",
        "hoofdgerechten": "Main",
        "main": "Main",
        "secondi": "Main",
        "pizza": "Pizza",
        "pasta": "Pasta",
        "dessert": "Dessert",
        "desserts": "Dessert",
        "dolci": "Dessert",
        "kindergerechten": "Kids",
        "kids food": "Kids",
        "kids drinks": "Kids",
        "vlees": "Main",
        "vis": "Main",
        "vega": "Main",
        "vegetarisch": "Main",
        "broiler": "Main",
        "bar bites en aperitieven": "Starters",
        "voor ieder wat wils - koude gerechten": "Starters",
        "voor ieder wat wils - warme gerechten": "Main",
        "voor ieder wat wils - desserts": "Dessert",
    }

    key = category.lower()

    if menu_type == "Lunch":
        return lunch_map.get(key, category.title())

    if menu_type == "Dinner":
        return dinner_map.get(key, category.title())

    if menu_type == "Dessert":
        return "Dessert"

    return category.title()


def detect_tags(dish, description, existing_tags=None):
    text = f"{dish or ''} {description or ''}".lower()

    tags = set()

    if existing_tags and not pd.isna(existing_tags):
        for tag in str(existing_tags).split(","):
            tag = tag.strip().lower()
            if tag:
                tags.add(tag)

    vegan_keywords = {
        "vegan", "plant-based", "plantaardig", "veganistisch"
    }

    vegetarian_keywords = {
        "vegetarian", "vegetarisch", "mozzarella", "burrata", "brie",
        "goat cheese", "geitenkaas", "parmezaan", "parmesan", "gorgonzola",
        "cheddar", "kaas", "egg", "ei", "mascarpone", "yoghurt", "room",
        "crème fraîche", "ricotta", "feta", "halloumi", "burrata",
        "mozzarella", "fontina", "pecorino", "grana padano"
    }

    meat_keywords = {
        "chicken", "kip", "beef", "rund", "runder", "carpaccio", "steak",
        "biefstuk", "burger", "ham", "serranoham", "prosciutto", "salami",
        "spek", "bacon", "pork", "varkens", "rib", "spareribs", "saté",
        "duck", "eend", "lamb", "lam", "pastrami", "kebab", "mortadella",
        "nduja", "worst", "sausage", "ossenhaas", "stoofpot", "rendang",
        "buikspek", "rib-eye", "ribeye", "varkenshaas", "lamshaas",
        "gehakt", "frikandel", "kroket", "bitterbal"
    }

    fish_keywords = {
        "fish", "vis", "salmon", "zalm", "tuna", "tonijn", "shrimp", "gamba",
        "prawn", "cod", "kabeljauw", "sea bass", "zeebaars", "makreel",
        "mackerel", "herring", "haring", "oyster", "oester", "halibut",
        "heilbot", "sardine", "ansjovis", "anchovy", "scallop", "coquille",
        "sashimi", "tataki", "mussels", "mosselen", "garnalen", "garnaal",
        "schelvis", "zalmfilet", "tonijntartaar", "makreelsalade"
    }

    spicy_keywords = {
        "spicy", "pikant", "pittig", "chili", "chilli", "jalapeño",
        "jalapeno", "sriracha", "hot honey", "gochujang", "piccante",
        "nduja", "sambal", "rode peper", "peper", "kimchi", "wasabi"
    }

    if any(word in text for word in vegan_keywords):
        tags.add("vegan")

    if any(word in text for word in fish_keywords):
        tags.add("fish")

    if any(word in text for word in meat_keywords):
        tags.add("meat")

    if any(word in text for word in spicy_keywords):
        tags.add("spicy")

    if "vegan" not in tags and "fish" not in tags and "meat" not in tags:
        if any(word in text for word in vegetarian_keywords):
            tags.add("vegetarian")

    return ", ".join(sorted(tags)) if tags else None


def clean_menu_data(df):
    df = df.copy()

    expected_columns = [
        "restaurant",
        "city",
        "menu_type",
        "category",
        "dish",
        "price",
        "description",
        "tags",
    ]

    for col in expected_columns:
        if col not in df.columns:
            df[col] = None

    # text cleaning
    for col in ["restaurant", "city", "menu_type", "category", "dish", "description", "tags"]:
        df[col] = df[col].apply(clean_text)

    # price cleaning
    df["price"] = df["price"].apply(clean_price)

    # menu type cleaning
    df["menu_type"] = df["menu_type"].apply(standardize_menu_type)

    # category cleaning
    df["category"] = df.apply(
        lambda row: standardize_category(row["category"], row["menu_type"]),
        axis=1
    )

    # auto tags
    df["tags"] = df.apply(
        lambda row: detect_tags(row["dish"], row["description"], row["tags"]),
        axis=1
    )

    # remove rows without dish names
    df = df[df["dish"].notna()].copy()

    # remove duplicates
    df = df.drop_duplicates(
        subset=["restaurant", "city", "menu_type", "category", "dish", "price"]
    ).reset_index(drop=True)

    return df


def main():
    raw_df = scrape_all_menus()
    clean_df = clean_menu_data(raw_df)

    print("Raw rows:", len(raw_df))
    print("Clean rows:", len(clean_df))
    print(clean_df.head(20))

    clean_df.to_csv("data/menus_cleaned.csv", index=False)
    print("\nSaved cleaned dataset to: data/menus_cleaned.csv")


if __name__ == "__main__":
    main()