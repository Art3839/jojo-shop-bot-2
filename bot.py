import asyncio
import logging
import sys

# Фикс для Python 3.11+ на Raspberry Pi
if sys.version_info >= (3, 11):
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import TELEGRAM_TOKEN, is_admin, ADMIN_USER_IDS, ADMIN_CHAT_ID
from database import init_db, get_products, get_product, add_to_cart, get_user_cart, clear_cart, create_order, add_order_items, save_user_info, get_user_info, get_user_orders, add_product, get_all_users, get_statistics, get_all_products, update_product, delete_product
from keyboards import main_menu, category_menu, product_keyboard, cart_keyboard, checkout_keyboard, admin_orders_keyboard, cancel_keyboard, admin_edit_products_keyboard, product_edit_keyboard, confirm_delete_keyboard
from payment import create_payment_stub

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальное состояние пользователей
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await save_user_info(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    is_user_admin = is_admin(user.id)
    
    welcome_text = f"🌟 Добро пожаловать в JoJo Shop, {user.first_name}!\n"
    welcome_text += "Здесь ты найдешь лучшие товары по аниме JoJo's Bizarre Adventure!"
    
    if is_user_admin:
        welcome_text = "👑 Добро пожаловать в админ-панель JoJo Shop!"
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu(is_user_admin)
    )

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 Выберите категорию:", reply_markup=category_menu())

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Пока показываем все товары
    products = await get_products()
    
    if not products:
        await query.message.reply_text("😔 Каталог пуст")
        return
    
    # Получаем корзину пользователя для отображения количества
    user_cart = await get_user_cart(query.from_user.id)
    cart_dict = {item['product_id']: item['quantity'] for item in user_cart}
    
    for product in products:
        text = f"✨ <b>{product['name']}</b>\n"
        text += f"💰 Цена: {product['price']} руб.\n"
        text += f"📁 Категория: {product['category']}\n"
        text += f"📝 {product['description']}"
        
        quantity_in_cart = cart_dict.get(product['id'], 0)
        keyboard = product_keyboard(product['id'], quantity_in_cart)
        
        if product['image_path']:
            try:
                await query.message.reply_photo(
                    photo=open(product['image_path'], 'rb'),
                    caption=text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            except:
                await query.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)
        else:
            await query.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart_items = await get_user_cart(user_id)
    
    if not cart_items:
        await update.message.reply_text("🛒 Ваша корзина пуста")
        return
    
    total = 0
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    
    for item in cart_items:
        item_total = item['price'] * item['quantity']
        text += f"📦 {item['name']} x{item['quantity']} = {item_total} руб.\n"
        total += item_total
    
    text += f"\n<b>ИТОГО: {total} руб.</b>"
    
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=cart_keyboard())

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    orders = await get_user_orders(user_id)
    
    if not orders:
        await update.message.reply_text("📦 У вас пока нет заказов")
        return
    
    text = "📦 <b>Ваши заказы:</b>\n\n"
    for order in orders:
        text += f"🆔 Заказ #{order['id']}\n"
        text += f"💰 Сумма: {order['total_amount']} руб.\n"
        text += f"📅 Дата: {order['created_at']}\n"
        text += f"📊 Статус: {order['status']}\n\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = await get_user_info(user.id)
    
    text = f"👤 <b>Ваш профиль:</b>\n"
    text += f"🆔 ID: {user.id}\n"
    text += f"👤 Имя: {user.first_name}\n"
    if user.last_name:
        text += f"👥 Фамилия: {user.last_name}\n"
    if user.username:
        text += f"🏷 Username: @{user.username}\n"
    
    if user_info:
        if user_info['phone']:
            text += f"📱 Телефон: {user_info['phone']}\n"
        if user_info['address']:
            text += f"🏠 Адрес: {user_info['address']}\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📞 <b>Поддержка JoJo Shop:</b>\n\n"
    text += "Если у вас есть вопросы или проблемы с заказом:\n"
    text += "• Напишите администратору\n"
    text += "• Опишите проблему подробно\n"
    text += "• Приложите скриншоты если нужно\n\n"
    text += "⏰ Время ответа: в течение 24 часов"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('add_to_cart_'):
        product_id = int(query.data.split('_')[-1])
        await add_to_cart(query.from_user.id, product_id)
        await query.message.reply_text("✅ Товар добавлен в корзину!")
        
    elif query.data == 'back_to_main':
        is_user_admin = is_admin(query.from_user.id)
        await query.message.reply_text("🏠 Главное меню", reply_markup=main_menu(is_user_admin))
        
    elif query.data == 'back_to_catalog':
        await show_products(update, context)
        
    elif query.data == 'checkout':
        await query.message.reply_text("📦 Оформление заказа", reply_markup=checkout_keyboard())
        
    elif query.data == 'pay_order':
        # Здесь будет логика оплаты
        cart_items = await get_user_cart(query.from_user.id)
        if not cart_items:
            await query.message.reply_text("🛒 Корзина пуста")
            return
            
        total = sum(item['price'] * item['quantity'] for item in cart_items)
        payment_url, payment_id = create_payment_stub(total, "Заказ в JoJo Shop", query.from_user.id)
        
        # Создаем заказ в БД
        order_id = await create_order(query.from_user.id, total, payment_id)
        
        # Сохраняем элементы заказа
        order_items = [
            {
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'price': item['price']
            }
            for item in cart_items
        ]
        await add_order_items(order_id, order_items)
        
        # Очищаем корзину
        await clear_cart(query.from_user.id)
        
        text = f"💳 <b>Оплата заказа #{order_id}</b>\n\n"
        text += f"💰 Сумма к оплате: {total} руб.\n\n"
        text += "Нажмите кнопку ниже для перехода к оплате:"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Перейти к оплате", url=payment_url)],
            [InlineKeyboardButton("🏠 « Назад", callback_data="back_to_main")]
        ])
        
        await query.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)
        
    elif query.data.startswith('cat_'):
        category = query.data.split('_')[1]
        await query.message.reply_text(f"Категория: {category}")
        
    elif query.data == 'clear_cart':
        await clear_cart(query.from_user.id)
        await query.message.reply_text("🗑 Корзина очищена")
        
    elif query.data == 'back_to_cart':
        await show_cart(query, context)
        
    elif query.data == 'back_to_admin':
        await query.message.reply_text("👑 Админ-панель", reply_markup=main_menu(True))

# Админские функции
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Доступ запрещен")
        return
        
    await update.message.reply_text("👑 Админ-панель JoJo Shop", reply_markup=main_menu(True))

async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
        
    user_states[update.effective_user.id] = 'adding_product'
    await update.message.reply_text(
        "➕ Добавление нового товара\n\n"
        "Введите данные в формате:\n"
        "Название|Описание|Цена|Категория|Путь к изображению (опционально)\n\n"
        "Пример:\n"
        "Фигурка Dio|Эпичная фигурка|1999|Фигурки|data/images/dio.jpg",
        reply_markup=cancel_keyboard()
    )

async def handle_product_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
        
    if user_id in user_states and user_states[user_id] == 'adding_product':
        if update.message.text == "❌ Отмена":
            user_states.pop(user_id, None)
            await update.message.reply_text("❌ Добавление товара отменено", reply_markup=main_menu(True))
            return
            
        try:
            parts = update.message.text.split('|')
            if len(parts) < 4:
                raise ValueError("Недостаточно параметров")
                
            name = parts[0].strip()
            description = parts[1].strip()
            price = int(parts[2].strip())
            category = parts[3].strip()
            image_path = parts[4].strip() if len(parts) > 4 else None
            
            product_id = await add_product(name, description, price, category, image_path)
            
            user_states.pop(user_id, None)
            await update.message.reply_text(
                f"✅ Товар успешно добавлен!\nID: {product_id}\nНазвание: {name}",
                reply_markup=main_menu(True)
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}\nПопробуйте ещё раз или нажмите 'Отмена'")

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
        
    stats = await get_statistics()
    
    text = "📊 <b>Статистика магазина:</b>\n\n"
    text += f"👥 Пользователей: {stats['users_count']}\n"
    text += f"📦 Заказов: {stats['orders_count']}\n"
    text += f"💰 Доход: {stats['total_revenue']} руб.\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
        
    users = await get_all_users()
    
    if not users:
        await update.message.reply_text("👥 Пользователей пока нет")
        return
    
    text = f"👥 <b>Все пользователи ({len(users)}):</b>\n\n"
    for user in users[-10:]:  # Показываем последние 10
        text += f"🆔 {user['user_id']} - {user['first_name']}"
        if user['username']:
            text += f" (@{user['username']})"
        text += "\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
        
    user_states[update.effective_user.id] = 'broadcast'
    await update.message.reply_text(
        "📢 Рассылка сообщения всем пользователям\n\n"
        "Введите текст сообщения для рассылки:",
        reply_markup=cancel_keyboard()
    )

