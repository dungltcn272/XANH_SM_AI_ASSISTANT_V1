import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, Iterable, List


def strip_accents(text: str) -> str:
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_text(text: str) -> str:
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class ServiceAlias:
    canonical: str
    aliases: tuple[str, ...]
    category_hint: str = ""
    document_type_hint: str = ""


@dataclass(frozen=True)
class IntentAlias:
    canonical: str
    aliases: tuple[str, ...]
    category_hints: tuple[str, ...] = ()
    document_type_hints: tuple[str, ...] = ()
    canonical_terms: tuple[str, ...] = ()


@dataclass
class DomainQueryUnderstanding:
    original_query: str
    normalized_query: str
    services: List[str] = field(default_factory=list)
    intents: List[str] = field(default_factory=list)
    category_hints: List[str] = field(default_factory=list)
    document_type_hints: List[str] = field(default_factory=list)
    expanded_terms: List[str] = field(default_factory=list)
    expanded_queries: List[str] = field(default_factory=list)

    @property
    def primary_service(self) -> str:
        return self.services[0] if self.services else ""

    @property
    def primary_intent(self) -> str:
        return self.intents[0] if self.intents else ""


SERVICE_ALIASES: tuple[ServiceAlias, ...] = (
    ServiceAlias("Xanh SM", ("xanh sm", "xsm", "gsm", "green sm", "greensm", "xanh"), "user", "service"),
    ServiceAlias("V-GREEN", ("v-green", "v green", "vgreen", "tram sac", "trạm sạc", "sac pin", "sạc pin"), "vehicle", "policy"),
    ServiceAlias("Green Express", ("green express", "green exress", "express", "xanh express", "gsm express", "xanh giao hang", "giao hang xanh"), "user", "service"),
    ServiceAlias("Green SM Limo", ("green sm limo", "greensm limo", "green limo", "limo", "limo green", "xanh limo"), "vehicle-car", "vehicle"),
    ServiceAlias("Green SM Car", ("green sm car", "greensm car", "xanh sm car", "taxi xanh", "xanh taxi", "taxi dien"), "user", "service"),
    ServiceAlias("Green SM Bike", ("green sm bike", "greensm bike", "xanh bike", "bike", "xe may dien", "xe máy điện"), "vehicle-bike", "vehicle"),
    ServiceAlias("Green SM Ngon", ("green sm ngon", "greensm ngon", "green food", "xanh food", "ngon", "giao do an", "do an"), "user", "service"),
    ServiceAlias("Green Van", ("green van", "xanh van", "van", "xe van", "ec van", "ecvan", "giao hang cong kenh"), "vehicle-car", "vehicle"),
    ServiceAlias("Green Care", ("green care", "bao hiem", "bảo hiểm", "bao hiem xanh", "bao hiem chuyen di"), "green-care", "policy"),
    ServiceAlias("Driver", ("tai xe", "tài xế", "tx", "driver", "doi tac tai xe", "bac tai", "chay xe", "lai xe"), "driver", "driver"),
    ServiceAlias("Merchant", ("merchant", "doi tac cua hang", "nha hang", "quan an", "cua hang"), "merchant", "merchant"),
    ServiceAlias("VinFast", ("vinfast", "vin fat", "vinfat", "vf", "vf3", "vf 3", "vf5", "vf 5", "vf6", "vf 6", "vf7", "vf 7", "herio", "herio green", "feliz", "evo", "viper"), "vehicle", "vehicle"),
    ServiceAlias("Green SM Platform", ("green sm platform", "platform", "platfom", "gsm platform", "mua xe platform", "thue xe platform"), "platform", "policy"),
)


