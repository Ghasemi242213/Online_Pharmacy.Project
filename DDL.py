import mysql.connector
from config import db_config

database_name = db_config['database']

def drop_n_create_database(database_name):
    conn = mysql.connector.connect(user=db_config['user'], password=db_config['password'], host=db_config['host'])
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {database_name};")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {database_name};")
    conn.commit()
    cur.close()
    conn.close()
    print(f'database {database_name} created successfully')

def create_table_customer():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE CUSTOMER (
                    `CID`               BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
                    `TELEGRAM_ID`       BIGINT NOT NULL UNIQUE,
                    `NAME`              VARCHAR(150) NOT NULL,
                    `USERNAME`          VARCHAR(255),
                    `PHONE`             VARCHAR(13),
                    `ADDRESS`           TEXT,
                    `REGISTER_DATE`     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `LAST_UPDATE`       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                );""")
    conn.commit()
    cur.close()
    conn.close()
    print(f'TABLE CUSTOMER created successfully')

def create_table_admin():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE ADMIN (
                    `ID`                INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
                    `TELEGRAM_ID`       BIGINT NOT NULL UNIQUE,
                    `NAME`              VARCHAR(150) NOT NULL,
                    `USERNAME`          VARCHAR(255),
                    `ROLE`              ENUM('ADMIN', 'SUPER_ADMIN') DEFAULT 'ADMIN',
                    `REGISTER_DATE`     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `LAST_UPDATE`       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                );""")
    conn.commit()
    cur.close()
    conn.close()
    print(f'TABLE ADMIN created successfully')

def create_table_product():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE PRODUCT (
                    `ID`                INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
                    `NAME`              VARCHAR(100) NOT NULL,
                    `DESCRIPTION`       TEXT,
                    `PRICE`             DOUBLE NOT NULL,
                    `INVENTORY`         MEDIUMINT UNSIGNED NOT NULL DEFAULT 0,
                    `CATEGORY`          ENUM('MEDICINE', 'MEDICAL_SUPPLIES', 'HEALTH_CARE', 'OTHER'),
                    `FILE_ID`           VARCHAR(255),
                    `TELEGRAM_FILE_ID`  VARCHAR(255),
                    `REGISTER_DATE`     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `LAST_UPDATE`       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                );""")
    conn.commit()
    cur.close()
    conn.close()
    print(f'TABLE PRODUCT created successfully')

def create_table_cart():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE CART (
                    `ID`                INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
                    `CUSTOMER_CID`      BIGINT UNSIGNED NOT NULL,
                    `PRODUCT_ID`        INT UNSIGNED NOT NULL,
                    `QUANTITY`          TINYINT UNSIGNED NOT NULL DEFAULT 1,
                    `ADDED_DATE`        DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (CUSTOMER_CID) REFERENCES CUSTOMER (CID) ON DELETE CASCADE,
                    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT (ID) ON DELETE CASCADE,
                    UNIQUE KEY unique_cart_item (CUSTOMER_CID, PRODUCT_ID)
                );""")
    conn.commit()
    cur.close()
    conn.close()
    print(f'TABLE CART created successfully')

def create_table_payment():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE PAYMENT (
                    `ID`                INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
                    `CUSTOMER_CID`      BIGINT UNSIGNED NOT NULL,
                    `AMOUNT`            DOUBLE NOT NULL,
                    `CARD_NUMBER`       VARCHAR(16),
                    `CVV2`              VARCHAR(4),
                    `EXPIRY_DATE`       VARCHAR(5),
                    `PAYMENT_STATUS`    ENUM('PENDING', 'VERIFIED', 'REJECTED') DEFAULT 'PENDING',
                    `RECEIPT_FILE_ID`   VARCHAR(255),
                    `REGISTER_DATE`     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `LAST_UPDATE`       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (CUSTOMER_CID) REFERENCES CUSTOMER (CID) ON DELETE CASCADE
                );""")
    conn.commit()
    cur.close()
    conn.close()
    print(f'TABLE PAYMENT created successfully')

def create_table_sale():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE SALE (
                    `ID`                INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
                    `CUSTOMER_CID`      BIGINT UNSIGNED NOT NULL,
                    `PAYMENT_ID`        INT UNSIGNED,
                    `TOTAL_AMOUNT`      DOUBLE NOT NULL,
                    `SALE_STATUS`       ENUM('PENDING', 'PAID', 'SHIPPED', 'DELIVERED', 'CANCELLED') DEFAULT 'PENDING',
                    `SHIPPING_ADDRESS`  TEXT,
                    `REGISTER_DATE`     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `LAST_UPDATE`       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (CUSTOMER_CID) REFERENCES CUSTOMER (CID) ON DELETE CASCADE,
                    FOREIGN KEY (PAYMENT_ID) REFERENCES PAYMENT (ID) ON DELETE SET NULL
                );""")
    conn.commit()
    cur.close()
    conn.close()
    print(f'TABLE SALE created successfully')



if __name__ == "__main__":
    drop_n_create_database(database_name)
    create_table_customer()
    create_table_admin()
    create_table_product()
    create_table_cart()
    create_table_payment()
    create_table_sale()
 