async def handle_broadcast_input(update: Update, context: Application):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
        
    if user_id in user_states and user_states[user_id] == 'broadcast':
        if update.message.text == "❌ Отмена":
            user_states.pop(user_id, None)
            await update.message.reply_text("❌ Рассылка отменена", reply_markup=main_menu(True))
            return
            
        # Получаем всех пользователей
        users = await get_all_users()
        success_count = 0
        fail_count = 0
        
        message_text = update.message.text
        
        # Отправляем сообщение всем пользователям
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 <b>Сообщение от JoJo Shop:</b>\n\n{message_text}",
                    parse_mode='HTML'
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user['user_id']}: {e}")
                fail_count += 1
        
        user_states.pop(user_id, None)
        await update.message.reply_text(
            f"✅ Рассылка завершена!\n"
            f"Успешно: {success_count}\n"
            f"Ошибок: {fail_count}",
            reply_markup=main_menu(True)
        )

# НОВЫЕ ФУНКЦИИ ДЛЯ РЕДАКТИРОВАНИЯ ТОВАРОВ
# Показать меню редактирования товаров
async def edit_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
        
    products = await get_all_products()
    
    if not products:
        await update.message.reply_text("📦 Товары отсутствуют")
        return
    
    text = "✏️ <b>Редактирование товаров:</b>\n\n"
    text += "Выберите товар для редактирования:"
    
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=admin_edit_products_keyboard(products))

# Показать меню редактирования конкретного товара
async def edit_product_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    product_id = int(query.data.split('_')[-1])
    product = await get_product(product_id)
    
    if not product:
        await query.message.reply_text("❌ Товар не найден")
        return
    
    text = f"✏️ <b>Редактирование товара:</b>\n\n"
    text += f"🆔 ID: {product['id']}\n"
    text += f"🏷 Название: {product['name']}\n"
    text += f"💰 Цена: {product['price']} руб.\n"
    text += f"📁 Категория: {product['category']}\n"
    text += f"📝 Описание: {product['description']}\n"
    if product['image_path']:
        text += f"🖼 Изображение: {product['image_path']}\n"
    
    await query.message.reply_text(text, parse_mode='HTML', reply_markup=product_edit_keyboard(product_id))

# Начать редактирование поля
async def start_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    parts = query.data.split('_')
    field = parts[1]  # name, desc, price, category, image
    product_id = int(parts[2])
    
    field_names = {
        'name': 'название',
        'desc': 'описание',
        'price': 'цену',
        'category': 'категорию',
        'image': 'путь к изображению'
    }
    
    user_states[query.from_user.id] = {
        'state': f'editing_{field}',
        'product_id': product_id,
        'field': field
    }
    
    await query.message.reply_text(
        f"📝 Введите новое {field_names.get(field, field)} товара:",
        reply_markup=cancel_keyboard()
    )

# Обработать ввод нового значения
async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if user_id not in user_states or not isinstance(user_states[user_id], dict):
        return
    
    state_info = user_states[user_id]
    if not state_info.get('state', '').startswith('editing_'):
        return
    
    if update.message.text == "❌ Отмена":
        user_states.pop(user_id, None)
        await update.message.reply_text("❌ Редактирование отменено", reply_markup=main_menu(True))
        return
    
    field = state_info['field']
    product_id = state_info['product_id']
    new_value = update.message.text
    
    # Обновляем соответствующее поле
    update_fields = {}
    if field == 'name':
        update_fields['name'] = new_value
    elif field == 'desc':
        update_fields['description'] = new_value
    elif field == 'price':
        try:
            update_fields['price'] = int(new_value)
        except ValueError:
            await update.message.reply_text("❌ Цена должна быть числом. Попробуйте ещё раз:")
            return
    elif field == 'category':
        update_fields['category'] = new_value
    elif field == 'image':
        update_fields['image_path'] = new_value
    
    success = await update_product(product_id, **update_fields)
    
    if success:
        user_states.pop(user_id, None)
        await update.message.reply_text(
            "✅ Товар успешно обновлён!",
            reply_markup=main_menu(True)
        )
    else:
        await update.message.reply_text("❌ Ошибка при обновлении товара. Попробуйте ещё раз.")

