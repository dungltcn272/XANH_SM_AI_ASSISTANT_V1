from __future__ import annotations

from .common import *

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=lambda: generate_id("merchant"))
    name = Column(String, nullable=False, index=True)
    owner_actor_id = Column(String, ForeignKey("actors.id"), nullable=True)
    category = Column(String, nullable=True, index=True)
    address = Column(Text, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    city = Column(String, nullable=True, index=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    open_hours_json = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class MerchantMenuItem(Base):
    __tablename__ = "merchant_menu_items"

    id = Column(String, primary_key=True, default=lambda: generate_id("item"))
    item_id = Column(String, nullable=True, unique=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    merchant_name = Column(String, nullable=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)
    cuisine = Column(String, nullable=True)
    taste_tags_json = Column(Text, nullable=True)
    diet_tags_json = Column(Text, nullable=True)
    ingredient_tags_json = Column(Text, nullable=True)
    price = Column(Integer, nullable=True)
    discount_percent = Column(Integer, nullable=True)
    final_price = Column(Integer, nullable=True)
    currency = Column(String, default="VND", nullable=False)
    image_url = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=True)
    merchant_rating = Column(Float, nullable=True)
    merchant_review_count = Column(Integer, nullable=True)
    merchant_address = Column(Text, nullable=True)
    merchant_lat = Column(Float, nullable=True)
    merchant_lng = Column(Float, nullable=True)
    merchant_open_hours_json = Column(Text, nullable=True)
    avg_prep_minutes = Column(Float, nullable=True)
    base_delivery_fee = Column(Integer, nullable=True)
    fee_per_km = Column(Integer, nullable=True)
    service_radius_km = Column(Float, nullable=True)
    source = Column(String, default="shopeefood", nullable=True)
    source_url = Column(Text, nullable=True)
    city = Column(String, nullable=True, index=True)
    city_slug = Column(String, nullable=True)
    raw_ref = Column(String, nullable=True)
    raw_json = Column(Text, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class FoodInteraction(Base):
    __tablename__ = "food_interactions"

    id = Column(String, primary_key=True, default=lambda: generate_id("foodevt"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=True, index=True)
    menu_item_id = Column(String, ForeignKey("merchant_menu_items.id"), nullable=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    rank_position = Column(Integer, nullable=True)
    query = Column(Text, nullable=True)
    context_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)

    @property
    def event_id(self) -> str:
        return self.id

    @property
    def item_id(self) -> str | None:
        return self.menu_item_id

    @item_id.setter
    def item_id(self, value: str | None) -> None:
        self.menu_item_id = value

    @property
    def user_id(self) -> str | None:
        return self.actor_id

    @user_id.setter
    def user_id(self, value: str | None) -> None:
        self.actor_id = value

    @property
    def session_id(self) -> str | None:
        return self.actor_id

    @session_id.setter
    def session_id(self, value: str | None) -> None:
        self.actor_id = value

    @property
    def request_context_json(self) -> str | None:
        return self.context_json

    @request_context_json.setter
    def request_context_json(self, value: str | None) -> None:
        self.context_json = value

class MerchantMetricSnapshot(Base):
    __tablename__ = "merchant_metric_snapshots"

    id = Column(String, primary_key=True, default=lambda: generate_id("mermetric"))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    orders_count = Column(Integer, default=0, nullable=False)
    gross_revenue = Column(Integer, default=0, nullable=False)
    net_revenue = Column(Integer, nullable=True)
    avg_rating = Column(Float, nullable=True)
    cancel_rate = Column(Float, nullable=True)
    prep_time_avg_minutes = Column(Float, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class MerchantReview(Base):
    __tablename__ = "merchant_reviews"

    id = Column(String, primary_key=True, default=lambda: generate_id("merreview"))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    menu_item_id = Column(String, ForeignKey("merchant_menu_items.id"), nullable=True, index=True)
    rating = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    sentiment = Column(String, nullable=True, index=True)
    topics_json = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
