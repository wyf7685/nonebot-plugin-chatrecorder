from datetime import datetime, timezone
from typing import cast

from nonebot import get_driver
from nonebot.adapters.milky import Adapter, Bot, Message, MessageSegment
from nonebot.adapters.milky.config import ClientInfo
from nonebot.adapters.milky.event import (
    FriendMessageEvent,
    GroupMessageEvent,
    MessageEvent,
    TempMessageEvent,
)
from nonebot.adapters.milky.model.api import MessageResponse
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebug.app import App

from .utils import check_record


def fake_group_message_event(content: str, message_seq: int) -> GroupMessageEvent:
    event = MessageEvent(  # pyright: ignore[reportCallIssue]
        __event_type__="message_receive",
        time=1000000,
        self_id=2233,
        data=IncomingMessage(
            message_scene="group",
            peer_id=5566,
            message_seq=message_seq,
            sender_id=3344,
            time=1000000,
            segments=[{"type": "text", "data": {"text": content}}],
        ),
    )
    return cast("GroupMessageEvent", event.convert())


def fake_private_message_event(content: str, message_seq: int) -> FriendMessageEvent:
    event = MessageEvent(  # pyright: ignore[reportCallIssue]
        __event_type__="message_receive",
        time=1000000,
        self_id=2233,
        data=IncomingMessage(
            message_scene="friend",
            peer_id=3344,
            message_seq=message_seq,
            sender_id=3344,
            time=1000000,
            segments=[{"type": "text", "data": {"text": content}}],
        ),
    )
    return cast("FriendMessageEvent", event.convert())


def fake_temp_message_event(content: str, message_seq: int) -> TempMessageEvent:
    event = MessageEvent(  # pyright: ignore[reportCallIssue]
        __event_type__="message_receive",
        time=1000000,
        self_id=2233,
        data=IncomingMessage(
            message_scene="temp",
            peer_id=5566,
            message_seq=message_seq,
            sender_id=3344,
            time=1000000,
            segments=[{"type": "text", "data": {"text": content}}],
        ),
    )
    return cast("TempMessageEvent", event.convert())


async def test_record_recv_msg(app: App):
    """测试记录收到的消息"""
    from nonebot_plugin_uninfo import Scene, SceneType, Session, User

    from nonebot_plugin_chatrecorder.adapters.milky import record_recv_msg
    from nonebot_plugin_chatrecorder.message import serialize_message

    group_msg = "test group message"
    group_msg_seq = 114514

    private_msg = "test private message"
    private_msg_seq = 114515

    temp_msg = "test temp message"
    temp_msg_seq = 114516

    async with app.test_api() as ctx:
        adapter = get_driver()._adapters[Adapter.get_name()]
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter,
            self_id="2233",
            info=ClientInfo(
                host="127.0.0.1",
                port=8080,
            ),
        )

    # 测试群消息
    event = fake_group_message_event(group_msg, group_msg_seq)
    session = Session(
        self_id="2233",
        adapter="Milky",
        scope="QQClient",
        scene=Scene(id="5566", type=SceneType.GROUP),
        user=User(id="3344"),
    )
    await record_recv_msg(event, session)
    await check_record(
        session,
        datetime.fromtimestamp(1000000, timezone.utc),
        "message",
        str(group_msg_seq),
        serialize_message(bot, Message(group_msg)),
        group_msg,
    )

    # 测试私聊消息
    event = fake_private_message_event(private_msg, private_msg_seq)
    session = Session(
        self_id="2233",
        adapter="Milky",
        scope="QQClient",
        scene=Scene(id="3344", type=SceneType.PRIVATE),
        user=User(id="3344"),
    )
    await record_recv_msg(event, session)
    await check_record(
        session,
        datetime.fromtimestamp(1000000, timezone.utc),
        "message",
        str(private_msg_seq),
        serialize_message(bot, Message(private_msg)),
        private_msg,
    )

    # 测试临时消息
    event = fake_temp_message_event(temp_msg, temp_msg_seq)
    session = Session(
        self_id="2233",
        adapter="Milky",
        scope="QQClient",
        scene=Scene(id="5566_3344", type=SceneType.GROUP),
        user=User(id="3344"),
    )
    await record_recv_msg(event, session)
    await check_record(
        session,
        datetime.fromtimestamp(1000000, timezone.utc),
        "message",
        str(temp_msg_seq),
        serialize_message(bot, Message(temp_msg)),
        temp_msg,
    )


async def test_record_send_msg(app: App):
    """测试记录发送的消息"""
    from nonebot_plugin_uninfo import Scene, SceneType, Session, User

    from nonebot_plugin_chatrecorder.adapters.milky import record_send_msg
    from nonebot_plugin_chatrecorder.message import serialize_message

    async with app.test_api() as ctx:
        adapter = get_driver()._adapters[Adapter.get_name()]
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter,
            self_id="2233",
            info=ClientInfo(
                host="127.0.0.1",
                port=8080,
            ),
        )

    # 测试发送群消息
    message_seq = 114517
    time = 1000001
    message = Message("test send_group_message")
    await record_send_msg(
        bot,
        None,
        "send_group_message",
        {
            "group_id": 5566,
            "message": [MessageSegment.text("test send_group_message")],
        },
        MessageResponse(message_seq=message_seq, time=time),
    )
    await check_record(
        Session(
            self_id="2233",
            adapter="Milky",
            scope="QQClient",
            scene=Scene(id="5566", type=SceneType.GROUP),
            user=User(id="2233"),
        ),
        datetime.fromtimestamp(time, timezone.utc),
        "message_sent",
        str(message_seq),
        serialize_message(bot, message),
        message.extract_plain_text(),
    )

    # 测试发送私聊消息
    message_seq = 114518
    time = 1000002
    message = Message("test send_private_message")
    await record_send_msg(
        bot,
        None,
        "send_private_message",
        {
            "user_id": 3344,
            "message": [MessageSegment.text("test send_private_message")],
        },
        MessageResponse(message_seq=message_seq, time=time),
    )
    await check_record(
        Session(
            self_id="2233",
            adapter="Milky",
            scope="QQClient",
            scene=Scene(id="3344", type=SceneType.PRIVATE),
            user=User(id="2233"),
        ),
        datetime.fromtimestamp(time, timezone.utc),
        "message_sent",
        str(message_seq),
        serialize_message(bot, message),
        message.extract_plain_text(),
    )
