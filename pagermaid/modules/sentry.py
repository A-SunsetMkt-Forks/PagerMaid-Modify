import sys
from subprocess import run, PIPE
from time import time

import sentry_sdk
from telethon.errors import UnauthorizedError, UsernameInvalidError
from sentry_sdk.integrations.httpx import HttpxIntegration

from pagermaid.config import Config, SESSION_PATH
from pagermaid.enums import Client, Message
from pagermaid.hook import Hook
from pagermaid.utils import safe_remove


def sentry_before_send(event, hint):
    global sentry_sdk_report_time
    exc_info = hint.get("exc_info")
    if exc_info and isinstance(exc_info[1], (UnauthorizedError, UsernameInvalidError)):
        # The user has been deleted/deactivated or session revoked
        safe_remove(SESSION_PATH)
        sys.exit(1)
    if time() <= sentry_sdk_report_time + 30:
        sentry_sdk_report_time = time()
        return None
    else:
        sentry_sdk_report_time = time()
        return event


sentry_sdk_report_time = time()
sentry_sdk_git_hash = (
    run("git rev-parse HEAD", stdout=PIPE, shell=True, check=True)
    .stdout.decode()
    .strip()
)

# fixme: Not enough for dynamic disable sentry,
#  web server will still report if pgm start with Config.ERROR_REPORT = True
if Config.ERROR_REPORT:
    sentry_sdk.init(
        Config.SENTRY_API,
        traces_sample_rate=1.0,
        release=sentry_sdk_git_hash,
        before_send=sentry_before_send,
        environment="production",
        integrations=[
            HttpxIntegration(),
        ],
    )
else:
    sentry_sdk.init()


@Hook.on_startup()
async def sentry_init_id(bot: Client):
    if not bot.me:
        bot.me = await bot.get_me()
    data = {"id": bot.me.id, "name": bot.me.first_name, "ip_address": "{{auto}}"}
    if bot.me.username:
        data["username"] = bot.me.username
    sentry_sdk.set_user(data)


@Hook.process_error()
async def sentry_report(message: Message, command, exc_info, **_):
    if not Config.ERROR_REPORT:
        return
    sender_id = message.sender_id
    sentry_sdk.set_context(
        "Target",
        {
            "ChatID": str(message.chat_id),
            "UserID": str(sender_id),
            "Msg": message.text or "",
        },
    )
    if command:
        sentry_sdk.set_tag("com", command)
    sentry_sdk.capture_exception(exc_info)
