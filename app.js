// App.js
import React, { useState, useEffect, createContext, useContext } from 'react';

// --- Contexts ---
const AuthContext = createContext(null);
const AppContext = createContext(null);

// --- Backend API Service (api.js equivalent) ---
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000'; // Default for local dev

const api = {
    register: async (email, password) => {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        return response.json();
    },
    login: async (email, password) => {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        return response.json();
    },
    initiateMpesaStkPush: async (phoneNumber, amount, accountReference, transactionDesc) => {
        const response = await fetch(`${API_BASE_URL}/mpesa_stk_push`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone_number: phoneNumber,
                amount: amount,
                account_reference: accountReference,
                transaction_desc: transactionDesc,
            }),
        });
        return response.json();
    },
    saveOrder: async (userEmail, cartItems, totalAmount, personalizationData, checkoutRequestId) => {
        const response = await fetch(`${API_BASE_URL}/save_order`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_email: userEmail,
                cart_items: cartItems,
                total_amount: totalAmount,
                personalization_data: personalizationData,
                checkout_request_id: checkoutRequestId,
            }),
        });
        return response.json();
    },
    getUserOrders: async (userEmail) => {
        const response = await fetch(`${API_BASE_URL}/get_orders`, {
            method: 'POST', // Using POST for consistency with other data-sending calls
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_email: userEmail }),
        });
        return response.json();
    },
    getOrderDetails: async (orderId) => {
        const response = await fetch(`${API_BASE_URL}/get_order_details`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId }),
        });
        return response.json();
    },
    updateOrderStatus: async (orderId, newStatus) => {
        const response = await fetch(`${API_BASE_URL}/update_order_status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId, new_status: newStatus }),
        });
        return response.json();
    },
};

// --- Translations Data ---
const translations = {
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
    "out_of_stock_warning": {
        "English": "Sorry, {meal_name} is out of stock or requested quantity exceeds available stock.",
        "Chinese": "抱歉，{meal_name} 库存不足或请求数量超过可用库存。",
        "Kiswahili": "Samahani, {meal_name} imekwisha au kiasi kilichoombwa kinazidi kiasi kilichopo.",
        "French": "Désolé, {meal_name} est en rupture de stock ou la quantité demandée dépasse le stock disponible."
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
        "French": "Votre numéro ya simu"
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
    },
    "view_receipt_button": {
        "English": "🧾 View Receipt",
        "Chinese": "🧾 查看收据",
        "Kiswahili": "🧾 Tazama Risiti",
        "French": "🧾 Voir le reçu"
    },
    "download_receipt_button": {
        "English": "⬇️ Download Receipt",
        "Chinese": "⬇️ 下载收据",
        "Kiswahili": "⬇️ Pakua Risiti",
        "French": "⬇️ Télécharger le reçu"
    },
    "analytics_dashboard_button": {
        "English": "📊 Analytics Dashboard",
        "Chinese": "📊 分析仪表板",
        "Kiswahili": "📊 Dashibodi ya Uchambuzi",
        "French": "📊 Tableau de bord d'analyse"
    }
};

// Initial meal data with stock
const initialMealsData = [
    {"id": 1, "name": "Chapati Beans", "description": "Served with steamed vegetables", "price": 90, "stock": 50,
     "image": "https://raw.githubusercontent.com/Mokereri/webpage/refs/heads/main/Assets/images/Chapati_beans.jpeg"},
    {"id": 2, "name": "Cup of Tea", "description": "Milk tea with sugar", "price": 20, "stock": 100,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/cup%20of%20chai.jpeg?raw=true"},
    {"id": 3, "name": "Ugali Omena", "description": "Served with fresh vegetables", "price": 100, "stock": 40,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/ugali-omena.jpeg?raw=true"},
    {"id": 4, "name": "Rice Beans", "description": "Steamed rice with seasoned beans", "price": 100, "stock": 60,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/rice_beans.jpeg?raw=true"},
    {"id": 5, "name": "Rice Beef", "description": "Spiced rice served with beef stew", "price": 170, "stock": 30,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/rice_beef.jpeg?raw=true"},
    {"id": 6, "name": "Ugali Matumbo", "description": "Tender beef tripe served with ugali", "price": 140, "stock": 35,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/ugali_matumbo.jpeg?raw=true"},
    {"id": 7, "name": "Chicken Masala", "description": "Deliciously spiced chicken in a creamy masala sauce", "price": 320, "stock": 25,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/Chicken_masala.jpeg?raw=true"},
    {"id": 8, "name": "Beef Stew", "description": "Tender beef chunks in a rich stew sauce", "price": 280, "stock": 20,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/beef_stew.jpeg?raw=true"},
    {"id": 9, "name": "Chicken Pasta", "description": "Creamy pasta tossed with grilled chicken", "price": 350, "stock": 15,
     "image": "https://github.com/Mokereri/webpage/blob/main/Assets/images/chicken%20pasta.jpeg?raw=true"}
];

// --- Utility Functions ---
const generateReceiptContent = (orderDetails, orderItems) => {
    let receipt = `--- Edgewood Hotel Kitchen Receipt ---\n`;
    receipt += `Order ID: ${orderDetails.order_id}\n`;
    receipt += `Date: ${new Date(orderDetails.order_date).toLocaleString()}\n`;
    receipt += `Customer Email: ${orderDetails.user_email}\n`;
    receipt += `------------------------------------\n`;
    receipt += `Items:\n`;
    orderItems.forEach(item => {
        receipt += `- ${item.meal_name} x ${item.quantity} @ KES ${item.price_per_item.toFixed(2)} = KES ${(item.quantity * item.price_per_item).toFixed(2)}\n`;
    });
    receipt += `------------------------------------\n`;
    receipt += `Total Amount: KES ${orderDetails.total_amount.toFixed(2)}\n`;
    receipt += `Payment Status: ${orderDetails.status}\n`;
    if (orderDetails.mpesa_receipt_number) {
        receipt += `M-Pesa Receipt: ${orderDetails.mpesa_receipt_number}\n`;
    }
    if (orderDetails.mpesa_transaction_date) {
        receipt += `M-Pesa Date: ${new Date(orderDetails.mpesa_transaction_date).toLocaleString()}\n`;
    }
    if (orderDetails.personalization_name || orderDetails.personalization_message) {
        receipt += `------------------------------------\n`;
        receipt += `Personalization Details:\n`;
        if (orderDetails.personalization_name) {
            receipt += `  Name: ${orderDetails.personalization_name}\n`;
        }
        if (orderDetails.personalization_phone) {
            receipt += `  Phone: ${orderDetails.personalization_phone}\n`;
        }
        if (orderDetails.personalization_message) {
            receipt += `  Message: ${orderDetails.personalization_message}\n`;
        }
    }
    receipt += `------------------------------------\n`;
    receipt += `Thank you for your order!\n`;
    return receipt;
};

// --- Components ---

const Notification = ({ message, type, onClose }) => {
    const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
    return (
        <div className={`fixed top-4 right-4 p-4 rounded-lg shadow-lg text-white ${bgColor} z-50`}>
            <span>{message}</span>
            <button onClick={onClose} className="ml-4 font-bold">X</button>
        </div>
    );
};

const LoginRegister = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { login } = useContext(AuthContext);
    const { language, showNotification } = useContext(AppContext);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!email || !password) {
            showNotification(translations["login_warning"][language], 'warning');
            return;
        }

        const success = await login(email, password);
        if (success) {
            showNotification(translations["login_success"][language], 'success');
        } else {
            showNotification(translations["user_exists_warning"][language], 'warning');
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">{translations["login_register_expander"][language]}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                        {translations["email_input"][language]}
                    </label>
                    <input
                        type="email"
                        id="email"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                        {translations["password_input"][language]}
                    </label>
                    <input
                        type="password"
                        id="password"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button
                    type="submit"
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                    {translations["login_register_button"][language]}
                </button>
            </form>
        </div>
    );
};

const MealList = () => {
    const { cart, setCart, mealsData, setMealsData, language, showNotification } = useContext(AppContext);

    const handleAddToCart = (meal, qty) => {
        if (qty <= 0) {
            showNotification(translations["select_qty_warning"][language], 'warning');
            return;
        }

        const currentItemInCart = cart.find(item => item.id === meal.id);
        const currentItemInCartQty = currentItemInCart ? currentItemInCart.quantity : 0;
        const availableStock = meal.stock + currentItemInCartQty; // Stock considers what's already in cart

        if (qty > availableStock) {
            showNotification(translations["out_of_stock_warning"][language].replace('{meal_name}', meal.name), 'warning');
            return;
        }

        const updatedCart = cart.map(item =>
            item.id === meal.id ? { ...item, quantity: qty } : item
        );

        if (!cart.some(item => item.id === meal.id)) {
            updatedCart.push({ ...meal, quantity: qty });
        }

        // Update stock in mealsData
        const updatedMealsData = mealsData.map(m => {
            if (m.id === meal.id) {
                const newStock = m.stock - (qty - currentItemInCartQty);
                return { ...m, stock: newStock };
            }
            return m;
        });

        setCart(updatedCart.filter(item => item.quantity > 0)); // Filter out items with 0 quantity
        setMealsData(updatedMealsData);
        showNotification(translations["added_to_cart_success"][language].replace('{qty}', qty).replace('{meal_name}', meal.name), 'success');
    };

    return (
        <div className="p-4">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">{translations["select_meal_subheader"][language]}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {mealsData.map(meal => (
                    <div key={meal.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                        <img src={meal.image} alt={meal.name} className="w-full h-48 object-cover rounded-t-lg" onError={(e) => { e.target.onerror = null; e.target.src = `https://placehold.co/600x400/cccccc/ffffff?text=${meal.name.replace(/\s/g, '+')}`; }} />
                        <div className="p-4">
                            <h3 className="text-xl font-semibold text-gray-900">{meal.name}</h3>
                            <p className="text-gray-600 text-sm italic mb-2">{meal.description}</p>
                            <p className="text-lg font-bold text-blue-600 mb-2">KES {meal.price.toFixed(2)}</p>
                            <p className="text-sm text-gray-700 mb-4">Stock: {meal.stock}</p>
                            <div className="flex items-center space-x-2">
                                <input
                                    type="number"
                                    min="0"
                                    max={meal.stock + (cart.find(item => item.id === meal.id)?.quantity || 0)}
                                    defaultValue={cart.find(item => item.id === meal.id)?.quantity || 0}
                                    onChange={(e) => {
                                        const qty = parseInt(e.target.value, 10);
                                        // Update the quantity in the cart directly from the input
                                        const updatedCart = cart.map(item =>
                                            item.id === meal.id ? { ...item, quantity: qty } : item
                                        );
                                        if (!cart.some(item => item.id === meal.id)) {
                                            if (qty > 0) updatedCart.push({ ...meal, quantity: qty });
                                        }
                                        setCart(updatedCart.filter(item => item.quantity > 0));
                                    }}
                                    className="w-20 p-2 border border-gray-300 rounded-md text-center"
                                />
                                <button
                                    onClick={() => handleAddToCart(meal, parseInt(document.querySelector(`input[type="number"][min="0"][max="${meal.stock + (cart.find(item => item.id === meal.id)?.quantity || 0)}"][defaultValue="${cart.find(item => item.id === meal.id)?.quantity || 0}"]`).value, 10))}
                                    className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition duration-200 ease-in-out"
                                >
                                    {translations["add_to_cart_button"][language].replace('{meal_name}', meal.name)}
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

const CartSidebar = () => {
    const { cart, setCart, mealsData, setMealsData, language, showNotification, user, setCurrentOrderId } = useContext(AppContext);
    const [mpesaPhone, setMpesaPhone] = useState('');
    const [showReceipt, setShowReceipt] = useState(false);
    const [receiptContent, setReceiptContent] = useState('');
    const [lastOrderId, setLastOrderId] = useState(null);

    const totalCost = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    const handleUpdateCartQuantity = (index, newQty) => {
        const itemToUpdate = cart[index];
        const oldQty = itemToUpdate.quantity;

        const updatedCart = [...cart];
        if (newQty === 0) {
            updatedCart.splice(index, 1); // Remove item
        } else {
            updatedCart[index] = { ...itemToUpdate, quantity: newQty };
        }

        // Adjust stock in mealsData
        const updatedMealsData = mealsData.map(meal => {
            if (meal.id === itemToUpdate.id) {
                const stockChange = oldQty - newQty; // If oldQty > newQty, stock increases
                return { ...meal, stock: meal.stock + stockChange };
            }
            return meal;
        });

        setCart(updatedCart);
        setMealsData(updatedMealsData);
    };

    const handleRemoveFromCart = (index) => {
        const itemToRemove = cart[index];
        const updatedCart = [...cart];
        updatedCart.splice(index, 1);

        // Return stock to mealsData
        const updatedMealsData = mealsData.map(meal => {
            if (meal.id === itemToRemove.id) {
                return { ...meal, stock: meal.stock + itemToRemove.quantity };
            }
            return meal;
        });

        setCart(updatedCart);
        setMealsData(updatedMealsData);
    };

    const handleCheckout = async () => {
        if (!user || !user.email) {
            showNotification("Please login to proceed with checkout.", "warning");
            return;
        }
        if (cart.length === 0) {
            showNotification(translations["please_select_dish"][language], 'warning');
            return;
        }
        if (!mpesaPhone || mpesaPhone.length !== 12 || !mpesaPhone.startsWith("254")) {
            showNotification(translations["invalid_phone_warning"][language], 'warning');
            return;
        }
        if (totalCost <= 0) {
            showNotification("Total amount must be greater than 0.", 'warning');
            return;
        }

        showNotification(translations["sending_payment_request"][language], 'info');

        const accountReference = `HOTELPAYMENT-${Date.now()}`; // Unique reference for M-Pesa
        const transactionDesc = `Payment for Hotel Kitchen Order ${accountReference}`;
        const amount = parseInt(totalCost, 10);

        try {
            const mpesaResponse = await api.initiateMpesaStkPush(mpesaPhone, amount, accountReference, transactionDesc);

            if (mpesaResponse && mpesaResponse.CheckoutRequestID) {
                const checkoutRequestId = mpesaResponse.CheckoutRequestID;
                showNotification(translations["payment_success"][language], 'success');

                const orderItemsForDb = cart.map(item => ({
                    id: item.id,
                    name: item.name,
                    quantity: item.quantity,
                    price: item.price,
                }));

                const saveOrderResponse = await api.saveOrder(
                    user.email,
                    orderItemsForDb,
                    totalCost,
                    null, // Personalization details are handled separately if submitted
                    checkoutRequestId
                );

                if (saveOrderResponse.success) {
                    const orderIdDb = saveOrderResponse.order_id;
                    setLastOrderId(orderIdDb); // Store for immediate receipt viewing
                    setCurrentOrderId(orderIdDb); // Update global current order ID
                    showNotification(`Order saved successfully! Order ID: ${orderIdDb}`, 'success');

                    // Fetch order details for receipt generation
                    const [orderDetailsForReceipt, orderItemsForReceipt] = await Promise.all([
                        api.getOrderDetails(orderIdDb).then(res => res.order),
                        api.getOrderDetails(orderIdDb).then(res => res.items)
                    ]);

                    if (orderDetailsForReceipt) {
                        setReceiptContent(generateReceiptContent(orderDetailsForReceipt, orderItemsForReceipt));
                        setShowReceipt(true);
                    }

                    setCart([]); // Clear cart after successful order initiation
                    // Personalization details are not cleared here, as they are part of the form
                    // and might be used for subsequent orders if not explicitly reset.
                    // If you want to clear them, add: setPersonalizationDetails({});
                } else {
                    showNotification(`Failed to save order to database: ${saveOrderResponse.error}`, 'error');
                    // Revert stock if order saving failed
                    const revertedMealsData = [...mealsData];
                    cart.forEach(cartItem => {
                        const mealIndex = revertedMealsData.findIndex(meal => meal.id === cartItem.id);
                        if (mealIndex !== -1) {
                            revertedMealsData[mealIndex].stock += cartItem.quantity;
                        }
                    });
                    setMealsData(revertedMealsData);
                    showNotification("Stock reverted due to failed order save.", 'warning');
                }
            } else {
                const errorMessage = mpesaResponse.errorMessage || "Unknown error";
                showNotification(translations["payment_failed"][language].replace('{error_message}', errorMessage), 'error');
                showNotification("Please check your M-Pesa phone for prompts or try again.", 'info');
            }
        } catch (error) {
            console.error("Checkout error:", error);
            showNotification(`An unexpected error occurred during checkout: ${error.message}`, 'error');
        }
    };

    return (
        <div className="p-4 bg-gray-100 rounded-lg shadow-inner h-full flex flex-col">
            <h2 className="text-xl font-bold mb-4 text-gray-800">{translations["cart_summary_subheader"][language]}</h2>
            {cart.length === 0 ? (
                <p className="text-gray-600">{translations["please_select_dish"][language]}</p>
            ) : (
                <>
                    <ul className="space-y-2 flex-grow overflow-y-auto pr-2">
                        {cart.map((item, index) => (
                            <li key={item.id} className="flex items-center justify-between bg-white p-3 rounded-md shadow-sm">
                                <div className="flex-1">
                                    <span className="font-medium text-gray-800">{item.name}</span>
                                    <span className="block text-sm text-gray-600">KES {item.price.toFixed(2)}</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <input
                                        type="number"
                                        min="0"
                                        max={mealsData.find(m => m.id === item.id)?.stock + item.quantity || 10} // Allow increasing up to current stock + cart quantity
                                        value={item.quantity}
                                        onChange={(e) => handleUpdateCartQuantity(index, parseInt(e.target.value, 10))}
                                        className="w-16 p-1 border border-gray-300 rounded-md text-center text-sm"
                                    />
                                    <button
                                        onClick={() => handleRemoveFromCart(index)}
                                        className="bg-red-500 text-white p-1 rounded-md hover:bg-red-600 transition duration-200 ease-in-out"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                    <div className="mt-4 pt-4 border-t border-gray-300">
                        <p className="text-lg font-bold text-gray-900 flex justify-between">
                            <span>{translations["total_label"][language]}</span>
                            <span>KES {totalCost.toFixed(2)}</span>
                        </p>
                        <h3 className="text-lg font-semibold mt-4 mb-2 text-gray-800">{translations["checkout_subheader"][language]}</h3>
                        <input
                            type="tel"
                            placeholder={translations["mpesa_phone_input"][language]}
                            value={mpesaPhone}
                            onChange={(e) => setMpesaPhone(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-md mb-4"
                            maxLength="12"
                        />
                        <button
                            onClick={handleCheckout}
                            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200 ease-in-out"
                        >
                            {translations["pay_now_button"][language]}
                        </button>
                    </div>
                </>
            )}

            {showReceipt && lastOrderId && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full">
                        <h3 className="text-xl font-semibold mb-4">Your Order Receipt</h3>
                        <textarea
                            className="w-full h-64 border border-gray-300 rounded-md p-2 font-mono text-sm"
                            readOnly
                            value={receiptContent}
                        ></textarea>
                        <div className="mt-4 flex justify-end space-x-2">
                            <button
                                onClick={() => {
                                    const blob = new Blob([receiptContent], { type: 'text/plain' });
                                    const url = URL.createObjectURL(blob);
                                    const a = document.createElement('a');
                                    a.href = url;
                                    a.download = `receipt_${lastOrderId}.txt`;
                                    document.body.appendChild(a);
                                    a.click();
                                    document.body.removeChild(a);
                                    URL.revokeObjectURL(url);
                                }}
                                className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700"
                            >
                                {translations["download_receipt_button"][language]}
                            </button>
                            <button
                                onClick={() => setShowReceipt(false)}
                                className="bg-gray-300 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-400"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const PersonalizeMeal = () => {
    const { language, showNotification, setPersonalizationDetails, personalizationDetails, setShowPersonalizePage } = useContext(AppContext);
    const [pName, setPName] = useState(personalizationDetails.name || '');
    const [pPhone, setPPhone] = useState(personalizationDetails.phone || '');
    const [pMessage, setPMessage] = useState(personalizationDetails.message || '');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (pName && pPhone && pMessage) {
            setPersonalizationDetails({ name: pName, phone: pPhone, message: pMessage });
            showNotification(translations["personalization_success"][language], 'success');
        } else {
            showNotification(translations["personalization_warning"][language], 'warning');
        }
    };

    return (
        <div className="p-4">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">{translations["personalize_header"][language]}</h2>
            <button
                onClick={() => setShowPersonalizePage(false)}
                className="mb-4 bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300 transition duration-200 ease-in-out"
            >
                {translations["back_to_meals_button"][language]}
            </button>
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md space-y-4">
                <div>
                    <label htmlFor="pName" className="block text-sm font-medium text-gray-700">
                        {translations["your_name_input"][language]}
                    </label>
                    <input
                        type="text"
                        id="pName"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        value={pName}
                        onChange={(e) => setPName(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="pPhone" className="block text-sm font-medium text-gray-700">
                        {translations["your_phone_input"][language]}
                    </label>
                    <input
                        type="tel"
                        id="pPhone"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        value={pPhone}
                        onChange={(e) => setPPhone(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="pMessage" className="block text-sm font-medium text-gray-700">
                        {translations["special_request_textarea"][language]}
                    </label>
                    <textarea
                        id="pMessage"
                        rows="4"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        value={pMessage}
                        onChange={(e) => setPMessage(e.target.value)}
                        required
                    ></textarea>
                </div>
                <button
                    type="submit"
                    className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                    {translations["submit_personalization_button"][language]}
                </button>
            </form>
        </div>
    );
};

const OrderHistory = () => {
    const { language, showNotification, user, setShowOrderHistory, adminMode } = useContext(AppContext);
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedOrder, setExpandedOrder] = useState(null);
    const [receiptContent, setReceiptContent] = useState('');
    const [showReceiptModal, setShowReceiptModal] = useState(false);

    useEffect(() => {
        const fetchOrders = async () => {
            if (user && user.email) {
                setLoading(true);
                try {
                    const data = await api.getUserOrders(user.email);
                    setOrders(data || []);
                } catch (error) {
                    console.error("Error fetching orders:", error);
                    showNotification("Failed to fetch order history.", 'error');
                    setOrders([]);
                } finally {
                    setLoading(false);
                }
            }
        };
        fetchOrders();
    }, [user, showNotification]);

    const handleUpdateStatus = async (orderId, newStatus) => {
        try {
            const response = await api.updateOrderStatus(orderId, newStatus);
            if (response.success) {
                showNotification(translations["status_updated_success"][language], 'success');
                // Re-fetch orders to update the list
                const data = await api.getUserOrders(user.email);
                setOrders(data || []);
            } else {
                showNotification(`Failed to update status: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error("Error updating status:", error);
            showNotification("An error occurred while updating status.", 'error');
        }
    };

    const handleViewReceipt = async (orderId) => {
        try {
            const data = await api.getOrderDetails(orderId);
            if (data.order && data.items) {
                setReceiptContent(generateReceiptContent(data.order, data.items));
                setShowReceiptModal(true);
            } else {
                showNotification("Could not load receipt details.", 'warning');
            }
        } catch (error) {
            console.error("Error loading receipt:", error);
            showNotification("Failed to load receipt.", 'error');
        }
    };

    return (
        <div className="p-4">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">{translations["order_history_header"][language]}</h2>
            <button
                onClick={() => setShowOrderHistory(false)}
                className="mb-4 bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300 transition duration-200 ease-in-out"
            >
                {translations["back_to_meals_button"][language]}
            </button>

            {loading ? (
                <p>Loading orders...</p>
            ) : orders.length === 0 ? (
                <p className="text-gray-600">{translations["no_past_orders"][language]}</p>
            ) : (
                <div className="space-y-4">
                    {orders.map((order) => (
                        <div key={order.order_id} className="bg-white rounded-lg shadow-md p-4">
                            <div className="flex justify-between items-center cursor-pointer" onClick={() => setExpandedOrder(expandedOrder === order.order_id ? null : order.order_id)}>
                                <h3 className="text-lg font-semibold text-gray-900">Order ID: {order.order_id.substring(0, 8)}...</h3>
                                <span className="text-sm text-gray-500">Status: {order.status}</span>
                            </div>
                            {expandedOrder === order.order_id && (
                                <div className="mt-4 border-t pt-4">
                                    <p className="text-gray-700"><strong>{translations["order_date_label"][language]}</strong> {new Date(order.order_date).toLocaleString()}</p>
                                    <p className="text-gray-700"><strong>{translations["total_amount_label_order"][language]}</strong> KES {order.total_amount.toFixed(2)}</p>
                                    {order.mpesa_receipt_number && <p className="text-gray-700"><strong>M-Pesa Receipt:</strong> {order.mpesa_receipt_number}</p>}
                                    {order.mpesa_transaction_date && <p className="text-gray-700"><strong>M-Pesa Date:</strong> {new Date(order.mpesa_transaction_date).toLocaleString()}</p>}

                                    {(order.personalization_name || order.personalization_message) && (
                                        <>
                                            <p className="text-gray-700 mt-2"><strong>{translations["personalization_details_label"][language]}</strong></p>
                                            {order.personalization_name && <p className="text-gray-700 text-sm">Name: {order.personalization_name}</p>}
                                            {order.personalization_phone && <p className="text-gray-700 text-sm">Phone: {order.personalization_phone}</p>}
                                            {order.personalization_message && <p className="text-gray-700 text-sm">Message: {order.personalization_message}</p>}
                                        </>
                                    )}

                                    <p className="text-gray-700 mt-2"><strong>{translations["items_ordered_label"][language]}</strong></p>
                                    <ul className="list-disc list-inside text-gray-700 text-sm">
                                        {order.items && order.items.map(item => ( // Assuming order.items is populated
                                            <li key={item.id}>{item.meal_name} x {item.quantity} @ KES {item.price_per_item.toFixed(2)}</li>
                                        ))}
                                    </ul>

                                    <button
                                        onClick={() => handleViewReceipt(order.order_id)}
                                        className="mt-4 bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 transition duration-200 ease-in-out"
                                    >
                                        {translations["view_receipt_button"][language]}
                                    </button>

                                    {/* Admin mode: Update status */}
                                    {user.role === "admin" && adminMode && (
                                        <div className="mt-4 pt-4 border-t border-gray-200">
                                            <h4 className="text-md font-semibold mb-2">Admin: Update Order Status</h4>
                                            <select
                                                value={order.status}
                                                onChange={(e) => handleUpdateStatus(order.order_id, e.target.value)}
                                                className="w-full p-2 border border-gray-300 rounded-md mb-2"
                                            >
                                                {['Pending Payment Confirmation', 'Paid', 'Processing', 'Ready', 'Delivered', 'Cancelled', 'Payment Failed'].map(status => (
                                                    <option key={status} value={status}>{status}</option>
                                                ))}
                                            </select>
                                            <button
                                                onClick={() => handleUpdateStatus(order.order_id, order.status)}
                                                className="w-full bg-yellow-500 text-white py-2 px-4 rounded-md hover:bg-yellow-600 transition duration-200 ease-in-out"
                                            >
                                                {translations["update_status_button"][language]}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {showReceiptModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full">
                        <h3 className="text-xl font-semibold mb-4">Your Order Receipt</h3>
                        <textarea
                            className="w-full h-64 border border-gray-300 rounded-md p-2 font-mono text-sm"
                            readOnly
                            value={receiptContent}
                        ></textarea>
                        <div className="mt-4 flex justify-end space-x-2">
                            <button
                                onClick={() => {
                                    const blob = new Blob([receiptContent], { type: 'text/plain' });
                                    const url = URL.createObjectURL(blob);
                                    const a = document.createElement('a');
                                    a.href = url;
                                    a.download = `receipt_${expandedOrder}.txt`;
                                    document.body.appendChild(a);
                                    a.click();
                                    document.body.removeChild(a);
                                    URL.revokeObjectURL(url);
                                }}
                                className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700"
                            >
                                {translations["download_receipt_button"][language]}
                            </button>
                            <button
                                onClick={() => setShowReceiptModal(false)}
                                className="bg-gray-300 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-400"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const TrackOrder = () => {
    const { language, showNotification, user, setShowTrackOrder, currentOrderId, setCurrentOrderId, adminMode } = useContext(AppContext);
    const [trackOrderIdInput, setTrackOrderIdInput] = useState(currentOrderId || '');
    const [trackedOrderDetails, setTrackedOrderDetails] = useState(null);
    const [trackedOrderItems, setTrackedOrderItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [receiptContent, setReceiptContent] = useState('');
    const [showReceiptModal, setShowReceiptModal] = useState(false);


    const handleTrackOrder = async () => {
        if (!trackOrderIdInput) {
            showNotification("Please enter an Order ID to track.", 'warning');
            setTrackedOrderDetails(null);
            setTrackedOrderItems([]);
            return;
        }

        setLoading(true);
        try {
            const data = await api.getOrderDetails(trackOrderIdInput);
            if (data.order && (data.order.user_email === user.email || user.role === "admin")) {
                setTrackedOrderDetails(data.order);
                setTrackedOrderItems(data.items || []);
                setCurrentOrderId(trackOrderIdInput); // Keep track of the last tracked ID
            } else {
                showNotification(translations["order_not_found"][language], 'warning');
                setTrackedOrderDetails(null);
                setTrackedOrderItems([]);
            }
        } catch (error) {
            console.error("Error tracking order:", error);
            showNotification("Failed to track order.", 'error');
            setTrackedOrderDetails(null);
            setTrackedOrderItems([]);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateStatus = async (orderId, newStatus) => {
        try {
            const response = await api.updateOrderStatus(orderId, newStatus);
            if (response.success) {
                showNotification(translations["status_updated_success"][language], 'success');
                // Re-fetch details for the currently tracked order
                await handleTrackOrder();
            } else {
                showNotification(`Failed to update status: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error("Error updating status:", error);
            showNotification("An error occurred while updating status.", 'error');
        }
    };

    const handleViewReceipt = async (orderId) => {
        try {
            const data = await api.getOrderDetails(orderId);
            if (data.order && data.items) {
                setReceiptContent(generateReceiptContent(data.order, data.items));
                setShowReceiptModal(true);
            } else {
                showNotification("Could not load receipt details.", 'warning');
            }
        } catch (error) {
            console.error("Error loading receipt:", error);
            showNotification("Failed to load receipt.", 'error');
        }
    };

    return (
        <div className="p-4">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">{translations["track_order_header"][language]}</h2>
            <button
                onClick={() => setShowTrackOrder(false)}
                className="mb-4 bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300 transition duration-200 ease-in-out"
            >
                {translations["back_to_meals_button"][language]}
            </button>

            <div className="bg-white p-6 rounded-lg shadow-md mb-6">
                <label htmlFor="trackOrderId" className="block text-sm font-medium text-gray-700 mb-2">
                    {translations["enter_order_id"][language]}
                </label>
                <div className="flex space-x-2">
                    <input
                        type="text"
                        id="trackOrderId"
                        className="flex-1 border border-gray-300 rounded-md shadow-sm p-2"
                        value={trackOrderIdInput}
                        onChange={(e) => setTrackOrderIdInput(e.target.value)}
                        placeholder="Enter Order ID"
                    />
                    <button
                        onClick={handleTrackOrder}
                        className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200 ease-in-out"
                        disabled={loading}
                    >
                        {loading ? 'Tracking...' : translations["track_button"][language]}
                    </button>
                </div>
            </div>

            {trackedOrderDetails && (
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-xl font-semibold mb-4 text-gray-900">Details for Order ID: {trackedOrderDetails.order_id.substring(0, 8)}...</h3>
                    <p className="text-gray-700"><strong>Status:</strong> {trackedOrderDetails.status}</p>
                    <p className="text-gray-700"><strong>Order Date:</strong> {new Date(trackedOrderDetails.order_date).toLocaleString()}</p>
                    <p className="text-gray-700"><strong>Total Amount:</strong> KES {trackedOrderDetails.total_amount.toFixed(2)}</p>
                    {trackedOrderDetails.mpesa_receipt_number && <p className="text-gray-700"><strong>M-Pesa Receipt:</strong> {trackedOrderDetails.mpesa_receipt_number}</p>}
                    {trackedOrderDetails.mpesa_transaction_date && <p className="text-gray-700"><strong>M-Pesa Date:</strong> {new Date(trackedOrderDetails.mpesa_transaction_date).toLocaleString()}</p>}

                    {(trackedOrderDetails.personalization_name || trackedOrderDetails.personalization_message) && (
                        <>
                            <p className="text-gray-700 mt-2"><strong>Personalization Details:</strong></p>
                            {trackedOrderDetails.personalization_name && <p className="text-gray-700 text-sm">Name: {trackedOrderDetails.personalization_name}</p>}
                            {trackedOrderDetails.personalization_phone && <p className="text-gray-700 text-sm">Phone: {trackedOrderDetails.personalization_phone}</p>}
                            {trackedOrderDetails.personalization_message && <p className="text-gray-700 text-sm">Message: {trackedOrderDetails.personalization_message}</p>}
                        </>
                    )}

                    <p className="text-gray-700 mt-2"><strong>Items Ordered:</strong></p>
                    <ul className="list-disc list-inside text-gray-700 text-sm">
                        {trackedOrderItems.map(item => (
                            <li key={item.id}>{item.meal_name} x {item.quantity} @ KES {item.price_per_item.toFixed(2)}</li>
                        ))}
                    </ul>

                    <button
                        onClick={() => handleViewReceipt(trackedOrderDetails.order_id)}
                        className="mt-4 bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 transition duration-200 ease-in-out"
                    >
                        {translations["view_receipt_button"][language]}
                    </button>

                    {/* Admin mode: Update status */}
                    {user.role === "admin" && adminMode && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                            <h4 className="text-md font-semibold mb-2">Admin: Update Order Status</h4>
                            <select
                                value={trackedOrderDetails.status}
                                onChange={(e) => handleUpdateStatus(trackedOrderDetails.order_id, e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded-md mb-2"
                            >
                                {['Pending Payment Confirmation', 'Paid', 'Processing', 'Ready', 'Delivered', 'Cancelled', 'Payment Failed'].map(status => (
                                    <option key={status} value={status}>{status}</option>
                                ))}
                            </select>
                            <button
                                onClick={() => handleUpdateStatus(trackedOrderDetails.order_id, trackedOrderDetails.status)}
                                className="w-full bg-yellow-500 text-white py-2 px-4 rounded-md hover:bg-yellow-600 transition duration-200 ease-in-out"
                            >
                                {translations["update_status_button"][language]}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {showReceiptModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full">
                        <h3 className="text-xl font-semibold mb-4">Your Order Receipt</h3>
                        <textarea
                            className="w-full h-64 border border-gray-300 rounded-md p-2 font-mono text-sm"
                            readOnly
                            value={receiptContent}
                        ></textarea>
                        <div className="mt-4 flex justify-end space-x-2">
                            <button
                                onClick={() => {
                                    const blob = new Blob([receiptContent], { type: 'text/plain' });
                                    const url = URL.createObjectURL(blob);
                                    const a = document.createElement('a');
                                    a.href = url;
                                    a.download = `receipt_${trackedOrderDetails.order_id}.txt`;
                                    document.body.appendChild(a);
                                    a.click();
                                    document.body.removeChild(a);
                                    URL.revokeObjectURL(url);
                                }}
                                className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700"
                            >
                                {translations["download_receipt_button"][language]}
                            </button>
                            <button
                                onClick={() => setShowReceiptModal(false)}
                                className="bg-gray-300 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-400"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};


const App = () => {
    // --- Auth State ---
    const [user, setUser] = useState(JSON.parse(sessionStorage.getItem('user')) || null); // Load user from session storage
    const [isAuthenticated, setIsAuthenticated] = useState(!!user);

    // --- App State ---
    const [cart, setCart] = useState(JSON.parse(sessionStorage.getItem('cart')) || []);
    const [mealsData, setMealsData] = useState(JSON.parse(sessionStorage.getItem('mealsData')) || initialMealsData);
    const [selectedLanguage, setSelectedLanguage] = useState(sessionStorage.getItem('selectedLanguage') || 'English');
    const [showPersonalizePage, setShowPersonalizePage] = useState(false);
    const [showOrderHistory, setShowOrderHistory] = useState(false);
    const [showTrackOrder, setShowTrackOrder] = useState(false);
    const [currentOrderId, setCurrentOrderId] = useState(sessionStorage.getItem('currentOrderId') || null);
    const [personalizationDetails, setPersonalizationDetails] = useState(JSON.parse(sessionStorage.getItem('personalizationDetails')) || {});
    const [adminMode, setAdminMode] = useState(false);
    const [notification, setNotification] = useState(null); // { message, type }

    // Persist state to session storage
    useEffect(() => {
        sessionStorage.setItem('user', JSON.stringify(user));
        setIsAuthenticated(!!user);
    }, [user]);

    useEffect(() => {
        sessionStorage.setItem('cart', JSON.stringify(cart));
    }, [cart]);

    useEffect(() => {
        sessionStorage.setItem('mealsData', JSON.stringify(mealsData));
    }, [mealsData]);

    useEffect(() => {
        sessionStorage.setItem('selectedLanguage', selectedLanguage);
    }, [selectedLanguage]);

    useEffect(() => {
        sessionStorage.setItem('currentOrderId', currentOrderId);
    }, [currentOrderId]);

    useEffect(() => {
        sessionStorage.setItem('personalizationDetails', JSON.stringify(personalizationDetails));
    }, [personalizationDetails]);

    // Notification handler
    const showNotification = (message, type = 'info') => {
        setNotification({ message, type });
        setTimeout(() => {
            setNotification(null);
        }, 5000); // Notification disappears after 5 seconds
    };

    // Auth functions
    const login = async (email, password) => {
        try {
            const data = await api.login(email, password);
            if (data.success) {
                setUser({ email: data.email, role: data.role });
                return true;
            } else {
                // If login fails, try to register
                const registerData = await api.register(email, password);
                if (registerData.success) {
                    setUser({ email: registerData.email, role: registerData.role });
                    return true;
                } else {
                    return false;
                }
            }
        } catch (error) {
            console.error("Auth error:", error);
            showNotification(`Authentication failed: ${error.message}`, 'error');
            return false;
        }
    };

    const logout = () => {
        setUser(null);
        setCart([]);
        setMealsData(initialMealsData); // Reset meals data on logout
        setSelectedLanguage('English');
        setShowPersonalizePage(false);
        setShowOrderHistory(false);
        setShowTrackOrder(false);
        setCurrentOrderId(null);
        setPersonalizationDetails({});
        setAdminMode(false);
        sessionStorage.clear(); // Clear all session storage on logout
        showNotification("Logged out successfully.", 'info');
    };

    const currentLanguage = translations[selectedLanguage] ? selectedLanguage : 'English';

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
            <AppContext.Provider value={{
                cart, setCart,
                mealsData, setMealsData,
                language: currentLanguage, setSelectedLanguage,
                showPersonalizePage, setShowPersonalizePage,
                showOrderHistory, setShowOrderHistory,
                showTrackOrder, setShowTrackOrder,
                currentOrderId, setCurrentOrderId,
                personalizationDetails, setPersonalizationDetails,
                adminMode, setAdminMode,
                showNotification,
                user, // Pass user from AuthContext directly to AppContext for convenience
            }}>
                <div className="flex h-screen font-inter">
                    {/* Sidebar */}
                    <div className="w-1/4 bg-gray-800 text-white p-6 flex flex-col rounded-r-lg shadow-lg">
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold mb-4">🌐 Choose Language</h2>
                            <select
                                value={selectedLanguage}
                                onChange={(e) => setSelectedLanguage(e.target.value)}
                                className="w-full p-2 rounded-md bg-gray-700 border border-gray-600 text-white"
                            >
                                {Object.keys(translations.welcome_title).map(lang => (
                                    <option key={lang} value={lang}>{lang}</option>
                                ))}
                            </select>
                        </div>

                        <hr className="border-gray-700 my-4" />

                        <h2 className="text-xl font-bold mb-4">{translations["total_cost_label"][currentLanguage]}</h2>
                        <div className="mb-6">
                            <p className="text-3xl font-extrabold text-green-400">
                                KES {cart.reduce((sum, item) => sum + item.price * item.quantity, 0).toFixed(2)}
                            </p>
                            <p className="text-lg mt-2">{translations["items_in_cart_label"][currentLanguage]}</p>
                            <ul className="space-y-2 max-h-60 overflow-y-auto pr-2">
                                {cart.length === 0 ? (
                                    <p className="text-gray-400 text-sm">{translations["please_select_dish"][currentLanguage]}</p>
                                ) : (
                                    cart.map((item, index) => (
                                        <li key={item.id} className="flex items-center justify-between bg-gray-700 p-2 rounded-md">
                                            <span className="text-sm">{item.name}</span>
                                            <div className="flex items-center space-x-2">
                                                <input
                                                    type="number"
                                                    min="0"
                                                    max={mealsData.find(m => m.id === item.id)?.stock + item.quantity || 10}
                                                    value={item.quantity}
                                                    onChange={(e) => {
                                                        const newQty = parseInt(e.target.value, 10);
                                                        const itemToUpdate = cart[index];
                                                        const oldQty = itemToUpdate.quantity;

                                                        const updatedCart = [...cart];
                                                        if (newQty === 0) {
                                                            updatedCart.splice(index, 1);
                                                        } else {
                                                            updatedCart[index] = { ...itemToUpdate, quantity: newQty };
                                                        }

                                                        const updatedMealsData = mealsData.map(meal => {
                                                            if (meal.id === itemToUpdate.id) {
                                                                const stockChange = oldQty - newQty;
                                                                return { ...meal, stock: meal.stock + stockChange };
                                                            }
                                                            return meal;
                                                        });

                                                        setCart(updatedCart.filter(i => i.quantity > 0));
                                                        setMealsData(updatedMealsData);
                                                    }}
                                                    className="w-12 p-1 bg-gray-600 border border-gray-500 rounded-md text-center text-white text-xs"
                                                />
                                                <button
                                                    onClick={() => {
                                                        const itemToRemove = cart[index];
                                                        const updatedCart = [...cart];
                                                        updatedCart.splice(index, 1);

                                                        const updatedMealsData = mealsData.map(meal => {
                                                            if (meal.id === itemToRemove.id) {
                                                                return { ...meal, stock: meal.stock + itemToRemove.quantity };
                                                            }
                                                            return meal;
                                                        });
                                                        setCart(updatedCart);
                                                        setMealsData(updatedMealsData);
                                                    }}
                                                    className="bg-red-500 text-white p-1 rounded-md hover:bg-red-600 text-xs"
                                                >
                                                    🗑️
                                                </button>
                                            </div>
                                        </li>
                                    ))
                                )}
                            </ul>
                        </div>

                        <hr className="border-gray-700 my-4" />

                        {isAuthenticated && (
                            <div className="space-y-3">
                                <button
                                    onClick={() => {
                                        setShowTrackOrder(true);
                                        setShowOrderHistory(false);
                                        setShowPersonalizePage(false);
                                    }}
                                    className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-200 ease-in-out"
                                >
                                    {translations["track_order_button"][currentLanguage]}
                                </button>
                                <button
                                    onClick={() => {
                                        setShowOrderHistory(true);
                                        setShowTrackOrder(false);
                                        setShowPersonalizePage(false);
                                    }}
                                    className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 transition duration-200 ease-in-out"
                                >
                                    {translations["view_history_button"][currentLanguage]}
                                </button>
                                {user && user.role === "admin" && (
                                    <>
                                        <label className="flex items-center space-x-2 text-white mt-4">
                                            <input
                                                type="checkbox"
                                                checked={adminMode}
                                                onChange={(e) => setAdminMode(e.target.checked)}
                                                className="form-checkbox h-5 w-5 text-blue-600 rounded"
                                            />
                                            <span>{translations["admin_mode_checkbox"][currentLanguage]}</span>
                                        </label>
                                        <a
                                            href={process.env.REACT_APP_ANALYTICS_DASHBOARD_URL || '#'}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="w-full block text-center bg-teal-600 text-white py-2 px-4 rounded-md hover:bg-teal-700 transition duration-200 ease-in-out"
                                        >
                                            {translations["analytics_dashboard_button"][currentLanguage]}
                                        </a>
                                    </>
                                )}
                                <button
                                    onClick={logout}
                                    className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition duration-200 ease-in-out mt-4"
                                >
                                    Logout
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Main Content */}
                    <div className="flex-1 p-8 bg-gray-50 overflow-y-auto">
                        <h1 className="text-4xl font-extrabold mb-8 text-gray-900 text-center">
                            {translations["welcome_title"][currentLanguage]}
                        </h1>

                        {!isAuthenticated ? (
                            <LoginRegister />
                        ) : showPersonalizePage ? (
                            <PersonalizeMeal />
                        ) : showOrderHistory ? (
                            <OrderHistory />
                        ) : showTrackOrder ? (
                            <TrackOrder />
                        ) : (
                            <MealList />
                        )}
                    </div>

                    {notification && (
                        <Notification
                            message={notification.message}
                            type={notification.type}
                            onClose={() => setNotification(null)}
                        />
                    )}
                </div>
            </AppContext.Provider>
        </AuthContext.Provider>
    );
};

export default App;