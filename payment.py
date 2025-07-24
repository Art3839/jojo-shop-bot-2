# Пока заглушка, можно расширить интеграцией с ЮKassa
def create_payment_stub(amount, description, user_id):
    # Здесь будет интеграция с платежной системой
    payment_url = "https://example.com/payment"  # Заглушка
    payment_id = "payment_12345"  # Заглушка
    return payment_url, payment_id

# Реальная интеграция с ЮKassa (раскомментируйте при необходимости)
"""
from yookassa import Payment, Configuration
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
import uuid

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

def create_payment(amount, description, user_id, return_url="https://t.me/your_bot"):
    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": user_id
        }
    })
    return payment.confirmation.confirmation_url, payment.id
"""
