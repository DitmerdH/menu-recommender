import pandas as pd
import streamlit as st

st.set_page_config(page_title="Menu Recommender", layout="wide")
st.title("Menu Recommender")
st.write("Find dishes based on your preferences.")

try:
    from recommender.recommended_dishes import recommend_dishes
except Exception as e:
    st.error(f"Import error: {e}")
    st.stop()

@st.cache_data
def load_data():
    return pd.read_csv("data/menus_cleaned.csv")

try:
    df = load_data()
    st.success("Dataset loaded successfully.")
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    max_price = st.number_input("Maximum price", min_value=0.0, value=20.0, step=0.5)

with col2:
    dietary = st.selectbox(
        "Dietary preference",
        ["", "vegetarian", "vegan", "meat", "fish", "spicy"]
    )

with col3:
    menu_type = st.selectbox(
        "Menu type",
        ["", "Lunch", "Dinner", "Dessert"]
    )

with col4:
    city = st.selectbox(
        "City",
        ["", "Leeuwarden", "Groningen"]
    )

with col5:
    keyword = st.text_input("Keyword", placeholder="e.g. pasta, burger")
    

if st.button("Get recommendations"):
    try:
        results = recommend_dishes(
            df,
            max_price=max_price if max_price > 0 else None,
            keyword=keyword if keyword else None,
            dietary=dietary if dietary else None,
            menu_type=menu_type if menu_type else None
        )

        if results.empty:
            st.warning("No matching dishes found.")
        else:
            st.success(f"Found {len(results)} matching dishes.")
            st.dataframe(results, use_container_width=True)
    except Exception as e:
        st.error(f"Recommendation error: {e}")