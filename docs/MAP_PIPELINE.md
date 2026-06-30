# 🗺️ Luồng Xử Lý Map Intelligence (Phase 10)

Tính năng **Map Intelligence** là một phân hệ (sub-system) chuyên biệt trong Xanh SM AI Assistant, được thiết kế để xử lý các câu hỏi về bản đồ, chỉ đường, kẹt xe, và mật độ tài xế. Thay vì dùng RAG truyền thống, phân hệ này sử dụng mô hình **ReAct (Reasoning and Acting) Agent** thông qua OpenAI Function Calling, cho phép AI tự động phân tích ngữ cảnh và "chủ động" gọi các công cụ bên ngoài (tools) để lấy dữ liệu.

## 1. Kiến Trúc Tổng Quan (Agentic Workflow)

```mermaid
graph TD
    A([User Input]) --> B[NLU Classifier]
    B -- "intent: map_intelligence" --> C[Map Intelligence Chain]
    
    C --> D{Kiểm tra Tọa độ (Lat/Lng)}
    D -- "Thiếu vị trí" --> E[Trả về UI Form yêu cầu vị trí]
    
    D -- "Có vị trí" --> F[Khởi tạo LLM Agent (MAP_ANSWER_MODEL)]
    F --> G{LLM Reasoning Loop}
    
    G -- "Cần tọa độ đích" --> T1[Tool: search_places]
    T1 -- "Nominatim API" --> G
    
    G -- "Cần vẽ đường" --> T2[Tool: get_osrm_routes]
    T2 -- "OSRM API" --> G
    
    G -- "Đã đủ dữ liệu" --> H[LLM Synthesis & Streaming]
    
    H --> I([Trả về Text + MapPayload])
```

## 2. Chi Tiết Các Bước Xử Lý

### Bước 1: NLU Trích Xuất & Phân Loại
Luồng bắt đầu từ file `app/nlu/classifier.py`. Khi mô hình nhận diện câu hỏi mang tính chất không gian/địa lý (vd: *"Tìm đường đến Lăng Bác"*), nó:
1. Gán `intent = "map_intelligence"`.
2. Trích xuất các thực thể trong câu vào `map_slots` (ví dụ: tọa độ thô nếu người dùng gõ vào, hoặc địa danh).
3. Đẩy luồng xử lý sang `MapIntelligenceChain` thông qua `Orchestrator`.

### Bước 2: Validation & Missing Location Handling
Trong `app/map_intelligence/chain.py` (`_resolve_location`):
- Hệ thống cố gắng lấy tọa độ xuất phát theo thứ tự: NLU Slots -> Regex trong câu hỏi -> `current_location` từ Frontend.
- **Tính năng mới Phase 10**: Nếu không tìm thấy tọa độ, hệ thống sẽ KHÔNG đoán mò (ví dụ: không lấy mặc định tọa độ trung tâm TP.HCM). Thay vào đó, nó dừng suy luận, bắn log `missing_location` và kích hoạt sự kiện `food_missing_info` (dùng chung payload UI với Food) để hiển thị form *"Anh/chị muốn tìm đường từ đâu?"* trên giao diện.

### Bước 3: ReAct Tool-calling Loop
Khi đã có tọa độ xuất phát, hệ thống cung cấp cho LLM (vd: `gpt-4o-mini`) một danh sách các công cụ (`MAP_TOOLS`):
1. **`search_places`**: Gọi OpenStreetMap Nominatim API để tìm tọa độ của một địa danh (Geocoding).
2. **`get_osrm_routes`**: Gọi OSRM (Open Source Routing Machine) API để lấy danh sách tuyến đường, khoảng cách (km), thời gian (phút) và tập hợp các điểm GeoJSON để vẽ lên bản đồ.
3. **`get_traffic_zones`**: Truy vấn vùng kẹt xe (Mock data/DB).
4. **`get_driver_density`**: Truy vấn mật độ tài xế xung quanh (Mock data/DB).

LLM tự động phân tích:
> *"Khách muốn đi Lăng Bác. Mình chưa có tọa độ Lăng Bác. Gọi `search_places('Lăng Bác')`... Có tọa độ rồi, gọi tiếp `get_osrm_routes(lat_start, lng_start, lat_end, lng_end)`... Đã có dữ liệu tuyến đường, dừng gọi tool và trả lời."*

### Bước 4: Trả Lời & Render UI (Streaming)
- **Luồng Text**: LLM tuân theo `MAP_INTELLIGENCE_SYSTEM_PROMPT` (CSKH Xanh SM, xưng "em", không đọc tọa độ thô, format Markdown) và stream chữ về Frontend qua Server-Sent Events (SSE).
- **Luồng Map Payload**: Các kết quả thu được từ Tool được code Python đóng gói thành object `map_payload` (chứa `markers`, `routes`, `zones`).
- **Frontend (`ChatLayout.jsx`)**: Khi nhận được `map_payload`, React tự động render component `MapInsightCard.jsx`, kết hợp với React-Leaflet để vẽ bản đồ trực quan. Mỗi tuyến đường được cấp một màu sắc riêng (Xanh, Cam, Lục) và hiển thị marker điểm đầu (Xanh lá)/điểm cuối (Đỏ).

## 3. Các Thành Phần Code Chính
- **Prompt**: `app/prompts/map_prompts.py`
- **Chain Logic**: `app/map_intelligence/chain.py`
- **Tools**: `app/map_intelligence/tools.py`
- **Schemas**: `app/map_intelligence/schemas.py`
- **Frontend Component**: `frontend/src/components/chat/MapInsightCard.jsx`
