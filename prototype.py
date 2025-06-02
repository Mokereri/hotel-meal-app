import streamlit as st

# Set page config first!
st.set_page_config(page_title="Hotel Kitchen", layout="wide")

import base64
import requests
from decouple import config
from datetime import datetime
import streamlit.components.v1 as components

# Inject JavaScript to get browser language and redirect
components.html(
    """
    <script>
    const userLang = navigator.language || navigator.userLanguage;
    const currentUrl = new URL(window.location.href);
    if (!currentUrl.searchParams.get("lang")) {
        currentUrl.searchParams.set("lang", userLang.split("-")[0]); // e.g., 'en', 'fr'
        window.location.href = currentUrl.href;
    }
    </script>
    """,
    height=0
)

# ==== Helper Functions ====

def get_access_token(consumer_key, consumer_secret):
    auth_string = f"{consumer_key}:{consumer_secret}"
    encoded = base64.b64encode(auth_string.encode()).decode()

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate"
    headers = {"Authorization": f"Basic {encoded}"}
    params = {"grant_type": "client_credentials"}

    response = requests.get(url, headers=headers, params=params)
    return response.json().get("access_token")


def lipa_na_mpesa_online(phone_number, amount):
    access_token = get_access_token(config("CONSUMER_KEY"), config("CONSUMER_SECRET"))
    if not access_token:
        return {"error": "Failed to get access token"}

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    business_shortcode = config("BUSINESS_SHORTCODE")
    passkey = config("PASSKEY")
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
        "AccountReference": "Order001",
        "TransactionDesc": "Meal Order"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers
    )
    return response.json()

# ==== Session States ====
if "cart" not in st.session_state:
    st.session_state.cart = []
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "orders" not in st.session_state:
    st.session_state.orders = []
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False
if "show_personalize_page" not in st.session_state:
    st.session_state.show_personalize_page = False
if "payment_feedback" not in st.session_state:
    st.session_state.payment_feedback = None
if "show_faq" not in st.session_state:
    st.session_state.show_faq = False
if "last_Youtube" not in st.session_state:
    st.session_state.last_Youtube = ""

# ==== Language Detection ====
query_params = st.query_params
browser_lang = query_params.get("lang", ["en"])[0]

language_map = {
    "en": "English",
    "sw": "Kiswahili",
    "fr": "French",
    "zh": "Chinese"
}
default_lang = language_map.get(browser_lang, "English")

# Sidebar: Language selection
with st.sidebar:
    st.markdown("🌐 **Choose Language**")
    selected_language = st.selectbox(
        "Select Language",
        ["English", "Chinese", "Kiswahili", "French"],
        index=["English", "Chinese", "Kiswahili", "French"].index(default_lang),
        key="selected_language"
    )
    st.markdown("---")

language = selected_language

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
    "phone_prompt": {
        "English": "📱 Enter your phone number to pay",
        "Kiswahili": "📱 Weka nambari yako ya simu kulipa",
        "Chinese": "📱 输入你的电话号码支付",
        "French": "📱 Entrez votre numéro de téléphone pour payer"
    },
    "ask_question_button": {
        "English": "❓ Ask a Question",
        "Kiswahili": "❓ Uliza Swali",
        "Chinese": "❓ 提问",
        "French": "❓ Poser une question"
    },
    "your_question_placeholder": {
        "English": "e.g., Is Ugali Fish available today?",
        "Kiswahili": "mfano, Je, Ugali Samaki inapatikana leo?",
        "Chinese": "例如, 今天有玉米粥配鱼吗?",
        "French": "par exemple, L'Ugali Poisson est-il disponible aujourd'hui?"
    },
    "ask_button": {
        "English": "Ask",
        "Kiswahili": "Uliza",
        "Chinese": "提问",
        "French": "Demander"
    },
    "Youtube_title": {
        "English": "Your Question & Answer",
        "Kiswahili": "Swali Lako & Jibu",
        "Chinese": "您的问题与答案",
        "French": "Votre question et réponse"
    }
}

