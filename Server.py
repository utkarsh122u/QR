import json
from datetime import datetime
import pytz
import streamlit as st
from supabase import create_client, Client
import uuid
st.set_page_config(page_icon="🍽️", page_title="Admin Control")

# Initialize Supabase client
SUPABASE_URL = "https://ekgpqzdeulclmzilaqlr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVrZ3BxemRldWxjbG16aWxhcWxyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI3MzgxMTAsImV4cCI6MjA1ODMxNDExMH0.mU8kMXXLYIdb2t5GSzh3EPvj5Uioa4Yj-m0FROSuptY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.markdown("### 🍽️ Cook/Admin Panel")
# Tabs
menu_tab, seats_tab, orders_tab = st.tabs(["Menu Management", "Seat Management", "Live Orders"])

# Menu Management
with menu_tab:
    st.markdown("<div><h5><b>📋 Add New Dish</b></h5></div>", unsafe_allow_html=True)
    with st.form("add_menu_form"):
        new_item = st.text_input("Dish Name", placeholder="Dosa, Mattar Paneer, etc...")
        new_price = st.number_input("Price", min_value=10.0, max_value=10000.00)
        new_status = st.selectbox("Availability", ["Available", "Not Available"])
        new_type = st.multiselect("Dish Type", ["🍞 Normie ", "🌶️ Spicy", "🍬 Sweet", "🍋 Sour", "🍫 Bitter", "🧂 Salty", "🍖 Umami"], key=f"{new_item}_{new_price*100}", placeholder="🍋 Sour")
        new_desc = st.text_area("Description", placeholder="Cheezy + Veg Mix")
        uploaded_image = st.file_uploader("Dish Image", type=["jpg", "png"])
        submit_menu = st.form_submit_button("Add Dish")

        if submit_menu and new_item and uploaded_image:
            image_filename = f"{uuid.uuid4().hex}_{uploaded_image.name}"
            file_path = f"{image_filename}"
            supabase.storage.from_("dish-image").upload(file_path, uploaded_image.getvalue())
            image_url = supabase.storage.from_("dish-image").get_public_url(file_path)

            data = {
                "item": new_item,
                "price": new_price,
                "available": 1 if new_status == "Available" else 0,
                "description": new_desc,
                "image_url": image_url,
                "dish_type": new_type
            }
            supabase.table("menu").insert(data).execute()
            st.success("Dish added successfully!")

    st.markdown("<div><h5><b>📃 Current Menu</b></h5></div>", unsafe_allow_html=True)
    menu = supabase.table("menu").select("*").execute().data
    for dish in menu:
        with st.expander(f"Edit {dish['item']}", expanded=False):
            new_name = st.text_input("Dish Name", value=dish['item'], key=f"name_{dish['item']}")
            new_price = st.number_input("Price", min_value=0.0, value=float(dish['price']), format="%.2f", key=f"price_{dish['item']}")
            new_desc = st.text_area("Description", placeholder="Wanna Update ?", value=dish['description'], key=f"desc_{dish['item']}")
            new_status = st.selectbox("Availability", ["Available", "Not Available"], index=0 if dish['available'] else 1, key=f"status_{dish['item']}")
            updated_image = st.file_uploader("Update Dish Image", type=["jpg", "png"], key=f"image_{dish['item']}")
            up_type = st.multiselect("Dish Type", ["🍞 Normie ", "🌶️ Spicy", "🍬 Sweet", "🍋 Sour", "🍫 Bitter", "🧂 Salty", "🍖 Umami"], key=f"{new_desc}_{new_type}", placeholder="🍋 Sour")

            con = st.container()
            c1,c2 = st.columns([1,1])
            with con:
                with c1:
                    if st.button("💾 Save Changes", key=f"save_{dish['item']}"):
                        image_url = dish['image_url']
                        if updated_image:
                            new_filename = f"{uuid.uuid4().hex}_{updated_image.name}"
                            supabase.storage.from_("dish-image").upload(new_filename, updated_image.getvalue())
                            image_url = supabase.storage.from_("dish-image").get_public_url(new_filename)

                        update_data = {
                            "item": new_name,
                            "price": new_price,
                            "description": new_desc,
                            "available": 1 if new_status == "Available" else 0,
                            "image_url": image_url,
                            "dish_type": up_type
                        }
                        supabase.table("menu").update(update_data).eq("item", dish['item']).execute()
                        st.success(f"{new_name} updated successfully!")
                with c2:
                    if st.button("🗑️ Delete Dish", key=f"delete_{dish['item']}"):
                        supabase.table("menu").delete().eq("item", dish['item']).execute()
                        st.warning(f"{dish['item']} deleted successfully!")
                        st.rerun()

            st.image(dish['image_url'], width=150)
            st.markdown("---")

