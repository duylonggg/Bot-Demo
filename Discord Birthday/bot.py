import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta, time
import pytz
import asyncio

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="\\", intents=intents)

BIRTHDAY_FILE = "birthdays.json"

# Cài đặt múi giờ Việt Nam
local_tz = pytz.timezone("Asia/Ho_Chi_Minh")

def load_birthdays():
    if os.path.exists(BIRTHDAY_FILE):
        with open(BIRTHDAY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}

def save_birthdays(data):
    with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.event
async def on_ready():
    print(f"{bot.user} đã sẵn sàng!")
    check_birthdays.start()
    check_tomorrow_birthdays.start()

@tasks.loop(time=time(0, 0, 0, tzinfo=local_tz))
async def check_birthdays():
    """Kiểm tra xem hôm nay có sinh nhật ai không."""
    now = datetime.now(local_tz)
    birthdays = load_birthdays()
    for name, details in birthdays.items():
        birth_date = datetime.strptime(details["date_of_birth"], "%d/%m/%Y")
        if birth_date.day == now.day and birth_date.month == now.month:
            channel = discord.utils.get(bot.get_all_channels(), name="bot-chat")
            if channel:
                await channel.send(
                    f"# 🎉 Hôm nay là sinh nhật của {name}!\n"
                    f"Chúc mừng sinh nhật {name}! 🎂. Chúc {name} tuổi mới vui vẻ hạnh phúc, ngày càng thành công trên con đường phía trước 🎉🎉🎉!\n"
                    f"@everyone hãy chúc mừng sinh nhật {name} nhé!!!"
                )
                if details["wishes"]:
                    wishes = "\n".join(details["wishes"])
                    await channel.send(f"Lời chúc từ mọi người:\n{wishes}")

@tasks.loop(time=time(0, 0, 0, tzinfo=local_tz))
async def check_tomorrow_birthdays():
    """Kiểm tra xem ngày mai có sinh nhật ai không."""
    now = datetime.now(local_tz)
    tomorrow = now + timedelta(days=1)
    birthdays = load_birthdays()
    
    for name, details in birthdays.items():
        birth_date = datetime.strptime(details["date_of_birth"], "%d/%m/%Y")
        if birth_date.day == tomorrow.day and birth_date.month == tomorrow.month:
            channel = discord.utils.get(bot.get_all_channels(), name="bot-chat")
            if channel:
                await channel.send(
                    f"# Danh sách các thành viên có sinh nhật vào ngày mai - {tomorrow.strftime('%d/%m')} 🎂:\n"
                    f"- {name}. 🥳\n\n"
                    f"@everyone Hãy cùng chuẩn bị chúc mừng sinh nhật cho các thành viên có sinh nhật vào ngày mai nhé! 🎉🎊"
                )
        else:
            if details["wishes"]:
                details["wishes"] = []  # Xóa lời chúc nếu ngày mai không phải sinh nhật

    save_birthdays(birthdays)

@bot.command(name="birthday_wishes")
async def birthday_wishes(ctx, *, wish=None):
    """Người dùng gửi lời chúc sinh nhật."""
    if not wish:
        await ctx.send("Vui lòng nhập lời chúc sinh nhật.")
        return

    birthdays = load_birthdays()
    now = datetime.now(local_tz) + timedelta(days=1)
    for name, details in birthdays.items():
        birth_date = datetime.strptime(details["date_of_birth"], "%d/%m/%Y")
        if birth_date.day == now.day and birth_date.month == now.month:
            details["wishes"].append(f"{ctx.author.nick}: {wish}")
            save_birthdays(birthdays)
            await ctx.send(f"Đã lưu lời chúc của bạn cho {name}.")
            return
    await ctx.send("Ngày mai không có sinh nhật nào để lưu lời chúc.")

@bot.command(name="birthdays")
async def birthdays(ctx):
    """In ra danh sách sinh nhật của tất cả người dùng, sắp xếp theo ngày sinh."""
    birthdays = load_birthdays()
    if not birthdays:
        await ctx.send("Không có dữ liệu sinh nhật nào được lưu trữ.")
        return

    message = "# 🎉 Danh sách ngày sinh của các thành viên:\n"
    sorted_birthdays = sorted(birthdays.items(), key=lambda item: datetime.strptime(item[1]['date_of_birth'], "%d/%m/%Y"))

    for name, details in sorted_birthdays:
        message += f"- {name}: {details['date_of_birth']}\n"

    await ctx.send(message)

@bot.command()
async def hello(ctx):
    nickname = ctx.author.nick or ctx.author.name
    await ctx.send(f"Xin chào {nickname}!\nChúc bạn một ngày vui vẻ!")

@bot.command(name="code")
async def help_command(ctx):
    help_message = """
# Danh sách các lệnh của bot:
- `\\hello` : Lệnh chào hỏi và gửi lời chúc.
- `\\birthdays` : Hiển thị danh sách sinh nhật của các thành viên trong nhóm.
- `\\birthday_wishes <lời chúc>` : Gửi lời chúc sinh nhật cho thành viên có sinh nhật vào ngày mai.
- `\\code` : Hiển thị danh sách các lệnh và chức năng của bot.
"""
    await ctx.send(help_message)

bot.run(TOKEN)