INTENT_ALIASES: tuple[IntentAlias, ...] = (
    IntentAlias(
        "pricing_fee",
        ("phi", "phí", "phu phi", "phụ phí", "cuoc", "cước", "gia", "giá", "gia cuoc", "bang gia", "bao nhieu tien", "bn tien", "mat bao nhieu", "tinh tien", "don gia"),
        ("user", "vehicle", "vehicle-car", "vehicle-bike", "platform"),
        ("pricing", "service", "policy"),
        ("giá cước", "phụ phí", "bảng giá", "đơn giá"),
    ),
    IntentAlias(
        "insurance_compensation",
        ("den", "đền", "den hang", "đền hàng", "boi thuong", "bồi thường", "boi hoan", "bồi hoàn", "bao hiem", "bảo hiểm", "mat hang", "hong hang", "do vo", "tai nan", "thiet hai"),
        ("green-care", "user"),
        ("policy", "faq"),
        ("bảo hiểm", "bồi thường", "bồi hoàn", "quyền lợi bảo hiểm"),
    ),
    IntentAlias(
        "cancellation_policy",
        ("huy", "hủy", "huy chuyen", "hủy chuyến", "huy don", "cancel", "khong nhan chuyen", "phi huy", "hoan tien", "refund"),
        ("user", "driver", "merchant"),
        ("policy", "faq"),
        ("chính sách hủy", "phí hủy", "hoàn tiền", "bồi hoàn"),
    ),
    IntentAlias(
        "registration_onboarding",
        ("dang ky", "đăng ký", "dk", "đk", "tham gia", "lam tai xe", "chay xe", "doi tac", "ho so", "giay to", "thu tuc", "ung tuyen"),
        ("driver", "merchant", "vehicle", "vehicle-car", "vehicle-bike", "platform"),
        ("driver", "merchant", "guide", "policy"),
        ("đăng ký", "hồ sơ", "giấy tờ", "điều kiện tham gia", "thủ tục"),
    ),
    IntentAlias(
        "revenue_bonus_commission",
        ("thuong", "thưởng", "doanh thu", "an chia", "ăn chia", "chiet khau", "hoa hong", "van doanh", "thu nhap", "luong"),
        ("driver", "merchant", "vehicle", "vehicle-car", "vehicle-bike", "platform"),
        ("pricing", "policy", "driver"),
        ("thưởng", "doanh thu", "ăn chia", "chiết khấu", "vận doanh", "hoa hồng"),
    ),
    IntentAlias(
        "operating_policy",
        ("quy dinh", "quy định", "quy che", "dieu khoan", "chinh sach", "chính sách", "che tai", "phat", "vi pham", "tam ngung", "khoa tai khoan"),
        ("term-policies", "driver", "vehicle", "vehicle-car", "vehicle-bike", "platform"),
        ("policy", "policy_pdf"),
        ("quy định", "quy chế", "điều khoản", "chế tài", "vi phạm"),
    ),
    IntentAlias(
        "document_requirement",
        ("can gi", "cần gì", "yeu cau gi", "giay to", "ho so", "dieu kien", "điều kiện", "cccd", "bang lai", "dang kiem"),
        ("driver", "merchant", "vehicle", "vehicle-car", "vehicle-bike", "platform"),
        ("guide", "policy", "driver"),
        ("hồ sơ", "giấy tờ", "điều kiện", "yêu cầu"),
    ),
    IntentAlias(
        "promotion_financing",
        ("uu dai", "ưu đãi", "khuyen mai", "vay von", "vay vốn", "tra gop", "trả góp", "ho tro von", "giam gia", "mien phi", "free"),
        ("vehicle", "vehicle-car", "vehicle-bike", "driver", "platform"),
        ("promotion", "policy", "pricing"),
        ("ưu đãi", "khuyến mại", "vay vốn", "trả góp", "miễn phí"),
    ),
    IntentAlias(
        "battery_charging",
        ("sac", "sạc", "sac pin", "tram sac", "vgreen", "v green", "v-green", "doi pin", "đổi pin", "thue pin", "thuê pin", "pin"),
        ("vehicle", "vehicle-bike", "vehicle-car"),
        ("policy", "pricing", "vehicle"),
        ("sạc pin", "trạm sạc V-GREEN", "đổi pin", "thuê pin", "chính sách pin"),
    ),
)


def _match_aliases(normalized_query: str, aliases: Iterable[str]) -> bool:
    padded = f" {normalized_query} "
    for alias in aliases:
        norm_alias = normalize_text(alias)
        if not norm_alias:
            continue
        if f" {norm_alias} " in padded or norm_alias in normalized_query:
            return True
    return False


def _append_unique(items: list[str], values: Iterable[str]):
    for value in values:
        if value and value not in items:
            items.append(value)


def understand_query(query: str) -> DomainQueryUnderstanding:
    normalized = normalize_text(query)
    result = DomainQueryUnderstanding(original_query=query, normalized_query=normalized)

    for service in SERVICE_ALIASES:
        if _match_aliases(normalized, service.aliases):
            _append_unique(result.services, [service.canonical])
            _append_unique(result.category_hints, [service.category_hint])
            _append_unique(result.document_type_hints, [service.document_type_hint])

    for intent in INTENT_ALIASES:
        if _match_aliases(normalized, intent.aliases):
            _append_unique(result.intents, [intent.canonical])
            _append_unique(result.category_hints, intent.category_hints)
            _append_unique(result.document_type_hints, intent.document_type_hints)
            _append_unique(result.expanded_terms, intent.canonical_terms)

    expanded_queries = [query]
    for service in result.services[:3]:
        expanded_queries.append(service)

    for term in result.expanded_terms[:8]:
        for service in result.services[:2]:
            expanded_queries.append(f"{term} {service}")
        expanded_queries.append(term)

    for service in result.services[:2]:
        for intent in result.intents[:2]:
            expanded_queries.append(f"{service} {intent.replace('_', ' ')}")

    result.expanded_queries = list(dict.fromkeys(q for q in expanded_queries if q and q.strip()))
    return result


def enrich_queries(query: str, existing_queries: Iterable[str] | None = None, max_queries: int = 8) -> list[str]:
    understanding = understand_query(query)
    queries = list(existing_queries or [])
    _append_unique(queries, [query])
    _append_unique(queries, understanding.expanded_queries)
    return queries[:max_queries]


def canonical_rewrite_hint(query: str) -> str:
    understanding = understand_query(query)
    if not understanding.primary_service and not understanding.primary_intent:
        return query

    intent_terms: Dict[str, str] = {
        "pricing_fee": "giá cước, phụ phí và bảng giá",
        "insurance_compensation": "bảo hiểm, bồi thường và bồi hoàn",
        "cancellation_policy": "chính sách hủy, phí hủy và hoàn tiền",
        "registration_onboarding": "đăng ký, hồ sơ và điều kiện tham gia",
        "revenue_bonus_commission": "thưởng, doanh thu, ăn chia và chiết khấu",
        "operating_policy": "quy định, điều khoản, chế tài và vi phạm",
        "document_requirement": "hồ sơ, giấy tờ và điều kiện",
        "promotion_financing": "ưu đãi, khuyến mại, vay vốn và trả góp",
        "battery_charging": "sạc pin, trạm sạc V-GREEN, đổi pin và thuê pin",
    }

    parts = []
    if understanding.primary_intent:
        parts.append(intent_terms.get(understanding.primary_intent, understanding.primary_intent.replace("_", " ")))
    if understanding.primary_service:
        parts.append(f"liên quan đến {understanding.primary_service}")

    if understanding.primary_intent and understanding.primary_service:
        return "Thông tin về " + " ".join(parts)
    if understanding.primary_service:
        return f"Thông tin liên quan đến {understanding.primary_service}"
    return "Thông tin về " + " ".join(parts)
