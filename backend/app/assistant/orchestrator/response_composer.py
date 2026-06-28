from __future__ import annotations

import json
from typing import Any


def compose_response(*, persona: str, intent: str, tool_results: list[dict[str, Any]]) -> str:
    if intent == "small_talk":
        if persona == "driver":
            return "Chào anh/chị tài xế, em sẵn sàng hỗ trợ về chuyến đi, điểm sạc, khu vực đông khách hoặc trạng thái cuốc xe."
        if persona == "merchant":
            return "Chào anh/chị, em sẵn sàng hỗ trợ phân tích doanh thu, menu, đánh giá khách hàng và gợi ý vận hành cửa hàng."
        if persona == "operator":
            return "Chào anh/chị, em sẵn sàng hỗ trợ theo dõi đội xe, doanh thu vận hành, cảnh báo rủi ro và sự cố."
        if persona == "executive":
            return "Chào anh/chị, em sẵn sàng hỗ trợ phân tích kinh doanh, dự báo, mô phỏng tăng trưởng và khuyến nghị chiến lược."
        return "Chào anh/chị, em là trợ lý AI Xanh SM. Anh/chị cần hỗ trợ đặt xe, giá cước, ưu đãi, xe điện hay thông tin dịch vụ nào ạ?"
    if intent == "missing_info":
        return "Em cần thêm một chút thông tin để hỗ trợ chính xác hơn. Anh/chị có thể nói rõ nhu cầu, địa điểm hoặc dịch vụ đang quan tâm không ạ?"
    if intent == "sensitive":
        return "Em chưa thể hỗ trợ yêu cầu này. Anh/chị có thể đặt câu hỏi khác về dịch vụ, chuyến đi, ưu đãi hoặc hỗ trợ Xanh SM không ạ?"

    if not tool_results:
        return "Em chưa có đủ dữ liệu để trả lời chính xác. Anh/chị có thể nói rõ hơn nhu cầu cần hỗ trợ không ạ?"

    primary = tool_results[0].get("output", {})
    if isinstance(primary, dict) and "answer" in primary:
        return str(primary["answer"])

    payload = json.dumps(tool_results, ensure_ascii=False, indent=2, default=str)
    return f"Kết quả demo cho persona `{persona}` / intent `{intent}`:\n\n```json\n{payload}\n```"
