import subprocess
import os
import time
from .db_settings import *


def dump_db():
    """
    Создает резервную копию базы данных с помощью команды pg_dump.
    """
    os.makedirs(os.path.join(os.getcwd(), 'backup_db'), exist_ok=True)
    dump_file_path = os.path.join(os.getcwd(), 'backup_db', f'{DB_NAME}_{int(time.time())}.sql')
    os.environ['PGPASSWORD'] = DB_PASSWORD
    try:
        command = f'pg_dump -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -F p -b -v -f {dump_file_path} {DB_NAME}'
        subprocess.run(command, check=True, text=True)
        print(f'Database dump successful. File saved at {dump_file_path}')
    except subprocess.CalledProcessError as e:
        print(f'Database dump failed. {str(e)}')