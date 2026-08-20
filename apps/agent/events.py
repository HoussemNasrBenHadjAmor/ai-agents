from typing import Awaitable, Callable, Optional


EventCallback = Optional[
    Callable[[dict], Awaitable[None]]
]


async def emit(
    callback: EventCallback,
    event_type: str,
    **data,
):
    if callback is None:
        return

    await callback(
        {
            "type": event_type,
            **data,
        }
    )
