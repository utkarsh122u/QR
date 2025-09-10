import json
import streamlit as st
import uuid
from PIL import Image
import requests
from io import BytesIO
from supabase import create_client, Client
import pandas as pd

# Supabase credentials
SUPABASE_URL = "https://ekgpqzdeulclmzilaqlr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVrZ3BxemRldWxjbG16aWxhcWxyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI3MzgxMTAsImV4cCI6MjA1ODMxNDExMH0.mU8kMXXLYIdb2t5GSzh3EPvj5Uioa4Yj-m0FROSuptY"
@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# Streamlit config
st.set_page_config(page_title="Menu", page_icon="logo.jpg", layout="wide", initial_sidebar_state="expanded")

# Get seat_id from query parameters
seat_id = st.query_params.get("seat_id")
if isinstance(seat_id, list):
    seat_id = seat_id[0]

if not seat_id:
    st.error("❌ Seat ID missing in URL. Please scan your QR.")
    st.stop()

# Validate seat_id in Supabase
seat_check = supabase.table("seats").select("seat_id").eq("seat_id", seat_id).execute()
if len(seat_check.data) == 0:
    st.error("❌ Invalid seat ID. Access denied.")
    st.stop()
menu_tab,rate_us = st.tabs(['📋 Menu', '⭐ Rate Us'])
# Page Title
with menu_tab:
    st.success(f"🪑 Ordering from: **{seat_id}**")

    # Fetch available menu items
    @st.cache_data
    def fetch_menu():
        return supabase.table("menu").select("*").eq("available", True).execute().data or []

    menu = fetch_menu()
    if not menu:
        st.warning("⚠️ No menu items available today.")
        st.stop()

    # State dictionary for selections
    if "order_data" not in st.session_state:
        st.session_state.order_data = {}

    @st.cache_data(show_spinner=False)
    def load_image_from_url(url: str):
        try:
            resp = requests.get(url, timeout=5)
            return resp.content  # return raw image bytes
        except:
            return None

    # Search Bar
    st.markdown("<h5><b>📋Menu</b></h5>", unsafe_allow_html=True)

    search_query = st.text_input("🔍 Search for a dish", placeholder="search any dish")
    # Filter items by search
    def filter_items(query, items):
        return [item for item in items if query.lower() in item["item"].lower()]

    display_menu = filter_items(search_query, menu) if search_query.strip() else menu

    if search_query.strip() and not display_menu:
        st.error("Dish Not Found !", icon='😔')

    ch = []
    for item in display_menu:
        with st.expander(f"{item['item']}  - ₹{item['price']}", expanded=True):
            cols = st.columns([1, 2])
            with cols[0]:
                if item["image_url"]:
                    try:
                        img_data = load_image_from_url(item["image_url"])
                        image = Image.open(BytesIO(img_data))
                        st.image(image, use_container_width=True)  # Image fits well
                    except:
                        st.warning("⚠️ Failed to load image.")
                else:
                    st.info("No image available.")

                dd = json.loads(item.get("dish_type", "[]"))
                if len(dd) > 0:
                    choice = st.pills(options=dd, label="Available In", key=f"{item['item']+str(item['price'])}_", selection_mode="single")

                    if choice:
                        ch.append(choice)

            with cols[1]:
                st.markdown(f"<b><h4 id={item['item'].lower().replace(" ", "-")}>{str(item['item']).upper()}</h4></b>", unsafe_allow_html=True)
                st.markdown(f"<b>[💵] Price: ₹{item['price']}</b>", unsafe_allow_html=True)
                st.text(f"[📜] Menu:\n{item['description']+'\n' or 'No description provided'}")
                item_name = item["item"]
                if item_name not in st.session_state.order_data:
                    st.session_state.order_data[item_name] = {
                        "item": item_name,
                        "quantity": 1,
                        "price": item["price"],
                        "selected": False
                    }
                # 🔁 Get existing values
                prev_data = st.session_state.order_data[item_name]
                qty = st.number_input(
                    f"Quantity for {item['item']}",
                    min_value=1,
                    max_value=50,
                    value=1,
                    key=f"qty_{item['item']}"
                )
                selected = st.checkbox("Select", value=prev_data["selected"], key=f"select_{item['item']}")

                st.session_state.order_data[item_name]["selected"] = selected
                st.session_state.order_data[item_name]["quantity"] = qty

                # Store item details in session state
                st.session_state.order_data[item['item']] = {
                    "item": item["item"],
                    "quantity": qty,
                    "price": item["price"],
                    "selected": selected
                }

                # If item is selected, add to Supabase cart
                if selected:
                    data = {
                        "item_name": item["item"],
                        "quantity": qty,
                        "price": item["price"]
                    }
                    response = supabase.table("cart").upsert([data]).execute()
                    if response:
                        st.success(f"✅ {item['item']} added to cart!")
                else:
                    # Remove from cart if unchecked
                    supabase.table("cart").delete().eq("item_name", item["item"]).execute()
    # 💡 Sidebar Cart Preview
    with st.sidebar:
        st.subheader("🛒 Your Cart")

        cart_empty = True
        total_items = 0
        with st.container(border=10):
            for item_id, data in st.session_state.order_data.items():
                if data.get("selected", False):
                    item_name = data.get("item", "Unknown")
                    qty = data.get("quantity", 1)
                    total_items += qty
                    st.markdown(f"• **{item_name}** x {qty}")
                    cart_empty = False

            else:
                def total_item():
                    return sum(
                        1 for item in st.session_state.order_data.values() if item["selected"]
                    )
                total_items = total_item()

                total_price = sum(
                    item["price"] * item["quantity"]
                    for item in st.session_state.order_data.values()
                    if item["selected"]
                )

                if total_items > 0:
                    with st.container(border=10):
                        st.info(f"⭐ Total items: {total_items}")
                        st.info(f"💵 Total price: ₹{total_price}")
                else:
                    st.info("🛒 No items selected yet.")


        if not cart_empty:
            if st.button("🧹 Clear Cart"):
                for item_id in list(st.session_state.order_data.keys()):
                    st.session_state.order_data[item_id]["selected"] = False
                    st.session_state.order_data[item_id]["quantity"] = 1
                st.rerun()

        if st.button("✅ Place Order"):
            selected_items = [
                {
                    "item": data["item"],
                    "quantity": data["quantity"]
                }
                for item_id, data in st.session_state.order_data.items()
                if data["selected"]
            ]

            if not selected_items:
                st.warning("⚠️ Select at least one item to place an order.")
            else:
                order_id = str(uuid.uuid4())
                supabase.table("orders").insert({
                    "order_id": order_id,
                    "seat_id": seat_id,
                    "items": selected_items,
                }).execute()
                st.success(f"🎉 Order placed successfully! Your token: `{order_id[:8]}`")
                st.balloons()
                st.session_state.order_data.clear()
