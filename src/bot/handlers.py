from uuid import UUID

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from pydantic import HttpUrl, TypeAdapter, ValidationError

from src.bot.messages import *
from src.services.url_service import get_id_from_url
from src.services.url_service import URLService

router = Router()

@router.message(Command("start"))
async def command_start(message: Message, service: URLService):
    user = message.from_user
    full_name = user.full_name
    await message.answer(START_MESSAGE.format(name=full_name), 
                         parse_mode="markdown")


@router.message(Command("stats"))
async def command_stats(message: Message, command: CommandObject, service: URLService):
    adapter = TypeAdapter(UUID)
    try:
        token = command.args or ""
 
        adapter.validate_python(token)

        url_data = await service.get_short_url_data(token)
        
        if url_data is None:
            await message.reply(TOKEN_NOT_FOUND.format(token=token),
                                parse_mode="markdown")

        else:
            await message.reply(TOKEN_FOUND.format(
                url_id = url_data.url_id,
                original_url = url_data.original_url,
                clicks = url_data.clicks,
                created_at = url_data.created_at,
                status_token = url_data.status_token
                ), parse_mode="markdown")
        
    except ValidationError:
        await message.reply(NOT_TOKEN.format(token=token),
                      parse_mode="markdown")
    

@router.message(Command("create"))
async def command_create(message: Message, command: CommandObject, service: URLService):
    adapter = TypeAdapter(HttpUrl)
    try:
        url = command.args or ""

        adapter.validate_python(url)

        url_data = await service.create_short_url(url)

        await message.reply(URL_CREATED.format(
            url_id = url_data.url_id,
            original_url = url_data.original_url,
            clicks = url_data.clicks,
            created_at = url_data.created_at,
            status_token = url_data.status_token
            ), parse_mode="markdown")
        
    except ValidationError:
        await message.reply(NOT_URL.format(text=url),
                      parse_mode="markdown")


@router.message(F.text)
async def handle_text(message: Message, service: URLService):
    text = message.text
    url_id = get_id_from_url(text)

    original_url = await service.get_original_url(url_id)
    if original_url is None:
        await message.reply(URL_NOT_FOUND.format(url=text),
                            parse_mode="markdown")
    
    else:
        await message.reply(URL_FOUND.format(url=original_url),
                        parse_mode="markdown")
