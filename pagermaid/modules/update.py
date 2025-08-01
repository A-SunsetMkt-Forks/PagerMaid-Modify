from pagermaid.common.update import update as update_function
from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.utils import lang, alias_command


@listener(
    is_plugin=False,
    outgoing=True,
    command=alias_command("update"),
    need_admin=True,
    description=lang("update_des"),
    parameters="<true/debug>",
)
async def update(message: Message):
    await update_function(len(message.parameter) > 0)
    await message.edit(lang("update_success"))
    await message.client.disconnect()
