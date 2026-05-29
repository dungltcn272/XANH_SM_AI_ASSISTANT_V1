import json
import re
from typing import Dict, Any, List, Tuple, Optional
from openai import OpenAI
from app.config import config
from app.rag.prompt import INTENT_CLASSIFIER_PROMPT, SLOT_FILLING_PROMPT

class XanhSMClassifier:
    """
    Intent Classifier & Slot Filling Engine for Phase 3.
    """
    
    def __init__(self):
        pass

    def classify_intent(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Classifies the user query intent into: small-talk, faq, rag, task-agent, sensitive.
        Uses OpenAI LLM and supports robust offline rule-based fallback.
        """
        query_lower = query.lower()
        
        # Rule-based safety triggers (fast early exit for sensitive words)
        from app.rag.gateway import XanhSMGateway
        gateway = XanhSMGateway()
        safety_res = gateway.safety_precheck(query)
        if not safety_res["safe"]:
            return {
                "intent": "sensitive",
                "confidence": 1.0,
                "sub_task": None,
                "reason": safety_res["reason"]
            }

        # Rule-based Small-talk fast check (exact matches or very short phrases)
        greeting_check = gateway.is_greeting_or_thanks(query)
        if greeting_check["type"] != "none":
            return {
                "intent": "small-talk",
                "confidence": 0.95,
                "sub_task": None
            }

        # Rule-based Task-Agent check for Refund Calculator
        refund_indicators = {"tính phí hủy", "phạt hủy chuyến", "phạt hủy cuốc", "hủy chuyến phạt bao nhiêu", "hủy xe mất bao nhiêu", "phí hủy chuyến"}
        if any(ind in query_lower for ind in refund_indicators):
            # Check if wait time or vehicle type mentioned
            return {
                "intent": "task-agent",
                "confidence": 0.98,
                "sub_task": "refund_calculator"
            }

        # If LLM is available, use it for rich intent classification
        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                history_str = ""
                if chat_history:
                    for turn in chat_history[-3:]:
                        role_tag = "User" if turn.get("role") == "user" else "Assistant"
                        history_str += f"{role_tag}: {turn.get('content')}\n"

                client = OpenAI(api_key=config.OPENAI_API_KEY)
                user_prompt = f"Lịch sử hội thoại:\n{history_str}\nCâu hỏi người dùng: '{query}'\nJSON kết quả:"
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": INTENT_CLASSIFIER_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0
                )
                res_content = response.choices[0].message.content.strip()
                # Clean possible markdown block markers
                res_content = re.sub(r"```json|```", "", res_content).strip()
                result = json.loads(res_content)
                return result
            except Exception as e:
                print(f"[WARN] LLM Intent Classification failed: {e}. Falling back to Rule-based.")
                
        # Default Fallback
        # If it contains "chính sách", "quy định", "chiết khấu", "chế tài" -> RAG
        rag_indicators = {"chính sách", "quy định", "chiết khấu", "tác phong", "phạt", "thưởng", "đối soát", "hoa hồng"}
        if any(ind in query_lower for ind in rag_indicators):
            return {
                "intent": "rag",
                "confidence": 0.8,
                "sub_task": None
            }
            
        return {
            "intent": "rag", # Default to RAG for safety
            "confidence": 0.7,
            "sub_task": None
        }

    def fill_slots(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Binds parameters for 'refund_calculator': vehicle_type and waiting_time.
        Uses LLM and fallback rule-based regex extraction.
        """
        # Rule-based fallback extraction
        extracted_vehicle = None
        extracted_time = None
        
        query_lower = query.lower()
        
        # Regex for waiting time
        time_matches = re.findall(r"\b(\d+)\s*(phút|p)\b", query_lower)
        if time_matches:
            extracted_time = int(time_matches[0][0])
        else:
            # Check simple numbers in query
            single_numbers = re.findall(r"\b(\d+)\b", query_lower)
            if single_numbers:
                extracted_time = int(single_numbers[0])

        # Regex for vehicle type
        if "bike" in query_lower or "xe máy" in query_lower or "2 bánh" in query_lower:
            extracted_vehicle = "xanh_bike"
        elif "luxury" in query_lower or "vf8" in query_lower or "vf9" in query_lower or "xe sang" in query_lower:
            extracted_vehicle = "xanh_luxury"
        elif "car" in query_lower or "ô tô" in query_lower or "vf5" in query_lower or "vfe34" in query_lower or "4 bánh" in query_lower or "taxi" in query_lower:
            extracted_vehicle = "xanh_car"

        # Check in history if not found in query
        if chat_history:
            for turn in reversed(chat_history[-3:]):
                hist_content = turn.get("content", "").lower()
                if not extracted_time:
                    t_matches = re.findall(r"\b(\d+)\s*(phút|p)\b", hist_content)
                    if t_matches:
                        extracted_time = int(t_matches[0][0])
                if not extracted_vehicle:
                    if "bike" in hist_content or "xe máy" in hist_content:
                        extracted_vehicle = "xanh_bike"
                    elif "luxury" in hist_content or "vf8" in hist_content or "vf9" in hist_content:
                        extracted_vehicle = "xanh_luxury"
                    elif "car" in hist_content or "ô tô" in hist_content or "vf5" in hist_content:
                        extracted_vehicle = "xanh_car"

        # If LLM is available, use it to refine slot filling
        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                # Format history for LLM context
                history_str = ""
                if chat_history:
                    for turn in chat_history[-3:]:
                        role_tag = "User" if turn.get("role") == "user" else "Assistant"
                        history_str += f"{role_tag}: {turn.get('content')}\n"
                
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": SLOT_FILLING_PROMPT},
                        {"role": "user", "content": f"Lịch sử hội thoại:\n{history_str}\nCâu hỏi mới nhất: '{query}'\nJSON kết quả:"}
                    ],
                    temperature=0.0
                )
                res_content = response.choices[0].message.content.strip()
                res_content = re.sub(r"```json|```", "", res_content).strip()
                result = json.loads(res_content)
                return result
            except Exception as e:
                print(f"[WARN] LLM Slot Filling failed: {e}. Using rule-based fallback.")

        # Rule-based Slot Filling response format
        slots = {
            "vehicle_type": extracted_vehicle,
            "waiting_time": extracted_time
        }
        
        missing = False
        clarification = None
        
        if not extracted_vehicle:
            missing = True
            clarification = "Dạ, quý khách vui lòng cho biết mình đang sử dụng loại dịch vụ nào của Xanh SM: Xanh Bike (xe máy), Xanh Car (ô tô tiêu chuẩn) hay Xanh Luxury (ô tô cao cấp) ạ?"
        elif not extracted_time:
            missing = True
            clarification = "Quý khách vui lòng cung cấp thêm thông tin mình đã hủy chuyến sau bao nhiêu phút kể từ khi tài xế nhận cuốc xe ạ?"

        return {
            "slots": slots,
            "missing_info": missing,
            "clarification_question": clarification
        }


