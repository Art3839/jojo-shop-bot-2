from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

def main_menu(is_admin=False):
    if is_admin:
        return ReplyKeyboardMarkup([
            ["➕ Добавить товар", "✏️ Редактировать товары"],
            ["📊 Статистика", "📦 Заказы"],
            ["👥 Пользователи", "📢 Рассылка"],
            ["🏠 Главное меню"]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ["🛍 Каталог", "🛒 Корзина"],
            ["📦 Мои заказы", "👤 Профиль"],
            ["💳 Оплата", "📞 Поддержка"]
        ], resize_keyboard=True)

def category_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎭 Фигурки", callback_data="cat_figures")],
        [InlineKeyboardButton("👕 Одежда", callback_data="cat_clothes")],
        [InlineKeyboardButton("💍 Аксессуары", callback_data="cat_accessories")],
        [InlineKeyboardButton("📚 Манга", callback_data="cat_manga")],
        [InlineKeyboardButton("🎮 Игры", callback_data="cat_games")],
        [InlineKeyboardButton("🏠 « Назад", callback_data="back_to_main")]
    ])

def product_keyboard(product_id, quantity_in_cart=0):
    buttons = [
        [InlineKeyboardButton("🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_id}")],
        [InlineKeyboardButton("⭐ В избранное", callback_data=f"favorite_{product_id}")],
    ]
    
    if quantity_in_cart > 0:
        buttons.append([InlineKeyboardButton(f"✅ В корзине: {quantity_in_cart} шт.", callback_data="already_in_cart")])
    
    buttons.append([InlineKeyboardButton("🏠 « Назад", callback_data="back_to_catalog")])
    return InlineKeyboardMarkup(buttons)

def cart_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton("🗑 Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton("🏠 « Назад", callback_data="back_to_main")]
    ])

def checkout_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить", callback_data="pay_order")],
        [InlineKeyboardButton("📱 Ввести данные", callback_data="enter_data")],
        [InlineKeyboardButton("🏠 « Назад", callback_data="back_to_cart")]
    ])

def admin_orders_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Все заказы", callback_data="admin_all_orders")],
        [InlineKeyboardButton("🔍 Поиск заказа", callback_data="admin_search_order")],
        [InlineKeyboardButton("🏠 « Назад", callback_data="back_to_admin")]
    ])

def cancel_keyboard():
    return ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)

# НОВЫЕ КЛАВИАТУРЫ ДЛЯ РЕДАКТИРОВАНИЯ
def admin_edit_products_keyboard(products):
    buttons = []
    for product in products:
        buttons.append([InlineKeyboardButton(
            f"✏️ {product['name']} ({product['price']} руб.)", 
            callback_data=f"edit_product_{product['id']}"
        )])
    buttons.append([InlineKeyboardButton("🏠 « Назад", callback_data="back_to_admin")])
    return InlineKeyboardMarkup(buttons)

def product_edit_keyboard(product_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Изменить название", callback_data=f"edit_name_{product_id}")],
        [InlineKeyboardButton("📝 Изменить описание", callback_data=f"edit_desc_{product_id}")],
        [InlineKeyboardButton("💰 Изменить цену", callback_data=f"edit_price_{product_id}")],
        [InlineKeyboardButton("📁 Изменить категорию", callback_data=f"edit_category_{product_id}")],
        [InlineKeyboardButton("🖼 Изменить изображение", callback_data=f"edit_image_{product_id}")],
        [InlineKeyboardButton("🗑 Удалить товар", callback_data=f"delete_product_{product_id}")],
        [InlineKeyboardButton("🏠 « Назад", callback_data="admin_edit_menu")]
    ])

def confirm_delete_keyboard(product_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{product_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"edit_product_{product_id}")]
    ])
