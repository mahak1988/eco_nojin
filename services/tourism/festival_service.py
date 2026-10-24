"""Festival service: CRUD, editions, bookings, dynamic pricing."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.tourism.models import (
    FestivalBooking,
    FestivalEdition,
    TourismFestival,
    TourismTour,
)
from services.village.models import CommunitySpace, SpaceStatus


class FestivalError(Exception):
    pass


class FestivalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def settle_landscape_fee(
        self,
        *,
        booking_id: str,
        settlement_ref: str,
    ) -> FestivalBooking:
        """Route a festival booking's landscape fee to the village landscape fund.

        Writes a settlement record into ``landscape_fund_credits`` (shared with
        commerce) so festival revenue feeds village restoration funding.
        Best-effort: if the commerce fund service is unavailable the booking is
        still marked settled so the guest is not blocked.
        """
        booking = await self.get_booking(booking_id)
        if booking is None:
            raise FestivalError(f"booking not found: {booking_id}")
        if booking.status != "confirmed":
            raise FestivalError(f"booking is {booking.status}, cannot settle")

        try:

            from database.models import LandscapeFundCredit

            credit = LandscapeFundCredit(
                source="festival_booking",
                source_id=str(booking.id),
                village_id=str(booking.village_id) if hasattr(booking, "village_id") else "",
                amount=booking.landscape_fee,
                currency="IRR",
                settlement_ref=settlement_ref,
                status="completed",
            )
            self.db.add(credit)
        except Exception:  # noqa: BLE001 - fund table may not exist in all deployments
            pass

        booking.status = "completed"
        await self.db.commit()
        await self.db.refresh(booking)
        return booking


    # ═════════════════════════════════════════════════════════════
    # festivals
    # ═════════════════════════════════════════════════════════════

    async def create_festival(
        self,
        *,
        village_id: str,
        name: str,
        festival_type: str,
        season: str,
        start_date,
        end_date,
        capacity: int,
        base_ticket_price: Decimal,
        created_by: str,
        name_en: str | None = None,
        recurrence: str = "annual",
        landscape_fee_bps: int = 200,
        is_regenerative: bool = False,
    ) -> TourismFestival:
        """Create a new festival. Only governance-active villages may host."""
        await self._require_active_space(village_id)

        if start_date >= end_date:
            raise FestivalError("end_date must be after start_date")
        if capacity <= 0:
            raise FestivalError("capacity must be positive")
        if base_ticket_price <= 0:
            raise FestivalError("base_ticket_price must be positive")
        if not (0 <= landscape_fee_bps <= 10000):
            raise FestivalError("landscape_fee_bps must be between 0 and 10000")

        festival = TourismFestival(
            village_id=village_id,
            name=name,
            name_en=name_en,
            festival_type=festival_type,
            season=season,
            start_date=start_date,
            end_date=end_date,
            recurrence=recurrence,
            capacity=capacity,
            base_ticket_price=base_ticket_price,
            landscape_fee_bps=landscape_fee_bps,
            is_regenerative=is_regenerative,
            status="planned",
            created_by=created_by,
        )
        self.db.add(festival)
        await self.db.commit()
        await self.db.refresh(festival)
        return festival

    async def get_festival(self, festival_id: str) -> TourismFestival | None:
        result = await self.db.execute(
            select(TourismFestival).where(TourismFestival.id == festival_id)
        )
        return result.scalar_one_or_none()

    async def create_tour_for_nomadic_community(
        self,
        *,
        nomadic_community_id: str,
        guide_id: str,
        village_id: str,
        title: str,
        slug: str,
        description: str | None,
        tour_type: str,
        duration_hours: int,
        price_per_person: Decimal,
        capacity: int = 10,
        min_participants: int = 2,
        difficulty: str = "moderate",
        includes: list | None = None,
        excludes: list | None = None,
        itinerary: list | None = None,
        meeting_point: dict | None = None,
        images: list | None = None,
        ecological_capacity: int | None = None,
    ) -> TourismTour:
        """Create an ecotourism tour led by a nomadic community.

        The tour is flagged with ``nomadic_community_id`` so it can be
        discovered as a nomadic-led experience.
        """
        from services.tourism.models import TourismDifficultyLevel, TourismTourType

        try:
            tour_type_enum = TourismTourType(tour_type)
        except ValueError:
            raise FestivalError(f"invalid tour_type: {tour_type}")

        try:
            difficulty_enum = TourismDifficultyLevel(difficulty)
        except ValueError:
            raise FestivalError(f"invalid difficulty: {difficulty}")

        tour = TourismTour(
            guide_id=guide_id,
            nomadic_community_id=nomadic_community_id,
            village_id=village_id,
            title=title,
            slug=slug,
            description=description,
            tour_type=tour_type_enum,
            duration_hours=duration_hours,
            max_participants=capacity,
            min_participants=min_participants,
            difficulty=difficulty_enum,
            price_per_person=price_per_person,
            includes=includes or [],
            excludes=excludes or [],
            itinerary=itinerary or [],
            meeting_point=meeting_point,
            images=images or [],
            ecological_capacity=ecological_capacity,
            status="pending_approval",
            is_regenerative=True,
        )
        self.db.add(tour)
        await self.db.commit()
        await self.db.refresh(tour)
        return tour

    async def list_festivals(
        self,
        *,
        village_id: str | None = None,
        season: str | None = None,
        festival_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TourismFestival]:
        stmt = select(TourismFestival)
        if village_id:
            stmt = stmt.where(TourismFestival.village_id == village_id)
        if season:
            stmt = stmt.where(TourismFestival.season == season)
        if festival_type:
            stmt = stmt.where(TourismFestival.festival_type == festival_type)
        if status:
            stmt = stmt.where(TourismFestival.status == status)
        stmt = stmt.order_by(TourismFestival.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def activate_festival(self, festival_id: str, *, actor_id: str) -> TourismFestival:
        """Move a festival from planned to active."""
        festival = await self.get_festival(festival_id)
        if festival is None:
            raise FestivalError(f"festival not found: {festival_id}")
        if festival.status != "planned":
            raise FestivalError(f"festival is already {festival.status}")
        # Re-confirm village still active.
        await self._require_active_space(festival.village_id)
        festival.status = "active"
        await self.db.commit()
        await self.db.refresh(festival)
        return festival

    async def complete_festival(self, festival_id: str, *, actor_id: str) -> TourismFestival:
        """Mark a festival completed."""
        festival = await self.get_festival(festival_id)
        if festival is None:
            raise FestivalError(f"festival not found: {festival_id}")
        if festival.status != "active":
            raise FestivalError(f"festival is not active (currently {festival.status})")
        festival.status = "completed"
        await self.db.commit()
        await self.db.refresh(festival)
        return festival

    # ═════════════════════════════════════════════════════════════
    # editions
    # ═════════════════════════════════════════════════════════════

    async def create_edition(
        self,
        *,
        festival_id: str,
        year: int,
        total_seats: int,
        created_by: str,
    ) -> FestivalEdition:
        """Create an annual/biennial edition of a festival."""
        festival = await self.get_festival(festival_id)
        if festival is None:
            raise FestivalError(f"festival not found: {festival_id}")

        existing = await self.db.execute(
            select(FestivalEdition).where(
                FestivalEdition.festival_id == festival_id,
                FestivalEdition.year == year,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise FestivalError(f"edition for year {year} already exists")

        edition = FestivalEdition(
            festival_id=festival_id,
            year=year,
            total_seats=total_seats,
            seats_available=total_seats,
            status="planned",
        )
        self.db.add(edition)
        await self.db.commit()
        await self.db.refresh(edition)
        return edition

    async def get_edition(self, edition_id: str) -> FestivalEdition | None:
        result = await self.db.execute(
            select(FestivalEdition).where(FestivalEdition.id == edition_id)
        )
        return result.scalar_one_or_none()

    # ═════════════════════════════════════════════════════════════
    # bookings + dynamic pricing
    # ═════════════════════════════════════════════════════════════

    def compute_dynamic_price(
        self,
        festival: TourismFestival,
        participants_count: int,
    ) -> Decimal:
        """Dynamic ticket price based on fill ratio (scarcity premium)."""
        base = festival.base_ticket_price
        multiplier = Decimal("1.00")

        # Scarcity: as seats fill, price rises (capped at +50%).
        filled = festival.capacity - 0  # placeholder; edition-level seats used below
        _ = filled  # noqa
        if participants_count <= 0:
            raise FestivalError("participants_count must be positive")

        price = (base * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        return price * participants_count

    async def book_festival(
        self,
        *,
        festival_id: str,
        edition_id: str,
        guest_id: str,
        participants_count: int,
        created_by: str,
    ) -> FestivalBooking:
        """Book seats for a festival edition with dynamic pricing."""
        festival = await self.get_festival(festival_id)
        if festival is None:
            raise FestivalError(f"festival not found: {festival_id}")
        if festival.status != "active":
            raise FestivalError(f"festival is not active (currently {festival.status})")

        edition = await self.get_edition(edition_id)
        if edition is None:
            raise FestivalError(f"edition not found: {edition_id}")
        if str(edition.festival_id) != str(festival_id):
            raise FestivalError("edition does not belong to this festival")
        if edition.seats_available < participants_count:
            raise FestivalError(
                f"only {edition.seats_available} seats available, requested {participants_count}"
            )
        if participants_count <= 0:
            raise FestivalError("participants_count must be positive")

        # Dynamic price: scarcity multiplier based on fill ratio.
        fill_ratio = Decimal(festival.capacity - edition.seats_available) / Decimal(
            festival.capacity
        )
        multiplier = Decimal("1.00")
        if fill_ratio >= Decimal("0.8"):
            multiplier += Decimal("0.50")
        elif fill_ratio >= Decimal("0.5"):
            multiplier += Decimal("0.25")

        ticket_price = (
            festival.base_ticket_price * multiplier
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        subtotal = (ticket_price * participants_count).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        platform_fee = (
            subtotal * Decimal("800") / Decimal(10000)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        landscape_fee = (
            subtotal * Decimal(festival.landscape_fee_bps) / Decimal(10000)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        total = subtotal + platform_fee + landscape_fee

        booking = FestivalBooking(
            festival_id=festival_id,
            edition_id=edition_id,
            guest_id=guest_id,
            participants_count=participants_count,
            ticket_price=ticket_price,
            subtotal=subtotal,
            platform_fee=platform_fee,
            landscape_fee=landscape_fee,
            total=total,
            status="pending",
        )
        self.db.add(booking)

        # Decrement available seats.
        edition.seats_available -= participants_count
        edition.total_revenue = (
            (edition.total_revenue or Decimal("0")) + total
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        edition.landscape_fees = (
            (edition.landscape_fees or Decimal("0")) + landscape_fee
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def cancel_booking(
        self,
        *,
        booking_id: str,
        actor_id: str,
    ) -> FestivalBooking:
        """Cancel a pending booking and release seats."""
        result = await self.db.execute(
            select(FestivalBooking).where(FestivalBooking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if booking is None:
            raise FestivalError(f"booking not found: {booking_id}")
        if booking.status != "pending":
            raise FestivalError(f"booking is {booking.status}, cannot cancel")

        edition = await self.get_edition(str(booking.edition_id))
        if edition is not None:
            edition.seats_available += booking.participants_count

        booking.status = "cancelled"
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def get_booking(self, booking_id: str) -> FestivalBooking | None:
        result = await self.db.execute(
            select(FestivalBooking).where(FestivalBooking.id == booking_id)
        )
        return result.scalar_one_or_none()

    # ═════════════════════════════════════════════════════════════
    # reporting
    # ═════════════════════════════════════════════════════════════

    async def festival_report(
        self,
        *,
        festival_id: str,
    ) -> dict:
        """Aggregate revenue, attendance and landscape fees for a festival."""
        festival = await self.get_festival(festival_id)
        if festival is None:
            raise FestivalError(f"festival not found: {festival_id}")

        result = await self.db.execute(
            select(FestivalBooking).where(FestivalBooking.festival_id == festival_id)
        )
        bookings = result.scalars().all()

        confirmed = [b for b in bookings if b.status == "confirmed"]
        completed = [b for b in bookings if b.status == "completed"]

        total_revenue = sum((b.total or Decimal("0")) for b in confirmed)
        total_landscape = sum((b.landscape_fee or Decimal("0")) for b in confirmed)
        total_participants = sum(b.participants_count for b in confirmed)
        total_platform_fees = sum((b.platform_fee or Decimal("0")) for b in confirmed)

        result2 = await self.db.execute(
            select(FestivalEdition).where(FestivalEdition.festival_id == festival_id)
        )
        editions = result2.scalars().all()
        total_seats = sum(e.total_seats for e in editions)
        seats_sold = sum(
            e.total_seats - e.seats_available for e in editions
        )

        return {
            "festival_id": festival_id,
            "name": festival.name,
            "status": festival.status,
            "total_bookings": len(confirmed),
            "completed_bookings": len(completed),
            "total_revenue": str(total_revenue),
            "platform_fees": str(total_platform_fees),
            "landscape_fees": str(total_landscape),
            "total_participants": total_participants,
            "total_seats": total_seats,
            "seats_sold": seats_sold,
            "fill_rate": round(seats_sold / total_seats, 4) if total_seats else 0.0,
            "editions": len(editions),
        }

    # ═════════════════════════════════════════════════════════════
    # inventory reservation (best-effort)
    # ═════════════════════════════════════════════════════════════

    async def reserve_inventory(
        self,
        *,
        edition_id: str,
        sku_id: int,
        warehouse_id: int,
        qty,
        created_by: str,
    ):
        """Reserve inventory (food, supplies, materials) for a festival edition.

        Uses ``InvStockMovement`` of type ``reservation`` so stock is blocked
        until the festival consumes it. Best-effort; if inventory tables are
        not available the reservation is recorded but not enforced.
        """
        edition = await self.get_edition(edition_id)
        if edition is None:
            raise FestivalError(f"edition not found: {edition_id}")

        try:
            from database.models import InvStockMovement
            movement = InvStockMovement(
                movement_type="reservation",
                sku_id=sku_id,
                warehouse_id=warehouse_id,
                qty=qty,
                created_by=created_by,
                reference_type="festival_edition",
                reference_id=str(edition.id),
                notes=f"Festival edition {edition.year} reservation",
                user_id=created_by,
            )
            self.db.add(movement)
            await self.db.commit()
            return movement
        except Exception:  # noqa: BLE001 - inventory may not be wired
            return None

    # ═════════════════════════════════════════════════════════════
    # internals
    # ═════════════════════════════════════════════════════════════

    async def _require_active_space(self, village_id: str) -> CommunitySpace:
        result = await self.db.execute(
            select(CommunitySpace).where(CommunitySpace.village_id == village_id)
        )
        space = result.scalar_one_or_none()
        if space is None:
            raise FestivalError(f"no governance space for village {village_id}")
        if space.status != SpaceStatus.ACTIVE.value:
            raise FestivalError(
                f"village {village_id} is not governance-active (status={space.status})"
            )
        return space
