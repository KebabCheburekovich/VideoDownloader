import asyncio

from aiogram.types import Message

from keyboards.inline import button_resolutions, checkSubMenu
from keyboards.inline import link_in_button
from main import dp, bot
from utils.helpers import send_message, delete_message, send_video, get_link_via_resolution
from utils.match_urls import match_urls
from utils.tiktok.tiktok_helpers import get_tik_tok_data
from utils.vk.vk_main import get_vk_data
from utils.youtube.youtube_main import get_youtube_data


async def send(query, state):
    if await state.get_data():
        async with state.proxy() as data:
            link = await get_link_via_resolution(data["video_data"], query.data if query is not None else None)
            user = data["user_data"]
        lang = user["lang"]
        chat_id = state.chat
        last_message_id = user["last_message_id"] if "last_message_id" in user.keys() else None
        await state.reset_state()
        if last_message_id is not None:
            await delete_message(chat_id, last_message_id)
        last_message_id = await send_message(chat_id, "send_video", lang)
        if await send_video(chat_id, link, lang, last_message_id.message_id):
            # await send_message(chat_id, "send_video_complete", lang, last_message_id.message_id)
            await send_message(chat_id, "Adsub", lang, last_message_id.message_id, markup=checkSubMenu)
        else:
            await asyncio.sleep(.5)
            await send_message(chat_id, "failed_send_video", lang, last_message_id.message_id,
                               markup=await link_in_button(link))


@dp.message_handler()  # Answer to all messages
@dp.throttled(rate=2)  # Prevent flooding
async def chat_messages(message: Message):
    lang = "ru"
    last_message = await send_message(message.chat.id, "search_video", lang)
    host = await match_urls(message.text)

    if host == "TIKTOK":
        data, error = await get_tik_tok_data(message.text)
    elif host == "YOUTUBE":
        data, error = await get_youtube_data(message.text)
    elif host == "VK":
        data, error = await get_vk_data(message.text)
    else:
        await send_message(message.chat.id, "url_not_match", lang, last_message.message_id)
        return
    if error is not None:
        await send_message(message.chat.id, error, lang, last_message.message_id)
        return
    # print(link)
    await send_message(message.chat.id, "search_complete", lang, last_message.message_id)
    await asyncio.sleep(1)
    if await button_resolutions(message.chat.id, "video_preview", lang, last_message.message_id, data):
        await send(None, dp.get_current().current_state())
