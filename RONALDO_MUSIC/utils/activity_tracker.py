"""Global activity tracker — shared across bot, assistants, and cmd_logger."""

from datetime import datetime

# Command stats
total_commands = 0
command_log = []          # last 10 commands: (user, chat, cmd)

# Assistant registry: {number: {"name": ..., "id": ..., "username": ...}}
assistant_info = {}

# Bot info
bot_name = ""
bot_id = 0
bot_username = ""
start_time = datetime.utcnow()


def record_command(user_name: str, user_id: int, chat_title: str, chat_id: int, cmd: str):
    global total_commands
    total_commands += 1
    entry = {
        "user": f"{user_name} ({user_id})",
        "chat": f"{chat_title} ({chat_id})",
        "cmd": cmd[:60],
    }
    command_log.append(entry)
    if len(command_log) > 10:
        command_log.pop(0)


def register_assistant(number: int, name: str, uid: int, username: str):
    assistant_info[number] = {"name": name, "id": uid, "username": username or "N/A"}


def set_bot_info(name: str, uid: int, username: str):
    global bot_name, bot_id, bot_username
    bot_name = name
    bot_id = uid
    bot_username = username


def get_uptime_str() -> str:
    delta = datetime.utcnow() - start_time
    hours, rem = divmod(int(delta.total_seconds()), 3600)
    mins = rem // 60
    return f"{hours}h {mins}m"
