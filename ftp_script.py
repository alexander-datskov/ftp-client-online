import os
from ftplib import FTP

def connect_ftp(host, port, username, password):
    try:
        ftp = FTP()
        ftp.connect(host, port)
        ftp.login(user=username, passwd=password)
        return ftp
    except Exception as e:
        print(f"Failed to connect or log in to {host}:{port}: {e}")
        return None

def download_file(ftp, remote_file_path, local_file_path):
    try:
        with open(local_file_path, 'wb') as local_file_handle:
            ftp.retrbinary(f"RETR {remote_file_path}", local_file_handle.write)
        print(f"File {remote_file_path} downloaded successfully")
    except Exception as e:
        print(f"Failed to download {remote_file_path}: {e}")

def upload_file(ftp, local_file_path, remote_file_path):
    try:
        with open(local_file_path, 'rb') as local_file_handle:
            ftp.storbinary(f'STOR {remote_file_path}', local_file_handle)
        print(f"File {local_file_path} uploaded successfully")
    except Exception as e:
        print(f"Failed to upload {local_file_path}: {e}")

def delete_file(ftp, file_path):
    try:
        ftp.delete(file_path)
        print(f"File {file_path} deleted successfully")
    except Exception as e:
        print(f"Failed to delete {file_path}: {e}")

def rename_file(ftp, old_name, new_name):
    try:
        ftp.rename(old_name, new_name)
        print(f"File {old_name} renamed to {new_name} successfully")
    except Exception as e:
        print(f"Failed to rename {old_name} to {new_name}: {e}")

def create_directory(ftp, dir_name):
    try:
        ftp.mkd(dir_name)
        print(f"Directory {dir_name} created successfully")
    except Exception as e:
        print(f"Failed to create directory {dir_name}: {e}")

def edit_file(ftp, file_path, new_content):
    try:
        with open(file_path, 'wb') as file:
            file.write(new_content.encode())
        print(f"File {file_path} edited successfully")
    except Exception as e:
        print(f"Failed to edit {file_path}: {e}")
