import streamlit as st
import base64
import requests
from decouple import config
from datetime import datetime
import uuid
import mysql.connector

# ==== Database Functions ====

def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=config("DB_HOST"),
            user=config("DB_USER"),
            password=config("DB_PASSWORD"),
            database=config("DB_NAME")
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None

def create_user(email, password):
    """Creates a new user in the database."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Check if user already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return False, "User with this email already exists."

            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            conn.commit()
            return True, "User registered successfully!"
        except mysql.connector.Error as err:
            st.error(f"Error creating user: {err}")
            return False, f"Error registering user: {err}"
        finally:
            cursor.close()
            conn.close()
    return False, "Database connection failed."

def verify_user(email, password):
    """Verifies user credentials against the database."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            return user is not None
        except mysql.connector.Error as err:
            st.error(f"Error verifying user: {err}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def save_order(user_email, cart_items, total_amount, personalization_data=None, checkout_request_id=None):
    """Saves an order and its items to the database."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            order_id = str(uuid.uuid4())
            order_date = datetime.now()
            status = "Pending Payment Confirmation" # Initial status for orders awaiting payment

            # Save order details
            cursor.execute(
                "INSERT INTO orders (order_id, user_email, order_date, total_amount, status, personalization_name, personalization_phone, personalization_message, checkout_request_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (order_id, user_email, order_date, total_amount, status,
                 personalization_data.get('name') if personalization_data else None,
                 personalization_data.get('phone') if personalization_data else None,
                 personalization_data.get('message') if personalization_data else None,
                 checkout_request_id) # Add checkout_request_id here
            )

            # Save order items
            for item in cart_items:
                cursor.execute(
                    "INSERT INTO order_items (order_id, meal_id, meal_name, quantity, price_per_item) VALUES (%s, %s, %s, %s, %s)",
                    (order_id, item['id'], item['name'], item['quantity'], item['price'])
                )
            conn.commit()
            return True, order_id
        except mysql.connector.Error as err:
            st.error(f"Error saving order: {err}")
            conn.rollback()
            return False, f"Error saving order: {err}"
        finally:
            cursor.close()
            conn.close()
    return False, "Database connection failed."

def get_user_orders(user_email):
    """Retrieves all orders for a given user from the database."""
    conn = get_db_connection()
    orders = []
    if conn:
        cursor = conn.cursor(dictionary=True) # Return rows as dictionaries
        try:
            cursor.execute("SELECT * FROM orders WHERE user_email = %s ORDER BY order_date DESC", (user_email,))
            orders = cursor.fetchall()
        except mysql.connector.Error as err:
            st.error(f"Error fetching user orders: {err}")
        finally:
            cursor.close()
            conn.close()
    return orders

def get_order_details(order_id):
    """Retrieves details for a specific order and its items."""
    conn = get_db_connection()
    order = None
    items = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
            order = cursor.fetchone()
            if order:
                cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
                items = cursor.fetchall()
        except mysql.connector.Error as err:
            st.error(f"Error fetching order details: {err}")
        finally:
            cursor.close()
            conn.close()
    return order, items

def update_order_status(order_id, new_status):
    """Updates the status of an order in the database."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            st.error(f"Error updating order status: {err}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    return False

# ==== Helper Functions (M-Pesa) ====

def get_access_token(consumer_key, consumer_secret):
    """Fetches the M-Pesa API access token."""
    auth_string = f"{consumer_key}:{consumer_secret}"
    encoded = base64.b64encode(auth_string.encode()).decode()

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate"
    headers = {"Authorization": f"Basic {encoded}"}
    params = {"grant_type": "client_credentials"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting access token: {e}")
        return None

def lipa_na_mpesa_online(phone_number, amount, account_reference, transaction_desc):
    """Initiates an M-Pesa STK Push transaction."""
    access_token = get_access_token(
        config("CONSUMER_KEY"), config("CONSUMER_SECRET")
    )
    if not access_token:
        return {"error": "Failed to get access token"}

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    business_shortcode = config("BUSINESS_SHORTCODE")
    passkey = config("PASSKEY") # This is the raw passkey, not encoded yet
    data_to_encode = business_shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()

    payload = {
        "BusinessShortCode": business_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": business_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": config("CALLBACK_URL"),
        "AccountReference": account_reference, # Use order_id for reference
        "TransactionDesc": transaction_desc
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error during M-Pesa STK Push: {e}")
        return {"error": f"Network or API error: {e}"}

# ==== Streamlit App Logic ====

st.set_page_config(page_title="Hotel Kitchen", layout="wide")

# Session states initialization
if "cart" not in st.session_state:
    st.session_state.cart = []
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False
if "show_personalize_page" not in st.session_state:
    st.session_state.show_personalize_page = False
if "show_order_history" not in st.session_state:
    st.session_state.show_order_history = False
if "show_track_order" not in st.session_state:
    st.session_state.show_track_order = False
if "current_order_id" not in st.session_state:
    st.session_state.current_order_id = None # To store the ID of the last placed order
if "personalization_details" not in st.session_state:
    st.session_state.personalization_details = {} # To store personalization details


# Sidebar
with st.sidebar:
    st.markdown("🌐 **Choose Language**")
    selected_language = st.selectbox(
        "Select Language",
        ["English", "Chinese", "Kiswahili", "French"],
        index=0,
        key="selected_language"
    )
    st.markdown("---")

# ==== Translations ====
translations = {
    "welcome_title": {
        "English": "🍽️ Welcome to Edgewood",
        "Chinese": "🍽️ 欢迎来到 Edgewood",
        "Kiswahili": "🍽️ Karibu Edgewood",
        "French": "🍽️ Bienvenue à Edgewood"
    },
    "select_meal_subheader": {
        "English": "🍲 Select Your Meal(s)",
        "Chinese": "🍲 选择你的餐点",
        "Kiswahili": "🍲 Chagua Chakula Chako",
        "French": "🍲 Sélectionnez votre repas"
    },
    "personalize_button": {
        "English": "🍴 Personalize Your Meal",
        "Chinese": "🍴 个性化你的餐点",
        "Kiswahili": "🍴 Binafsisha Chakula Chako",
        "French": "🍴 Personnalisez votre repas"
    },
    "track_order_button": {
        "English": "📍 Track My Order",
        "Chinese": "📍 追踪我的订单",
        "Kiswahili": "📍 Fuatilia Agizo Langu",
        "French": "📍 Suivre ma commande"
    },
    "view_history_button": {
        "English": "📖 View Order History",
        "Chinese": "📖 查看订单历史",
        "Kiswahili": "📖 Tazama Historia ya Agizo",
        "French": "📖 Afficher l'historique des commandes"
    },
    "no_order_found": {
        "English": "No order found to track!",
        "Chinese": "没有找到可追踪的订单！",
        "Kiswahili": "Hakuna agizo lililopatikana la kufuatilia!",
        "French": "Aucune commande trouvée à suivre !"
    },
    "admin_mode_checkbox": {
        "English": "🔐 Admin Mode",
        "Chinese": "🔐 管理员模式",
        "Kiswahili": "🔐 Hali ya Usimamizi",
        "French": "🔐 Mode administrateur"
    },
    "total_cost_label": {
        "English": "Total Cost",
        "Chinese": "总成本",
        "Kiswahili": "Jumla ya Gharama",
        "French": "Coût total"
    },
    "items_in_cart_label": {
        "English": "🛒 Items in Cart:",
        "Chinese": "🛒 购物车中的商品：",
        "Kiswahili": "🛒 Bidhaa kwenye Rukwama:",
        "French": "🛒 Articles dans le panier :"
    },
    "please_select_dish": {
        "English": "Please select a dish",
        "Chinese": "请选择一道菜",
        "Kiswahili": "Tafadhali chagua chakula",
        "French": "Veuillez sélectionner un plat"
    },
    "login_register_expander": {
        "English": "🔐 Login / Register to continue",
        "Chinese": "🔐 登录/注册以继续",
        "Kiswahili": "🔐 Ingia / Jisajili ili kuendelea",
        "French": "🔐 Se connecter / S'inscrire pour continuer"
    },
    "email_input": {
        "English": "Email",
        "Chinese": "电子邮件",
        "Kiswahili": "Barua pepe",
        "French": "E-mail"
    },
    "password_input": {
        "English": "Password",
        "Chinese": "密码",
        "Kiswahili": "Nenosiri",
        "French": "Mot de passe"
    },
    "login_register_button": {
        "English": "Login or Register",
        "Chinese": "登录或注册",
        "Kiswahili": "Ingia au Jisajili",
        "French": "Se connecter ou s'inscrire"
    },
    "login_success": {
        "English": "Logged in successfully!",
        "Chinese": "登录成功！",
        "Kiswahili": "Umefanikiwa kuingia!",
        "French": "Connecté avec succès !"
    },
    "login_warning": {
        "English": "Please enter both email and password.",
        "Chinese": "请输入电子邮件和密码。",
        "Kiswahili": "Tafadhali weka barua pepe na nenosiri.",
        "French": "Veuillez entrer l'e-mail et le mot de passe."
    },
    "user_exists_warning": {
        "English": "User with this email already exists. Please login.",
        "Chinese": "此电子邮件用户已存在。请登录。",
        "Kiswahili": "Mtumiaji mwenye barua pepe hii tayari yupo. Tafadhali ingia.",
        "French": "Un utilisateur avec cet e-mail existe déjà. Veuillez vous connecter."
    },
    "add_to_cart_button": {
        "English": "➕ Add {meal_name} to Cart",
        "Chinese": "➕ 将 {meal_name} 添加到购物车",
        "Kiswahili": "➕ Ongeza {meal_name} kwenye Rukwama",
        "French": "➕ Ajouter {meal_name} au panier"
    },
    "added_to_cart_success": {
        "English": "Added {qty} x {meal_name} to cart",
        "Chinese": "已将 {qty} x {meal_name} 添加到购物车",
        "Kiswahili": "Imeongeza {qty} x {meal_name} kwenye rukwama",
        "French": "Ajouté {qty} x {meal_name} au panier"
    },
    "select_qty_warning": {
        "English": "Select at least 1 quantity before adding.",
        "Chinese": "添加前请至少选择1个数量。",
        "Kiswahili": "Chagua angalau kiasi 1 kabla ya kuongeza.",
        "French": "Sélectionnez au moins 1 quantité avant d'ajouter."
    },
    "cart_summary_subheader": {
        "English": "🛒 Cart Summary",
        "Chinese": "🛒 购物车摘要",
        "Kiswahili": "🛒 Muhtasari wa Rukwama",
        "French": "🛒 Récapitulatif du panier"
    },
    "total_label": {
        "English": "Total:",
        "Chinese": "总计：",
        "Kiswahili": "Jumla:",
        "French": "Total :"
    },
    "checkout_subheader": {
        "English": "💳 Checkout",
        "Chinese": "💳 结账",
        "Kiswahili": "💳 Malipo",
        "French": "💳 Commander"
    },
    "mpesa_phone_input": {
        "English": "Enter your M-Pesa phone number (e.g., 254712345678)",
        "Chinese": "输入您的M-Pesa手机号码（例如，254712345678）",
        "Kiswahili": "Weka nambari yako ya simu ya M-Pesa (k.m., 254712345678)",
        "French": "Entrez votre numéro de téléphone M-Pesa (ex: 254712345678)"
    },
    "pay_now_button": {
        "English": "Pay Now",
        "Chinese": "立即支付",
        "Kiswahili": "Lipa Sasa",
        "French": "Payer maintenant"
    },
    "sending_payment_request": {
        "English": "Sending payment request...",
        "Chinese": "正在发送付款请求...",
        "Kiswahili": "Inatuma ombi la malipo...",
        "French": "Envoi de la demande de paiement..."
    },
    "payment_success": {
        "English": "✅ Payment request sent. Complete payment on your phone.",
        "Chinese": "✅ 付款请求已发送。请在您的手机上完成付款。",
        "Kiswahili": "✅ Ombi la malipo limetumwa. Kamilisha malipo kwenye simu yako.",
        "French": "✅ Demande de paiement envoyée. Veuillez compléter le paiement sur votre téléphone."
    },
    "payment_failed": {
        "English": "❌ Payment failed: {error_message}",
        "Chinese": "❌ 付款失败：{error_message}",
        "Kiswahili": "❌ Malipo yameshindwa: {error_message}",
        "French": "❌ Paiement échoué : {error_message}"
    },
    "invalid_phone_warning": {
        "English": "Enter a valid 12-digit Safaricom number.",
        "Chinese": "请输入有效的12位Safaricom号码。",
        "Kiswahili": "Weka nambari halali ya Safaricom yenye tarakimu 12.",
        "French": "Entrez un numéro Safaricom valide à 12 chiffres."
    },
    "personalize_header": {
        "English": "🍴 Personalize Your Meal",
        "Chinese": "🍴 个性化你的餐点",
        "Kiswahili": "🍴 Binafsisha Chakula Chako",
        "French": "🍴 Personnalisez votre repas"
    },
    "back_to_meals_button": {
        "English": "🔙 Back to Meals",
        "Chinese": "🔙 返回餐点",
        "Kiswahili": "🔙 Rudi kwenye Chakula",
        "French": "🔙 Retour aux repas"
    },
    "your_name_input": {
        "English": "Your Name",
        "Chinese": "你的名字",
        "Kiswahili": "Jina lako",
        "French": "Votre nom"
    },
    "your_phone_input": {
        "English": "Your Phone Number",
        "Chinese": "你的电话号码",
        "Kiswahili": "Nambari yako ya simu",
        "French": "Votre numéro de téléphone"
    },
    "special_request_textarea": {
        "English": "Write your special request (e.g. 'No onions, extra spicy')",
        "Chinese": "写下您的特殊要求（例如“不要洋葱，额外辣”）",
        "Kiswahili": "Andika ombi lako maalum (k.m. 'Bila vitunguu, pilipili nyingi')",
        "French": "Écrivez votre demande spéciale (ex: 'Pas d'oignons, très épicé')"
    },
    "submit_personalization_button": {
        "English": "Submit Personalization",
        "Chinese": "提交个性化",
        "Kiswahili": "Wasilisha Ubinafsishaji",
        "French": "Soumettre la personnalisation"
    },
    "personalization_success": {
        "English": "✅ Your personalization request has been saved with your order!",
        "Chinese": "✅ 您的个性化请求已随订单保存！",
        "Kiswahili": "✅ Ombi lako la ubinafsishaji limehifadhiwa na agizo lako!",
        "French": "✅ Votre demande de personnalisation a été enregistrée avec votre commande !"
    },
    "personalization_warning": {
        "English": "Please fill in all fields before submitting.",
        "Chinese": "提交前请填写所有字段。",
        "Kiswahili": "Tafadhali jaza sehemu zote kabla ya kuwasilisha.",
        "French": "Veuillez remplir tous les champs avant de soumettre."
    },
    "order_history_header": {
        "English": "📖 Your Order History",
        "Chinese": "📖 您的订单历史",
        "Kiswahili": "📖 Historia ya Agizo Lako",
        "French": "📖 Votre historique de commandes"
    },
    "no_past_orders": {
        "English": "You have no past orders.",
        "Chinese": "您没有过去的订单。",
        "Kiswahili": "Huna maagizo yaliyopita.",
        "French": "Vous n'avez aucune commande passée."
    },
    "order_id_label": {
        "English": "Order ID:",
        "Chinese": "订单ID：",
        "Kiswahili": "Kitambulisho cha Agizo:",
        "French": "ID de commande :"
    },
    "order_date_label": {
        "English": "Order Date:",
        "Chinese": "订单日期：",
        "Kiswahili": "Tarehe ya Agizo:",
        "French": "Date de commande :"
    },
    "total_amount_label_order": {
        "English": "Total Amount:",
        "Chinese": "总金额：",
        "Kiswahili": "Jumla ya Kiasi:",
        "French": "Montant total :"
    },
    "status_label": {
        "English": "Status:",
        "Chinese": "状态：",
        "Kiswahili": "Hali:",
        "French": "Statut :"
    },
    "personalization_details_label": {
        "English": "Personalization Details:",
        "Chinese": "个性化详情：",
        "Kiswahili": "Maelezo ya Ubinafsishaji:",
        "French": "Détails de personnalisation :"
    },
    "items_ordered_label": {
        "English": "Items Ordered:",
        "Chinese": "订购商品：",
        "Kiswahili": "Bidhaa zilizoagizwa:",
        "French": "Articles commandés :"
    },
    "track_order_header": {
        "English": "📍 Track Your Current Order",
        "Chinese": "📍 追踪您当前的订单",
        "Kiswahili": "📍 Fuatilia Agizo Lako la Sasa",
        "French": "📍 Suivre votre commande actuelle"
    },
    "enter_order_id": {
        "English": "Enter Order ID to track:",
        "Chinese": "输入订单ID以追踪：",
        "Kiswahili": "Weka Kitambulisho cha Agizo ili kufuatilia:",
        "French": "Entrez l'ID de commande à suivre :"
    },
    "track_button": {
        "English": "Track Order",
        "Chinese": "追踪订单",
        "Kiswahili": "Fuatilia Agizo",
        "French": "Suivre la commande"
    },
    "order_not_found": {
        "English": "Order not found or you don't have access.",
        "Chinese": "订单未找到或您无权访问。",
        "Kiswahili": "Agizo halikupatikana au huna ufikiaji.",
        "French": "Commande introuvable ou vous n'avez pas accès."
    },
    "update_status_button": {
        "English": "Update Status",
        "Chinese": "更新状态",
        "Kiswahili": "Sasisha Hali",
        "French": "Mettre à jour le statut"
    },
    "status_updated_success": {
        "English": "Order status updated successfully!",
        "Chinese": "订单状态更新成功！",
        "Kiswahili": "Hali ya agizo imesasishwa kwa mafanikio!",
        "French": "Statut de la commande mis à jour avec succès !"
    }
}

# Fallback to English if selected language is not in translations
language = st.session_state.get("selected_language", "English")
if language not in translations["welcome_title"]:
    language = "English"


# Use translated title and subheader
st.title(translations["welcome_title"][language])


with st.sidebar:
    st.header(translations["total_cost_label"][language])
    if st.session_state.cart:
        total_cost = sum(item["price"] * item["quantity"] for item in st.session_state.cart)
        st.metric(label=translations["total_cost_label"][language], value=f"KES {total_cost:.2f}")
        st.write(translations["items_in_cart_label"][language])
        # Display cart items with quantity adjustment and remove options
        for i, item in enumerate(st.session_state.cart):
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            with col1:
                st.write(f"- {item['name']}")
            with col2:
                # Use a unique key for each number_input
                new_qty = st.number_input(
                    "Qty",
                    min_value=0,
                    max_value=10,
                    value=item['quantity'],
                    step=1,
                    key=f"cart_qty_{item['id']}_{i}"
                )
                if new_qty != item['quantity']:
                    st.session_state.cart[i]['quantity'] = new_qty
                    # Remove item if quantity becomes 0
                    if new_qty == 0:
                        st.session_state.cart = [
                            cart_item for idx, cart_item in enumerate(st.session_state.cart) if idx != i
                        ]
                    st.rerun()
            with col3:
                # Use a unique key for each button
                if st.button("🗑️", key=f"remove_item_{item['id']}_{i}"):
                    st.session_state.cart = [
                        cart_item for idx, cart_item in enumerate(st.session_state.cart) if idx != i
                    ]
                    st.rerun()
    else:
        st.info(translations["please_select_dish"][language])

    st.markdown("---")
    if st.session_state.user_authenticated:
        if st.button(translations["track_order_button"][language], key="sidebar_track_order_btn"):
            st.session_state.show_track_order = True
            st.session_state.show_order_history = False # Hide history if tracking
            st.session_state.show_personalize_page = False # Hide personalize if tracking
            st.rerun()

        if st.button(translations["view_history_button"][language], key="sidebar_view_history_btn"):
            st.session_state.show_order_history = True
            st.session_state.show_track_order = False # Hide tracking if viewing history
            st.session_state.show_personalize_page = False # Hide personalize if viewing history
            st.rerun()

        if st.session_state.user_data.get("email") == "admin@kitchen.com":
            st.session_state.admin_mode = st.checkbox(translations["admin_mode_checkbox"][language])

# Meals
meals = [
    {"id": 1, "name": "Chapati Beans", "description": "Served with steamed vegetables", "price": 90,
     "image": "https://raw.githubusercontent.com/Mokereri/webpage/refs/heads/main/Assets/images/Chapati_beans.jpeg"},
    {"id": 2, "name": "Cup of Tea", "description": "Milk tea with sugar", "price": 20,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/cup%20of%20chai.jpeg?raw=true"},
    {"id": 3, "name": "Ugali Omena", "description": "Served with fresh vegetables", "price": 100,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/ugali-omena.jpeg?raw=true"},
    {"id": 4, "name": "Rice Beans", "description": "Steamed rice with seasoned beans", "price": 100,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/rice_beans.jpeg?raw=true"},
    {"id": 5, "name": "Rice Beef", "description": "Spiced rice served with beef stew", "price": 170,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/rice_beef.jpeg?raw=true"},
    {"id": 6, "name": "Ugali Matumbo", "description": "Tender beef tripe served with ugali", "price": 140,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/ugali_matumbo.jpeg?raw=true"},
    {"id": 7, "name": "Chicken Masala", "description": "Deliciously spiced chicken in a creamy masala sauce", "price": 320,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/Chicken_masala.jpeg?raw=true"},
    {"id": 8, "name": "Beef Stew", "description": "Tender beef chunks in a rich stew sauce", "price": 280,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/beef_stew.jpeg?raw=true"},
    {"id": 9, "name": "Chicken Pasta", "description": "Creamy pasta tossed with grilled chicken", "price": 350,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/chicken%20pasta.jpeg?raw=true"}
]

# --- Main Content Area ---

# Login/Register Section
if not st.session_state.user_authenticated:
    with st.expander(translations["login_register_expander"][language]):
        with st.form("login_register_form"): # Changed form key
            email = st.text_input(translations["email_input"][language], key="login_email")
            password = st.text_input(translations["password_input"][language], type="password", key="login_password")
            login_register_btn = st.form_submit_button(translations["login_register_button"][language])

            if login_register_btn:
                if email and password:
                    if verify_user(email, password):
                        st.session_state.user_authenticated = True
                        st.session_state.user_data = {"email": email}
                        st.success(translations["login_success"][language])
                        st.rerun()
                    else:
                        # If login fails, try to register
                        success, message = create_user(email, password)
                        if success:
                            st.session_state.user_authenticated = True
                            st.session_state.user_data = {"email": email}
                            st.success(translations["login_success"][language] + " " + message)
                            st.rerun()
                        else:
                            st.warning(translations["user_exists_warning"][language] if "exists" in message else message)
                else:
                    st.warning(translations["login_warning"][language])

# Main App View (after authentication)
if st.session_state.user_authenticated:
    if st.session_state.show_personalize_page:
        # Personalization Page
        st.header(translations["personalize_header"][language])
        if st.button(translations["back_to_meals_button"][language], key="back_to_meals_from_personalize"):
            st.session_state.show_personalize_page = False
            st.rerun()

        with st.form("personalize_form"):
            p_name = st.text_input(translations["your_name_input"][language], key="p_name")
            p_phone = st.text_input(translations["your_phone_input"][language], key="p_phone")
            p_message = st.text_area(translations["special_request_textarea"][language], key="p_message")
            personalize_submit = st.form_submit_button(translations["submit_personalization_button"][language])

            if personalize_submit:
                if p_name and p_phone and p_message:
                    st.session_state.personalization_details = {
                        "name": p_name,
                        "phone": p_phone,
                        "message": p_message
                    }
                    st.success(translations["personalization_success"][language])
                else:
                    st.warning(translations["personalization_warning"][language])

    elif st.session_state.show_order_history:
        # Order History Page
        st.header(translations["order_history_header"][language])
        if st.button(translations["back_to_meals_button"][language], key="back_to_meals_from_history"):
            st.session_state.show_order_history = False
            st.rerun()

        user_orders = get_user_orders(st.session_state.user_data["email"])
        if user_orders:
            for order in user_orders:
                with st.expander(f"Order ID: {order['order_id']} - {order['order_date'].strftime('%Y-%m-%d %H:%M')} - Status: {order['status']}"):
                    st.write(f"**{translations['order_id_label'][language]}** {order['order_id']}")
                    st.write(f"**{translations['order_date_label'][language]}** {order['order_date'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**{translations['total_amount_label_order'][language]}** KES {order['total_amount']:.2f}")
                    st.write(f"**{translations['status_label'][language]}** {order['status']}")

                    if order['personalization_name'] or order['personalization_message']:
                        st.markdown(f"**{translations['personalization_details_label'][language]}**")
                        if order['personalization_name']:
                            st.write(f"Name: {order['personalization_name']}")
                        if order['personalization_phone']:
                            st.write(f"Phone: {order['personalization_phone']}")
                        if order['personalization_message']:
                            st.write(f"Message: {order['personalization_message']}")

                    st.markdown(f"**{translations['items_ordered_label'][language]}**")
                    _, order_items = get_order_details(order['order_id'])
                    for item in order_items:
                        st.write(f"- {item['meal_name']} x {item['quantity']} @ KES {item['price_per_item']:.2f}")

                    # Admin mode: Update status
                    if st.session_state.admin_mode:
                        st.markdown("---")
                        st.subheader("Admin: Update Order Status")
                        new_status = st.selectbox(
                            "Select new status:",
                            ['Pending', 'Processing', 'Ready', 'Delivered', 'Cancelled'],
                            index=['Pending', 'Processing', 'Ready', 'Delivered', 'Cancelled'].index(order['status']),
                            key=f"status_select_{order['order_id']}"
                        )
                        if st.button(translations["update_status_button"][language], key=f"update_status_btn_{order['order_id']}"):
                            if update_order_status(order['order_id'], new_status):
                                st.success(translations["status_updated_success"][language])
                                st.rerun()
                            else:
                                st.error("Failed to update status.")
        else:
            st.info(translations["no_past_orders"][language])

    elif st.session_state.show_track_order:
        # Track Order Page
        st.header(translations["track_order_header"][language])
        if st.button(translations["back_to_meals_button"][language], key="back_to_meals_from_track"):
            st.session_state.show_track_order = False
            st.rerun()

        track_order_id = st.text_input(translations["enter_order_id"][language], value=st.session_state.current_order_id or "")
        if st.button(translations["track_button"][language], key="track_order_btn"):
            if track_order_id:
                order_details, order_items = get_order_details(track_order_id)
                if order_details and order_details['user_email'] == st.session_state.user_data['email']:
                    st.subheader(f"Details for Order ID: {order_details['order_id']}")
                    st.write(f"**Status:** {order_details['status']}")
                    st.write(f"**Order Date:** {order_details['order_date'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Total Amount:** KES {order_details['total_amount']:.2f}")

                    if order_details['personalization_name'] or order_details['personalization_message']:
                        st.markdown(f"**{translations['personalization_details_label'][language]}**")
                        if order_details['personalization_name']:
                            st.write(f"Name: {order_details['personalization_name']}")
                        if order_details['personalization_phone']:
                            st.write(f"Phone: {order_details['personalization_phone']}")
                        if order_details['personalization_message']:
                            st.write(f"Message: {order_details['personalization_message']}")

                    st.markdown(f"**{translations['items_ordered_label'][language]}**")
                    for item in order_items:
                        st.write(f"- {item['meal_name']} x {item['quantity']} @ KES {item['price_per_item']:.2f}")

                    # Admin mode: Update status
                    if st.session_state.admin_mode:
                        st.markdown("---")
                        st.subheader("Admin: Update Order Status")
                        new_status = st.selectbox(
                            "Select new status:",
                            ['Pending', 'Processing', 'Ready', 'Delivered', 'Cancelled'],
                            index=['Pending', 'Processing', 'Ready', 'Delivered', 'Cancelled'].index(order_details['status']),
                            key=f"status_select_track_{order_details['order_id']}"
                        )
                        if st.button(translations["update_status_button"][language], key=f"update_status_btn_track_{order_details['order_id']}"):
                            if update_order_status(order_details['order_id'], new_status):
                                st.success(translations["status_updated_success"][language])
                                # Re-fetch and re-display to show updated status
                                st.session_state.current_order_id = track_order_id # Keep the ID for re-display
                                st.rerun()
                            else:
                                st.error("Failed to update status.")
                else:
                    st.warning(translations["order_not_found"][language])
            else:
                st.info("Please enter an Order ID to track.")

    else:
        # Main meal selection page
        st.subheader(translations["select_meal_subheader"][language])

        # Add "Personalize Your Meal" button at the top of the main menu
        if st.button(translations["personalize_button"][language], key="personalize_meal_button"):
            st.session_state.show_personalize_page = True
            st.session_state.show_order_history = False
            st.session_state.show_track_order = False
            st.rerun()

        st.markdown("---")

        cols_per_row = 3
        meal_chunks = [meals[i:i + cols_per_row] for i in range(0, len(meals), cols_per_row)]

        for row_idx, meal_row in enumerate(meal_chunks):
            cols = st.columns(cols_per_row)
            for col_idx, meal in enumerate(meal_row):
                with cols[col_idx]:
                    st.image(meal["image"], use_column_width=True)
                    st.markdown(f"**{meal['name']}**")
                    st.write(f"*{meal['description']}*")
                    st.write(f"**KES {meal['price']:.2f}**")

                    qty = st.number_input(
                        f"Quantity for {meal['name']}",
                        min_value=0,
                        max_value=10,
                        value=0,
                        step=1,
                        key=f"qty_{meal['id']}" # Unique key for each quantity input
                    )

                    add_to_cart_btn = st.button(
                        translations["add_to_cart_button"][language].format(meal_name=meal['name']),
                        key=f"add_{meal['id']}" # Unique key for each add button
                    )

                    if add_to_cart_btn:
                        if qty > 0:
                            # Check if item already exists in cart, update quantity
                            found = False
                            for item_in_cart in st.session_state.cart:
                                if item_in_cart['id'] == meal['id']:
                                    item_in_cart['quantity'] += qty
                                    found = True
                                    break
                            if not found:
                                st.session_state.cart.append(
                                    {"id": meal['id'], "name": meal['name'], "price": meal['price'], "quantity": qty}
                                )
                            st.success(translations["added_to_cart_success"][language].format(qty=qty, meal_name=meal['name']))
                            st.rerun() # Rerun to update sidebar cart immediately
                        else:
                            st.warning(translations["select_qty_warning"][language])

        st.markdown("---")

        if st.session_state.cart:
            st.subheader(translations["checkout_subheader"][language])
            mpesa_phone = st.text_input(
                translations["mpesa_phone_input"][language],
                value=st.session_state.user_data.get("phone_number", ""), # Pre-fill if exists
                max_chars=12,
                key="mpesa_phone_input"
            )

            total_amount_for_checkout = sum(item["price"] * item["quantity"] for item in st.session_state.cart)

            if st.button(translations["pay_now_button"][language], key="pay_now_button"):
                if mpesa_phone and len(mpesa_phone) == 12 and mpesa_phone.startswith('2547'):
                    with st.spinner(translations["sending_payment_request"][language]):
                        transaction_desc = "Hotel Meal Payment"
                        account_reference = f"ORDER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{st.session_state.user_data['email'].split('@')[0]}"

                        # M-Pesa API expects amount as an integer for KES
                        mpesa_amount = int(total_amount_for_checkout)

                        response = lipa_na_mpesa_online(mpesa_phone, mpesa_amount, account_reference, transaction_desc)

                        if response and "CheckoutRequestID" in response:
                            st.success(translations["payment_success"][language])
                            st.session_state.current_order_id = account_reference # Store for tracking
                            # Save order to DB regardless of M-Pesa confirmation for now
                            # In a real app, you'd confirm M-Pesa callback before saving as "Paid"
                            success, order_id = save_order(
                                st.session_state.user_data["email"],
                                st.session_state.cart,
                                total_amount_for_checkout,
                                st.session_state.personalization_details
                            )
                            if success:
                                st.success(f"Order saved successfully! Order ID: {order_id}")
                                st.session_state.cart = [] # Clear cart after successful order
                                st.session_state.personalization_details = {} # Clear personalization
                                st.rerun()
                            else:
                                st.error(f"Failed to save order to database: {order_id}")
                        else:
                            error_message = response.get("errorMessage", "Unknown error") if response else "No response"
                            st.error(translations["payment_failed"][language].format(error_message=error_message))
                else:
                    st.warning(translations["invalid_phone_warning"][language])
        else:
            st.info("Your cart is empty. Add some delicious meals!")

