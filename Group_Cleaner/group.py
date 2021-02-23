import asyncio

import aiojobs

from pyrogram import Client, filters  # class pyrogram
from pyrogram.types import Message, InlineKeyboardButton, \
    InlineKeyboardMarkup, CallbackQuery  # class pyrogram
from pyrogram.errors.exceptions.bad_request_400 import UserIdInvalid, UserNotParticipant  # telegram error

from Group_Cleaner.helper import json_load, json_dump

groups_list = 'Group_Cleaner/groups.json'


def is_admin_filter(_, __, msg: Message):
    if not msg.from_user:
        return True

    try:
        member = msg.chat.get_member(msg.from_user.id)
        if member.status in ("creator", "administrator"):
            return True
    except UserNotParticipant:
        return False

    return False


@Client.on_message(filters.group & filters.create(is_admin_filter) &
                   filters.command(["clean", 'clean@GroupCleanerHebBot']))
# func for kick existing members
# using with telegram-commands: "/clean"
async def clean_group(client: Client, message: Message, name=None):
    # check if bot is admin
    me = await client.get_me()
    print(me)
    get_me = await message.chat.get_member(user_id=me.id)
    if get_me.status != "administrator":
        await message.reply("הרובוט דורש ניהול!\nThe robot requires management!")
        return

    count = 0  # Counted kickers
    async for member in message.chat.iter_members():
        id_member = member.user.id
        get_member = await message.chat.get_member(id_member)

        if get_member.status not in ["creator", "administrator"]:
            await message.chat.kick_member(id_member)  # kick member
            await message.chat.unban_member(id_member)  # remove member from black_list
            count += 1

    if count > 0:
        await message.reply(f'''מספר משתמשים שהוסרו:\nNumber of users removed:\n`{count}`''',
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("Delete / מחק", callback_data="delete")]]))

    else:
        await message.reply("לא נמצאו משתמשים להסרה!\nNo removable users found")


@Client.on_callback_query(filters.regex("delete"))
# func for delete msg with Click on button
def delete_msg_count(_: Client, call: CallbackQuery):
    call.message.delete()


@Client.on_message(filters.group & filters.new_chat_members)
# func for remove new_members
async def group(client: Client, message: Message):
    me = await client.get_me()

    scheduler = await aiojobs.create_scheduler()

    for new_member in message.new_chat_members:
        if me.id == new_member.id:
            continue

        try:
            member_id = new_member.id

            print(f'Kicking {member_id} from {message.chat.id}')
            kick = await message.chat.kick_member(member_id)

            await scheduler.spawn(unban(message, member_id))

            if type(kick) != bool:
                await kick.delete()  # delete the message "<bot> removed <user>"
        except UserIdInvalid:
            pass

    await message.delete()  # delete the message "<user> joined the group"

    # saved group to DB
    all_groups: list = json_load(groups_list)
    if message.chat.id not in all_groups:
        all_groups.append(message.chat.id)
        json_dump(all_groups, groups_list)


async def unban(message, member_id):
    print(f'Unbanning {member_id} from {message.chat.id}')

    await asyncio.sleep(20)

    await message.chat.unban_member(member_id)  # remove member from black_list


@Client.on_message(filters.group & filters.service, group=1)
# func for delete other service message
async def service_messages(_: Client, message: Message):
    await message.delete()