with rate_us:
    with st.form(key='rating', border=3, enter_to_submit=True):
        st.markdown("<b><h4>⭐ Rate Us !</h4></b>", unsafe_allow_html=True)
        name = st.text_input("Name", placeholder="Enter your name")
        email = st.text_input("Email", placeholder="Enter your email")
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            food_rating = st.slider("Food 🍲", 1, 5, 3)
        with col2:
            service_rating = st.slider("Service 🧑‍🍳", 1, 5, 3)
        with col3:
            ambience_rating = st.slider("Ambience 🎶", 1, 5, 3)
        st.markdown("---")
        best_things = st.multiselect("What did you like the most? 💖", [
            "Tasty Food", "Quick Service", "Friendly Staff", "Ambience", "Cleanliness"
        ])
        additional_feedback = st.text_area("Any suggestions or comments? ✍️", placeholder="So how was it all?")

        if st.form_submit_button(label="Submit", icon="👍", type='secondary'):
            try:
                dataS = {
                    'Name':name,
                    'Email':email,
                    'food':food_rating,
                    'service':service_rating,
                    'ambience':ambience_rating,
                    'most_liked':', '.join(best_things),
                    'feedback':additional_feedback
                }
                supabase.table("feedback").insert(dataS).execute()
                st.info('Thank You ❤️')
            except Exception as e:

                print(e)
