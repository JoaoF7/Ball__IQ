from data.loader import *
import sqlite3


class UserDatabase:
    """
    Class to interact with SQLite database table 'users'.

    Schema:
    - user_id: INTEGER PRIMARY KEY AUTOINCREMENT
    - username: TEXT NOT NULL
    - email: TEXT UNIQUE NOT NULL
    - password: TEXT NOT NULL
    - team_name TEXT NOT NULL,
    - budget REAL NOT NULL CHECK(budget >= 0 AND budget <= 100),
    - points INTEGER DEFAULT 0 CHECK(points >= 0)

    This class provides methods for common operations such as adding,
    removing, and updating users, as well as verifying and retrieving user data.
    """

    def __init__(self):
        """
        Initialize the UserDatabase instance.

        Args:
            conn (sqlite3.Connection): SQLite database connection object.
        """
        db_path = get_sqlite_database_path()
        self.db = sqlite3.connect(db_path)

    def check_if_email_exists(self, email):
        """
        Check if an email already exists in the database.

        Args:
            email (str): Email address to check.

        Returns:
            bool: True if the email exists, False otherwise.
        """
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "SELECT email FROM users WHERE email = :email", {"email": email}
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def add_user(self, username, email, password, team_name):
        """
        Add a new user to the database.

        Args:
            username (str): User's username.
            email (str): User's email address.
            password (str): User's password (hashed).
            team_name (str): User's team name

        Returns:
            bool: True if the user was added successfully, False otherwise.
        """
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (username, email, password, team_name, budget, points)
                VALUES (:username, :email, :password, :team_name, :budget, :points)
                """,
                {
                    "username": username,
                    "email": email,
                    "password": password,
                    "team_name": team_name,
                    "budget": 100,
                    "points": 0,
                },
            )
            self.db.commit()
            return True
        except Exception as e:
            return False
        finally:
            cursor.close()

    def remove_user(self, email):
        """
        Remove a user from the database by email.

        Args:
            email (str): Email address of the user to remove.

        Returns:
            bool: True if a user was removed, False otherwise.
        """
        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE email = :email", {"email": email})
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def verify_user(self, email, password):
        """
        Verify if a user exists with the provided email and password.

        Args:
            email (str): User's email address.
            password (str): User's password (hashed).

        Returns:
            bool: True if the user is verified, False otherwise.
        """
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "SELECT user_id FROM users WHERE email = :email AND password = :password",
                {"email": email, "password": password},
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def get_user_id(self, email):
        """
        Retrieve the ID of a user by their email.

        Args:
            email (str): User's email address.

        Returns:
            int or None: User ID if found, None otherwise.
        """
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "SELECT user_id FROM users WHERE email = :email", {"email": email}
            )
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()

    def get_user_details(self, email):
        """
        Retrieve detailed information about a user by their email.

        Args:
            email (str): User's email address.

        Returns:
            tuple or None: User details (first_name, last_name, email, phone, address, gender, date_of_birth)
            if found, None otherwise.
        """
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """SELECT username, email, team_name, budget, points
                FROM users WHERE email = :email""",
                {"email": email},
            )
            return cursor.fetchone()
        finally:
            cursor.close()

    def update_user(self, email, **kwargs):
        """
        Update user information in the database.

        Args:
            email (str): Email address of the user to update.
            **kwargs: Key-value pairs representing the fields to update.

        Returns:
            bool: True if a user was updated, False otherwise.
        """
        cursor = self.db.cursor()
        try:
            update_fields = ", ".join([f"{k} = :{k}" for k in kwargs.keys()])
            query = f"UPDATE users SET {update_fields} WHERE email = :email"
            cursor.execute(query, {**kwargs, "email": email})
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()