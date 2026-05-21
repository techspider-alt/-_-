# NOBITA MUSIC Bot

A Telegram music bot for playing audio and video in Telegram voice chats, built with Pyrogram and PyTgCalls.

## Overview

This is a Telegram bot that allows users to play music and videos in Telegram group voice chats. It supports YouTube, Spotify, SoundCloud, and Apple Music, with multi-assistant support for up to 5 concurrent userbot sessions.

## Architecture

- **Language**: Python 3.12
- **Telegram API**: Pyrogram (Kurigram fork)
- **Voice Chat Engine**: py-tgcalls 1.2.1 with ntgcalls 1.2.1
- **Database**: MongoDB (via motor)
- **Media**: yt-dlp for YouTube downloads, FFmpeg for audio/video processing

## Required Secrets

Before the bot can run, you must set these in the Secrets tab:

- `API_ID` — Telegram API ID from my.telegram.org/apps
- `API_HASH` — Telegram API Hash from my.telegram.org/apps
- `BOT_TOKEN` — Bot token from @BotFather
- `MONGO_DB_URI` — MongoDB connection string from cloud.mongodb.com
- `OWNER_ID` — Your Telegram user ID (from @userinfobot)
- `LOGGER_ID` — Telegram group ID for bot logs (bot must be admin there)
- `STRING_SESSION` — Pyrogram v2 session string from @StringFatherBot (required for voice chats)

## Running

The workflow command is `bash start`, which runs `python3 -m NOBITA_MUSIC`.

## Setup Notes

- The `NOBITA_MUSIC/` directory is the main package.
- All package names were normalized from `RONALDO_MUSIC` to `NOBITA_MUSIC` during import.
- py-tgcalls 1.2.1 is used with ntgcalls 1.2.1 for voice chat support.
- FFmpeg is installed as a system dependency via Nix.

## User Preferences

- Package names are normalized to `NOBITA_MUSIC` throughout the codebase.
