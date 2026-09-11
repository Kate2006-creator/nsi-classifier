from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
import pandas as pd
import re
import os

from config import APP_NAME
from database import get_db, init_db, save_etalons_to_db, save_positions_to_db, SessionLocal, load_model
from models import Etalon, Position, ClassificationLog
from classifier import load_data
from semantic_classifier import classifier

init_db()

load_model()

def load_data_to_db():
    try:
        db = SessionLocal()
        existing_count = db.query(Position).count()
        etalon_count = db.query(Etalon).count()
        db.close()
        
        # Всегда загружаем эталоны в классификатор (даже если данные уже есть)
        if existing_count > 0 and etalon_count > 0:
            print(f"Данные уже загружены в БД: {existing_count} записей, {etalon_count} эталонов")
            
            # загружаем эмбединги в классиф-р
            db = SessionLocal()
            loaded = classifier.load_etalons(db)
            db.close()
            
            if not loaded:
                print("Эмбеддинги эталонов не загружены!")
            else:
                print(f"Семантический поиск готов: {len(classifier.etalon_names)} эталонов")
            
            return True
        
        print("Загружаем данные из CSV файлов...")
        
        df_clean, cluster_df, etalon_df = load_data()
        
        print(f"Загружено должностей: {len(df_clean)}")
        print(f"Загружено эталонов: {len(etalon_df)}")
        
        save_etalons_to_db(etalon_df)
        save_positions_to_db(df_clean)

        # Загружаем эталоны в классификатор
        db = SessionLocal()
        classifier.load_etalons(db)
        db.close()

        db = SessionLocal()
        new_count = db.query(Position).count()
        db.close()
        
        print(f"В БД загружено {new_count} записей")
        return new_count > 0
        
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        import traceback
        traceback.print_exc()
        return False

# Загружаем данные при старте
data_loaded = load_data_to_db()

if not data_loaded:
    print("Данные не загружены Надо проверить файлы CSV.")
else:
    print("Приложение готово к работе!")

app = FastAPI(title=APP_NAME)
app.mount("/static", StaticFiles(directory="static"), name="static")

def normalize_query(query: str) -> str:
    if not query:
        return ""
    query = query.lower().strip()
    query = re.sub(r'[-/.,:;()]', ' ', query)
    query = ' '.join(query.split())
    return query


def get_best_match(query: str, db: Session):
    if not query or query.strip() == "":
        return None, None, 0.0, "none"
    
    query = normalize_query(query)
    etalon_name, cluster, confidence = classifier.classify(query)

    if etalon_name and confidence > 0.2:
        pos = db.query(Position).filter(Position.etalon_name == etalon_name).first()
        if pos:
            print(f"Найдено семантически: {pos.etalon_name} (уверенность: {confidence:.3f})")
            return pos, etalon_name, confidence, "semantic"
    
    # Строковые методы
    words = query.split()
    
    # Точное совпадение с etalon_name
    pos = db.query(Position).filter(Position.etalon_name == query).first()
    if pos:
        return pos, pos.etalon_name, 1.0, "string_exact"
    
    # Частичное совпадение
    pos = db.query(Position).filter(Position.etalon_name.contains(query)).first()
    if pos:
        return pos, pos.etalon_name, 0.8, "string_partial"
    
    # По первому слову
    first_word = words[0] if words else ""
    if len(first_word) > 2:
        pos = db.query(Position).filter(
            Position.etalon_name.contains(first_word)
        ).first()
        if pos:
            return pos, pos.etalon_name, 0.5, "string_first_word"
    
    # Семантика с низкой уверенностью
    if etalon_name:
        pos = db.query(Position).filter(Position.etalon_name == etalon_name).first()
        if pos:
            return pos, etalon_name, confidence, "semantic_low"
    
    return None, None, 0.0, "none"


def get_suggestions(query: str, db: Session, limit: int = 10):
    if not query:
        return []
    
    query = normalize_query(query)
    semantic_suggestions = classifier.get_suggestions(query, limit=limit)
    
    if semantic_suggestions:
        result = []
        for sugg in semantic_suggestions:
            pos = db.query(Position).filter(
                Position.etalon_name == sugg['etalon_name']
            ).first()
            if pos:
                result.append({
                    "core_name": pos.core_name,
                    "etalon_name": pos.etalon_name,
                    "cluster": pos.cluster,
                    "score": sugg['score']
                })
        
        if result:
            return result
    
    # Строковые ещё
    suggestions = []
    seen = set()
    
    # Ищем по эталону
    matches = db.query(Position).filter(
        Position.etalon_name.contains(query)
    ).limit(limit).all()
    
    for m in matches:
        if m.core_name not in seen:
            suggestions.append({
                "core_name": m.core_name,
                "etalon_name": m.etalon_name,
                "cluster": m.cluster
            })
            seen.add(m.core_name)
    
    # Ищем по core_name
    if len(suggestions) < limit:
        matches = db.query(Position).filter(
            Position.core_name.contains(query)
        ).limit(limit - len(suggestions)).all()
        for m in matches:
            if m.core_name not in seen:
                suggestions.append({
                    "core_name": m.core_name,
                    "etalon_name": m.etalon_name,
                    "cluster": m.cluster
                })
                seen.add(m.core_name)
    
    return suggestions[:limit]


