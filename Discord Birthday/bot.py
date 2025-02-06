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
    
    birthday_list = []  # Danh sách lưu những người có sinh nhật vào ngày mai

    for name, details in birthdays.items():
        birth_date = datetime.strptime(details["date_of_birth"], "%d/%m/%Y")
        if birth_date.day == tomorrow.day and birth_date.month == tomorrow.month:
            birthday_list.append(name)
    
    if birthday_list:
        channel = discord.utils.get(bot.get_all_channels(), name="bot-chat")
        if channel:
            message = (
                f"# Danh sách các thành viên có sinh nhật vào ngày mai - {tomorrow.strftime('%d/%m')} 🎂:\n"
                + "\n".join(f"- {name} 🥳" for name in birthday_list)
                + "\n\n@everyone Hãy cùng chuẩn bị chúc mừng sinh nhật cho các thành viên có sinh nhật vào ngày mai nhé! 🎉🎊"
            )
            await channel.send(message)

    # Xóa lời chúc của tất cả thành viên (vì hôm nay không phải ngày sinh nhật của họ)
    for details in birthdays.values():
        details["wishes"] = []

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
    
@bot.command(name="birthday_month")
async def birthday_month(ctx, month: int):
    """Hiển thị danh sách những người có sinh nhật trong tháng được chỉ định."""
    if month < 1 or month > 12:
        await ctx.send("Vui lòng nhập một tháng hợp lệ (1-12).")
        return

    birthdays = load_birthdays()
    found = []

    for name, details in birthdays.items():
        birth_date = datetime.strptime(details["date_of_birth"], "%d/%m/%Y")
        if birth_date.month == month:
            found.append(f"- {name}: {details['date_of_birth']}")

    if found:
        message = f"# 🎂 Danh sách thành viên có sinh nhật trong tháng {month}:\n" + "\n".join(found)
    else:
        message = f"Không có thành viên nào có sinh nhật trong tháng {month}."

    await ctx.send(message)
    
# Hàm chuẩn hóa họ tên
def normalize_name(name: str) -> str:
    """Chuẩn hóa họ tên: xóa khoảng trắng thừa và viết hoa chữ cái đầu."""
    return ' '.join(word.capitalize() for word in name.split())
    
@bot.command(name="add_birthday")
async def add_birthday(ctx):
    """Thêm sinh nhật của thành viên vào danh sách (chỉ dành cho [Leader] Duy Long)."""
    if ctx.author.nick != "[Leader] Duy Long":
        await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
        return

    await ctx.send("📌 Vui lòng nhập tên:")
    try:
        name_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=60)
        name = normalize_name(name_msg.content.strip())  # Chuẩn hóa họ tên
        await ctx.send(f"✅ Đã nhận được tên: **{name}**!")
    except asyncio.TimeoutError:
        await ctx.send("⏳ Lỗi: Bạn đã không nhập thông tin kịp thời.")
        return
    
    # Kiểm tra nếu tên đã tồn tại
    birthdays = load_birthdays()
    if name in birthdays:
        await ctx.send(f"⚠️ **{name}** đã tồn tại trong danh sách sinh nhật!")
        return
    
    
    await ctx.send("📌 Vui lòng nhập ngày tháng năm sinh (dd/mm/yyyy):")
    # Hỏi ngày tháng năm sinh
    try:
        date_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=60)
        birth_date = date_msg.content.strip()
        
        # Kiểm tra định dạng ngày tháng năm sinh
        try:
            datetime.strptime(birth_date, "%d/%m/%Y")
        except ValueError:
            await ctx.send("⚠️ Sai định dạng! Vui lòng nhập đúng định dạng **dd/mm/yyyy**.")
            return
    except asyncio.TimeoutError:
        await ctx.send("⏳ Lỗi: Bạn đã không nhập thông tin kịp thời.")
        return

    # Lưu thông tin sinh nhật vào file
    birthdays[name] = {
        "date_of_birth": birth_date,
        "wishes": []
    }
    save_birthdays(birthdays)
    await ctx.send(f"🎉 Đã thêm sinh nhật của **{name}** vào danh sách thành công!")

@bot.command()
async def hello(ctx):
    nickname = ctx.author.nick or ctx.author.name
    await ctx.send(f"Xin chào {nickname}!\nChúc bạn một ngày vui vẻ!")

@bot.command(name="help_me")
async def help_command(ctx):
    help_message = """
# Danh sách các lệnh của bot:
- `\\hello` : Lệnh chào hỏi và gửi lời chúc.
- `\\birthdays` : Hiển thị danh sách sinh nhật của các thành viên trong nhóm.
- `\\birthday_month` : Hiển thị danh sách sinh nhật của các thành viên theo tháng.
- `\\birthday_wishes <lời chúc>` : Gửi lời chúc sinh nhật cho thành viên có sinh nhật vào ngày mai.
- `\\help_me` : Hiển thị danh sách các lệnh và chức năng của bot.
"""
    await ctx.send(help_message)

bot.run(TOKEN)
