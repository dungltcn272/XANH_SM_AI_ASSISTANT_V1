from .common import (
    NotificationAudience,
    NotificationStatus,
    UserRole,
    generate_id,
    get_vn_time,
)
from .identity import Actor, ActorIdentity, Persona, PersonaAccessGrant
from .conversation import Conversation, Message
from .observability import AiTraceEvent, AssistantRun, ToolCall
from .memory import ConversationSummary, Memory, ProfileSnapshot
from .knowledge import Document, DocumentChunk, KnowledgeSource, RetrievalEvent
from .faq import FaqCacheHit, FaqCandidate, FaqEntry, FaqQuestionVariant
from .food import FoodInteraction, Merchant, MerchantMenuItem, MerchantMetricSnapshot, MerchantReview
from .ride import ChargingStation, Driver, DriverStatusSnapshot, Trip
from .operations import FraudSignal, OperationalMetricSnapshot
from .analytics import EvaluationRun, ExecutiveInsightReport
from .engagement import Notification, NotificationRead, Payment, UserFeedback

# Compatibility names used by legacy modules during the refactor window.
User = Actor
GuestSession = Actor
UserMemory = Memory
UserProfile = ProfileSnapshot
AdminNotification = Notification
UserReview = UserFeedback
CrawlSource = KnowledgeSource
FoodCatalog = MerchantMenuItem
SemanticCache = FaqEntry
RagRequestLog = AssistantRun
BasicRequestLog = AssistantRun
FoodRequestLog = AssistantRun
SystemLog = AiTraceEvent
ErrorLog = AiTraceEvent


def actor_identity_subject(entity: object) -> str:
    return getattr(entity, "provider_subject", "") or getattr(entity, "id", "")


__all__ = [
    "NotificationAudience",
    "NotificationStatus",
    "UserRole",
    "generate_id",
    "get_vn_time",
    "Actor",
    "ActorIdentity",
    "Persona",
    "PersonaAccessGrant",
    "Conversation",
    "Message",
    "AssistantRun",
    "ToolCall",
    "AiTraceEvent",
    "Memory",
    "ProfileSnapshot",
    "ConversationSummary",
    "KnowledgeSource",
    "Document",
    "DocumentChunk",
    "RetrievalEvent",
    "FaqEntry",
    "FaqQuestionVariant",
    "FaqCandidate",
    "FaqCacheHit",
    "Merchant",
    "MerchantMenuItem",
    "FoodInteraction",
    "MerchantMetricSnapshot",
    "MerchantReview",
    "Driver",
    "Trip",
    "DriverStatusSnapshot",
    "ChargingStation",
    "OperationalMetricSnapshot",
    "FraudSignal",
    "ExecutiveInsightReport",
    "Payment",
    "Notification",
    "NotificationRead",
    "UserFeedback",
    "EvaluationRun",
    "User",
    "GuestSession",
    "UserMemory",
    "UserProfile",
    "AdminNotification",
    "UserReview",
    "CrawlSource",
    "FoodCatalog",
    "SemanticCache",
    "RagRequestLog",
    "BasicRequestLog",
    "FoodRequestLog",
    "SystemLog",
    "ErrorLog",
    "actor_identity_subject",
]
