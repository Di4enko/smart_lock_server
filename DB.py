import psycopg2
import logging

class DB:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    def __init__(self):
        self.DB_ADDRESS = 'localhost'
        self.DB_USER = 'admin'
        self.DB_NAME = "iot"
        self.DB_PASSWORD = 'admin'
        self.__conn = None
        self.__cur = None
        self._connect()

    def _connect(self):
        """Установка соединения с БД"""
        try:
            # Если старое соединение есть, попробуем его закрыть перед новым
            if self.__conn:
                self.__conn.close()
            self.__conn = psycopg2.connect(
                dbname=self.DB_NAME,
                user=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_ADDRESS,
                port="5432",
                connect_timeout=5 # Чтобы не ждать вечно, если БД упала
            )
            self.__cur = self.__conn.cursor()
            logging.info("Соединение с БД успешно установлено.")
        except Exception as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            self.__conn = None # Гарантируем, что при ошибке тут None
            raise e

    @property
    def is_connected(self):
        # Проверка, активно ли соединение в данный момент
        if self.__conn is None or self.__conn.closed != 0:
            return False
        return True

    def __ensure_connection(self):
        # Проверяем соединение и переподключаемся при необходимости
        if not self.is_connected:
            logging.warning("Соединение с БД потеряно. Попытка переподключения...")
            self._connect()
            if not self.is_connected:
                raise Exception("Не удалось восстановить соединение с базой данных.")
            
    def addKey(self, visitior, key, labs, valid):
        try:
            self.__ensure_connection()
            query = '''INSERT INTO keys (key, visitor, labs, valid) VALUES (%s, %s, %s, %s)
                        ON CONFLICT(key) DO NOTHING'''
            self.__cur.execute(query, (key, visitior, labs, valid,))
            self.__conn.commit()
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления ключа для пользователя {visitior}: {e}")
            return False

    def dellKey(self, key):
        try:
            self.__ensure_connection()
            query = '''DELETE FROM keys where key=%s'''
            self.__cur.execute(query, (key,))
            self.__conn.commit()
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления ключа {key}: {e}")
            return False

    def getKey(self, key):
        try:
            self.__ensure_connection()
            query = ''' SELECT visitor, key, labs, valid from keys WHERE key=%s'''
            self.__cur.execute(query, (key,))
            res = self.__cur.fetchone()
            return res
        except Exception as e:
            logging.error(f"Ошибка получения ключа {key}: {e}") 

    def getKeys(self):
        try:
            self.__ensure_connection()
            query = ''' SELECT visitor, key, labs, valid from keys'''
            self.__cur.execute(query)
            res = self.__cur.fetchall()
            return res
        except Exception as e:
            logging.error(f"Ошибка получения ключей: {e}") 

    

    def updateKey(self, visitor, **kwargs):
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return False
        columns = ", ".join([f"{k} = %s" for k in updates.keys()])
        updates['visitor'] = visitor
        values = list(updates.values())
        try:
            self.__cur.execute(f"UPDATE keys SET {columns} WHERE visitor = %s", values)
            self.__conn.commit()
            return True
        except Exception as e:
            logging.error(f"Не удалось обновить ключ пользователя {visitor}: {e}")
            return False
    
    def saveVisit(self, key, lab, status):
        try:
            self.__ensure_connection()
            query = '''INSERT INTO access_history (key, lab, access) VALUES (%s, %s, %s)'''
            self.__cur.execute(query, (key, lab, status,))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Ошибка добавления id пользователя tg: {e}")

    def getLocks(self):
        try:
            self.__ensure_connection()
            query = '''SELECT lab, address from locks'''
            self.__cur.execute(query)
            locks = self.__cur.fetchall()
            return locks
        except Exception as e:
            logging.error("Ошибка получения списка замков")

    def updateLock(self, old_ip, **kwargs):
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return False
        columns = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values(), old_ip)
        try:
            self.__cur.execute(f"UPDATE keys SET {columns} WHERE address = ?", values)
            return True
        except Exception as e:
            logging.error("Ошибка получения списка замков")
            return False

    def addLock(self, lab, lock_ip):
        try:
            self.__ensure_connection()
            query = '''INSERT INTO locks (lab, address) values (%s, %s)''' 
            self.__cur.execute(query, (lab, lock_ip))
            self.__conn.commit()
            logging.info("Замок добавлен")
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления нового замка: {e}")
            return False
        
    def dellLock(self, lock_ip):
        try:
            self.__ensure_connection()
            query = '''DELETE FROM locks where address=%s''' 
            self.__cur.execute(query, (lock_ip,))
            self.__conn.commit()
            logging.info("Замок удален")
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления замка: {e}")
            return False