class RefundCalculatorTool:
    """
    Dedicated action engine to compute exact cancellation fees based on refund.md policies.
    """
    
    @staticmethod
    def calculate(vehicle_type: str, waiting_time: int) -> Dict[str, Any]:
        """
        Calculates refund penalty.
        Rules:
        - If waiting_time <= 2: Free of charge (0 VNĐ).
        - If waiting_time > 2:
            - xanh_bike: 10.000 VNĐ
            - xanh_car: 15.000 VNĐ
            - xanh_luxury: 30.000 VNĐ
        """
        v_type = vehicle_type.lower() if vehicle_type else "xanh_car"
        w_time = int(waiting_time) if waiting_time is not None else 0
        
        vehicle_display = {
            "xanh_bike": "xe máy điện Xanh Bike",
            "xanh_car": "ô tô điện Xanh Car (VF 5 / VF e34)",
            "xanh_luxury": "ô tô điện cao cấp Xanh Luxury (VF 8 / VF 9)"
        }.get(v_type, "ô tô điện Xanh Car")
        
        if w_time <= 2:
            fee = 0
            explanation = (
                f"Theo quy định chính sách hủy chuyến của Xanh SM:\n"
                f"Quý khách thực hiện hủy chuyến đối với dịch vụ **{vehicle_display}** trong vòng **{w_time} phút** (<= 2 phút) "
                f"kể từ lúc tài xế nhận cuốc xe. Do đó, quý khách được **HỦY CHUYẾN MIỄN PHÍ (0 VNĐ)**."
            )
        else:
            fee_mapping = {
                "xanh_bike": 10000,
                "xanh_car": 15000,
                "xanh_luxury": 30000
            }
            fee = fee_mapping.get(v_type, 15000)
            explanation = (
                f"Theo quy định chính sách hủy chuyến của Xanh SM:\n"
                f"Quý khách hủy chuyến đối với dịch vụ **{vehicle_display}** sau **{w_time} phút** (> 2 phút) "
                f"kể từ khi hệ thống điều phối tài xế thành công và tài xế đang di chuyển về điểm đón.\n\n"
                f"Mức phí phạt hủy chuyến áp dụng đối với bạn là: **{fee:,.0f} VNĐ**.\n\n"
                f"*Lưu ý: Khoản phí phạt hủy chuyến này sẽ được hệ thống ghi nợ và cộng dồn vào hóa đơn của chuyến đi tiếp theo của quý khách.*"
            )
            
        return {
            "fee": fee,
            "explanation": explanation,
            "vehicle_type": v_type,
            "waiting_time": w_time
        }

if __name__ == "__main__":
    classifier = XanhSMClassifier()
    print("Intent 1:", classifier.classify_intent("hủy xe Xanh Car được 3 phút bị phạt bao nhiêu?"))
    print("Slots 1:", classifier.fill_slots("hủy xe Xanh Car được 3 phút bị phạt bao nhiêu?"))
    print("Result 1:", RefundCalculatorTool.calculate("xanh_car", 3))
    print("\nIntent 2:", classifier.classify_intent("Chào ad nhé"))
    print("\nSlots 2 (missing time):", classifier.fill_slots("hủy chuyến xe máy điện"))
