import json
import os
from pathlib import Path

def normalize(text):
    return text.lower() if text else ""

def get_tags(name, category, cuisine):
    text = f"{normalize(name)} {normalize(category)} {normalize(cuisine)}"
    tags = set()
    
    # Dầu mỡ / Chiên xào
    if any(k in text for k in ["gà rán", "chiên", "xào", "nướng", "kfc", "lotteria", "jollibee", "burger", "mcdonald", "khoai tây chiên", "pizza", "bbq", "quay"]):
        tags.update(["dầu mỡ", "chiên xào", "fast food", "đồ ăn nhanh", "nhiều calo"])
        
    # Cay
    if any(k in text for k in ["cay", "mì cay", "lẩu thái", "kim chi", "tokbokki"]):
        tags.update(["cay", "vị cay"])
        
    # Nước / Thanh đạm
    if any(k in text for k in ["phở", "bún", "hủ tiếu", "cháo", "bánh canh", "lẩu", "miến"]):
        tags.update(["món nước", "dễ tiêu"])
    
    if any(k in text for k in ["salad", "chay", "healthy", "gỏi", "trái cây", "nước ép", "sinh tố", "sữa chua"]):
        tags.update(["healthy", "thanh đạm", "rau", "ít béo", "không dầu mỡ", "tốt cho sức khỏe"])
        
    # Ngọt
    if any(k in text for k in ["trà sữa", "chè", "bánh ngọt", "kem", "trà đào", "nước mía", "cafe", "cà phê", "sinh tố"]):
        tags.update(["ngọt", "đồ uống", "tráng miệng"])
        
    return list(tags)

def main():
    root_dir = Path(__file__).parent.parent.parent
    catalog_path = root_dir / "data" / "food_catalog" / "shopeefood_catalog.jsonl"
    
    if not catalog_path.exists():
        print(f"File not found: {catalog_path}")
        return
        
    entries = []
    with open(catalog_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
                
    count = 0
    for entry in entries:
        tags = get_tags(entry.get("name"), entry.get("category"), entry.get("cuisine"))
        if tags:
            existing = set(entry.get("taste_tags", []) or [])
            existing.update(tags)
            entry["taste_tags"] = list(existing)
            count += 1
            
    # Write back
    with open(catalog_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"Successfully enriched {count}/{len(entries)} items with new taste_tags.")

if __name__ == "__main__":
    main()
