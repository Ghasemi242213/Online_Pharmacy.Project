import mysql.connector
from config import db_config

def get_connection():
    """ایجاد اتصال به پایگاه داده"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"❌ خطا در اتصال به دیتابیس: {err}")
        return None

def get_all_products():
    """دریافت همه محصولات"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM PRODUCT ORDER BY ID DESC"
        cursor.execute(query)
        products = cursor.fetchall()
        cursor.close()
        conn.close()
    
        formatted_products = []
        for product in products:
            formatted_products.append({
                'id': product['ID'],
                'name': product['NAME'],
                'desc': product['DESCRIPTION'] or 'بدون توضیح',
                'price': f"{int(product['PRICE']):,} تومان",
                'inventory': product['INVENTORY'],
                'image': product['TELEGRAM_FILE_ID'] or None
            })
        
        print(f"✅ {len(formatted_products)} محصول از دیتابیس خوانده شد")
        return formatted_products
    except mysql.connector.Error as err:
        print(f"❌ خطا در دریافت محصولات: {err}")
        conn.close()
        return []

def get_product_by_id(product_id):
    """دریافت محصول بر اساس ID"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM PRODUCT WHERE ID = %s"
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if product:
            return {
                'id': product['ID'],
                'name': product['NAME'],
                'desc': product['DESCRIPTION'] or '',
                'price': f"{int(product['PRICE']):,} تومان",
                'inventory': product['INVENTORY'],
                'image': product['TELEGRAM_FILE_ID']
            }
        return None
    except mysql.connector.Error as err:
        print(f"❌ خطا در دریافت محصول: {err}")
        conn.close()
        return None

def get_cart_items(telegram_id):
    """دریافت آیتم‌های سبد خرید کاربر"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT 
            p.ID as product_id,
            p.NAME,
            p.DESCRIPTION,
            p.PRICE,
            p.TELEGRAM_FILE_ID as image,
            c.QUANTITY
        FROM CART c
        JOIN PRODUCT p ON c.PRODUCT_ID = p.ID
        WHERE c.CUSTOMER_CID = (SELECT CID FROM CUSTOMER WHERE TELEGRAM_ID = %s)
        """
        cursor.execute(query, (telegram_id,))
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"✅ {len(items)} آیتم از سبد کاربر {telegram_id} خوانده شد")
        return items
    except mysql.connector.Error as err:
        print(f"❌ خطا در دریافت سبد خرید: {err}")
        conn.close()
        return []

def get_user(telegram_id):
    """دریافت اطلاعات کاربر"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM CUSTOMER WHERE TELEGRAM_ID = %s"
        cursor.execute(query, (telegram_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except mysql.connector.Error as err:
        print(f"❌ خطا در دریافت کاربر: {err}")
        conn.close()
        return None