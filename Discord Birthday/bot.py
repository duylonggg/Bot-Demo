import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
import asyncio

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="\\", intents=intents)

BIRTHDAY_FILE = "birthdays.json"

def load_birthdays():
    if os.path.exists(BIRTHDAY_FILE):
        with open(BIRTHDAY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}

def save_birthdays(data):
    with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_time_until_midnight():
    """Tính thời gian còn lại đến 00h00p00s của ngày hôm sau."""
    now = datetime.now()
    midnight = datetime.combine(now + timedelta(days=1), datetime.min.time())  # Ngày tiếp theo vào 00h00
    return midnight - now

@bot.event
async def on_ready():
    print(f"{bot.user} đã sẵn sàng!\n")
    
    # Tính thời gian còn lại đến 00h00p00s để bắt đầu vòng lặp
    time_until_midnight = get_time_until_midnight()
    await bot.wait_until_ready()
    
    # Sau khi đợi đến đúng 00h00p00s, sẽ bắt đầu vòng lặp kiểm tra sinh nhật
    print(f"{bot.user} sẽ chạy kiểm tra sinh nhật sau {time_until_midnight}\n")
    await asyncio.sleep(time_until_midnight.total_seconds())  # Đợi đến 00h00p00s
    check_birthdays.start()
    check_tomorrow_birthdays.start()

@tasks.loop(hours=24)
async def check_tomorrow_birthdays():
    """Kiểm tra xem ngày mai có sinh nhật ai không."""
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    birthdays = load_birthdays()
    for name, details in birthdays.items():
        birth_date = datetime.strptime(details["date_of_birth"], "%d/%m/%Y")
        # So sánh chỉ ngày và tháng
        if birth_date.day == tomorrow.day and birth_date.month == tomorrow.month:
            channel = discord.utils.get(bot.get_all_channels(), name="bot-chat")
            if channel:
                await channel.send(
                    f"🌟 Ngày mai là sinh nhật của {name}!\n"
                    f"Hãy gửi lời chúc cho bạn ấy thông qua lệnh `\\birthday_wishes`."
                )
        else:
            if details["wishes"]:
                details["wishes"] = []  # Xóa lời chúc nếu ngày mai không phải sinh nhật

    # Lưu lại dữ liệu đã cập nhật vào file
    save_birthdays(birthdays)

@tasks.loop(hours=24)
async def check_birthdays():
    """Kiểm tra xem hôm nay có sinh nhật ai không."""
    now = datetime.now()
    birthdays = load_birthdays()
    for name, details in birthdays.items():
        birth_date = datetime.strptime(details["date_of_birth"], "%d/%m/%Y")
        if birth_date.day == now.day and birth_date.month == now.month:
            channel = discord.utils.get(bot.get_all_channels(), name="bot-chat")
            if channel:
                await channel.send(f"🎉 Hôm nay là sinh nhật của {name}! Chúc mừng sinh nhật! 🎂")
                if details["wishes"]:
                    wishes = "\n".join(details["wishes"])
                    await channel.send(f"Lời chúc từ mọi người:\n{wishes}")

@bot.command(name="birthday_wishes")
async def birthday_wishes(ctx, *, wish=None):
    """Người dùng gửi lời chúc sinh nhật."""
    if not wish:
        await ctx.send("Vui lòng nhập lời chúc sinh nhật.")
        return

    birthdays = load_birthdays()
    now = datetime.now() + timedelta(days=1)
    for name, details in birthdays.items():
        birth_date = datetime.strptime(details["date_of_birth"], "%d/%m/%Y")
        if birth_date.day == now.day and birth_date.month == now.month:
            details["wishes"].append(f"{ctx.author.nick}: {wish}")
            save_birthdays(birthdays)
            await ctx.send(f"Đã lưu lời chúc của bạn cho {name}.")
            return
    await ctx.send("Ngày mai không có sinh nhật nào để lưu lời chúc.")
    
@bot.command()
async def hello(ctx):
    # Lấy tên người dùng (có thể là nick hoặc username)
    nickname = ctx.author.nick
    # Gửi lời chào
    await ctx.send(f"Xin chào {nickname}!\nChúc bạn một ngày vui vẻ!")
    
@bot.command(name="birthdays")
async def birthdays(ctx):
    """In ra danh sách sinh nhật của tất cả người dùng, sắp xếp theo ngày sinh."""
    birthdays = load_birthdays()  # Tải dữ liệu sinh nhật từ file
    if not birthdays:
        await ctx.send("Không có dữ liệu sinh nhật nào được lưu trữ.")
        return

    # Tạo tiêu đề cho danh sách
    message = "🎉 **Danh sách ngày sinh của các thành viên trong Nhà Khoa Học Thất Tình**:\n"

    # Sắp xếp danh sách theo ngày sinh (theo định dạng yyyy-mm-dd)
    sorted_birthdays = sorted(birthdays.items(), key=lambda item: datetime.strptime(item[1]['date_of_birth'], "%d/%m/%Y"))

    # Thêm từng thành viên và ngày sinh vào danh sách
    for name, details in sorted_birthdays:
        message += f"- {name}: {details['date_of_birth']}\n"

    # Gửi danh sách sinh nhật
    await ctx.send(message)
    
@bot.command(name="code")
async def help_command(ctx):
    """Hiển thị danh sách các lệnh và chức năng của bot."""
    help_message = """
**Danh sách các lệnh bot:**

- `\\hello` : Lệnh chào hỏi và gửi lời chúc.
- `\\birthdays` : Hiển thị danh sách sinh nhật của các thành viên trong nhóm.
- `\\birthday_wishes <lời chúc>` : Gửi lời chúc sinh nhật cho thành viên có sinh nhật vào ngày mai.
- `\\code` : Hiển thị danh sách các lệnh và chức năng của bot.

**Chúc bạn có một ngày vui vẻ! 🎉**
"""
    await ctx.send(help_message)

bot.run(TOKEN)