@app.get("/")
async def root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>Классификатор НСИ</title></head>
            <body>
                <h1>Классификатор НСИ</h1>
                <p>Файл static/index.html не найден</p>
                <p>Используйте API напрямую:</p>
                <ul>
                    <li><a href="/classify?name=врач">/classify?name=врач</a></li>
                    <li><a href="/search?query=врач">/search?query=врач</a></li>
                    <li><a href="/stats">/stats</a></li>
                    <li><a href="/etalon">/etalon</a></li>
                </ul>
            </body>
        </html>
        """)


@app.get("/classify")
async def classify(name: str, db: Session = Depends(get_db)):
    if not name or name.strip() == "":
        return {"error": "Введите название должности", "found": False}
    
    count = db.query(Position).count()
    if count == 0:
        return {
            "error": "База данных пуста! Загрузите данные.",
            "found": False,
            "message": "Нет данных для поиска"
        }
    
    # Аварийная догрузка
    if len(classifier.etalon_names) == 0:
        classifier.load_etalons(db)
    
    pos, etalon, confidence, method = get_best_match(name, db)
    
    # Логируем запрос
    log = ClassificationLog(
        query=name,
        result=etalon
    )
    db.add(log)
    db.commit()
    
    if pos and pos.etalon_name:
        return {
            "position": name,
            "etalon": pos.etalon_name,
            "cluster": pos.cluster,
            "confidence": round(confidence, 3),   #  уверенность
            "found": True,
            "matched_core": pos.core_name,
            "method": method                       # и метод
        }
    else:
        suggestions = get_suggestions(name, db)
        return {
            "position": name,
            "etalon": None,
            "cluster": None,
            "found": False,
            "suggestions": suggestions,
            "message": "Должность не найдена в справочнике"
        }
    

@app.get("/etalon")
async def get_etalon(db: Session = Depends(get_db)):
    etalons = db.query(Etalon).all()
    return [{
        "cluster_id": e.cluster_id,
        "etalon_name": e.etalon_name,
        "cluster_size": e.cluster_size
    } for e in etalons]


@app.get("/search")
async def search(query: str, db: Session = Depends(get_db)):
    if not query:
        return []
    
    query = normalize_query(query)
    
    # аварийная догрузка эталонов в классиф-р
    if len(classifier.etalon_names) == 0:
        classifier.load_etalons(db)
    
    # Сначала семантический поиск
    semantic_results = classifier.get_suggestions(query, limit=10)
    if semantic_results:
        return semantic_results
    
    # Затем строковый поиск
    positions = db.query(Position).filter(
        Position.core_name.contains(query)
    ).limit(20).all()
    
    if not positions:
        positions = db.query(Position).filter(
            Position.etalon_name.contains(query)
        ).limit(20).all()
    
    return [{
        "core_name": p.core_name,
        "etalon_name": p.etalon_name,
        "cluster": p.cluster
    } for p in positions]


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total = db.query(Position).count()
    covered = db.query(Position).filter(Position.etalon_name.isnot(None)).count()
    etalon_count = db.query(Etalon).count()
    cluster_count = db.query(Position).distinct(Position.cluster).count()
    
    return {
        "total_positions": total,
        "covered_positions": covered,
        "coverage_percent": round(covered / total * 100, 1) if total > 0 else 0,
        "etalon_count": etalon_count,
        "cluster_count": cluster_count
    }


@app.get("/logs")
async def get_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(ClassificationLog).order_by(
        ClassificationLog.timestamp.desc()
    ).limit(limit).all()
    
    return [{
        "query": l.query,
        "result": l.result,
        "timestamp": l.timestamp.isoformat()
    } for l in logs]


@app.get("/status")
async def get_status():
    from database import SessionLocal
    db = SessionLocal()
    count = db.query(Position).count()
    etalon_count = db.query(Etalon).count()
    db.close()
    
    return {
        "positions_count": count,
        "etalons_count": etalon_count,
        "data_loaded": count > 0,
        "semantic_loaded": len(classifier.etalon_names) > 0,
        "status": "ready" if count > 0 else "no_data"
    }


@app.post("/load-data")
async def reload_data():
    success = load_data_to_db()
    return {
        "success": success,
        "message": "Данные загружены" if success else "Ошибка загрузки данных"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)