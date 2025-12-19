import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.util import antiflood
import os
import time
from config import *
from DML import *
from DQL import *
from text import texts
import logging
logging.basicConfig(filename='logs/project.log', format='%(asctime)s - %(levelname)s - %(message)s')
os.makedirs('logs/Data', exist_ok=True)
bot = telebot.TeleBot(API_TOKEN)
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            print(f'{m.chat.first_name} [{str(m.chat.id)}]: {m.text}')
        elif m.content_type == 'photo':
            print(f'{m.chat.first_name} [{str(m.chat.id)}]: sent photo')
            
bot.set_update_listener(listener)

all_products = []
user_baskets = {}
user_data = {}
payment_data = {}
info_data = {}
known_users = []
user_current_page = {}

def insert_user_data(cid, name, username=None, phone=None, address=None):
    return insert_user(cid, name, username, phone, address)

def send_message(cid, text, reply_markup=None):
    try:
        return antiflood(bot.send_message, cid, text, reply_markup=reply_markup)
    except:
        return None

def check_user(cid):
    if cid not in known_users:
        try:
            info = bot.get_chat(cid)
            if insert_user_data(cid, info.first_name, username=info.username):
                known_users.append(cid)
        except:
            pass
    return True

def load_products_from_db():
    global all_products
    all_products = get_all_products()

