from supabase import create_client, Client
import os, uuid, requests
import streamlit as st

class SupabaseStorage:
    def __init__(self, url, key):
        self.url = st.secrets["SUPABASE_URL"]  # Set this in your .env file
        self.key = st.secrets["SUPABASE_KEY"]  # Set this in your .env file
        self.supabase: Client = create_client(self.url, self.key)
        self.bucket_name = "uploads"  # The bucket you created on Supabase

    def _open(self, name, file_dir, mode='rb'):
        """
        Open the file in Supabase storage.
        """
        # Generate the file URL to retrieve it
        file_path = f"{file_dir}/{name}"
        response = self.supabase.storage.from_(self.bucket_name).download(file_path)

        if response.status_code == 200:
            return response.content
        else:
            raise FileNotFoundError(f"File {name} not found in Supabase storage")

    def exists(self, name, file_dir):
        """
        Check if a file exists in the Supabase storage.
        """
        try:
            file_path = f"{file_dir}/{name}"
            response = self.supabase.storage.from_(self.bucket_name).download(file_path)
            return response['data'] is not None
        except Exception:
            return False

    def upload_file(self, file, file_name, file_directory, unique_name=True):
        """ Upload a file to Supabase storage """
        if unique_name:
            file_name = f"{file_name.split('.')[0]}_{uuid.uuid4().hex}_{file_name}"

        file_path = f"{file_directory}/{file_name}"  # Set the path within the bucket
        response = self.supabase.storage.from_(self.bucket_name).upload(file_path, file, {
            'contentType': 'application/octet-stream'
        })
        return file_name
    
    def upload_image(self, image, image_name, file_directory, unique_name=False):
        """
        Upload an image file to Supabase storage.

        Args:
            image (bytes): The image file contents.
            image_name (str): The name of the image file.
            file_directory (str): The directory where the image will be stored.

        Returns:
            str: The unique name of the uploaded image file.
        """
        # Check if the image is valid
        if not image:
            raise ValueError("Invalid image")

        # Get the file extension from the image name
        file_extension = image_name.split('.')[-1].lower()

        # Determine the content type based on the file extension
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
        }
        content_type = content_types.get(file_extension, 'application/octet-stream')

        # Upload the image file
        if unique_name:
            file_name = f"{image_name.split('.')[0]}_{uuid.uuid4().hex}_{image_name}"

        file_path = f"{file_directory}/{file_name}"  # Set the path within the bucket
        response = self.supabase.storage.from_(self.bucket_name).upload(file_path, image, {
            'contentType': content_type
        })

        return file_name

    def get_file_url(self, file_name, file_directory):
        """ Generate a publicly accessible URL for the file """
        file_path = f"{file_directory}/{file_name}"
        response = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
        return response


    def delete_file(self, file_name, folder_name):
        """
        Delete a file from the storage.

        Args:
            file_name (str): The name of the file to delete.
            folder_name (str): The name of the folder where the file is located.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        try:
            # Use the Supabase API to delete the file
            print(file_name)
            print("\n"*10)
            data = self.supabase.storage.from_(self.bucket_name).remove([f"{folder_name}/{file_name}"])
            if data['data'] == [f"{folder_name}/{file_name}"]:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def insert_data(self, data, table):
        """
        Insert data into a Supabase table.

        Args:
            data (dict or list): The data to be inserted.
            table (str): The name of the table to insert into.

        Returns:
            dict: The inserted data with the generated ID.
        """
        try:
            # Insert data into the table
            response = self.supabase.table(table).insert(data).execute()
            return response.data
        except Exception as e:
            # Handle any errors that occur during insertion
            print(f"Error inserting data: {e}")
            return None
    
    def get_data(self, table_name):
        """
        Get data from a Supabase table.

        Args:
            table_name (str): The name of the table to retrieve data from.

        Returns:
            list: A list of dictionaries containing the data from the table.
        """
        try:
            # Retrieve data from the Supabase table
            supabase_data = self.supabase.from_(table_name).select("*").execute()
            return supabase_data.data
        except Exception as e:
            # Handle any errors that occur during data retrieval
            print(f"Error retrieving data: {e}")
            return None