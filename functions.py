import os
import random
import string
import firebase_admin
from firebase_admin import credentials, firestore
import mysql.connector
from datetime import datetime

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",
        database="fibohack"
    )


def generate_unique_filename(path, filename):
    _, ext = os.path.splitext(filename)
    
    def generate_random_name():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    random_name = generate_random_name()
    unique_filename = os.path.join(path, random_name + ext)
    
    while os.path.exists(unique_filename):
        random_name = generate_random_name()
        unique_filename = os.path.join(path, random_name + ext)
    
    return random_name+f"{ext}"

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

def delete_post(post_type, id):
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
        WHERE id = %s
        """
        
        cursor.execute(query, (id,))
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