def main_menu(cid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(texts["show_products"], texts["basket"])
    kb.add(texts["info"], texts["support"])
    if cid in admins:
        kb.add(texts["admin"])
    send_message(cid, "به داروخانه خوش آمدید 🌿", reply_markup=kb)

@bot.message_handler(commands=['start'])
def start_command(message):
    cid = message.chat.id
    check_user(cid)
    load_products_from_db()
    main_menu(cid)
@bot.message_handler(func=lambda m: m.text == "💳 پرداخت")
def payment(message):
    cid = message.chat.id
    cart_items = get_cart_items(cid)
    
    if not cart_items:
        send_message(cid, "❌ سبد خرید شما خالی است")
        return
    
    total_price = 0
    basket_items = []
    
    for item in cart_items:
        quantity = item['QUANTITY']
        price = float(item['PRICE'])
        item_total = price * quantity
        total_price += item_total
        basket_items.append(f"📦 {item['NAME']}: {quantity} × {int(price):,} = {int(item_total):,} تومان")
    
    payment_data[cid] = {
        'step': 'card_number', 
        'total_price': total_price,
        'basket_items': basket_items
    }
    
    text = "💳 اطلاعات پرداخت\n\n"
    for item in basket_items:
        text += f"{item}\n"
    
    text += f"\n💰 مبلغ قابل پرداخت: {int(total_price):,} تومان\n\nلطفاً شماره کارت بانکی را وارد کنید:"
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 بازگشت به سبد")
    send_message(cid, text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.chat.id in payment_data)
def handle_payment_steps(message):
    cid = message.chat.id
    
    if message.text == "🔙 بازگشت به سبد":
        del payment_data[cid]
        basket(message)
        return
    
    step = payment_data[cid]['step']
    
    if step == 'card_number':
        
        payment_data[cid]['card_number'] = message.text
        payment_data[cid]['step'] = 'cvv2'
        send_message(cid, "🔢 لطفاً CVV2 را وارد کنید:")
    
    elif step == 'cvv2':
        
        payment_data[cid]['cvv2'] = message.text
        payment_data[cid]['step'] = 'expiry_date'
        send_message(cid, "📅 لطفاً تاریخ انقضا را وارد کنید (مثال: ۱۲/۲۷):")
    
    elif step == 'expiry_date':
    
        payment_data[cid]['expiry_date'] = message.text
        payment_data[cid]['step'] = 'receipt'
        
        text = f"✅ اطلاعات کارت ثبت شد\n\n"
        text += f"💰 مبلغ: {int(payment_data[cid]['total_price']):,} تومان\n\n"
        text += "📸 لطفاً اسکرین‌شات پرداخت را ارسال کنید:"
        
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📸 ارسال اسکرین‌شات")
        kb.add("🔙 بازگشت به سبد")
        
        send_message(cid, text, reply_markup=kb)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    cid = message.chat.id
    

    if cid in payment_data and payment_data[cid]['step'] == 'receipt':
    
        for admin_id in admins:
            try:
                admin_msg = f"💰 پرداخت جدید\n\n"
                admin_msg += f"👤 کاربر آیدی: {cid}\n"
                admin_msg += f"💰 مبلغ: {int(payment_data[cid]['total_price']):,} تومان\n\n"
                admin_msg += "محصولات:\n"
                
                for item in payment_data[cid]['basket_items']:
                    admin_msg += f"{item}\n"
                
                bot.send_message(admin_id, admin_msg)
                bot.forward_message(admin_id, cid, message.message_id)
            except:
                pass
        send_message(cid, "✅ پرداخت شما ثبت شد\n📩 اسکرین‌شات برای پشتیبانی ارسال شد")   
        clear_user_cart(cid)
        if cid in payment_data:
            del payment_data[cid]
        main_menu(cid)
    elif cid in user_data and user_data[cid].get('step') == 'image':
        user_data[cid]['image'] = message.photo[-1].file_id
        product_id = insert_product(
            name=user_data[cid]['name'],
            description=user_data[cid]['desc'],
            price=user_data[cid]['price'],
            inventory=user_data[cid]['inventory'],
            telegram_file_id=user_data[cid]['image']
        )
        if product_id:
            send_message(cid, "✅ محصول ثبت شد و به لیست محصولات اضافه شد")
            load_products_from_db()
        else:
            send_message(cid, "❌ خطا در ثبت محصول")
        
        del user_data[cid]
        
        if cid in admins:
            admin_panel(message)
        else:
            main_menu(cid)
@bot.message_handler(commands=['admin'])
def admin_command(message):
    cid = message.chat.id
    if cid not in admins:
        send_message(cid, "❌ دسترسی ندارید")
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن محصول", "🗑️ حذف محصول")
    kb.add("📊 مشاهده محصولات", "🔄 ریست همه سبدها")
    kb.add("🔙 بازگشت به منوی اصلی")
    send_message(cid, "👨‍💼 پنل مدیریت", reply_markup=kb)

def send_product_page(cid, page=0):
    if not all_products:
        send_message(cid, "📭 هیچ محصولی موجود نیست")
        return None, None, None
    
    user_current_page[cid] = page
    
    total_pages = len(all_products)
    if page < 0:
        page = total_pages - 1
    elif page >= total_pages:
        page = 0
    
    product = all_products[page]
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("➕ افزودن به سبد (۱۰ عدد)", callback_data=f"add_{product['id']}"))
    
    if len(all_products) > 1:
        keyboard.row(
            InlineKeyboardButton("◀️ قبلی", callback_data=f"prev_{page}"),
            InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="page_info"),
            InlineKeyboardButton("بعدی ▶️", callback_data=f"next_{page}")
        )
    
    caption = f"🏷️ نام: {product['name']}\n📝 توضیحات: {product['desc']}\n💰 قیمت: {product['price']}\n📦 موجودی: {product['inventory']}"
    
    return caption, keyboard, product['image']

@bot.message_handler(func=lambda m: m.text == texts["show_products"])
def show_products(message):
    cid = message.chat.id
    
    load_products_from_db()
    
    if not all_products:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 بازگشت به منوی اصلی")
        send_message(cid, "📭 هیچ محصولی موجود نیست", reply_markup=kb)
        return
    
    caption, keyboard, image = send_product_page(cid, 0)
    
    try:
        if image:
            bot.send_photo(cid, image, caption=caption, reply_markup=keyboard)
        else:
            send_message(cid, caption, reply_markup=keyboard)
    except:
        send_message(cid, caption, reply_markup=keyboard)
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 بازگشت به منوی اصلی")
    send_message(cid, "با دکمه‌های ◀️ و ▶️ بین محصولات حرکت کنید:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def add_to_basket(call):
    cid = call.message.chat.id
    product_id = int(call.data.split('_')[1])
    
    success = add_to_cart(cid, product_id, 10)
    
    if success:
        bot.answer_callback_query(call.id, "✅ ۱۰ عدد به سبد اضافه شد")
    else:
        bot.answer_callback_query(call.id, "❌ خطا در افزودن به سبد")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('prev_', 'next_')))
