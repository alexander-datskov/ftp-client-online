import os
import subprocess
from ftplib import FTP, error_perm
from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file, jsonify
from dotenv import load_dotenv
import zipfile
import io
import logging
from mcrcon import MCRcon

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

def install_requirements():
    if os.path.exists('requirements.txt'):
        try:
            logging.debug("Installing requirements")
            subprocess.check_call(['pip', 'install', '-r', 'requirements.txt'])
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install dependencies: {e}")

def connect_ftp(host, port, username, password):
    try:
        logging.debug(f"Connecting to FTP server at {host}:{port} with username {username}")
        ftp = FTP()  # Removed timeout
        ftp.connect(host, port)
        ftp.login(user=username, passwd=password)
        logging.debug("FTP connection established")
        return ftp
    except error_perm as e:
        flash(f"Permission error: {e}")
        logging.error(f"FTP permission error: {e}")
        return None
    except Exception as e:
        flash(f"Failed to connect or log in to {host}:{port}: {e}")
        logging.error(f"FTP connection failed: {e}")
        return None

def connect_rcon(host, port, password):
    try:
        logging.debug(f"Connecting to RCON server at {host}:{port}")
        rcon = MCRcon(host, password, port=port)
        rcon.connect()
        logging.debug("RCON connection established")
        return rcon
    except Exception as e:
        flash(f"Failed to connect to RCON server at {host}:{port}: {e}")
        logging.error(f"RCON connection failed: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['ftp_host'] = request.form['ftp_host']
        session['ftp_port'] = int(request.form['ftp_port'])
        session['ftp_username'] = request.form['ftp_username']
        session['ftp_password'] = request.form['ftp_password']
        session['rcon_host'] = request.form['rcon_host']
        session['rcon_port'] = int(request.form['rcon_port'])
        session['rcon_password'] = request.form['rcon_password']
        logging.debug("Session variables set, redirecting to /ftp")
        return redirect(url_for('ftp'))
    return render_template('index.html')

@app.route('/ftp', methods=['GET', 'POST'])
def ftp():
    if 'ftp_host' not in session:
        flash("Session expired. Please log in again.")
        logging.warning("Session expired")
        return redirect(url_for('index'))

    ftp = connect_ftp(session['ftp_host'], session['ftp_port'], session['ftp_username'], session['ftp_password'])
    if not ftp:
        logging.error("Failed to establish FTP connection, redirecting to index")
        return redirect(url_for('index'))

    current_path = request.args.get('path', '/')
    try:
        ftp.cwd(current_path)
        logging.debug(f"Changed directory to {current_path}")
    except error_perm as e:
        flash(f"Permission error: {e}")
        logging.error(f"Failed to change directory to {current_path} due to permission error: {e}")
        current_path = '/'
        ftp.cwd(current_path)
    except Exception as e:
        flash(f"Failed to change directory: {e}")
        logging.error(f"Failed to change directory to {current_path}: {e}")
        current_path = '/'
        ftp.cwd(current_path)

    try:
        files = ftp.nlst()
        directories = [f for f in files if '.' not in f]
        files = [f for f in files if '.' in f]
        logging.debug(f"Retrieved directory contents: {directories} and files: {files}")
    except Exception as e:
        flash(f"Failed to list directory contents: {e}")
        logging.error(f"Failed to list directory contents: {e}")
        directories = []
        files = []

    if request.method == 'GET' and request.args.get('action') == 'get_content':
        file_path = request.args.get('file_path')
        try:
            content = []
            ftp.retrlines(f"RETR {file_path}", content.append)
            content = "\n".join(content)
            logging.debug(f"Retrieved content for file: {file_path}")
            return content
        except Exception as e:
            logging.error(f"Failed to read file {file_path}: {e}")
            return str(e)

    if request.method == 'POST':
        action = request.form['action']
        if action == 'download':
            file_path = request.form['file_path']
            local_file_path = os.path.join('downloads', os.path.basename(file_path))
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)  # Ensure the directory exists
            try:
                with open(local_file_path, 'wb') as local_file_handle:
                    ftp.retrbinary(f"RETR {file_path}", local_file_handle.write)
                logging.debug(f"Downloaded file: {file_path}")
                return send_file(local_file_path, as_attachment=True)
            except Exception as e:
                flash(f"Failed to download {file_path}: {e}")
                logging.error(f"Failed to download {file_path}: {e}")
        elif action == 'download_zip':
            folder_path = request.form['folder_path']
            zip_buffer = io.BytesIO()
            try:
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for file in ftp.nlst(folder_path):
                        file_name = os.path.basename(file)
                        file_data = io.BytesIO()
                        ftp.retrbinary(f'RETR {file}', file_data.write)
                        file_data.seek(0)
                        zip_file.writestr(file_name, file_data.read())
                zip_buffer.seek(0)
                logging.debug(f"Created ZIP for folder: {folder_path}")
                return send_file(zip_buffer, as_attachment=True, download_name=f'{os.path.basename(folder_path)}.zip')
            except Exception as e:
                flash(f"Failed to create ZIP for {folder_path}: {e}")
                logging.error(f"Failed to create ZIP for {folder_path}: {e}")
        elif action == 'upload':
            files = request.files.getlist('file')
            for file in files:
                remote_file_path = os.path.join(current_path, file.filename)
                try:
                    ftp.storbinary(f'STOR {remote_file_path}', file.stream)
                    flash(f"File {file.filename} uploaded successfully")
                    logging.debug(f"Uploaded file: {file.filename}")
                except Exception as e:
                    flash(f"Failed to upload {file.filename}: {e}")
                    logging.error(f"Failed to upload {file.filename}: {e}")
        elif action == 'delete':
            file_paths = request.form.getlist('file_paths')
            for file_path in file_paths:
                try:
                    ftp.delete(file_path)
                    flash(f"File {file_path} deleted successfully")
                    logging.debug(f"Deleted file: {file_path}")
                except Exception as e:
                    flash(f"Failed to delete {file_path}: {e}")
                    logging.error(f"Failed to delete {file_path}: {e}")
        elif action == 'rename':
            file_path = request.form['file_path']
            new_name = request.form['new_name']
            try:
                ftp.rename(file_path, os.path.join(current_path, new_name))
                flash(f"File {file_path} renamed to {new_name} successfully")
                logging.debug(f"Renamed file {file_path} to {new_name}")
            except Exception as e:
                flash(f"Failed to rename {file_path}: {e}")
                logging.error(f"Failed to rename {file_path}: {e}")
        elif action == 'create_dir':
            dir_name = request.form['dir_name']
            try:
                ftp.mkd(dir_name)
                flash(f"Directory {dir_name} created successfully")
                logging.debug(f"Created directory: {dir_name}")
            except Exception as e:
                flash(f"Failed to create directory {dir_name}: {e}")
                logging.error(f"Failed to create directory {dir_name}: {e}")
        elif action == 'create_file':
            file_name = request.form['new_file_name']
            file_content = request.form['new_file_content']
            try:
                file_content_io = io.BytesIO(file_content.encode('utf-8'))
                ftp.storbinary(f'STOR {os.path.join(current_path, file_name)}', file_content_io)
                flash(f"File {file_name} created successfully")
                logging.debug(f"Created file: {file_name}")
            except Exception as e:
                flash(f"Failed to create file {file_name}: {e}")
                logging.error(f"Failed to create file {file_name}: {e}")
        elif action == 'edit':
            file_path = request.form['file_path']
            new_content = request.form['content']
            try:
                new_content_io = io.BytesIO(new_content.encode('utf-8'))
                ftp.storbinary(f'STOR {file_path}', new_content_io)
                flash(f"File {file_path} edited successfully")
                logging.debug(f"Edited file: {file_path}")
            except Exception as e:
                flash(f"Failed to edit {file_path}: {e}")
                logging.error(f"Failed to edit {file_path}: {e}")

    ftp.quit()
    return render_template('ftp.html', current_path=current_path, directories=directories, files=files, os=os)