# Seat Management
with seats_tab:
    st.markdown("<div><h5><b>💺 Seat Management</div></h5></b>", unsafe_allow_html=True)
    with st.form("add_seat_form"):
        new_seat = st.text_input("New Seat ID (e.g., A1, B2)", placeholder='Seat1')
        submit_seat = st.form_submit_button("Add Seat")

        if submit_seat and new_seat:
            supabase.table("seats").insert({"seat_id": new_seat}).execute()
            st.success(f"Seat {new_seat} added.")

    st.markdown("<div><h5><b>🪑Existing Seats</div></h5></b>", unsafe_allow_html=True)
    seats = supabase.table("seats").select("*").execute().data
    if seats:
        with st.container(border=40):
            for seat in seats:
                col1, col2 = st.columns([1, 1], vertical_alignment="center")
                col1.write(f"<div><b><h6>》 Seat: {seat['seat_id']}</h6></b></div>", unsafe_allow_html=True)
                if col2.button("🗑️", key=f"delete_seat_{seat['seat_id']}"):
                    supabase.table("seats").delete().eq("seat_id", seat['seat_id']).execute()
                    st.rerun()
    else:
        st.info("No seats added yet.")

    if st.button("Delete All Seats", icon="❌"):
        supabase.table("seats").delete().neq("seat_id", "").execute()
        st.warning("All seats deleted.")

def format_orders(order_data):
    try:
        # Parse the JSON string if it's not already a list
        if isinstance(order_data, str):
            order_data = json.loads(order_data)

        # Convert list to readable format
        formatted_order = "\n".join([f"🍽️ {item['item']} - {item['quantity']}x" for item in order_data])

        return formatted_order

    except Exception as e:
        return f"Error formatting order: {e}"

# Live Orders
with orders_tab:
    col11,col22 = st.columns([2,1], vertical_alignment="center")
    with col11:
        st.markdown("<div><h5><b>📦 Live Orders</div></h5></b>", unsafe_allow_html=True)
        response = supabase.table("orders").select("*").order("timestamp", desc=True).execute()
        orders = response.data
    with col22:
        if st.button("↻  Refresh"):
            st.rerun()

    if not orders:
        st.info("No current orders.")
    else:
        def format_time(time_str):
            # Parse the ISO time and treat it as UTC
            utc_dt = datetime.fromisoformat(time_str).replace(tzinfo=pytz.utc)

            # Convert to IST
            ist = pytz.timezone('Asia/Kolkata')
            ist_dt = utc_dt.astimezone(ist)

            return ist_dt.strftime("🕒 Time: %B %d, %Y — %I:%M %p")

        for order in orders:
            with st.container(border=10):
                st.markdown(f"🧾 Order #{order['order_id']}")
                st.markdown(f"<b>🪑 Seat: {order['seat_id']}</b>", unsafe_allow_html=True)
                st.text(f"📋 Items:\n{format_orders(order['items'])}")
                st.markdown(f"{format_time(order['timestamp'])}")
                if order['status'] != "Done":
                    if st.button(f"Mark Done - Order #{order['order_id']}", key=f"done_{order['order_id']}"):
                        supabase.table("orders").update({"status": "Done"}).eq("order_id", order['order_id']).execute()
                        st.success("Order marked as done!")
                        st.rerun()
    st.markdown('---')

    if st.button("❌ Delete All Orders"):
        dummy_uuid = "00000000-0000-0000-0000-000000000000"
        supabase.table("orders").delete().neq("order_id", dummy_uuid).execute()
        st.rerun()