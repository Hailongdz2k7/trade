import discord
import asyncio
from breakout_bot import scan_market, check_one

TOKEN = "MTM5NzIwMjY1MzM2NDM1OTIwMA.GOS7sC.31tkL3NsIw5dgzfufVNQGX2XMM6eQ7I2OhqBA4"
CHANNEL_ID = 1397092859991035904  # Thay bằng channel ID bạn muốn gửi tín hiệu

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"[✅] Đã đăng nhập thành: {bot.user}")
    bot.loop.create_task(run_hourly_check())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!out all"):
        await message.channel.send("⏳ Đang quét tín hiệu toàn thị trường...")
        signals = scan_market()
        if not signals:
            await message.channel.send("❌ Không tìm thấy tín hiệu breakout nào.")
        for symbol, price, chart in signals:
            file = discord.File(chart, filename=f"{symbol}.png")
            await message.channel.send(
                content=f"🚨 Breakout: **{symbol}**\n💰 Giá: `{price}` USDT",
                file=file
            )

    elif message.content.startswith("!out "):
        _, symbol = message.content.split(" ", 1)
        result = check_one(symbol.upper())
        if result:
            sym, price, chart = result
            file = discord.File(chart, filename=f"{sym}.png")
            await message.channel.send(
                content=f"🚨 Breakout: **{sym}**\n💰 Giá: `{price}` USDT",
                file=file
            )
        else:
            await message.channel.send(f"❌ Không có tín hiệu breakout cho `{symbol.upper()}`.")

async def run_hourly_check():
    await bot.wait_until_ready()
    while not bot.is_closed():
        channel = bot.get_channel(CHANNEL_ID)
        signals = scan_market()
        for symbol, price, chart in signals:
            file = discord.File(chart, filename=f"{symbol}.png")
            await channel.send(
                content=f"📢 **Tín hiệu tự động phát hiện breakout**: {symbol}\n💰 Giá: `{price}` USDT",
                file=file
            )
        await asyncio.sleep(3600)  # 1 giờ

bot.run(TOKEN)
