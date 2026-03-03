import os
from fastapi import FastAPI, HTTPException
import pymysql
from dotenv import load_dotenv
from pydantic import BaseModel
import requests
import json
import re
from decimal import Decimal
from datetime import date, datetime

load_dotenv()

app = FastAPI(title="Mini Tienda API")

def get_conn():
    try:
        return pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection error: {e}")

@app.get("/health")
def health():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok;")
            row = cur.fetchone()
        return {"status": "ok", "db": row}
    finally:
        conn.close()

@app.get("/productos")
def productos():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.sku, p.nombre, p.categoria, p.precio, i.stock, i.stock_min
                FROM productos p
                JOIN inventario i ON i.producto_id = p.id
                ORDER BY p.id;
            """)
            rows = cur.fetchall()
        return {"count": len(rows), "items": rows}
    finally:
        conn.close()

@app.get("/ventas/resumen")
def ventas_resumen():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                  DATE(fecha) AS dia,
                  COUNT(*) AS num_ventas,
                  ROUND(SUM(total), 2) AS facturacion
                FROM ventas
                GROUP BY DATE(fecha)
                ORDER BY dia DESC
                LIMIT 10;
            """)
            rows = cur.fetchall()
        return {"items": rows}
    finally:
        conn.close()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

class AskRequest(BaseModel):
    question: str

ALLOWED_TABLES = {"productos", "inventario", "clientes", "ventas", "venta_lineas"}

def basic_sql_guard(sql: str) -> str:
    s = sql.strip()

    if ";" in s or "--" in s or "/*" in s:
        raise HTTPException(400, "SQL inválida (caracteres no permitidos).")

    low = s.lower()

    if not low.startswith("select"):
        raise HTTPException(400, "Solo se permiten consultas SELECT.")

    forbidden = [" drop ", " delete ", " update ", " insert ", " alter ", " truncate ", " create "]
    if any(f in f" {low} " for f in forbidden):
        raise HTTPException(400, "SQL contiene operaciones no permitidas.")

    tables = set(re.findall(r"(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", low))
    if not tables.issubset(ALLOWED_TABLES):
        raise HTTPException(400, f"Tablas no permitidas: {sorted(tables - ALLOWED_TABLES)}")

    if " limit " not in f" {low} ":
        s = s + " LIMIT 50"

    return s

def extract_json(text: str) -> dict:
    t = text.strip()

    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, flags=re.DOTALL | re.IGNORECASE)
    if m:
        t = m.group(1).strip()

    if not t.startswith("{"):
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            t = t[start:end+1]

    return json.loads(t)

@app.post("/ask")
def ask(req: AskRequest):
    system = (
        "Eres un generador de SQL para MySQL. Devuelve SOLO JSON válido con la clave 'sql'. "
        "No incluyas texto extra. Solo SELECT. No uses ';'.\n"
        "Esquema:\n"
        "- productos(id, sku, nombre, categoria, precio, coste, activo, creado_en)\n"
        "- inventario(producto_id, stock, stock_min, actualizado_en)\n"
        "- clientes(id, nombre, email, creado_en)\n"
        "- ventas(id, fecha, cliente_id, metodo_pago, total)\n"
        "- venta_lineas(id, venta_id, producto_id, cantidad, precio_unit, subtotal)\n"
        "Relaciones:\n"
        "- inventario.producto_id -> productos.id\n"
        "- ventas.cliente_id -> clientes.id\n"
        "- venta_lineas.venta_id -> ventas.id\n"
        "- venta_lineas.producto_id -> productos.id\n"
        "Reglas:\n"
        "- Si piden 'top', usa ORDER BY + LIMIT.\n"
        "- Si piden un periodo (hoy/ayer/últimos 7 días), usa ventas.fecha.\n"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": req.question}
        ],
        "stream": False
    }

    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
    if r.status_code != 200:
        raise HTTPException(502, f"Error Ollama: {r.text}")

    content = r.json()["message"]["content"]

    try:
        obj = extract_json(content)
        sql = obj["sql"]
    except Exception:
        raise HTTPException(400, f"El modelo no devolvió JSON válido: {content}")

    sql_safe = basic_sql_guard(sql)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_safe)
            rows = cur.fetchall()
    finally:
        conn.close()

    return {"question": req.question, "sql": sql_safe, "rows": rows}

class AskAnswerResponse(BaseModel):
    question: str
    sql: str
    answer: str
    rows_preview: list

def json_safe(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)

@app.post("/ask/answer")
def ask_answer(req: AskRequest):
    system_sql = (
        "Eres un generador de SQL para MySQL. Devuelve SOLO JSON válido con la clave 'sql'. "
        "No incluyas texto extra. Solo SELECT. No uses ';'.\n"
        "Esquema:\n"
        "- productos(id, sku, nombre, categoria, precio, coste, activo, creado_en)\n"
        "- inventario(producto_id, stock, stock_min, actualizado_en)\n"
        "- clientes(id, nombre, email, creado_en)\n"
        "- ventas(id, fecha, cliente_id, metodo_pago, total)\n"
        "- venta_lineas(id, venta_id, producto_id, cantidad, precio_unit, subtotal)\n"
        "Relaciones:\n"
        "- inventario.producto_id -> productos.id\n"
        "- ventas.cliente_id -> clientes.id\n"
        "- venta_lineas.venta_id -> ventas.id\n"
        "- venta_lineas.producto_id -> productos.id\n"
        "Reglas:\n"
        "- Si piden 'top', usa ORDER BY + LIMIT.\n"
        "- Si piden un periodo (hoy/ayer/últimos 7 días), usa ventas.fecha.\n"
    )

    payload_sql = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_sql},
            {"role": "user", "content": req.question}
        ],
        "stream": False
    }

    r1 = requests.post(f"{OLLAMA_URL}/api/chat", json=payload_sql)
    if r1.status_code != 200:
        raise HTTPException(502, f"Error Ollama (SQL): {r1.text}")

    content = r1.json()["message"]["content"]
    try:
        obj = extract_json(content)
        sql = obj["sql"]
    except Exception:
        raise HTTPException(400, f"El modelo no devolvió JSON válido: {content}")

    sql_safe = basic_sql_guard(sql)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_safe)
            rows = cur.fetchall()
    finally:
        conn.close()

    preview_rows = rows[:50]

    system_answer = (
        "Eres un asistente de análisis de datos de un pequeño comercio. "
        "Responde en español, claro y profesional.\n"
        "Reglas:\n"
        "- Usa SOLO los datos proporcionados en 'RESULTADOS'. No inventes cifras.\n"
        "- Si no hay filas, dilo y sugiere qué consultar.\n"
        "- Si hay muchas filas, resume (top/bloques) y menciona cuántas filas hay.\n"
        "- Formato sugerido:\n"
        "  1) Respuesta corta (1-2 frases)\n"
        "  2) Detalles en viñetas\n"
    )

    user_answer = {
        "pregunta": req.question,
        "sql_ejecutada": sql_safe,
        "num_filas": len(rows),
        "resultados": preview_rows
    }

    payload_answer = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_answer},
            {"role": "user", "content": "RESULTADOS:\n" + json.dumps(user_answer, ensure_ascii=False, default=json_safe)}
        ],
        "stream": False
    }

    r2 = requests.post(f"{OLLAMA_URL}/api/chat", json=payload_answer)
    if r2.status_code != 200:
        raise HTTPException(502, f"Error Ollama (answer): {r2.text}")

    answer = r2.json()["message"]["content"].strip()

    return {
        "question": req.question,
        "sql": sql_safe,
        "answer": answer,
        "rows_preview": preview_rows
    }