def handle_navigation(call):
    cid = call.message.chat.id
    
    data_parts = call.data.split('_')
    action = data_parts[0]
    current_page = int(data_parts[1]) if len(data_parts) > 1 else 0
    
    if action == 'prev':
        new_page = current_page - 1
        if new_page < 0:
            new_page = len(all_products) - 1
    else:
        new_page = current_page + 1
        if new_page >= len(all_products):
            new_page = 0
    
    caption, keyboard, image = send_product_page(cid, new_page)
    
    if not caption:
        bot.answer_callback_query(call.id, "محصولی یافت نشد")
        return
    
    try:
        if image:
            try:
                bot.edit_message_media(
                    chat_id=cid,
                    message_id=call.message.message_id,
                    media=telebot.types.InputMediaPhoto(image, caption=caption),
                    reply_markup=keyboard
                )
            except:
                bot.edit_message_caption(
                    chat_id=cid,
                    message_id=call.message.message_id,
                    caption=caption,
                    reply_markup=keyboard
                )
        else:
            bot.edit_message_text(
                chat_id=cid,
                message_id=call.message.message_id,
                text=caption,
                reply_markup=keyboard
            )
    except:
        pass
    
    bot.answer_callback_query(call.id, "")

@bot.callback_query_handler(func=lambda call: call.data == "page_info")
def handle_page_info(call):
    bot.answer_callback_query(call.id, "")

@bot.message_handler(func=lambda m: m.text == texts["basket"])
def basket(message):
    cid = message.chat.id
    
    cart_items = get_cart_items(cid)
    
    if not cart_items:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 بازگشت به منوی اصلی")
        send_message(cid, "🛒 سبد خرید شما خالی است", reply_markup=kb)
        return
    
    total_items = 0
    total_price = 0
    
    for item in cart_items:
        quantity = item['QUANTITY']
        price = float(item['PRICE'])
        item_total = price * quantity
        total_items += quantity
        total_price += item_total
        
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("➖ ۱۰", callback_data=f"minus_{item['product_id']}"),
            InlineKeyboardButton(f"{quantity}", callback_data="noop"),
            InlineKeyboardButton("➕ ۱۰", callback_data=f"plus_{item['product_id']}")
        )
        keyboard.row(InlineKeyboardButton("❌ حذف", callback_data=f"remove_{item['product_id']}"))
        
        caption = f"🏷️ نام: {item['NAME']}\n💰 قیمت واحد: {int(price):,} تومان\n📦 تعداد: {quantity}\n💰 جمع این محصول: {int(item_total):,} تومان"
        send_message(cid, caption, reply_markup=keyboard)
    
    summary = f"📊 خلاصه سبد خرید\n\n📦 تعداد کل کالاها: {total_items}\n💰 جمع کل خرید: {int(total_price):,} تومان"
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💳 پرداخت", "❌ پاک کردن سبد")
    kb.add("🔙 بازگشت به منوی اصلی")
    
    send_message(cid, summary, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    cid = call.message.chat.id
    
    if call.data == "noop":
        bot.answer_callback_query(call.id, "")
        return
    
    if call.data.startswith(('prev_', 'next_', 'page_info')):
        return
    
    if call.data.startswith('add_'):
        return
    
    elif call.data.startswith(('plus_', 'minus_', 'remove_')):
        try:
            data_parts = call.data.split('_')
            action = data_parts[0]
            product_id = int(data_parts[1])
            
            cart_items = get_cart_items(cid)
            current_qty = 0
            
            for item in cart_items:
                if item['product_id'] == product_id:
                    current_qty = item['QUANTITY']
                    break
            
            if action == "plus":
                new_qty = current_qty + 10
            elif action == "minus":
                new_qty = max(10, current_qty - 10)
            elif action == "remove":
                new_qty = 0
            
            success = update_cart_quantity(cid, product_id, new_qty)
            
            if success:
                bot.answer_callback_query(call.id, "✅ بروزرسانی شد")
                fake_msg = telebot.types.Message(
                    message_id=1,
                    date=time.time(),
                    chat=call.message.chat,
                    content_type='text',
                    options={},
                    json_string=""
                )
                fake_msg.text = texts["basket"]
                basket(fake_msg)
            else:
                bot.answer_callback_query(call.id, "❌ خطا در بروزرسانی")
                
        except Exception as e:
            print(f"خطا در تغییر سبد: {e}")
            bot.answer_callback_query(call.id, "❌ خطا در بروزرسانی")

@bot.message_handler(func=lambda m: m.text == "❌ پاک کردن سبد")
def clear_basket(message):
    cid = message.chat.id
    success = clear_user_cart(cid)
    
    if success:
        send_message(cid, "🗑️ سبد خرید پاک شد")
    else:
        send_message(cid, "❌ خطا در پاک کردن سبد")
    
    main_menu(cid)

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به سبد")
def back_to_basket(message):
    cid = message.chat.id
    if cid in payment_data:
        del payment_data[cid]
    fake_msg = telebot.types.Message(
        message_id=1,
        date=time.time(),
        chat=message.chat,
        content_type='text',
        options={},
        json_string=""
    )
    fake_msg.text = texts["basket"]
    basket(fake_msg)

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منوی اصلی")
def back_to_menu(message):
    cid = message.chat.id
    if cid in user_data:
        del user_data[cid]
    if cid in payment_data:
        del payment_data[cid]
    if cid in info_data:
        del info_data[cid]
    if cid in user_current_page:
        del user_current_page[cid]
    main_menu(cid)

@bot.message_handler(func=lambda m: m.text == texts["support"])
def support(message):
    cid = message.chat.id
    keyboard = InlineKeyboardMarkup()
    support_button = InlineKeyboardButton("📞 شروع چت با پشتیبانی", url="https://t.me/reza13940")
    keyboard.add(support_button)
    send_message(cid, "برای ارتباط با پشتیبانی روی دکمه زیر کلیک کنید:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == texts["info"])
def info(message):
    cid = message.chat.id
    info_data[cid] = {'step': 'name'}
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 بازگشت به منوی اصلی")
    
    send_message(cid, "👤 ثبت اطلاعات شخصی\n\nلطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.chat.id in info_data)
def handle_info_steps(message):
    cid = message.chat.id
    
    if message.text == "🔙 بازگشت به منوی اصلی":
        del info_data[cid]
        main_menu(cid)
        return
    
    step = info_data[cid]['step']
    
    if step == 'name':
        info_data[cid]['name'] = message.text
        info_data[cid]['step'] = 'phone'
        send_message(cid, "📱 لطفاً شماره تلفن همراه خود را وارد کنید:")
    
    elif step == 'phone':
        info_data[cid]['phone'] = message.text
        info_data[cid]['step'] = 'address'
        send_message(cid, "📍 لطفاً آدرس کامل خود را وارد کنید:")
    
    elif step == 'address':
        info_data[cid]['address'] = message.text
        
        insert_user_data(
            cid,
            info_data[cid]['name'],
            phone=info_data[cid]['phone'],
            address=info_data[cid]['address']
        )
        
        text = f"✅ اطلاعات شما ثبت شد\n\n👤 نام: {info_data[cid]['name']}\n📱 تلفن: {info_data[cid]['phone']}\n📍 آدرس: {info_data[cid]['address']}"
        
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 بازگشت به منوی اصلی")
        
        send_message(cid, text, reply_markup=kb)
        del info_data[cid]

@bot.message_handler(func=lambda m: m.text == texts["admin"])
def admin_panel(message):
    cid = message.chat.id
    if cid not in admins:
        send_message(cid, "❌ دسترسی ندارید")
        return
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن محصول", "🗑️ حذف محصول")
    kb.add("📊 مشاهده محصولات", "🔄 ریست همه سبدها")
    kb.add("🔙 بازگشت به منوی اصلی")
    send_message(cid, "👨‍💼 پنل مدیریت", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ افزودن محصول")
def add_product_start(message):
    cid = message.chat.id
    user_data[cid] = {'step': 'name'}
    send_message(cid, "📝 نام محصول:")

@bot.message_handler(func=lambda m: m.text == "🗑️ حذف محصول")
def delete_product_start(message):
    cid = message.chat.id
    
    load_products_from_db()
    
    if not all_products:
        send_message(cid, "📭 هیچ محصولی برای حذف وجود ندارد")
        return
    
    text = "🗑️ حذف محصولات\n\n" 
    
    for idx, product in enumerate(all_products):
        text += f"{idx+1}. 🏷️ {product['name']} - 💰 {product['price']}\n"
    
    text += "\nبرای حذف، شماره محصول را ارسال کنید (مثال: 1):"   
    user_data[cid] = {'step': 'delete_product'}
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ انصراف")
    send_message(cid, text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.chat.id in user_data and user_data.get(m.chat.id, {}).get('step') == 'delete_product')
def delete_product_handler(message):
    cid = message.chat.id  
    if message.text == "❌ انصراف":
        if cid in user_data:
            del user_data[cid]
        admin_panel(message)
        return
    
    try:
        product_num = int(message.text) - 1
        
        if 0 <= product_num < len(all_products):
            product = all_products[product_num]
            
            success = delete_product(product['id'])
            
            if success:
                send_message(cid, f"✅ محصول '{product['name']}' با موفقیت حذف شد")
                load_products_from_db()
            
            if cid in user_data:
                del user_data[cid]
            
            admin_panel(message)
        else:
            send_message(cid, "❌ شماره محصول نامعتبر است")
    except:
        send_message(cid, "❌ لطفاً یک عدد وارد کنید")

@bot.message_handler(func=lambda m: m.text == "📊 مشاهده محصولات")
def view_admin_products(message):
    cid = message.chat.id
    
    load_products_from_db()
    
    if not all_products:
        send_message(cid, "📭 هیچ محصولی موجود نیست")
        return
    
    text = "📊 لیست محصولات (مدیریت)\n\n"
    for idx, product in enumerate(all_products):
        text += f"{idx+1}. 🏷️ {product['name']}\n   📝 {product['desc']}\n   💰 {product['price']}\n   📦 موجودی: {product['inventory']}\n\n"
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 بازگشت به مدیریت")
    
    send_message(cid, text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🔄 ریست همه سبدها")
def reset_all_baskets(message):
    cid = message.chat.id
    success = clear_all_carts()
    
    if success:
        send_message(cid, "✅ همه سبدهای خرید کاربران ریست شد")
    else:
        send_message(cid, "❌ خطا در ریست سبدها")
    
    admin_panel(message)

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به مدیریت")
def back_to_admin(message):
    admin_panel(message)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    cid = message.chat.id
    if cid not in user_data:
        return
    
    step = user_data[cid].get('step')
    
    if step == 'name':
        user_data[cid]['name'] = message.text
        user_data[cid]['step'] = 'desc'
        send_message(cid, "📄 توضیحات:")
    
    elif step == 'desc':
        user_data[cid]['desc'] = message.text
        user_data[cid]['step'] = 'price'
        send_message(cid, "💰 قیمت:")
    
    elif step == 'price':
        user_data[cid]['price'] = message.text
        user_data[cid]['step'] = 'inventory'
        send_message(cid, "📦 موجودی:")
    
    elif step == 'inventory':
        user_data[cid]['inventory'] = message.text
        user_data[cid]['step'] = 'image'
        send_message(cid, "🖼️ عکس محصول:")
load_products_from_db()
bot.infinity_polling()