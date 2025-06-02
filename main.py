import math
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import io

app = FastAPI()

def safe_json_value(val):
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return 0
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    return val

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Только Excel или CSV файлы принимаются")

    contents = await file.read()

    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка про чтение файла: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Файл не содержит данных или поврежден.")

    print("Колонки в таблице:", df.columns.tolist())

    salary_sum = 0
    if "Зарплата($)" in df.columns:
        try:
            col = pd.to_numeric(df["Зарплата($)"], errors='coerce').fillna(0)
            col = col.where(np.isfinite(col), 0)
            print("Колонка Зарплата после обработки:", col.tolist())
            salary_sum = float(col.sum())
            print("Сумма Зарплаты:", salary_sum)
        except Exception as e:
            print("Ошибка при подсчете зарплаты:", e)
            salary_sum = 0

    preview = df.head(3).to_dict(orient="records")
    for row in preview:
        for k, v in row.items():
            row[k] = safe_json_value(v)

    stats = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_list": list(df.columns),
        "salary_total": salary_sum
    }

    return {
        "filename": file.filename,
        "preview": preview,
        "stats": stats
    }