# ==== Meal Translations ====
meal_translations = {
    1: {
        "name": {"English": "Chapati Beans", "Kiswahili": "Chapati Maharagwe", "Chinese": "豆饼", "French": "Chapati Haricots"},
        "desc": {"English": "Served with steamed vegetables", "Kiswahili": "Imetolewa na mboga zilizopikwa", "Chinese": "配蒸蔬菜", "French": "Servi avec des légumes vapeur"}
    },
    2: {
        "name": {"English": "Cup of Tea", "Kiswahili": "Kikombe cha Chai", "Chinese": "一杯茶", "French": "Tasse de thé"},
        "desc": {"English": "Milk tea with sugar", "Kiswahili": "Chai ya maziwa na sukari", "Chinese": "加糖奶茶", "French": "Thé au lait sucré"}
    },
    3: {
        "name": {"English": "Ugali Omena", "Kiswahili": "Ugali na Omena", "Chinese": "玉米粥配银鱼", "French": "Ugali Omena"},
        "desc": {"English": "Served with fresh vegetables", "Kiswahili": "Imetolewa na mboga mbichi", "Chinese": "配新鲜蔬菜", "French": "Servi avec des légumes frais"}
    },
    4: {
        "name": {"English": "Rice Beans", "Kiswahili": "Mchele Maharagwe", "Chinese": "米饭和豆类", "French": "Riz Haricots"},
        "desc": {"English": "Steamed rice with seasoned beans", "Kiswahili": "Mchele na maharagwe yaliyopikwa vizuri", "Chinese": "蒸米配调味豆", "French": "Riz vapeur avec haricots assaisonnés"}
    },
    5: {
        "name": {"English": "Rice Beef", "Kiswahili": "Mchele Nyama", "Chinese": "米饭和牛肉", "French": "Riz Bœuf"},
        "desc": {"English": "Spiced rice served with beef stew", "Kiswahili": "Mchele wa viungo na mchuzi wa nyama", "Chinese": "香料米饭配炖牛肉", "French": "Riz épicé avec ragoût de bœuf"}
    },
    6: {
        "name": {"English": "Ugali Matumbo", "Kiswahili": "Ugali na Matumbo", "Chinese": "玉米粥和牛肚", "French": "Ugali Matumbo"},
        "desc": {"English": "Tender beef tripe served with ugali", "Kiswahili": "Matumbo laini na ugali", "Chinese": "嫩牛肚配玉米粥", "French": "Tripes tendres avec ugali"}
    },
    7: {
        "name": {"English": "Chicken Masala", "Kiswahili": "Kuku Masala", "Chinese": "马萨拉鸡", "French": "Poulet Masala"},
        "desc": {"English": "Deliciously spiced chicken in a creamy masala sauce", "Kiswahili": "Kuku ya viungo kwenye mchuzi wa krimu", "Chinese": "香料鸡配奶油酱", "French": "Poulet épicé dans une sauce masala crémeuse"}
    },
    8: {
        "name": {"English": "Beef Stew", "Kiswahili": "Mchuzi wa Nyama", "Chinese": "炖牛肉", "French": "Ragoût de bœuf"},
        "desc": {"English": "Tender beef chunks in a rich stew sauce", "Kiswahili": "Vipande vya nyama kwenye mchuzi", "Chinese": "嫩牛肉配浓郁酱", "French": "Morceaux de bœuf dans une sauce riche"}
    },
    9: {
        "name": {"English": "Chicken Pasta", "Kiswahili": "Pasta ya Kuku", "Chinese": "鸡肉意面", "French": "Pâtes au poulet"},
        "desc": {"English": "Creamy pasta tossed with grilled chicken", "Kiswahili": "Pasta ya krimu na kuku wa kuchoma", "Chinese": "奶油意面配烤鸡", "French": "Pâtes crémeuses au poulet grillé"}
    }
}

meals = [
    {"id": 1, "price": 90, "image": "https://raw.githubusercontent.com/Mokereri/webpage/refs/heads/main/Assets/images/Chapati_beans.jpeg"},
    {"id": 2, "price": 20, "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/cup%20of%20chai.jpeg?raw=true"},
    {"id": 3, "price": 100, "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/ugali-omena.jpeg?raw=true"},
    {"id": 4, "price": 100, "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/rice_beans.jpeg?raw=true"},
    {"id": 5, "price": 170, "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/rice_beef.jpeg?raw=true"},
    {"id": 6, "price": 140, "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/ugali_matumbo.jpeg?raw=true"},
    {"id": 7, "price": 320, "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/Chicken_masala.jpeg?raw=true"},
    {"id": 8, "price": 280, "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/beef_stew.jpeg?raw=true"},
    {"id": 9, "price": 350, "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/chicken%20pasta.jpeg?raw=true"}
]

