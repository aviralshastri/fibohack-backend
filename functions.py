import os
import random
import string
import firebase_admin
from firebase_admin import credentials, firestore
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",
        database="fibohack"
    )


def generate_unique_filename(path):
    def generate_random_name():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    random_name = generate_random_name()
    existing_basenames = {os.path.splitext(f)[0] for f in os.listdir(path)}
    while random_name in existing_basenames:
        random_name = generate_random_name()
    return random_name


def generate_unique_folder(path):
    def generate_random_name():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    random_name = generate_random_name()
    unique_folder = os.path.join(path, random_name)
    while os.path.exists(unique_folder):
        random_name = generate_random_name()
        unique_folder = os.path.join(path, random_name)
    
    return random_name


def create_folder(path: str, folder_name: str) -> str:
    """
    Create a folder with the given name in the specified path.

    Parameters:
    - path (str): The directory in which to create the folder.
    - folder_name (str): The name of the folder to be created.

    Returns:
    - str: The full path of the created folder or a message if it already exists.
    """
    folder_path = os.path.join(path, folder_name)
    print(f"Base path: {path}")
    print(f"Full folder path: {folder_path}")
    if not os.path.exists(path):
        print("Base path does not exist. Creating base path...")
        os.makedirs(path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return f"Folder created: {folder_path}"
    else:
        return f"Folder already exists: {folder_path}"


def add_new_post_mysql(id, description, title, thumbnail, author,post_type):
    if post_type in ["articles","guides","tutorials"]:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            upload_date = datetime.now().strftime('%Y-%m-%d')

            query = f"""
            INSERT INTO {post_type} (id, description, title, thumbnail, author, upload_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (id, description, title, thumbnail, author, upload_date))
            connection.commit()
            print(f"Tutorial '{title}' added successfully.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            connection.close()
    
    else:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            upload_date = datetime.now().strftime('%Y-%m-%d')

            query = f"""
            INSERT INTO {post_type} (id, description, title, thumbnail, author, upload_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (id, description, title, thumbnail, author, upload_date))
            connection.commit()
            print(f"Tutorial '{title}' added successfully.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            connection.close()

def update_post_mysql(post_type, post_id, key=None, value=None):
    """
    Update a post in the database. If no key/value provided, only update changes_date.
    
    Parameters:
    - post_type: str (articles, guides, tutorials, etc.)
    - post_id: str (the post identifier)
    - key: str (optional) - the field to update
    - value: any (optional) - the new value for the field
    
    Returns:
    - bool: True if successful, False otherwise
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if key is None or value is None:
            query = f"""
            UPDATE {post_type}
            SET changes_date = %s
            WHERE id = %s
            """
            values = (current_date, post_id)
        else:
            query = f"""
            UPDATE {post_type}
            SET {key} = %s, changes_date = %s
            WHERE id = %s
            """
            values = (value, current_date, post_id)
        
        cursor.execute(query, values)
        connection.commit()
        
        if cursor.rowcount > 0:
            print(f"Post with ID '{post_id}' updated successfully in {post_type}.")
            return True
        else:
            print(f"No post found with ID '{post_id}' in {post_type}.")
            return False
            
    except mysql.connector.Error as err:
        print(f"Error updating post: {err}")
        return False
    finally:
        cursor.close()
        connection.close()


def delete_post_mysql(post_type, id,thumbnail_id):
    """
    Delete a post from the database.
    
    Parameters:
    - post_type: str (articles, guides, tutorials, etc.)
    - id: str (the unique identifier of the post)
    
    Returns:
    - bool: True if successful, False otherwise
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        query = f"""
        DELETE FROM {post_type}
        WHERE id = %s and thumbnail = %s
        """
        
        cursor.execute(query, (id,thumbnail_id,))
        connection.commit()
        
        if cursor.rowcount > 0:
            print(f"Post with ID '{id}' deleted successfully from {post_type}.")
            return True
        else:
            print(f"No post found with ID '{id}' in {post_type}.")
            return False
            
    except mysql.connector.Error as err:
        print(f"Error deleting post: {err}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_thumbnail(post_id: str, post_type: str):
    """
    Get thumbnail from a post from the database.
    
    Parameters:
    - post_type: str 
    - post_id: str (the unique identifier of the post)
    
    Returns:
    - Optional[str]: thumbnail file name if found, None if not found or error occurs
    
    Raises:
    - ValueError: If post_type or post_id is invalid
    """
    if not post_id or not post_type:
        raise ValueError("post_id and post_type must not be empty")
        
    connection = get_db_connection()
    if not connection:
        print("Failed to establish database connection")
        return None
        
    cursor = connection.cursor(dictionary=True)
    try:
        allowed_post_types = ['articles', 'guides', 'tutorials'] 
        if post_type not in allowed_post_types:
            raise ValueError(f"Invalid post_type. Must be one of {allowed_post_types}")
            
        query = f"""
        SELECT thumbnail FROM {post_type}
        WHERE id = %s
        """
        cursor.execute(query, (post_id,))
        result = cursor.fetchone()
        
        if not result:
            return None
            
        return result['thumbnail']
        
    except Error as err:
        print(f"Database error: {err}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_post_mysql(post_type, offset_upper=50, offset_lower=0):
    """
    Fetch posts from the database. If no offsets are provided, it will return data from index 50 to 0.
    If offsets are given, it will return data based on those limits.

    Parameters:
    - post_type: str (e.g., 'articles', 'guides', 'tutorials')
    - offset_upper: int (optional) - the upper bound for the data range
    - offset_lower: int (optional) - the lower bound for the data range

    Returns:
    - list: A list of tuples representing the rows fetched from the database
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    if offset_upper is None and offset_lower is None:
        offset_upper = 50
        offset_lower = 0

    query = f"SELECT * FROM {post_type} LIMIT %s OFFSET %s"
    
    limit = offset_upper - offset_lower
    offset = offset_lower

    try:
        cursor.execute(query, (limit, offset))
        result = cursor.fetchall()
        return result

    except mysql.connector.Error as err:
        print(f"Error fetching posts: {err}")
        return []
    
    finally:
        cursor.close()
        connection.close()
