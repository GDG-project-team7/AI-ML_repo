import sqlite3

DATABASE = 'users.db'

class Database:
    def init_db(self):
        """DB 테이블 생성"""
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password TEXT,
                    certified BOOLEAN
                )
            """)
            conn.commit()

    def register_user(self, username, email, password, certified):
        """회원가입 데이터 저장"""
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, email, password, certified)
                    VALUES (?, ?, ?, ?)
                """, (username, email, password, certified))
                conn.commit()
            return True, "회원가입 성공"
        except sqlite3.IntegrityError:
            return False, "이미 존재하는 사용자"
