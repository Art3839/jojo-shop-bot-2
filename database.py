import aiosqlite
import asyncio
import os
from config import DATABASE_PATH

async def init_db():
    # Создаем папку data если её нет
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Таблица товаров
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                category TEXT,
                image_path TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица корзины
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, product_id)
            )
        ''')
        
        # Таблица заказов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_amount INTEGER,
                status TEXT DEFAULT 'pending',
                payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица элементов заказа
        await db.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                price INTEGER,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        await db.commit()
        print("✅ База данных инициализирована")

async def get_products(category=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if category:
            async with db.execute('SELECT * FROM products WHERE is_active = 1 AND category = ?', (category,)) as cursor:
                return await cursor.fetchall()
        else:
            async with db.execute('SELECT * FROM products WHERE is_active = 1') as cursor:
                return await cursor.fetchall()

async def get_product(product_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM products WHERE id = ?', (product_id,)) as cursor:
            return await cursor.fetchone()

async def add_product(name, description, price, category, image_path=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO products (name, description, price, category, image_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, price, category, image_path))
        await db.commit()
        return cursor.lastrowid

async def get_user_cart(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT c.product_id, c.quantity, p.name, p.price, p.image_path
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,)) as cursor:
            return await cursor.fetchall()

async def add_to_cart(user_id, product_id, quantity=1):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Проверяем существование записи
        async with db.execute('''
            SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?
        ''', (user_id, product_id)) as cursor:
            row = await cursor.fetchone()
            
        if row:
            new_quantity = row[0] + quantity
            await db.execute('''
                UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?
            ''', (new_quantity, user_id, product_id))
        else:
            await db.execute('''
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            ''', (user_id, product_id, quantity))
        await db.commit()

async def remove_from_cart(user_id, product_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        await db.commit()

async def clear_cart(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await db.commit()

async def create_order(user_id, total_amount, payment_id=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO orders (user_id, total_amount, payment_id)
            VALUES (?, ?, ?)
        ''', (user_id, total_amount, payment_id))
        order_id = cursor.lastrowid
        await db.commit()
        return order_id

async def add_order_items(order_id, items):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for item in items:
            await db.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['quantity'], item['price']))
        await db.commit()

async def get_user_orders(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,)) as cursor:
            return await cursor.fetchall()

async def save_user_info(user_id, username=None, first_name=None, last_name=None, phone=None, address=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, phone, address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, phone, address))
        await db.commit()

async def get_user_info(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def get_all_users():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users') as cursor:
            return await cursor.fetchall()

async def get_statistics():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        stats = {}
        
        # Количество пользователей
        async with db.execute('SELECT COUNT(*) as count FROM users') as cursor:
            row = await cursor.fetchone()
            stats['users_count'] = row['count']
        
        # Количество заказов
        async with db.execute('SELECT COUNT(*) as count FROM orders') as cursor:
            row = await cursor.fetchone()
            stats['orders_count'] = row['count']
        
        # Общая сумма заказов
        async with db.execute('SELECT SUM(total_amount) as total FROM orders WHERE status = "paid"') as cursor:
            row = await cursor.fetchone()
            stats['total_revenue'] = row['total'] or 0
            
        return stats
