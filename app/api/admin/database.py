import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import String, Text, case, or_
from app.db.database import get_db, Base
from app.db.models import RagRequestLog, User, Conversation, DocumentChunk, ErrorLog, CrawlSource, EvaluationRun
from app.core.config import settings
from fastapi.responses import StreamingResponse
import asyncio
from typing import Optional

router = APIRouter()

KEYWORD_COLUMN_WEIGHTS = {
    "content": 100,
    "description": 90,
    "message": 80,
    "details": 75,
    "final_answer": 70,
    "original_query": 70,
    "rewritten_query": 65,
    "query": 65,
    "summary": 60,
    "title": 45,
    "section": 40,
    "source": 35,
    "email": 25,
    "name": 25,
}


def _is_searchable_text_column(column) -> bool:
    return isinstance(column.type, (String, Text))


def _parse_search_columns(search_columns: str, table) -> list[str]:
    if search_columns:
        requested = [c.strip() for c in search_columns.split(",") if c.strip()]
        return [
            col_name for col_name in requested
            if col_name in table.columns and _is_searchable_text_column(table.columns[col_name])
        ]

    weighted_cols = [
        col.name for col in table.columns
        if _is_searchable_text_column(col) and col.name in KEYWORD_COLUMN_WEIGHTS
    ]
    other_text_cols = [
        col.name for col in table.columns
        if _is_searchable_text_column(col) and col.name not in KEYWORD_COLUMN_WEIGHTS
    ]
    return sorted(
        weighted_cols,
        key=lambda name: KEYWORD_COLUMN_WEIGHTS.get(name, 1),
        reverse=True
    ) + other_text_cols

# --- DATABASE MANAGER ENDPOINTS ---

@router.get("/db/tables")
def get_db_tables(db: Session = Depends(get_db)):
    metadata = Base.metadata
    return list(metadata.tables.keys())

@router.get("/db/table/{table_name}")
def get_table_data(
    table_name: str, 
    limit: int = 50, 
    offset: int = 0, 
    sort_by: str = None,
    sort_order: str = "desc",
    start_date: str = None,
    end_date: str = None,
    level: str = None,
    error_type: str = None,
    keyword: str = None,
    search_columns: str = None,
    db: Session = Depends(get_db)
):
    metadata = Base.metadata
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail="Table not found")
        
    table = metadata.tables[table_name]
    
    # Build query
    query = db.query(table)
    
    # Apply date filters if date column exists
    date_col = None
    for col_name in ["created_at", "timestamp", "generated_at"]:
        if col_name in table.columns:
            date_col = table.columns[col_name]
            break
            
    if date_col is not None:
        if start_date:
            try:
                from datetime import datetime
                s_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(date_col >= s_dt)
            except Exception:
                pass
        if end_date:
            try:
                from datetime import datetime, time
                e_dt = datetime.strptime(end_date, "%Y-%m-%d")
                e_dt = datetime.combine(e_dt.date(), time(23, 59, 59, 999999))
                query = query.filter(date_col <= e_dt)
            except Exception:
                pass

    # Apply level/error_type exact filters if columns exist
    if level:
        if "level" in table.columns:
            query = query.filter(table.columns["level"] == level)
        elif "error_stage" in table.columns:
            query = query.filter(table.columns["error_stage"] == level)
            
    if error_type:
        if "error_type" in table.columns:
            query = query.filter(table.columns["error_type"] == error_type)
        elif "error_cause" in table.columns:
            query = query.filter(table.columns["error_cause"] == error_type)

    # Apply keyword search across safe text columns. The default set gives
    # higher priority to knowledge text such as document_chunks.content.
    searched_columns = []
    keyword_score_expr = None
    clean_keyword = keyword.strip() if keyword else ""
    if clean_keyword:
        searched_columns = _parse_search_columns(search_columns, table)
        if searched_columns:
            pattern = f"%{clean_keyword}%"
            match_conditions = []
            score_cases = []
            for col_name in searched_columns:
                col = table.columns[col_name]
                condition = col.ilike(pattern)
                match_conditions.append(condition)
                score_cases.append(
                    case(
                        (condition, KEYWORD_COLUMN_WEIGHTS.get(col_name, 10)),
                        else_=0
                    )
                )

            query = query.filter(or_(*match_conditions))
            keyword_score_expr = sum(score_cases)

    # Get total count after filtering
    total = db.query(func.count()).select_from(query.subquery()).scalar()
    
    # Sorting column selection
    sort_col = None
    if sort_by and sort_by in table.columns:
        sort_col = table.columns[sort_by]
    else:
        # Fallback to date column if exists, otherwise first column
        if date_col is not None:
            sort_col = date_col
        elif len(table.columns) > 0:
            sort_col = list(table.columns.values())[0]
            
    if keyword_score_expr is not None:
        query = query.order_by(keyword_score_expr.desc())

    if sort_col is not None:
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
            
    rows = query.offset(offset).limit(limit).all()
    # Convert Row objects to dicts
    data = [dict(row._mapping) for row in rows]
    
    # Extract dynamic metadata for unique choices (like levels or error types)
    extra_metadata = {}
    if "level" in table.columns:
        distinct_levels = db.query(table.columns["level"]).distinct().all()
        extra_metadata["levels"] = [r[0] for r in distinct_levels if r[0]]
    elif "error_stage" in table.columns:
        distinct_levels = db.query(table.columns["error_stage"]).distinct().all()
        extra_metadata["levels"] = [r[0] for r in distinct_levels if r[0]]
        
    if "error_type" in table.columns:
        distinct_error_types = db.query(table.columns["error_type"]).distinct().all()
        extra_metadata["error_types"] = [r[0] for r in distinct_error_types if r[0]]
    elif "error_cause" in table.columns:
        distinct_error_types = db.query(table.columns["error_cause"]).distinct().all()
        extra_metadata["error_types"] = [r[0] for r in distinct_error_types if r[0]]
    if searched_columns:
        extra_metadata["search_columns"] = searched_columns
        
    return {
        "total": total,
        "data": data,
        "columns": [c.name for c in table.columns],
        "metadata": extra_metadata
    }

class DeleteRecordsRequest(BaseModel):
    ids: list[str]

@router.post("/db/table/{table_name}/delete")
def delete_table_data(table_name: str, req: DeleteRecordsRequest, db: Session = Depends(get_db)):
    metadata = Base.metadata
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail="Table not found")
        
    table = metadata.tables[table_name]
    
    if 'id' not in table.columns:
        raise HTTPException(status_code=400, detail="Table does not have an 'id' column")
        
    stmt = table.delete().where(table.columns.id.in_(req.ids))
    result = db.execute(stmt)
    db.commit()
    
    return {"success": True, "deleted_count": result.rowcount}

@router.post("/db/table/{table_name}/delete_all")
def delete_all_table_data(table_name: str, db: Session = Depends(get_db)):
    metadata = Base.metadata
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail="Table not found")
        
    table = metadata.tables[table_name]
    stmt = table.delete()
    result = db.execute(stmt)
    db.commit()
    
    return {"success": True, "deleted_count": result.rowcount}
