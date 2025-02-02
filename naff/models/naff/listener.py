import asyncio
import inspect
from typing import Coroutine, Callable

from naff.api.events.internal import BaseEvent
from naff.client.const import MISSING, Absent
from naff.client.utils import get_event_name
from naff.models.naff.callback import CallbackObject

__all__ = ("Listener", "listen")


class Listener(CallbackObject):

    event: str
    """Name of the event to listen to."""
    callback: Coroutine
    """Coroutine to call when the event is triggered."""
    is_default_listener: bool
    """Whether this listener is provided automatically by the library, and might be unwanted by users."""
    disable_default_listeners: bool
    """Whether this listener supersedes default listeners.  If true, any default listeners will be unregistered."""
    delay_until_ready: bool
    """whether to delay the event until the client is ready"""

    def __init__(
        self,
        func: Callable[..., Coroutine],
        event: str,
        *,
        delay_until_ready: bool = False,
        is_default_listener: bool = False,
        disable_default_listeners: bool = False,
    ) -> None:
        super().__init__()

        if is_default_listener:
            disable_default_listeners = False

        self.event = event
        self.callback = func
        self.delay_until_ready = delay_until_ready
        self.is_default_listener = is_default_listener
        self.disable_default_listeners = disable_default_listeners

    @classmethod
    def create(
        cls,
        event_name: Absent[str | BaseEvent] = MISSING,
        *,
        delay_until_ready: bool = False,
        is_default_listener: bool = False,
        disable_default_listeners: bool = False,
    ) -> Callable[[Coroutine], "Listener"]:
        """
        Decorator for creating an event listener.

        Args:
            event_name: The name of the event to listen to. If left blank, event name will be inferred from the function name or parameter.
            delay_until_ready: Whether to delay the listener until the client is ready.
            is_default_listener: Whether this listener is provided automatically by the library, and might be unwanted by users.
            disable_default_listeners: Whether this listener supersedes default listeners.  If true, any default listeners will be unregistered.


        Returns:
            A listener object.

        """

        def wrapper(coro: Coroutine) -> "Listener":
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError("Listener must be a coroutine")

            name = event_name

            if name is MISSING:
                for typehint in coro.__annotations__.values():
                    if (
                        inspect.isclass(typehint)
                        and issubclass(typehint, BaseEvent)
                        and typehint.__name__ != "RawGatewayEvent"
                    ):
                        name = typehint.__name__
                        break

                if not name:
                    name = coro.__name__

            return cls(
                coro,
                get_event_name(name),
                delay_until_ready=delay_until_ready,
                is_default_listener=is_default_listener,
                disable_default_listeners=disable_default_listeners,
            )

        return wrapper


def listen(
    event_name: Absent[str | BaseEvent] = MISSING,
    *,
    delay_until_ready: bool = True,
    is_default_listener: bool = False,
    disable_default_listeners: bool = False,
) -> Callable[[Callable[..., Coroutine]], Listener]:
    """
    Decorator to make a function an event listener.

    Args:
        event_name: The name of the event to listen to. If left blank, event name will be inferred from the function name or parameter.
        delay_until_ready: Whether to delay the listener until the client is ready.
        is_default_listener: Whether this listener is provided automatically by the library, and might be unwanted by users.
        disable_default_listeners: Whether this listener supersedes default listeners.  If true, any default listeners will be unregistered.


    Returns:
        A listener object.

    """
    return Listener.create(
        event_name,
        delay_until_ready=delay_until_ready,
        is_default_listener=is_default_listener,
        disable_default_listeners=disable_default_listeners,
    )
