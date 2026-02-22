from datetime import datetime, timezone
from typing import Any

from nonebot.adapters import Bot as BaseBot
from nonebot.message import event_postprocessor
from nonebot_plugin_orm import get_session
from nonebot_plugin_uninfo import (
    Scene,
    SceneType,
    Session,
    SupportAdapter,
    SupportScope,
    Uninfo,
    User,
)
from nonebot_plugin_uninfo.orm import get_session_persist_id
from typing_extensions import override

from ..config import plugin_config
from ..message import (
    MessageDeserializer,
    MessageSerializer,
    register_deserializer,
    register_serializer,
    serialize_message,
)
from ..model import MessageRecord
from ..utils import record_type, remove_timezone

try:
    from nonebot.adapters.milky import Bot, Message, MessageEvent
    from nonebot.adapters.milky.model.api import MessageResponse

    adapter = SupportAdapter.milky

    @event_postprocessor
    async def record_recv_msg(event: MessageEvent, session: Uninfo):
        session_persist_id = await get_session_persist_id(session)

        record = MessageRecord(
            session_persist_id=session_persist_id,
            time=remove_timezone(datetime.fromtimestamp(event.time, timezone.utc)),
            type=record_type(event),
            message_id=str(event.data.message_seq),
            message=serialize_message(adapter, event.get_message()),
            plain_text=event.get_plaintext(),
        )
        async with get_session() as db_session:
            db_session.add(record)
            await db_session.commit()

    if plugin_config.chatrecorder_record_send_msg:

        @Bot.on_called_api
        async def record_send_msg(
            bot: BaseBot,
            e: Exception | None,
            api: str,
            data: dict[str, Any],
            result: Any,
        ):
            if not isinstance(bot, Bot):
                return
            if e or not result:
                return
            if api not in [
                "send_private_message",
                "send_group_message",
                "send_temp_message",
            ]:
                return

            if not isinstance(result, MessageResponse):
                return

            if api == "send_group_message":
                scene_type = SceneType.GROUP
                scene_id = str(data["group_id"])
            elif api == "send_private_message":
                scene_type = SceneType.PRIVATE
                scene_id = str(data["user_id"])
            elif api == "send_temp_message":
                scene_type = SceneType.PRIVATE
                scene_id = f"{data['user_id']}"
            else:
                return

            session = Session(
                self_id=bot.self_id,
                adapter=adapter,
                scope=SupportScope.qq_client,
                scene=Scene(id=scene_id, type=scene_type),
                user=User(id=bot.self_id),
            )
            session_persist_id = await get_session_persist_id(session)

            message = Message(data["message"])
            message_time = remove_timezone(
                datetime.fromtimestamp(result.time, timezone.utc)
            )

            record = MessageRecord(
                session_persist_id=session_persist_id,
                time=message_time,
                type="message_sent",
                message_id=str(result.message_seq),
                message=serialize_message(adapter, message),
                plain_text=message.extract_plain_text(),
            )
            async with get_session() as db_session:
                db_session.add(record)
                await db_session.commit()

    class Serializer(MessageSerializer[Message]):
        pass

    class Deserializer(MessageDeserializer[Message]):
        @classmethod
        @override
        def get_message_class(cls) -> type[Message]:
            return Message

    register_serializer(adapter, Serializer)
    register_deserializer(adapter, Deserializer)

except ImportError:
    pass