# Удаление товара
async def delete_product_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    product_id = int(query.data.split('_')[-1])
    product = await get_product(product_id)
    
    if not product:
        await query.message.reply_text("❌ Товар не найден")
        return
    
    text = f"⚠️ <b>Подтвердите удаление товара:</b>\n\n"
    text += f"🏷 {product['name']}\n"
    text += f"💰 {product['price']} руб.\n\n"
    text += "Товар будет скрыт из каталога, но останется в базе данных."
    
    await query.message.reply_text(
        text, 
        parse_mode='HTML', 
        reply_markup=confirm_delete_keyboard(product_id)
    )

# Подтверждение удаления
async def confirm_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    product_id = int(query.data.split('_')[-1])
    
    success = await delete_product(product_id)
    
    if success:
        await query.message.reply_text(
            "✅ Товар удалён (скрыт)!",
            reply_markup=main_menu(True)
        )
    else:
        await query.message.reply_text(
            "❌ Ошибка при удалении товара",
            reply_markup=main_menu(True)
        )

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверяем, находится ли пользователь в состоянии редактирования
    if user_id in user_states:
        state = user_states[user_id]
        if isinstance(state, dict) and state.get('state', '').startswith('editing_'):
            await handle_edit_input(update, context)
            return
        elif isinstance(state, str):
            # Старая система состояний (добавление товара, рассылка)
            if state == 'adding_product':
                await handle_product_input(update, context)
                return
            elif state == 'broadcast':
                await handle_broadcast_input(update, context.application)
                return
    
    await update.message.reply_text("❓ Неизвестная команда. Используйте меню для навигации.")

def main():
    # Инициализация базы данных
    asyncio.run(init_db())
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики текстовых сообщений
    application.add_handler(MessageHandler(filters.Regex("🛍 Каталог"), show_catalog))
    application.add_handler(MessageHandler(filters.Regex("🛒 Корзина"), show_cart))
    application.add_handler(MessageHandler(filters.Regex("📦 Мои заказы"), show_orders))
    application.add_handler(MessageHandler(filters.Regex("👤 Профиль"), show_profile))
    application.add_handler(MessageHandler(filters.Regex("📞 Поддержка"), support))
    application.add_handler(MessageHandler(filters.Regex("🏠 Главное меню"), start))
    
    # Админские функции
    application.add_handler(MessageHandler(filters.Regex("➕ Добавить товар"), add_product_start))
    application.add_handler(MessageHandler(filters.Regex("📊 Статистика"), show_statistics))
    application.add_handler(MessageHandler(filters.Regex("👥 Пользователи"), show_users))
    application.add_handler(MessageHandler(filters.Regex("📢 Рассылка"), broadcast_start))
    application.add_handler(MessageHandler(filters.Regex("👑 Админ-панель"), admin_panel))
    
    # НОВЫЕ АДМИНСКИЕ ФУНКЦИИ
    application.add_handler(MessageHandler(filters.Regex("✏️ Редактировать товары"), edit_products_menu))
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # НОВЫЕ CALLBACK ОБРАБОТЧИКИ
    application.add_handler(CallbackQueryHandler(edit_product_menu, pattern=r'^edit_product_\d+$'))
    application.add_handler(CallbackQueryHandler(start_edit_field, pattern=r'^edit_(name|desc|price|category|image)_\d+$'))
    application.add_handler(CallbackQueryHandler(delete_product_confirm, pattern=r'^delete_product_\d+$'))
    application.add_handler(CallbackQueryHandler(confirm_delete_product, pattern=r'^confirm_delete_\d+$'))
    application.add_handler(CallbackQueryHandler(lambda u, c: edit_products_menu(u, c), pattern=r'^admin_edit_menu$'))
    
    # Обработчик всех текстовых сообщений (для состояний)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command))
    
    # Запуск бота
    print("🤖 JoJo Shop Bot запущен!")
    print("Для остановки нажмите Ctrl+C")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    main()
