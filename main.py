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

    preview = df.head(3).to_dict(orient="records")
    for row in preview:
        for k, v in row.items():
            row[k] = safe_json_value(v)

    numeric_analysis = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                numeric_analysis[col] = {
                    "sum": float(series.sum()),
                    "mean": float(series.mean()),
                    "min": float(series.min()),
                    "max": float(series.max())
                }
            except Exception as e:
                numeric_analysis[col] = f"Ошибка при обработке: {str(e)}"

    stats = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_list": list(df.columns),
        "numeric_analysis": numeric_analysis
    }

    return {
        "filename": file.filename,
        "preview": preview,
        "stats": stats
    }
