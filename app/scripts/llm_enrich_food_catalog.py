import json
import os
from pathlib import Path
from openai import OpenAI
import time
import argparse

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "your-api-key")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = """Bạn là một chuyên gia về ẩm thực. Nhiệm vụ của bạn là phân tích danh sách các món ăn/quán ăn và trả về một mảng JSON (JSON array) chứa thông tin được chuẩn hóa.
Đối với mỗi item, hãy suy luận các trường:
- taste_tags: mảng các chuỗi mô tả vị trí/tính chất (ví dụ: "dầu mỡ", "chiên xào", "cay", "ngọt", "món nước", "healthy", "thanh đạm", "đồ uống").
- ingredient_tags: mảng các chuỗi nguyên liệu chính (ví dụ: "gà", "bò", "heo", "hải sản", "rau", "trái cây").
- category: phân loại chính của quán (ví dụ: "Cơm", "Phở/Bún", "Ăn vặt", "Trà sữa", "Đồ ăn nhanh", "Món chay", "Đồ uống").
- cuisine: nền ẩm thực (ví dụ: "Món Việt", "Món Hàn", "Món Nhật", "Món Âu", "Món Á", "Fast Food").

CHỈ TRẢ VỀ JSON ARRAY. KHÔNG BAO GỒM TEXT NÀO KHÁC BÊN NGOÀI JSON (Không dùng markdown code blocks).
Định dạng đầu ra:
[
  {
    "item_id": "...",
    "taste_tags": ["..."],
    "ingredient_tags": ["..."],
    "category": "...",
    "cuisine": "..."
  }
]
"""

def enrich_batch(batch):
    # Construct prompt
    items_to_send = []
    for item in batch:
        items_to_send.append({
            "item_id": item["item_id"],
            "name": item.get("name", ""),
            "description": item.get("description", ""),
            "merchant_name": item.get("merchant_name", "")
        })
    
    user_prompt = f"Hãy xử lý danh sách sau:\n{json.dumps(items_to_send, ensure_ascii=False, indent=2)}"
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content.strip()
        # Clean markdown code blocks if any
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content.strip())
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()

    root_dir = Path(__file__).parent.parent.parent
    input_path = root_dir / "data" / "food_catalog" / "shopeefood_catalog.jsonl"
    output_path = root_dir / "data" / "food_catalog" / "shopeefood_catalog_llm.jsonl"
    
    if not input_path.exists():
        print("Input file not found.")
        return
        
    # Read existing entries
    all_entries = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_entries.append(json.loads(line))
                
    # Check already processed if resuming
    processed_ids = set()
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    processed_ids.add(item["item_id"])
                    
    print(f"Total items: {len(all_entries)}. Already processed: {len(processed_ids)}.")
    
    # Filter items to process
    to_process = [e for e in all_entries if e["item_id"] not in processed_ids]
    
    # Process in batches
    batch_size = args.batch_size
    
    with open(output_path, "a", encoding="utf-8") as f:
        for i in range(0, len(to_process), batch_size):
            batch = to_process[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(to_process) + batch_size - 1)//batch_size} (Items {i} to {i+len(batch)})...")
            
            result_json = enrich_batch(batch)
            if result_json is None:
                print("Skipping batch due to error, will retry or skip.")
                time.sleep(2)
                continue
                
            # Map results
            result_map = {res["item_id"]: res for res in result_json if "item_id" in res}
            
            for item in batch:
                enriched_data = result_map.get(item["item_id"])
                if enriched_data:
                    item["taste_tags"] = enriched_data.get("taste_tags", [])
                    item["ingredient_tags"] = enriched_data.get("ingredient_tags", [])
                    item["category"] = enriched_data.get("category", item.get("category"))
                    item["cuisine"] = enriched_data.get("cuisine", item.get("cuisine"))
                
                # Write to output incrementally
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
            f.flush()
            time.sleep(1) # Small delay to respect rate limits if any

    print("Finished enrichment! You can now replace the original file with the new one.")

if __name__ == "__main__":
    main()
