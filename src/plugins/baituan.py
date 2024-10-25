import json
import time
import psycopg2
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, Message
from nonebot.params import CommandArg

echo = on_command("echo")


@echo.handle()
async def add_whitelist_handler(bot: Bot, event: PrivateMessageEvent, args: Message = CommandArg()):
    user_id = event.user_id
    await bot.send_private_msg(user_id=user_id, message=args)