@app.route('/rcon', methods=['POST'])
def rcon_command():
    if 'rcon_host' not in session:
        flash("Session expired. Please log in again.")
        logging.warning("Session expired")
        return redirect(url_for('index'))

    command = request.form['command']
    rcon = connect_rcon(session['rcon_host'], session['rcon_port'], session['rcon_password'])
    if not rcon:
        logging.error("Failed to establish RCON connection")
        return redirect(url_for('ftp'))

    try:
        response = rcon.command(command)
        logging.debug(f"RCON command executed: {command}, response: {response}")
        flash(f"Command executed successfully: {response}")
    except Exception as e:
        flash(f"Failed to execute command: {e}")
        logging.error(f"Failed to execute RCON command: {e}")

    rcon.disconnect()
    return redirect(url_for('ftp'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    results = []
    ftp = connect_ftp(session['ftp_host'], session['ftp_port'], session['ftp_username'], session['ftp_password'])
    if ftp:
        for dirpath, dirnames, filenames in ftp.walk('/'):
            for filename in filenames:
                if query.lower() in filename.lower():
                    results.append(os.path.join(dirpath, filename))
    logging.debug(f"Search results for query '{query}': {results}")
    return jsonify(results)

if __name__ == '__main__':
    install_requirements()
    app.run(host='0.0.0.0', port=5000, debug=True)
      