# Function to answer questions
def answer_question(question, current_language):
    question_lower = question.lower()
    
    # Check for specific meal availability
    if "ugali fish" in question_lower or "fish ugali" in question_lower:
        # Assuming Ugali Omena is the closest to "Ugali Fish" in your menu
        if any(meal_translations[meal["id"]]["name"]["English"].lower() == "ugali omena" for meal in meals):
            return {
                "English": "Yes, Ugali Omena is available today!",
                "Kiswahili": "Ndio, Ugali na Omena inapatikana leo!",
                "Chinese": "是的，玉米粥配银鱼今天有货！",
                "French": "Oui, l'Ugali Omena est disponible aujourd'sui !"
            }.get(current_language, "Yes, Ugali Omena is available today!")
    
    if "chapati beans" in question_lower or "beans chapati" in question_lower:
        if any(meal_translations[meal["id"]]["name"]["English"].lower() == "chapati beans" for meal in meals):
            return {
                "English": "Yes, Chapati Beans is available today!",
                "Kiswahili": "Ndio, Chapati Maharagwe inapatikana leo!",
                "Chinese": "是的，豆饼今天有货！",
                "French": "Oui, les Chapati Haricots sont disponibles aujourd'hui !"
            }.get(current_language, "Yes, Chapati Beans is available today!")

    if "cup of tea" in question_lower or "tea" in question_lower:
        if any(meal_translations[meal["id"]]["name"]["English"].lower() == "cup of tea" for meal in meals):
            return {
                "English": "Yes, a cup of tea is available.",
                "Kiswahili": "Ndio, kikombe cha chai kinapatikana.",
                "Chinese": "是的，有茶。",
                "French": "Oui, une tasse de thé est disponible."
            }.get(current_language, "Yes, a cup of tea is available.")
            
    # General availability query
    if "available today" in question_lower or "what's available" in question_lower:
        available_meals = [meal_translations[m["id"]]["name"][current_language] for m in meals]
        return {
            "English": f"Today we have: {', '.join(available_meals)}.",
            "Kiswahili": f"Leo tunayo: {', '.join(available_meals)}.",
            "Chinese": f"今天我们有: {', '.join(available_meals)}。",
            "French": f"Aujourd'hui nous avons: {', '.join(available_meals)}."
        }.get(current_language, f"Today we have: {', '.join(available_meals)}.")
        
    # Default fallback
    return {
        "English": "I'm sorry, I can only answer questions about meal availability. Please rephrase your question.",
        "Kiswahili": "Samahani, ninaweza tu kujibu maswali kuhusu upatikanaji wa chakula. Tafadhali uliza tena swali lako.",
        "Chinese": "抱歉，我只能回答关于餐点供应的问题。请重新提问。",
        "French": "Désolé, je ne peux répondre qu'aux questions sur la disponibilité des repas. Veuillez reformuler votre question."
    }.get(current_language, "I'm sorry, I can only answer questions about meal availability. Please rephrase your question.")


# ==== Main UI ====
st.title(translations["welcome_title"][language])
st.subheader(translations["select_meal_subheader"][language])

# Display Meals
columns = st.columns(3)
for i, meal in enumerate(meals):
    meal_id = meal["id"]
    name = meal_translations[meal_id]["name"][language]
    desc = meal_translations[meal_id]["desc"][language]
    col = columns[i % 3]
    with col:
        st.image(meal["image"], width=250)
        st.markdown(f"### {name}")
        st.caption(desc)
        st.markdown(f"**Price:** KES {meal['price']}")
        qty = st.number_input(f"Qty - {name}", min_value=0, value=0, step=1, key=f"qty_{meal_id}")
        if qty > 0:
            st.session_state.cart.append({"name": name, "price": meal["price"], "quantity": qty})

# --- Sidebar Cart and Payment ---
with st.sidebar:
    st.header("💵 To Pay")
    if st.session_state.cart:
        total_cost = sum(item["price"] * item["quantity"] for item in st.session_state.cart)
        st.metric(label="Total Cost", value=f"KES {total_cost:.2f}")
        st.write("🛒 Items in Cart:")
        for item in st.session_state.cart:
            st.write(f"- {item['name']} x {item['quantity']}")
        phone_number = st.text_input(translations["phone_prompt"][language], placeholder="07XXXXXXXX")
        if st.button("📲 Pay with Mpesa"):
            if phone_number and phone_number.startswith("07"):
                with st.spinner("Initiating STK Push..."):
                    response = lipa_na_mpesa_online(phone_number, total_cost)
                    st.session_state.payment_feedback = response
            else:
                st.warning("Please enter a valid Safaricom number.")
        if st.session_state.payment_feedback:
            if st.session_state.payment_feedback.get("ResponseCode") == "0":
                st.success("STK Push sent successfully. Check your phone!")
            else:
                st.error(f"Payment failed: {st.session_state.payment_feedback}")
    else:
        st.info("Please select a dish")

    # --- Ask a Question Section ---
    st.markdown("---")
    st.header(translations["Youtube_title"][language])
    
    # Button to toggle the question input
    if st.button(translations["ask_question_button"][language]):
        st.session_state.show_faq = not st.session_state.show_faq

    if st.session_state.show_faq:
        user_question = st.text_input(
            "", 
            placeholder=translations["your_question_placeholder"][language], 
            key="user_question_input"
        )
        if st.button(translations["ask_button"][language], key="submit_question_button"):
            if user_question:
                answer = answer_question(user_question, language)
                st.session_state.last_Youtube = f"**Q:** {user_question}\n\n**A:** {answer}"
            else:
                st.session_state.last_Youtube = {
                    "English": "Please type your question.",
                    "Kiswahili": "Tafadhali andika swali lako.",
                    "Chinese": "请键入您的问题。",
                    "French": "Veuillez taper votre question."
                }.get(language, "Please type your question.")
    
    if st.session_state.last_Youtube:
        st.markdown(st.session_state.last_Youtube)