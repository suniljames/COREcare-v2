"""Message thread service for the Client persona (issue #125).

Per Data Engineer §4: extends the existing Message model rather than forking
the messaging substrate. Adds MessageThread to anchor agency-side inbox
enumeration. The thread is one-per-Client-per-agency.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message_thread import MessageThread
from app.models.notification import Message


class MessageThreadService:
    """Get-or-create thread + send messages on behalf of a Client."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_for_client(
        self, client_id: uuid.UUID, agency_id: uuid.UUID
    ) -> MessageThread:
        """Return the (Client, Agency) thread, creating it if absent.

        Two simultaneous first-loads can race on the unique constraint on
        client_id; on IntegrityError we re-fetch the row created by the
        winning transaction (SRE §2, round-1 review).
        """
        result = await self.session.execute(
            select(MessageThread).where(
                MessageThread.client_id == client_id  # type: ignore[arg-type]
            )
        )
        thread = result.scalar_one_or_none()
        if thread is not None:
            return thread

        thread = MessageThread(
            client_id=client_id,
            agency_id=agency_id,
            last_message_at=datetime.now(UTC),
        )
        self.session.add(thread)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            result = await self.session.execute(
                select(MessageThread).where(
                    MessageThread.client_id == client_id  # type: ignore[arg-type]
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                raise
            return existing
        await self.session.refresh(thread)
        return thread

    async def list_messages(self, thread_id: uuid.UUID) -> list[Message]:
        """List messages in a thread, oldest first."""
        result = await self.session.execute(
            select(Message)
            .where(Message.thread_id == thread_id)  # type: ignore[arg-type]
            .order_by(Message.created_at.asc())  # type: ignore[attr-defined]
        )
        return list(result.scalars().all())

    async def send_from_client(
        self,
        *,
        client_id: uuid.UUID,
        sender_user_id: uuid.UUID,
        body: str,
        agency_id: uuid.UUID,
    ) -> Message:
        """Send a message from the Client into their thread.

        Routing is by thread_id — the agency-side inbox enumerates threads,
        not per-staff recipients. recipient_id is left None on Client→agency
        messages; per-recipient family messages still populate it.
        """
        thread = await self.get_or_create_for_client(client_id, agency_id)

        msg = Message(
            sender_id=sender_user_id,
            recipient_id=None,
            thread_id=thread.id,
            body=body,
            agency_id=agency_id,
        )
        self.session.add(msg)
        thread.last_message_at = datetime.now(UTC)
        self.session.add(thread)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg
