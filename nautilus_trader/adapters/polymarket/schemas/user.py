# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2024 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

import msgspec

from nautilus_trader.adapters.polymarket.common.enums import PolymarketEventType
from nautilus_trader.adapters.polymarket.common.enums import PolymarketLiquiditySide
from nautilus_trader.adapters.polymarket.common.enums import PolymarketOrderSide
from nautilus_trader.adapters.polymarket.common.enums import PolymarketOrderStatus
from nautilus_trader.adapters.polymarket.common.enums import PolymarketOrderType
from nautilus_trader.adapters.polymarket.common.enums import PolymarketTradeStatus
from nautilus_trader.adapters.polymarket.common.parsing import parse_order_side
from nautilus_trader.adapters.polymarket.common.parsing import parse_order_status
from nautilus_trader.adapters.polymarket.common.parsing import parse_time_in_force
from nautilus_trader.adapters.polymarket.schemas.order import PolymarketMakerOrder
from nautilus_trader.core.datetime import millis_to_nanos
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.reports import FillReport
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.model.enums import ContingencyType
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.instruments import BinaryOption


class PolymarketUserOrder(msgspec.Struct, tag="order", tag_field="event_type", frozen=True):
    """
    Represents a Polymarket user order status update.

    References
    ----------
    https://docs.polymarket.com/#user-channel

    """

    asset_id: str
    associate_trades: list[str] | None
    created_at: str
    expiration: str
    id: str
    maker_address: str
    market: str
    order_owner: str
    order_type: PolymarketOrderType  # time in force
    original_size: str
    outcome: str
    owner: str
    price: str
    side: PolymarketOrderSide
    size_matched: str
    status: PolymarketOrderStatus
    timestamp: str
    type: PolymarketEventType

    def get_venue_order_id(self) -> VenueOrderId:
        return VenueOrderId(self.id)

    def parse_to_order_status_report(
        self,
        account_id: AccountId,
        instrument: BinaryOption,
        client_order_id: ClientOrderId | None,
        ts_init: int,
    ) -> OrderStatusReport:
        timestamp_ms = int(self.timestamp)
        return OrderStatusReport(
            account_id=account_id,
            instrument_id=instrument.id,
            client_order_id=client_order_id,
            order_list_id=None,
            venue_order_id=self.get_venue_order_id(),
            order_side=parse_order_side(self.side),
            order_type=OrderType.LIMIT,
            contingency_type=ContingencyType.NO_CONTINGENCY,
            time_in_force=parse_time_in_force(order_type=self.order_type),
            expire_time=millis_to_nanos(int(self.expiration)) if self.expiration else None,
            order_status=parse_order_status(order_status=self.status),
            price=instrument.make_price(float(self.price)),
            quantity=instrument.make_qty(float(self.original_size)),
            filled_qty=instrument.make_qty(float(self.size_matched)),
            ts_accepted=millis_to_nanos(timestamp_ms),
            ts_last=millis_to_nanos(timestamp_ms),
            report_id=UUID4(),
            ts_init=ts_init,
        )


class PolymarketUserTrade(msgspec.Struct, tag="trade", tag_field="event_type", frozen=True):
    """
    Represents a Polymarket user trade.

    References
    ----------
    https://docs.polymarket.com/#user-channel

    """

    asset_id: str
    bucket_index: str
    fee_rate_bps: str
    id: str
    last_update: str
    maker_address: str
    maker_orders: list[PolymarketMakerOrder]
    market: str
    match_time: str
    outcome: str
    owner: str
    price: str
    side: PolymarketOrderSide
    size: str
    status: PolymarketTradeStatus
    taker_order_id: str
    timestamp: str
    trade_owner: str
    trader_side: PolymarketLiquiditySide
    type: PolymarketEventType

    def liqudity_side(self) -> LiquiditySide:
        if self.trader_side == PolymarketLiquiditySide.MAKER:
            return LiquiditySide.MAKER
        else:
            return LiquiditySide.TAKER

    def venue_order_id(self) -> VenueOrderId:
        if self.trader_side == PolymarketLiquiditySide.MAKER:
            return VenueOrderId(self.maker_orders[-1].order_id)
        else:
            return VenueOrderId(self.taker_order_id)

    def parse_to_fill_report(
        self,
        account_id: AccountId,
        instrument: BinaryOption,
        client_order_id: ClientOrderId | None,
        ts_init: int,
    ) -> FillReport:
        return FillReport(
            account_id=account_id,
            instrument_id=instrument.id,
            client_order_id=client_order_id,
            venue_order_id=self.venue_order_id(),
            trade_id=TradeId(self.id),
            order_side=parse_order_side(self.side),
            last_qty=instrument.make_qty(float(self.size)),
            last_px=instrument.make_price(float(self.price)),
            liquidity_side=self.liqudity_side(),
            report_id=UUID4(),
            ts_event=millis_to_nanos(int(self.match_time)),
            ts_init=ts_init,
        )


class PolymarketOpenOrder(msgspec.Struct, frozen=True):
    """
    Represents a Polymarket active order.

    References
    ----------
    https://docs.polymarket.com/#get-order

    """

    associate_trades: list[str] | None
    id: str
    status: PolymarketOrderStatus
    market: str
    original_size: str
    outcome: str
    maker_address: str
    owner: str
    price: str
    side: PolymarketOrderSide
    size_matched: str
    asset_id: str
    expiration: str
    order_type: PolymarketOrderType  # time in force
    created_at: int

    def get_venue_order_id(self) -> VenueOrderId:
        return VenueOrderId(self.id)

    def parse_to_order_status_report(
        self,
        account_id: AccountId,
        instrument: BinaryOption,
        client_order_id: ClientOrderId | None,
        ts_init: int,
    ) -> OrderStatusReport:
        return OrderStatusReport(
            account_id=account_id,
            instrument_id=instrument.id,
            client_order_id=client_order_id,
            order_list_id=None,
            venue_order_id=self.get_venue_order_id(),
            order_side=parse_order_side(self.side),
            order_type=OrderType.LIMIT,
            contingency_type=ContingencyType.NO_CONTINGENCY,
            time_in_force=parse_time_in_force(order_type=self.order_type),
            expire_time=millis_to_nanos(int(self.expiration)) if self.expiration else None,
            order_status=parse_order_status(order_status=self.status),
            price=instrument.make_price(float(self.price)),
            quantity=instrument.make_qty(float(self.original_size)),
            filled_qty=instrument.make_qty(float(self.size_matched)),
            ts_accepted=millis_to_nanos(self.created_at),
            ts_last=millis_to_nanos(self.created_at),  # TODO: TBD
            report_id=UUID4(),
            ts_init=ts_init,
        )
