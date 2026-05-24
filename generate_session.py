"""
RONALDO MUSIC — Pyrogram V2 Session Generator
Run this script ONCE locally or on any server to generate your STRING_SESSION.
Then copy the printed session string into Railway → Variables → STRING_SESSION

Usage:
    python3 generate_session.py
"""

import asyncio
import sys

try:
    from pyrogram import Client
    from pyrogram.errors import (
        ApiIdInvalid,
        PhoneNumberInvalid,
        PhoneCodeInvalid,
        PhoneCodeExpired,
        SessionPasswordNeeded,
        PasswordHashInvalid,
    )
except ImportError:
    print("Installing pyrogram + tgcrypto...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
        "git+https://github.com/KurimuzonAkuma/pyrogram.git@2ae00a2710dd3e347798473f3dd784e9639edb1a",
        "tgcrypto"
    ])
    from pyrogram import Client
    from pyrogram.errors import (
        ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid,
        PhoneCodeExpired, SessionPasswordNeeded, PasswordHashInvalid,
    )


async def generate():
    print("\n" + "="*55)
    print("   RONALDO MUSIC — Pyrogram V2 Session Generator")
    print("="*55)
    print("\nGet API_ID and API_HASH from: https://my.telegram.org/apps\n")

    api_id = input("Enter your API_ID   : ").strip()
    api_hash = input("Enter your API_HASH : ").strip()

    if not api_id.isdigit():
        print("\n[ERROR] API_ID must be a number!")
        return
    api_id = int(api_id)

    client = Client(
        name="session_gen",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    )

    await client.connect()

    phone = input("\nEnter your phone number (with country code, e.g. +91XXXXXXXXXX): ").strip()

    try:
        sent = await client.send_code(phone)
    except ApiIdInvalid:
        print("\n[ERROR] API_ID / API_HASH is invalid. Check https://my.telegram.org/apps")
        await client.disconnect()
        return
    except PhoneNumberInvalid:
        print("\n[ERROR] Phone number is invalid. Use format: +91XXXXXXXXXX")
        await client.disconnect()
        return

    code = input("\nEnter the OTP sent to your Telegram: ").strip()

    try:
        await client.sign_in(phone, sent.phone_code_hash, code)

    except PhoneCodeInvalid:
        print("\n[ERROR] OTP is incorrect. Try again.")
        await client.disconnect()
        return
    except PhoneCodeExpired:
        print("\n[ERROR] OTP expired. Run the script again.")
        await client.disconnect()
        return
    except SessionPasswordNeeded:
        print("\n[INFO] Two-step verification is enabled.")
        password = input("Enter your Telegram 2FA password: ").strip()
        try:
            await client.check_password(password)
        except PasswordHashInvalid:
            print("\n[ERROR] Wrong 2FA password.")
            await client.disconnect()
            return

    session_string = await client.export_session_string()
    me = await client.get_me()
    await client.disconnect()

    print("\n" + "="*55)
    print(f"  Logged in as: {me.first_name} (@{me.username})")
    print("="*55)
    print("\n YOUR STRING_SESSION (copy this into Railway):\n")
    print(session_string)
    print("\n" + "="*55)
    print("  Steps:")
    print("  1. Copy the session string above")
    print("  2. Go to Railway → Your Project → Variables")
    print("  3. Set STRING_SESSION = <paste here>")
    print("  4. Redeploy")
    print("="*55 + "\n")


if __name__ == "__main__":
    asyncio.run(generate())
