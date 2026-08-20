import os
import uuid

from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

DATABASE_URL = os.environ["HISTORY_DB_URL"]


engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


class Investigation(Base):

    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="running",
    )

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    result_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    metrics_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    events: Mapped[list["InvestigationEvent"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="InvestigationEvent.sequence",
    )


class InvestigationEvent(Base):

    __tablename__ = "investigation_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    investigation_id: Mapped[str] = mapped_column(
        ForeignKey(
            "investigations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    agent: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    tool: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    investigation: Mapped["Investigation"] = relationship(
        back_populates="events",
    )


async def init_history_database():

    async with engine.begin() as connection:

        await connection.run_sync(Base.metadata.create_all)


async def create_investigation(
    message: str,
) -> Investigation:

    investigation = Investigation(
        id=str(uuid.uuid4()),
        message=message,
        status="running",
        created_at=datetime.now(timezone.utc),
    )

    async with SessionLocal() as session:

        session.add(investigation)

        await session.commit()

        await session.refresh(investigation)

    return investigation


async def save_event(
    investigation_id: str,
    sequence: int,
    event: dict,
):

    known_fields = {
        "type",
        "agent",
        "tool",
        "message",
    }

    extra_data = {key: value for key, value in event.items() if key not in known_fields}

    db_event = InvestigationEvent(
        investigation_id=investigation_id,
        sequence=sequence,
        event_type=event.get(
            "type",
            "unknown",
        ),
        agent=event.get("agent"),
        tool=event.get("tool"),
        message=event.get("message"),
        data=extra_data or None,
        created_at=datetime.now(timezone.utc),
    )

    async with SessionLocal() as session:

        session.add(db_event)

        await session.commit()


async def complete_investigation(
    investigation_id: str,
    diagnosis: dict,
    metrics: dict,
):

    async with SessionLocal() as session:

        investigation = await session.get(
            Investigation,
            investigation_id,
        )

        if investigation is None:
            return

        investigation.status = "completed"

        investigation.result_json = diagnosis

        investigation.metrics_json = metrics

        investigation.result = diagnosis.get(
            "narrative",
            "",
        )

        investigation.completed_at = datetime.now(timezone.utc)

        await session.commit()


async def fail_investigation(
    investigation_id: str,
    error: str,
):

    async with SessionLocal() as session:

        investigation = await session.get(
            Investigation,
            investigation_id,
        )

        if investigation is None:
            return

        investigation.status = "failed"

        investigation.error = error

        investigation.completed_at = datetime.now(timezone.utc)

        await session.commit()


async def list_investigations(
    limit: int = 50,
):

    async with SessionLocal() as session:

        result = await session.execute(
            select(Investigation).order_by(Investigation.created_at.desc()).limit(limit)
        )

        investigations = result.scalars().all()

        return [
            {
                "id": item.id,
                "message": item.message,
                "status": item.status,
                "created_at": item.created_at.isoformat(),
                "completed_at": (
                    item.completed_at.isoformat() if item.completed_at else None
                ),
                "headline": (item.result_json or {})
                .get(
                    "summary",
                    {},
                )
                .get("headline"),
                "metrics": item.metrics_json,
            }
            for item in investigations
        ]


async def get_investigation(
    investigation_id: str,
):

    async with SessionLocal() as session:

        investigation = await session.get(
            Investigation,
            investigation_id,
        )

        if investigation is None:
            return None

        event_result = await session.execute(
            select(InvestigationEvent)
            .where(InvestigationEvent.investigation_id == investigation_id)
            .order_by(InvestigationEvent.sequence)
        )

        events = event_result.scalars().all()

        return {
            "id": investigation.id,
            "message": investigation.message,
            "status": investigation.status,
            "result": investigation.result,
            "diagnosis": investigation.result_json,
            "metrics": investigation.metrics_json,
            "error": investigation.error,
            "created_at": investigation.created_at.isoformat(),
            "completed_at": (
                investigation.completed_at.isoformat()
                if investigation.completed_at
                else None
            ),
            "events": [
                {
                    "sequence": event.sequence,
                    "type": event.event_type,
                    "agent": event.agent,
                    "tool": event.tool,
                    "message": event.message,
                    "data": event.data,
                    "created_at": event.created_at.isoformat(),
                }
                for event in events
            ],
        }
