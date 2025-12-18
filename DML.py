import mysql.connector
from config import db_config
from DQL import get_product_data

database_name = db_config['database']

def insert_user_data(cid, name, username=None, phone=None, address=None):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    SQL_QUERY = "INSERT IGNORE INTO CUSTOMER (CID, NAME, USERNAME, PHONE, ADDRESS) VALUES (%s, %s, %s, %s, %s);"
    cur.execute(SQL_QUERY, (cid, name, username, phone, address))
    conn.commit()
    cur.close()
    conn.close()
    print(f'user inserted successfully with cid: {cid}')
    return True



def insert_product_data(name, description, price, inventory, category=None, file_id=None):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    SQL_QUERY = "INSERT INTO PRODUCT (NAME, DESCRIPTION, PRICE, INVENTORY, CATEGORY, FILE_ID) VALUES (%s, %s, %s, %s, %s, %s);"
    cur.execute(SQL_QUERY, (name, description, price, inventory, category, file_id))
    conn.commit()
    pid = cur.lastrowid
    cur.close()
    conn.close()
    print(f'product info inserted successfully with id: {pid}')
    return pid

def set_product_category(pid, category):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    SQL_QUERY = "UPDATE PRODUCT SET CATEGORY=%s WHERE ID=%s;"
    cur.execute(SQL_QUERY, (category, pid))
    conn.commit()
    cur.close()
    conn.close()
    return True

def insert_sale_data(customer_cid, products):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    SQL_QUERY = "INSERT INTO SALE (CUSTOMER_CID) VALUES (%s);"
    cur.execute(SQL_QUERY, (customer_cid,))
    sale_id = cur.lastrowid
    for pid, qty in products.items():
        product_info = get_product_data(pid)
        if product_info['INVENTORY'] >= qty:
            SQL_QUERY = "INSERT INTO SALE_ROW (SALE_ID, PRODUCT_ID, QUANTITY) VALUES (%s, %s, %s);"
            cur.execute(SQL_QUERY, (sale_id, pid,qty))
        else:
            pass
    conn.commit()
    cur.close()
    conn.close()
    print(f'sale with id: {sale_id} inserted successfully')
    return True



if __name__ == "__main__":
    insert_user_data(34567890, 'Reza', 'reza123', '1234567890', 'Tehran, Iran')
    insert_product_data('Tablet 1', 200, 5, 'ASA')
    insert_product_data('Tablet 2', 210, 2, 'metformin')
    insert_sale_data(34567890, {1: 1, 2: 2})
