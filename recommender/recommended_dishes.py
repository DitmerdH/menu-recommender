import pandas as pd

df = pd.read_csv("data/menus_cleaned.csv")

def recommend_dishes(df, max_price=None, keyword=None, dietary=None, menu_type=None, city=None):

    results = df.copy()

    # price filter
    if max_price is not None:
        results = results[results["price"] <= max_price]

    # menu type filter
    if menu_type:
        results = results[results["menu_type"].str.lower() == menu_type.lower()]

    # dietary filter
    if dietary:
        results = results[results["tags"].str.contains(dietary, na=False)]

    # keyword filter
    if keyword:
        keyword = keyword.lower()
        results = results[
            results["dish"].str.contains(keyword, na=False) |
            results["description"].str.contains(keyword, na=False)
        ]

    # city filter
    if city:
        df = df[df["city"].str.lower() == city.lower()]

    return results.sort_values(by="price")