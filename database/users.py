from database.connection import get_connection

def subscribe_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (user_id, is_subscribed) VALUES (%s, TRUE)"
                           " ON CONFLICT (user_id) DO UPDATE SET is_subscribed = TRUE",
                           (user_id,))

def unsubscribe_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET is_subscribed = FALSE WHERE user_id = %s",
                           (user_id,))

def get_subscribed_users():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE is_subscribed = TRUE")
            users = cursor.fetchall()
            return [user[0] for user in users]

def is_user_subscribed(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT is_subscribed FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()

            return result is not None and result[0]
