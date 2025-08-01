from typing import NewType, Callable, Any, Awaitable, Union, TYPE_CHECKING, Optional

from ..inject import inject

if TYPE_CHECKING:
    from . import Message

CommandHandlerFunc = NewType("CommandHandlerFunc", Callable[[Any, Any], Awaitable[Any]])
CommandHandlerDecorator = NewType(
    "CommandHandlerDecorator",
    Callable[[Union["CommandHandler", CommandHandlerFunc]], "CommandHandler"],
)


class CommandHandler:
    ignore_sub_commands_key = "_ignore_sub_commands"

    def __init__(self, func: CommandHandlerFunc, command: Optional[str]) -> None:
        self._pgp_func__: CommandHandlerFunc = func
        self._pgp_command__: Optional[str] = command
        self._pgp_raw_handler = None

    def func(self) -> CommandHandlerFunc:
        return self._pgp_func__

    def __call__(self, *args, **kwargs):
        return self.func()(*args, **kwargs)

    def set_handler(self, handler):
        self._pgp_raw_handler = handler

    def get_handler(self):
        return self._pgp_raw_handler

    async def handler(self, context: "Message"):
        func = self.func()
        if data := inject(context, func):
            await func(**data)
        else:
            if func.__code__.co_argcount == 0:
                await func()
            if func.__code__.co_argcount == 1:
                await func(context)
            if func.__code__.co_argcount == 2:
                await func(context.client, context)

    def sub_command(self, **kwargs) -> CommandHandlerDecorator:
        if self._pgp_command__ is None:
            raise ValueError("Cannot add subcommand to a handler without a command")
        if self._pgp_raw_handler is None:
            raise ValueError("Cannot add subcommand to a handler without init")
        setattr(self._pgp_raw_handler, self.ignore_sub_commands_key, True)
        from pagermaid.listener import listener

        def decorator(func: CommandHandlerFunc) -> CommandHandlerFunc:
            return listener(__parent_command=self._pgp_command__, **kwargs)(func)

        return decorator
