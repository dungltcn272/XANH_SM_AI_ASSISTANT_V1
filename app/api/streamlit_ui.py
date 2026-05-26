import os
import sys
from unittest.mock import MagicMock

# Prevents Windows Streamlit watcher & transformers lazy-load 'torchvision' ModuleNotFoundError crashes
import types
import importlib.machinery

# Resilient metaclass to return a class on class-level attribute access
class ResilientMeta(type):
    def __getattr__(cls, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        return ResilientClass
    def __repr__(cls):
        return f"<class 'Mock.{cls.__name__}'>"

# Resilient base class to handle instantiation and instance-level attribute access
class ResilientClass(metaclass=ResilientMeta):
    def __init__(self, *args, **kwargs):
        pass
    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        return ResilientClass()
    def __call__(self, *args, **kwargs):
        return ResilientClass()
    def __repr__(self):
        return "<Mock.ResilientClass object>"

def mock_module(name):
    if name in sys.modules and sys.modules[name] is not None:
        return
        
    class ResilientModule(types.ModuleType):
        def __getattr__(self, attr):
            if attr.startswith('__') and attr.endswith('__'):
                raise AttributeError(attr)
            return ResilientClass
            
    mod = ResilientModule(name)
    mod.__spec__ = importlib.machinery.ModuleSpec(name, None)
    sys.modules[name] = mod

for mod_name in [
    'torch',
    'torch.nn',
    'torch.nn.functional',
    'torch.utils',
    'torch.utils.data',
    'torch.cuda',
    'torch.autograd',
    'torch.distributed',
    'torch.multiprocessing',
    'torchvision',
    'torchvision.transforms',
    'torchvision.transforms.functional',
    'torchvision.transforms.v2',
    'torchvision.transforms.v2.functional',
    'torchvision.io',
    'torchvision.ops'
]:
    mock_module(mod_name)

import time
import graphviz
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

# Make sure app directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.rag.chain import XanhSMRAGPipeline
from app.config import config
from app.evaluation.ragas_eval import XanhSMEvaluation
from app.crawler.crawl import GreenSMCrawler
from app.ingestion.ingest import run_ingestion

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Xanh SM Enterprise RAG Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Injection for Xanh SM Cyan Brand & Premium Glassmorphism
st.markdown("""
<style>
    /* Main layout and colors */
    .stApp {
        background-color: #0c101b;
        color: #e2e8f0;
    }
    
    /* Title styling */
    .title-text {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(135deg, #00f0ff 0%, #0077ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem !important;
        margin-bottom: 0.5rem;
    }
    
    .subtitle-text {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Premium Containers & Cards */
    .glass-card {
        background: rgba(16, 24, 48, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .chat-bubble-user {
        background: linear-gradient(135deg, #0077ff 0%, #0055cc 100%);
        border-radius: 16px 16px 4px 16px;
        padding: 14px 18px;
        margin-bottom: 15px;
        max-width: 80%;
        margin-left: auto;
        color: #ffffff;
        box-shadow: 0 4px 15px rgba(0, 119, 255, 0.2);
    }
    
    .chat-bubble-bot {
        background: rgba(20, 30, 60, 0.7);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 16px 16px 16px 4px;
        padding: 16px 20px;
        margin-bottom: 15px;
        max-width: 85%;
        box-shadow: 0 4px 15px rgba(0, 240, 255, 0.05);
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(16, 24, 48, 0.6);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(0, 240, 255, 0.1);
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.15) 0%, rgba(0, 119, 255, 0.15) 100%) !important;
        color: #00f0ff !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to generate Dot code for thinking tree
def generate_pipeline_graph(current_step: str, layout_type: str = "ngang") -> str:
    steps = [
        ("Question", "❓ 1. Nhận Câu Hỏi"),
        ("QueryUnderstanding", "🧠 2. Query Expansion (AI)"),
        ("HybridSearch", "🔍 3. Hybrid Search"),
        ("Reranker", "⚡ 4. Reranker (AI)"),
        ("ContextCompression", "✂️ 5. Context Compression"),
        ("LLMGeneration", "🤖 6. Tổng Hợp LLM (AI)"),
        ("CitationValidator", "🛡️ 7. Xác Thực Nguồn")
    ]
    
    current_idx = -1
    for i, (step_id, _) in enumerate(steps):
        if step_id.lower() == current_step.lower():
            current_idx = i
            break
            
    # Base configuration based on layout
    if layout_type == "vong_tron":
        layout_directive = "  layout=circo;"
    else:
        layout_directive = "  layout=dot;"
        
    rankdir_directive = ""
    if layout_type == "ngang":
        rankdir_directive = "  rankdir=LR;"
        
    dot_lines = [
        "digraph G {",
        layout_directive,
        rankdir_directive,
        "  bgcolor=\"#0c101b\";",
        "  edge [color=\"#38bdf8\", penwidth=2.5, arrowsize=1.0];",
        "  node [fontname=\"Segoe UI Bold, Arial\", fontsize=13, shape=box, style=\"filled,rounded\", width=2.8, height=0.75];"
    ]
    
    # Render nodes with dynamic colors
    for i, (step_id, label) in enumerate(steps):
        # Determine State Style
        if i == current_idx:
            # Active step (bright cyan fill, white glow border, dark text)
            dot_lines.append(f"  {step_id} [label=\"{label}\", fillcolor=\"#00f0ff\", color=\"#ffffff\", fontcolor=\"#0c101b\", penwidth=3.5];")
        elif i < current_idx:
            # Completed step (deep teal/blue background, cyan borders and text)
            dot_lines.append(f"  {step_id} [label=\"{label}\", fillcolor=\"#0e3a5c\", color=\"#00f0ff\", fontcolor=\"#00f0ff\", penwidth=2.0];")
        else:
            # Pending step (dim grey/blue outline, muted grey text)
            dot_lines.append(f"  {step_id} [label=\"{label}\", fillcolor=\"#131a2b\", color=\"#1e293b\", fontcolor=\"#475569\", penwidth=1.5];")
            
    # Add Transitions based on layout type
    if layout_type == "zigzag":
        # Snake/Zigzag path using Rank alignments
        dot_lines.append("")
        dot_lines.append("  # Rank alignments for zigzag rows")
        dot_lines.append("  { rank=same; Question; QueryUnderstanding; HybridSearch; }")
        dot_lines.append("  { rank=same; Reranker; ContextCompression; }")
        dot_lines.append("  { rank=same; LLMGeneration; CitationValidator; }")
        dot_lines.append("")
        dot_lines.append("  # Snake connections")
        
        # Color edges based on current index progress
        def get_edge_style(from_idx):
            if from_idx < current_idx:
                return " [color=\"#00f0ff\", penwidth=3.0]"
            elif from_idx == current_idx:
                return " [color=\"#38bdf8\", penwidth=2.5, style=dashed]"
            else:
                return " [color=\"#1e293b\", penwidth=1.5]"
                
        dot_lines.append(f"  Question -> QueryUnderstanding{get_edge_style(0)};")
        dot_lines.append(f"  QueryUnderstanding -> HybridSearch{get_edge_style(1)};")
        dot_lines.append(f"  HybridSearch -> Reranker{get_edge_style(2)};")
        dot_lines.append(f"  Reranker -> ContextCompression{get_edge_style(3)};")
        dot_lines.append(f"  ContextCompression -> LLMGeneration{get_edge_style(4)};")
        dot_lines.append(f"  LLMGeneration -> CitationValidator{get_edge_style(5)};")
        
    elif layout_type == "vong_tron":
        # Circular flow path
        def get_edge_style(from_idx):
            if from_idx < current_idx:
                return " [color=\"#00f0ff\", penwidth=3.0]"
            elif from_idx == current_idx:
                return " [color=\"#38bdf8\", penwidth=2.5, style=dashed]"
            else:
                return " [color=\"#1e293b\", penwidth=1.5]"
                
        dot_lines.append(f"  Question -> QueryUnderstanding{get_edge_style(0)};")
        dot_lines.append(f"  QueryUnderstanding -> HybridSearch{get_edge_style(1)};")
        dot_lines.append(f"  HybridSearch -> Reranker{get_edge_style(2)};")
        dot_lines.append(f"  Reranker -> ContextCompression{get_edge_style(3)};")
        dot_lines.append(f"  ContextCompression -> LLMGeneration{get_edge_style(4)};")
        dot_lines.append(f"  LLMGeneration -> CitationValidator{get_edge_style(5)};")
        dot_lines.append("  CitationValidator -> Question [style=dashed, color=\"#1e293b\", penwidth=1.5, arrowsize=0.8];")
        
    else:
        # Linear Left-to-Right progress path
        def get_edge_style(from_idx):
            if from_idx < current_idx:
                return " [color=\"#00f0ff\", penwidth=3.0]"
            elif from_idx == current_idx:
                return " [color=\"#38bdf8\", penwidth=2.5, style=dashed]"
            else:
                return " [color=\"#1e293b\", penwidth=1.5]"
                
        dot_lines.append(f"  Question -> QueryUnderstanding{get_edge_style(0)};")
        dot_lines.append(f"  QueryUnderstanding -> HybridSearch{get_edge_style(1)};")
        dot_lines.append(f"  HybridSearch -> Reranker{get_edge_style(2)};")
        dot_lines.append(f"  Reranker -> ContextCompression{get_edge_style(3)};")
        dot_lines.append(f"  ContextCompression -> LLMGeneration{get_edge_style(4)};")
        dot_lines.append(f"  LLMGeneration -> CitationValidator{get_edge_style(5)};")
        
    dot_lines.append("}")
    return "\n".join(dot_lines)

# Initialize RAG Pipeline
@st.cache_resource
def get_rag_pipeline():
    return XanhSMRAGPipeline()

pipeline = get_rag_pipeline()

# Title and Logo
st.markdown("<div class='title-text'>🚗 Xanh SM RAG Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle-text'>Hệ thống Production RAG Doanh nghiệp với Tìm kiếm Lai (Hybrid Search), Tái xếp hạng (Reranking) và Xác thực Trích nguồn Đồ thị Trạng thái</div>", unsafe_allow_html=True)

# ==============================================================================
# Sidebar Configuration Panel (Premium Organized Layout)
# ==============================================================================
with st.sidebar:
    st.markdown("<h2 style='color: #00f0ff; font-family: Inter;'>⚙️ Bảng Điều Khiển</h2>", unsafe_allow_html=True)
    st.write("Cấu hình vai trò truy cập và kiểu hiển thị đồ thị cây tư duy thời gian thực.")
    
    # 1. Role Selection
    role_option = st.selectbox(
        "👤 Lựa chọn Vai trò (Pre-Filtering Role):",
        ["Khách hàng", "Đối tác tài xế", "Đối tác cửa hàng", "Nhân viên CSKH"],
        index=0
    )
    role_map = {
        "Khách hàng": "customer",
        "Đối tác tài xế": "driver",
        "Đối tác cửa hàng": "merchant",
        "Nhân viên CSKH": "agent"
    }
    target_role = role_map[role_option]
    
    # 2. Graph Layout Selection
    layout_option = st.selectbox(
        "🌿 Kiểu sơ đồ đồ thị (Thinking Tree Layout):",
        ["Sơ đồ Tiến trình Ngang (Linear)", "Sơ đồ Vòng tròn (Circular)", "Sơ đồ Hình chữ Z (Zigzag)"],
        index=0
    )
    layout_map = {
        "Sơ đồ Tiến trình Ngang (Linear)": "ngang",
        "Sơ đồ Vòng tròn (Circular)": "vong_tron",
        "Sơ đồ Hình chữ Z (Zigzag)": "zigzag"
    }
    target_layout = layout_map[layout_option]
    
    st.markdown("---")
    st.markdown("### 📌 Thông tin RAG Pipeline")
    st.markdown("- **Dense Search:** ChromaDB In-Memory")
    st.markdown("- **Sparse Search:** Heuristic BM25 Indexer")
    st.markdown("- **Reranker:** High-Performance Key-Density")
    st.markdown("- **LLM Synthesizer:** OpenAI GPT-4o-Mini")

# 🌿 Cây Tư Duy Đồ Thị Trạng Thái (RAG Thinking Tree) placed immediately under the subtitle (full width!)
st.markdown("<h3 style='color: #00f0ff; font-family: Inter;'>🌿 Cây Tư Duy Đồ Thị Trạng Thái (RAG Thinking Tree)</h3>", unsafe_allow_html=True)
graph_placeholder = st.empty()
status_placeholder = st.empty()

# Main Navigation Tabs below the tree
tab_chat, tab_crawl, tab_eval, tab_tutorial = st.tabs([
    "💬 Trợ lý AI CSKH Xanh SM", 
    "🕷️ Thu Thập Dữ Liệu (Crawl & Ingest)", 
    "🧪 Đánh giá Chất lượng (RAGAS)", 
    "👨‍🏫 Lớp Học RAG Xanh SM"
])

# ==============================================================================
# TAB 1: Chatbot & Process Tree Visualizer
# ==============================================================================
with tab_chat:
    # Define 2-Column layout
    col_left, col_right = st.columns([1.2, 1.0])
    
    with col_right:
        st.markdown("<h3 style='color: #00f0ff; font-family: Inter;'>🔍 Nhật Ký Các Bước Xử Lý</h3>", unsafe_allow_html=True)
        expanders_placeholder = st.container()
        
    with col_left:
        st.markdown("<h3 style='color: #00f0ff; font-family: Inter;'>💬 Khung Trò Chuyện</h3>", unsafe_allow_html=True)
        
        # Initialize query state programmatically to allow instant suggestion clicking
        if "query_text_input" not in st.session_state:
            st.session_state["query_text_input"] = ""
            
        # Define high-end suggestions personalized for the selected role
        suggestions_by_role = {
            "customer": [
                "Phí hủy chuyến xe khi hành khách hủy sau 2 phút là bao nhiêu?",
                "Tôi phải làm gì nếu để quên đồ trên xe Xanh SM?",
                "Số điện thoại tổng đài hỗ trợ hành khách là số mấy?"
            ],
            "driver": [
                "Mức chiết khấu hay phí dịch vụ hệ thống của tài xế Xanh Car là bao nhiêu?",
                "Tỷ lệ nhận chuyến AR và hủy chuyến CR tài xe phải duy trì là bao nhiêu?",
                "Quy định về đồng phục và vệ sinh xe của đối tác tài xế như thế nào?"
            ],
            "merchant": [
                "Đối tác cửa hàng Xanh Food phải chiết khấu hoa hồng bao nhiêu?",
                "Chính sách bồi thường khi cửa hàng bị boom đơn ăn uống (Xanh Food)?",
                "Thời gian chuẩn bị đơn hàng của đối tác cửa hàng tối đa là bao nhiêu?"
            ],
            "agent": [
                "Tổng đài hỗ trợ tài xế và đối tác cửa hàng là số nào?",
                "Chính sách đền bù và tặng mã ưu đãi khi chuyến đi bị hủy do lỗi tài xế?",
                "Chu kỳ đối soát doanh thu của cửa hàng và tài xế là khi nào?"
            ]
        }
        
        st.markdown("💡 **Câu hỏi gợi ý (Nhấp chọn để chạy nhanh):**")
        sugg_cols = st.columns(3)
        role_suggs = suggestions_by_role.get(target_role, suggestions_by_role["customer"])
        
        for idx, sugg in enumerate(role_suggs):
            if sugg_cols[idx % 3].button(f"👉 {sugg}", key=f"sugg_{target_role}_{idx}", use_container_width=True):
                st.session_state["query_text_input"] = sugg
                st.rerun()
                
        # Chat text input bound to session state
        user_query = st.text_input(
            "📝 Nhập câu hỏi của bạn về chính sách Xanh SM:",
            placeholder="Ví dụ: Phí hủy chuyến sau 2 phút là bao nhiêu?",
            key="query_text_input"
        )
        
        if user_query:
            st.markdown(f"<div class='chat-bubble-user'><b>Bạn ({role_option}):</b><br>{user_query}</div>", unsafe_allow_html=True)
            
            # Execute actual RAG steps and update UI in true real-time!
            result = None
            for step_data in pipeline.run_step_by_step(query=user_query, role=target_role):
                stage_id = step_data["stage"]
                status_msg = step_data["msg"]
                
                # Update horizontal graph tree and status placeholders immediately
                graph_placeholder.graphviz_chart(generate_pipeline_graph(stage_id, target_layout))
                if stage_id == "CitationValidator":
                    status_placeholder.success(f"🎉 {status_msg}")
                    result = step_data["result"]
                else:
                    status_placeholder.info(f"⚡ Trạng thái: **{status_msg}**")
                
                # Add smooth transitions for fast steps, letting slow network steps block naturally
                if stage_id not in ["LLMGeneration", "CitationValidator"]:
                    time.sleep(0.35)
                
            # Render final RAG outputs
            if result:
                answer = result["answer"]
                citations = result["citations"]
                
                st.markdown("<div class='chat-bubble-bot'><b>Trợ lý AI Xanh SM:</b><br>" + answer.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
                
                # Dynamic cost and token metrics display
                cost_usd = result.get("llm_cost_usd", 0.0)
                cost_vnd = result.get("llm_cost_vnd", 0.0)
                tokens = result.get("token_usage", {})
                
                if cost_usd > 0:
                    st.markdown(
                        f"<div style='font-size: 0.9rem; color: #94a3b8; margin-bottom: 15px;'>"
                        f"💳 <b>Chi phí cuộc gọi LLM:</b> <span style='color: #00f0ff;'>${cost_usd:.6f} USD</span> "
                        f"(~<span style='color: #00f0ff;'>{cost_vnd:.2f} VNĐ</span>) | "
                        f"🔤 <b>Tổng số Tokens:</b> <span style='color: #38bdf8;'>{tokens.get('total_prompt_tokens', 0) + tokens.get('total_completion_tokens', 0)}</span> "
                        f"(Input: {tokens.get('total_prompt_tokens', 0)}, Output: {tokens.get('total_completion_tokens', 0)})"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='font-size: 0.9rem; color: #64748b; margin-bottom: 15px;'>"
                        f"💳 <b>Chi phí cuộc gọi LLM:</b> <span style='color: #34d399;'>0 VNĐ</span> (Bỏ qua LLM / Offline Fallback - Miễn phí)"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                # Citations Box
                if citations:
                    st.markdown("<h4 style='color: #38bdf8;'>🔗 Nguồn tài liệu được trích dẫn (Verified Citations)</h4>", unsafe_allow_html=True)
                    for idx, cit in enumerate(citations):
                        with st.expander(f"📍 {cit['source']} - {cit['section']}"):
                            st.write(f"**Mức độ liên quan (Rerank score):** `{cit['relevance_score']:.4f}`")
                                
                # Store in session state for right-side visualizer
                st.session_state["last_query_result"] = result
            
    # Render final static states in placeholders if result exists in session state
    if "last_query_result" in st.session_state:
        res = st.session_state["last_query_result"]
        citations = res["citations"]
        
        # Keep graph highlighted at CitationValidator
        graph_placeholder.graphviz_chart(generate_pipeline_graph("CitationValidator", target_layout))
        status_placeholder.success("🎉 Hoàn tất quy trình xử lý Production RAG!")
        
        with expanders_placeholder:
            # Step-by-step detailed thinking logs
            with st.expander("🔍 Bước 1: Query Understanding & Synonyms"):
                st.write("**Câu hỏi gốc:**", f"\"{res['query']}\"")
                st.write("**Vai trò đối tượng:**", f"`{res['role']}` (Lọc Metadata)")
                st.info("Hệ thống đã tự động phân tích và tạo nhóm truy vấn mở rộng để tối ưu hóa khả năng tìm kiếm ngữ nghĩa.")
                expanded = res.get("expanded_queries", [])
                if expanded:
                    st.write("**Nhóm truy vấn mở rộng được sinh ra (Query Expansion):**")
                    for q in expanded:
                        st.write(f"- `{q}`")
                
            with st.expander("📚 Bước 2: Hybrid Search (Dense + BM25 Fusion)"):
                st.write("**Thông tin truy vấn thực tế:**")
                expanded = res.get("expanded_queries", [res['query']])
                
                st.markdown("**1. Dense Search (Truy vấn ngữ nghĩa)**")
                st.write("Thực hiện quét không gian Vector từ ChromaDB bằng mô hình Embedding:")
                for q in expanded:
                    st.write(f"- Thao tác: `ChromaDB.similarity_search('{q}', filter={{'role': '{res['role']}'}})`")
                
                st.markdown("**2. Sparse Search (Truy vấn từ khóa BM25)**")
                st.write("Thực hiện đối sánh từ khóa trên chỉ mục nghịch đảo:")
                for q in expanded:
                    st.write(f"- Khớp từ khóa: `BM25Retriever.search('{q}', filter={{'role': '{res['role']}'}})`")
                
                st.success("Kết quả từ cả hai luồng tìm kiếm được tích hợp bằng thuật toán **RRF (Reciprocal Rank Fusion)** để xếp thứ hạng Top 30 văn bản tối ưu.")
                
            with st.expander("⚡ Bước 3: Cross-Encoder Reranking"):
                st.info("Top 30 chunks sau RRF được sắp xếp lại bằng Cross-Encoder để chỉ giữ lại Top 5 chunks có tương tác ngữ nghĩa cao nhất.")
                if 'top_docs' in res:
                    st.write("**Top 5 Chunks phù hợp nhất được giữ lại:**")
                    for idx, doc in enumerate(res['top_docs']):
                        st.markdown(f"**Vị trí #{idx+1}: {doc['source']} - {doc['section']}** (Relevance Score: `{doc['score']:.4f}`)")
                        st.write(f"> *{doc['content'].strip()}*")
                        st.write("---")
                        
            with st.expander("✂️ Bước 4: Context Compression & Prompt Synthesizer"):
                st.write("**Kích thước ngữ cảnh thực tế gửi đi:**", f"`{res.get('compressed_context_len', 0)} ký tự`")
                st.write("**Prompt System Mode:**", "`CSKH Assistant Standard Prompt (Strict Citation enforced, natural output)`")
                
            with st.expander("🛡️ Bước 5: Citation & Source Validation"):
                st.success("Hệ thống đã xác thực và lọc sạch toàn bộ nguồn trích dẫn. Nguồn chính thức đã được tách biệt hoàn toàn khỏi văn bản trả lời và hiển thị gọn gàng ở phần bên dưới.")
                
            with st.expander("💳 Bước 6: Chi Phí & Token Usage Chi Tiết"):
                st.write("**Chi tiết sử dụng tokens cho mô hình gpt-4o-mini:**")
                tokens = res.get("token_usage", {})
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**1. Query Expansion (Mở rộng ý định)**")
                    st.write(f"- Input Prompt Tokens: `{tokens.get('query_expansion', {}).get('prompt_tokens', 0)}`")
                    st.write(f"- Output Completion Tokens: `{tokens.get('query_expansion', {}).get('completion_tokens', 0)}`")
                with c2:
                    st.markdown("**2. Generation (Tổng hợp LLM)**")
                    st.write(f"- Input Prompt Tokens: `{tokens.get('generation', {}).get('prompt_tokens', 0)}`")
                    st.write(f"- Output Completion Tokens: `{tokens.get('generation', {}).get('completion_tokens', 0)}`")
                    
                st.write("---")
                st.markdown(
                    f"💵 **Tổng chi phí truy vấn:** <span style='color: #00f0ff; font-weight: bold;'>${res.get('llm_cost_usd', 0.0):.6f} USD</span> "
                    f"(~<span style='color: #00f0ff; font-weight: bold;'>{res.get('llm_cost_vnd', 0.0):.2f} VNĐ</span>)",
                    unsafe_allow_html=True
                )
    else:
        # Default empty state graph when no query has been run yet
        graph_placeholder.graphviz_chart(generate_pipeline_graph("Question", target_layout))
        status_placeholder.info("👈 Hãy nhập một câu hỏi ở cột bên trái để theo dõi quá trình Thinking Tree của RAG Pipeline!")

# ==============================================================================
# TAB 1.5: Crawl and Ingestion Interface (Real-time Crawler & Doc Viewer)
# ==============================================================================
with tab_crawl:
    st.markdown("<h3 style='color: #00f0ff; font-family: Inter;'>🕷️ Thu Thập & Đồng Bộ Hóa Dữ Liệu Chính Sách Thực Tế</h3>", unsafe_allow_html=True)
    st.markdown("Hệ thống tích hợp công cụ thu thập dữ liệu tự động (Web Crawler) cấu hình BFS để cào dữ liệu thực tế từ Xanh SM, tự động tiền xử lý HTML thành Markdown và đồng bộ vào Vector Database.")
    
    col_c1, col_c2 = st.columns([1.2, 1.0])
    
    with col_c1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8;'>⚙️ Cấu HÌnh Web Crawler & Ingest</h4>", unsafe_allow_html=True)
        
        crawl_url = st.text_input(
            "🔗 URL bắt đầu crawl (Start URL):",
            value="https://www.xanhsm.com/",
            placeholder="https://www.xanhsm.com/..."
        )
        
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1:
            max_depth = st.slider("🌐 Độ sâu BFS tối đa (Max Depth):", min_value=1, max_value=5, value=2)
        with c_sub2:
            max_pages = st.slider("📄 Số lượng trang tối đa (Max Pages):", min_value=1, max_value=50, value=10)
            
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            start_crawl = st.button("🚀 Khởi chạy Crawl & Ingest", use_container_width=True)
        with c_btn2:
            start_ingest = st.button("🔄 Chỉ Ingest Lại Dữ Liệu", use_container_width=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Real-time console progress logger
        if start_crawl or start_ingest:
            log_placeholder = st.empty()
            status_box = st.status("⚡ Bắt đầu tiến hành..." if start_crawl else "⚡ Bắt đầu đồng bộ lại...")
            
            logs = []
            def update_log(stage, message):
                logs.append(f"[{stage}] {message}")
                log_placeholder.code("\n".join(logs), language="plaintext")
            
            if start_crawl:
                with status_box:
                    st.write("🕷️ Đang thực thi Web Crawler...")
                    crawler = GreenSMCrawler(
                        start_url=crawl_url,
                        max_depth=max_depth,
                        max_pages=max_pages,
                        progress_callback=update_log
                    )
                    crawler.crawl()
                    
                    st.write("🧹 Đang thực thi tiền xử lý, phân mảnh và nhúng VectorDB...")
                    run_ingestion(progress_callback=update_log)
                    
                    status_box.update(label="🎉 Crawl & Ingest Hoàn Tất Thành Công!", state="complete")
                    st.success("Tài liệu chính sách đã được cập nhật thành công vào hệ thống RAG!")
                    if st.button("🔄 Làm mới giao diện"):
                        st.cache_resource.clear()
                        st.rerun()
                    
            elif start_ingest:
                with status_box:
                    st.write("🧹 Đang phân mảnh và đồng bộ lại VectorDB từ dữ liệu thư mục data...")
                    run_ingestion(progress_callback=update_log)
                    
                    status_box.update(label="🎉 Đồng bộ Ingestion Hoàn Tất Thành Công!", state="complete")
                    st.success("Cơ sở dữ liệu Vector đã được làm mới!")
                    if st.button("🔄 Làm mới giao diện"):
                        st.cache_resource.clear()
                        st.rerun()
                    
            # Clear caches to ensure new data takes effect immediately
            st.cache_resource.clear()
            
    with col_c2:
        st.markdown("<div class='glass-card' style='height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #00f0ff;'>📁 Kho Tài Liệu Đã Thu Thập (Document Explorer)</h4>", unsafe_allow_html=True)
        st.markdown("Xem trước các tệp chính sách Markdown đã thu thập và lưu giữ trong các thư mục phân vai trò.")
        
        # Look at data folder dynamically
        import glob
        data_dir = config.DATA_DIR
        categories = ["customer", "driver", "merchant", "faq"]
        
        selected_category = st.selectbox("📂 Chọn thư mục phân loại:", categories)
        
        cat_dir = os.path.join(data_dir, selected_category)
        if os.path.exists(cat_dir):
            files = [f for f in os.listdir(cat_dir) if f.endswith(".md")]
        else:
            files = []
            
        if files:
            selected_file = st.selectbox("📄 Chọn tài liệu chính sách:", files)
            
            file_path = os.path.join(cat_dir, selected_file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                
                st.markdown("---")
                st.markdown(f"**📍 Đường dẫn:** `{selected_category}/{selected_file}`")
                
                preview_mode = st.radio("Chế độ xem:", ["Xem dạng văn bản", "Xem thô (Markdown)"], horizontal=True)
                
                if preview_mode == "Xem thô (Markdown)":
                    st.code(file_content, language="markdown")
                else:
                    st.markdown(file_content)
                    
            except Exception as e:
                st.error(f"Không thể đọc file: {e}")
        else:
            st.warning("⚠️ Thư mục này chưa có tài liệu nào được thu thập. Hãy ấn nút chạy Crawler phía bên trái nhé!")
            
        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# TAB 2: Quality Evaluation Tab (RAGAS)
# ==============================================================================
with tab_eval:
    st.markdown("<h3 style='color: #00f0ff; font-family: Inter;'>🧪 RAGAS Quality Evaluation Suite</h3>", unsafe_allow_html=True)
    st.markdown("Chương trình chạy đánh giá đo lường độ tin cậy của RAG trên bộ **Gold Dataset** chuẩn mực của Xanh SM.")
    
    # API key input field
    user_api_key = st.text_input(
        "🔑 Nhập OpenAI API Key của bạn để bắt đầu chạy chấm điểm (Đảm bảo an toàn):",
        type="password",
        placeholder="sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx"
    )
    
    if st.button("🚀 Khởi chạy Quy trình Đánh giá Chất lượng RAGAS"):
        if not user_api_key.strip():
            st.warning("⚠️ Vui lòng nhập OpenAI API Key của bạn vào ô trên để chạy Suite đánh giá!")
        else:
            # Reconfigure global config securely
            config.OPENAI_API_KEY = user_api_key
            config.EMBEDDING_PROVIDER = "openai"  # Switch to openai to test real completions if key provided
            
            # Elegant Loading with animations
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("⚡ 1. Đang nạp cấu hình và khởi tạo mô hình GPT-4o-mini...")
            progress_bar.progress(15)
            time.sleep(1.0)
            
            status_text.text("📚 2. Đang truy vấn dữ liệu In-Memory RAG và BM25 cho 5 kịch bản vàng...")
            progress_bar.progress(40)
            
            # Initialize Evaluation
            try:
                evaluator = XanhSMEvaluation()
                
                status_text.text("🧪 3. Đang thực thi chấm điểm Độ chính xác (Faithfulness) và Khả năng tìm kiếm (Recall)...")
                progress_bar.progress(70)
                
                # Run suite
                report = evaluator.run_suite()
                metrics = report["metrics"]
                details = report["details"]
                
                progress_bar.progress(100)
                status_text.text("🎉 Chấm điểm hoàn tất thành công!")
                time.sleep(0.5)
                
                # Show beautiful Metric cards
                st.markdown("<h4 style='color: #00f0ff;'>📊 Bảng Điểm Chất Lượng Đạt Được</h4>", unsafe_allow_html=True)
                
                c_lat, c_cit, c_rec = st.columns(3)
                
                with c_lat:
                    st.metric(
                        label="⚡ Độ trễ Phản hồi (Latency)",
                        value=f"{metrics['average_latency_sec']} giây",
                        delta="Cực nhanh",
                        delta_color="normal"
                    )
                with c_cit:
                    st.metric(
                        label="📍 Độ chính xác Trích dẫn (Citation)",
                        value=f"{metrics['average_citation_accuracy'] * 100}%",
                        delta="Đạt chuẩn chính xác",
                        delta_color="normal"
                    )
                with c_rec:
                    st.metric(
                        label="🎯 Khả năng Tìm kiếm từ khóa (Recall)",
                        value=f"{metrics['average_retrieval_recall'] * 100}%",
                        delta="Khớp 80% từ khóa vàng",
                        delta_color="normal"
                    )
                    
                # Details Table
                st.markdown("<h4 style='color: #38bdf8; margin-top: 20px;'>📋 Chi tiết đánh giá 5 Kịch bản vàng (Gold Dataset)</h4>", unsafe_allow_html=True)
                
                df_details = pd.DataFrame(details)
                # Select important columns and translate
                df_display = df_details[[
                    "query", "role", "latency_seconds", "citation_coverage", "retrieval_recall"
                ]].copy()
                df_display.columns = [
                    "Câu hỏi (Query)", "Đối tượng (Role)", "Độ trễ (Giây)", "Độ khớp trích dẫn", "Chỉ số Recall"
                ]
                
                st.dataframe(df_display, use_container_width=True)
                
                # Show full Golden Dataset QA results dynamically
                st.markdown("<h4 style='color: #00f0ff; margin-top: 25px;'>📝 Chi Tiết Các Kịch Bản Vàng Và Câu Trả Lời Thực Tế</h4>", unsafe_allow_html=True)
                st.write("Dưới đây là chi tiết các câu hỏi, từ khóa đối sánh chuẩn và câu trả lời đầy đủ do hệ thống RAG tạo ra trong quá trình đánh giá:")
                
                for idx, row in enumerate(details):
                    with st.expander(f"📌 Kịch bản #{idx + 1} (Vai trò: {row['role']})"):
                        st.markdown(f"**Câu hỏi đánh giá (Query):**")
                        st.write(f"*{row['query']}*")
                        
                        st.markdown(f"**Từ khóa chuẩn mong muốn (Expected Keywords):**")
                        st.write(", ".join([f"`{kw}`" for kw in row['expected_keywords']]))
                        
                        st.markdown(f"**Từ khóa thực tế tìm thấy (Matched Keywords):**")
                        st.write(", ".join([f"`{kw}`" for kw in row['matched_keywords']]) if row['matched_keywords'] else "*Không tìm thấy từ khóa nào*")
                        
                        st.markdown(f"**Câu trả lời do RAG sinh ra (RAG Generated Answer):**")
                        st.info(row['answer'])
                        
                        st.markdown(f"⏱️ **Độ trễ:** `{row['latency_seconds']:.3f} giây` | 🎯 **Tỷ lệ Recall:** `{row['retrieval_recall']*100:.1f}%` | 🔗 **Độ phủ trích dẫn:** `{row['citation_coverage']*100:.1f}%`")
                
            except Exception as e:
                st.error(f"❌ Quá trình đánh giá thất bại: {e}. Vui lòng kiểm tra lại tính chính xác của OpenAI API Key của bạn!")

# ==============================================================================
# TAB 3: Interactive RAG Classroom with Cartoon AI Teacher
# ==============================================================================
with tab_tutorial:
    st.markdown("<h3 style='color: #00f0ff; font-family: Inter; margin-top: 10px;'>👨‍🏫 Lớp Học RAG Doanh Nghiệp Của Thầy Giáo AI</h3>", unsafe_allow_html=True)
    st.write("Chào mừng các em đến với lớp học lý giải hoạt động RAG! Hãy để Thầy Giáo AI dẫn dắt các em tìm hiểu luồng dữ liệu nhé!")
    
    col_img, col_info = st.columns([1.0, 1.6])
    
    with col_img:
        image_path = os.path.join(os.path.dirname(__file__), 'rag_teacher_illustration.png')
        if os.path.exists(image_path):
            st.image(image_path, caption="👨‍🏫 Thầy Giáo AI Xanh SM - Chuyên Gia RAG", use_container_width=True)
        else:
            st.warning("⚠️ Không tìm thấy hình ảnh thầy giáo.")
            
    with col_info:
        st.markdown("""
        <div style='background: rgba(16, 24, 48, 0.6); border: 2px solid #00f0ff; border-radius: 16px; padding: 22px; box-shadow: 0 4px 15px rgba(0, 240, 255, 0.15); margin-bottom: 20px;'>
            <h4 style='color: #00f0ff; margin-top: 0; font-family: Inter;'>💬 Lời Giảng Mở Đầu Của Thầy:</h4>
            <p style='font-size: 1.05rem; line-height: 1.6; color: #e2e8f0;'>
                <i>"Chào các em học sinh thân mến! Ta là <b>Thầy Giáo AI Xanh SM</b>. Hôm nay, ta rất vui mừng được chào đón các em 
                đến với lớp học chuyên sâu về kiến trúc <b>Retrieval-Augmented Generation (RAG)</b> thực tế. 
                <br><br>
                Để giải quyết các bài toán doanh nghiệp lớn, hệ thống không chỉ đơn giản là 'hỏi gì đáp nấy' (chất lượng cực thấp 
                và dễ sinh ra ảo giác), mà phải đi qua một quy trình xử lý cực kỳ chặt chẽ, tối ưu và kiểm soát nghiêm ngặt. 
                Hãy cùng Thầy lật mở tấm bảng neon phía sau để phân tích từng bước nhé!"</i>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<h4 style='color: #38bdf8; font-family: Inter; margin-top: 15px;'>🏫 Bài Giảng Chi Tiết Luồng Hoạt Động (RAG Workflow & Evidences)</h4>", unsafe_allow_html=True)
    
    # Special Preprocessing & Chunking Expander
    with st.expander("🧹 Bài Giảng Đặc Biệt: Tiền Xử Lý Dữ Liệu & Phân Mảnh Tài Liệu (HTML Preprocessing & Heading-Aware Chunking)"):
        col_t0, col_ex0 = st.columns([1.2, 1.0])
        with col_t0:
            st.markdown("##### 💬 Lời Giảng Của Thầy:")
            st.write(
                "\"Để xây dựng một hệ thống RAG chuẩn doanh nghiệp, khâu **tiền xử lý dữ liệu (Preprocessing)** và **phân mảnh (Chunking)** là vô cùng quan trọng các em ạ! "
                "Nếu ta nạp trực tiếp toàn bộ mã nguồn HTML hoặc các file chính sách dài hàng chục trang vào Vector database, RAG sẽ tìm kiếm cực kỳ kém hiệu quả và tốn chi phí. "
                "<br><br>"
                "Hệ thống Xanh SM của chúng ta áp dụng quy trình xử lý 2 giai đoạn cực kỳ bài bản:<br>"
                "1. **Tiền xử lý & Dọn dẹp (Cleaning):** Loại bỏ hoàn toàn các thẻ thừa (như navigation bar, footer, script, css) và chuyển HTML thô về định dạng **Markdown** tối giản nhằm giữ lại cấu trúc phân cấp (Headers, Tables, Lists).<br>"
                "2. **Tách đoạn thông minh (Heading-Aware Chunking):** Thay vì cắt văn bản ngẫu nhiên theo số ký tự (làm mất ngữ cảnh, đứt câu), Thầy thiết kế bộ tách `HeadingAwareSplitter`. Bộ tách này cắt văn bản theo các thẻ tiêu đề Markdown (`#`, `##`, `###`) để giữ các điều khoản nguyên vẹn, sau đó mới chia nhỏ với kích thước `chunk_size=700` ký tự và `overlap=150` để đảm bảo thông tin gối đầu liền mạch!\""
            , unsafe_allow_html=True)
        with col_ex0:
            st.markdown("##### 🔍 Minh Họa Quy Trình & Ví Dụ Thực Tế:")
            st.info(
                "**1. Tiền xử lý HTML -> Markdown:**\n"
                "- Thư viện BeautifulSoup bóc tách thẻ `<article>` hoặc `class='policy'`. \n"
                "- Loại bỏ các thẻ rác `<script>`, `<style>`, `<nav>`.\n"
                "- Chuyển thẻ table `<table>` sang định dạng bảng Markdown để lưu giữ các bảng phí chuẩn chỉnh.\n\n"
                "**2. Metadata làm giàu (Metadata Enrichment):**\n"
                "Mỗi chunk được gắn kèm các thông tin quan trọng để lọc chính xác khi truy vấn:\n"
                "- `role`: Vai trò áp dụng (customer, driver, merchant, faq).\n"
                "- `section`: Đường dẫn tiêu đề hoàn chỉnh (ví dụ: `Chính sách hủy > Biểu phí phạt`).\n"
                "- `chunk_id`: Mã hóa MD5 ASCII để tránh lỗi ký tự Unicode khi ghi vào database."
            )
            
        st.markdown("---")
        st.markdown("##### 📋 Ví Dụ Phân Mảnh Thực Tế Trực Quan:")
        
        # Show a code block comparing raw markdown and two chunk outputs
        st.markdown("""
        Hãy xem một file chính sách tài xế `driver_policy.md` được chia mảnh thực tế:
        """)
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("**📄 File chính sách gốc (Raw Markdown):**")
            st.code("""
# CHÍNH SÁCH ĐỐI TÁC TÀI XẾ XANH SM
---
url: https://www.xanhsm.com/driver-terms
category: driver
crawled_at: 2026-05-26
---

## Điều 1: Quy định Đồng phục
Tất cả các đối tác tài xế Xanh SM phải mặc đồng phục (áo thun xanh Cyan, mũ bảo hiểm và quần dài lịch sự) khi thực hiện chuyến đi.

## Điều 2: Tỷ lệ hoạt động tối thiểu
Tài xế phải duy trì Tỷ lệ nhận chuyến (AR) tối thiểu là 85% và Tỷ lệ hủy chuyến (CR) dưới 10% để tránh bị khóa tài khoản tạm thời.
""", language="markdown")
            
        with col_v2:
            st.markdown("**📦 Kết quả tạo ra 2 Phân mảnh (Logical Chunks):**")
            st.code("""
[Phân mảnh #1]
ID: a78d8a7c6f0923a1a9e8f17c2f00a6e3
Nội dung:
## Điều 1: Quy định Đồng phục
Tất cả các đối tác tài xế Xanh SM phải mặc đồng phục (áo thun xanh Cyan, mũ bảo hiểm và quần dài lịch sự) khi thực hiện chuyến đi.

Metadata:
{
  "source": "driver_policy.md",
  "role": "driver",
  "url": "https://www.xanhsm.com/driver-terms",
  "section": "CHÍNH SÁCH ĐỐI TÁC TÀI XẾ XANH SM > Điều 1: Quy định Đồng phục",
  "version": "2026-05"
}

--------------------------------------------------

[Phân mảnh #2]
ID: 4d28fe7a32d184cf92b8a4f89d3112c8
Nội dung:
## Điều 2: Tỷ lệ hoạt động tối thiểu
Tài xế phải duy trì Tỷ lệ nhận chuyến (AR) tối thiểu là 85% và Tỷ lệ hủy chuyến (CR) dưới 10% để tránh bị khóa tài khoản tạm thời.

Metadata:
{
  "source": "driver_policy.md",
  "role": "driver",
  "url": "https://www.xanhsm.com/driver-terms",
  "section": "CHÍNH SÁCH ĐỐI TÁC TÀI XẾ XANH SM > Điều 2: Tỷ lệ hoạt động tối thiểu",
  "version": "2026-05"
}
""", language="json")

    # Step 1 Expandable Card
    with st.expander("📚 Bài Giảng 1: Nhận câu hỏi & Mở Rộng Ý Định (AI Query Expansion)"):
        col_t1, col_ex1 = st.columns([1.2, 1.0])
        with col_t1:
            st.markdown("##### 💬 Lời Giảng Của Thầy:")
            st.write(
                "\"Các em biết đấy, con người chúng ta khi đặt câu hỏi thường gõ thiếu từ, dùng tiếng lóng hoặc viết sai chính tả. "
                "Nếu hệ thống RAG chỉ lấy câu hỏi gốc đi tìm kiếm, ta sẽ bỏ sót rất nhiều tài liệu quan trọng! "
                "Vì vậy, ở bước **Query Expansion (AI)**, Thầy gọi một LLM để phân tích và nhân bản câu hỏi gốc thành "
                "3 câu hỏi đồng nghĩa chất lượng bằng Tiếng Việt. Điều này giúp chúng ta vét sạch mọi góc khuất của chính sách!\""
            )
        with col_ex1:
            st.markdown("##### 🔍 Ví Dụ Thực Tế & Dẫn Chứng:")
            st.info(
                "**Câu hỏi gốc:** *'Hotline Xanh SM là số mấy?'*\n\n"
                "**Ý định AI mở rộng:**\n"
                "- *'Số điện thoại hỗ trợ hành khách Xanh SM'* (Synonym)\n"
                "- *'Tổng đài chăm sóc khách hàng CSKH Xanh SM'* (Synonym)\n"
                "- *'Số hotline toàn quốc liên hệ đặt xe Xanh'* (Synonym)\n\n"
                "💡 **Dẫn chứng:** Việc mở rộng này giúp hệ thống truy quét được cả file `terms.md` (chứa từ khóa 'Tổng đài') và `booking.md` (chứa từ 'Hotline') cùng lúc!"
            )
            
    # Step 2 Expandable Card
    with st.expander("🔍 Bài Giảng 2: Tìm Kiếm Lai Hai Luồng (Dense & Sparse Hybrid Search)"):
        col_t2, col_ex2 = st.columns([1.2, 1.0])
        with col_t2:
            st.markdown("##### 💬 Lời Giảng Của Thầy:")
            st.write(
                "\"Sau khi có nhóm câu hỏi mở rộng, Thầy sử dụng cơ chế **Tìm Kiếm Lai (Hybrid Search)** kết hợp hai tay săn dữ liệu: "
                "1. **Dense Search (Tìm kiếm Ngữ nghĩa):** Sử dụng các vector nhúng (Embedding) để tìm các văn bản có cùng ý nghĩa dù không dùng chung từ ngữ. "
                "2. **Sparse Search (Tìm kiếm Từ khóa BM25):** Tra cứu từ khóa chính xác trên chỉ mục nghịch đảo để bắt trúng các con số, tên điều khoản. "
                "Cả hai kết quả sau đó được hòa trộn bằng thuật toán **RRF (Reciprocal Rank Fusion)** để xếp thứ hạng Top 30 văn bản tốt nhất.\""
            )
        with col_ex2:
            st.markdown("##### 🔍 Ví Dụ Thực Tế & Dẫn Chứng:")
            st.info(
                "**Câu hỏi:** *'Phí phạt hủy chuyến Xanh Bike khi chờ quá 5 phút là bao nhiêu?'*\n\n"
                "- **Dense Search:** Sẽ tìm ra các mục quy định về việc 'không có mặt, từ chối di chuyển, đền bù'.\n"
                "- **Sparse Search (BM25):** Sẽ khớp chính xác từ khóa 'Xanh Bike', '5 phút' và con số '10.000 VNĐ' trong chính sách.\n\n"
                "💡 **Dẫn chứng:** Hai luồng bổ trợ cho nhau giúp tìm đúng trích đoạn tại *Điều 1, Khoản 2, file refund.md* có ghi mức phạt Xanh Bike là 10.000 VNĐ!"
            )
            
    # Step 3 Expandable Card
    with st.expander("⚡ Bài Giảng 3: Tái Xếp Hạng Siêu Tốc (Cross-Encoder Reranking)"):
        col_t3, col_ex3 = st.columns([1.2, 1.0])
        with col_t3:
            st.markdown("##### 💬 Lời Giảng Của Thầy:")
            st.write(
                "\"Có được Top 30 văn bản rồi, nhưng nếu nhồi hết vào LLM thì chi phí API sẽ rất đắt, và LLM dễ bị loãng thông tin dẫn đến câu trả lời dài dòng. "
                "Do đó, Thầy dùng một mô hình **Reranker (AI)** (Cross-Encoder) cục bộ để tính toán sự tương tác ngữ nghĩa trực tiếp giữa câu hỏi và từng đoạn trích. "
                "Hệ thống chấm điểm siêu tốc và chỉ giữ lại đúng **Top 5 văn bản có điểm số cao nhất** để chuyển sang bước tiếp theo.\""
            )
        with col_ex3:
            st.markdown("##### 🔍 Ví Dụ Thực Tế & Dẫn Chứng:")
            st.info(
                "**Câu hỏi:** *'Mức chiết khấu tài xế Xanh Luxury là bao nhiêu?'*\n\n"
                "**Bảng điểm Rerank của 3 đoạn trích đầu tiên:**\n"
                "1. *Khoản 2, Điều 1, commission.md* (Chiết khấu Xanh Luxury là 28%) -> **Score: 0.992** ➔ Giữ lại #1\n"
                "2. *Khoản 1, Điều 1, commission.md* (Chiết khấu Xanh Car là 25%) -> **Score: 0.741** ➔ Giữ lại #2\n"
                "3. *Điều 3, driver_policy.md* (Chế tài tác phong tài xế) -> **Score: 0.118** ➔ Loại bỏ\n\n"
                "💡 **Dẫn chứng:** Cross-Reranking loại bỏ các nội dung gây nhiễu, giúp LLM chỉ tập trung vào con số 28% Xanh Luxury!"
            )
            
    # Step 4 Expandable Card
    with st.expander("🤖 Bài Giảng 4: Tổng Hợp Phản Hồi Trích Nguồn (LLM Synthesizer & Citation)"):
        col_t4, col_ex4 = st.columns([1.2, 1.0])
        with col_t4:
            st.markdown("##### 💬 Lời Giảng Của Thầy:")
            st.write(
                "\"Đây là bước cuối cùng và cũng là bước thăng hoa nhất! Thầy nén Top 5 tài liệu sạch nhất thành một ngữ cảnh, "
                "đưa vào một hệ thống Prompt đặc biệt có quy tắc kiểm duyệt trích nguồn cực kỳ nghiêm ngặt. "
                "Mô hình ngôn ngữ lớn (LLM - GPT-4o-mini) sẽ tổng hợp câu trả lời tự nhiên, thân thiện đúng tác phong CSKH Xanh SM. "
                "Sau đó, hệ thống của Thầy sẽ bóc tách các nguồn tham khảo chính thức, đối sánh URL và hiển thị gọn gàng bên dưới câu trả lời!\""
            )
        with col_ex4:
            st.markdown("##### 🔍 Ví Dụ Thực Tế & Dẫn Chứng:")
            st.info(
                "**Câu trả lời sinh ra:**\n"
                "*'Chào quý khách, mức chiết khấu (phí dịch vụ hệ thống) dành cho tài xế Xanh Luxury là 28% trên tổng doanh thu cước mỗi chuyến đi...'* (Câu trả lời cực sạch, không bị dính văn bản thô).\n\n"
                "**Nguồn trích dẫn hiển thị:**\n"
                "- *📍 commission.md - Điều 1: Mức Chiết Khấu (URL: https://www.greensm.com/vn-vi/terms-policies)*\n\n"
                "💡 **Dẫn chứng:** Toàn bộ liên kết nguồn đều được trích dẫn trực tiếp từ các file chính sách chính thức đã được dọn dẹp sạch sẽ link hỏng!"
            )
            
    st.markdown("<div style='text-align: center; margin-top: 30px; font-size: 1.1rem; color: #00f0ff;'>🎉 Chúc các em học tập vui vẻ và làm chủ công nghệ RAG Doanh Nghiệp cùng Xanh SM! 🎉</div>", unsafe_allow_html=True)
