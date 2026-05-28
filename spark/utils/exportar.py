"""
Módulo de exportación de datos – UrbanBlade
Formatos: CSV, JSON, Excel (multi-hoja), PDF, Parquet, SQL
"""
import io
import pandas as pd
from datetime import datetime


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ─────────────────────────────────────────────────────────────
# CSV
# ─────────────────────────────────────────────────────────────
def a_csv(df: pd.DataFrame, separador: str = ",") -> bytes:
    """Exporta un DataFrame a bytes CSV."""
    return df.to_csv(index=False, sep=separador, encoding="utf-8-sig").encode("utf-8-sig")


# ─────────────────────────────────────────────────────────────
# JSON
# ─────────────────────────────────────────────────────────────
def a_json(df: pd.DataFrame, orientacion: str = "records") -> bytes:
    """
    Exporta a JSON.
    orientacion: 'records' | 'split' | 'index' | 'columns' | 'values'
    """
    return df.to_json(orient=orientacion, force_ascii=False,
                      indent=2, date_format="iso").encode("utf-8")


# ─────────────────────────────────────────────────────────────
# EXCEL (multi-hoja)
# ─────────────────────────────────────────────────────────────
def a_excel(hojas: dict[str, pd.DataFrame], resumen_kpis: dict | None = None) -> bytes:
    """
    hojas: {"Nombre Hoja": dataframe, ...}
    resumen_kpis: {"KPI": valor, ...} → se agrega como primera hoja
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # Hoja de portada/KPIs
        if resumen_kpis:
            df_kpi = pd.DataFrame(
                list(resumen_kpis.items()), columns=["Indicador", "Valor"]
            )
            df_kpi.to_excel(writer, sheet_name="📊 KPIs Ejecutivos", index=False)
            ws = writer.sheets["📊 KPIs Ejecutivos"]
            ws.column_dimensions["A"].width = 32
            ws.column_dimensions["B"].width = 20

        for nombre, df in hojas.items():
            hoja = nombre[:31]  # Excel limita a 31 chars
            df.to_excel(writer, sheet_name=hoja, index=False)
            ws = writer.sheets[hoja]
            # Auto-ajustar ancho de columnas
            for col in ws.columns:
                max_len = max(
                    (len(str(cell.value)) for cell in col if cell.value), default=10
                )
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    return buf.getvalue()


# ─────────────────────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────────────────────
def _limpiar(texto: str) -> str:
    """Elimina caracteres fuera de latin-1 (emojis, etc.) para compatibilidad PDF."""
    return texto.encode("latin-1", errors="ignore").decode("latin-1")


def a_pdf(titulo: str, secciones: list[dict]) -> bytes:
    """
    secciones: lista de dicts con claves:
      - "titulo": str
      - "texto": str  (opcional)
      - "df": pd.DataFrame  (opcional, máx 10 cols)
      - "kpis": dict  (opcional, pares clave:valor)
    """
    from fpdf import FPDF

    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 10)
            self.set_fill_color(15, 15, 15)
            self.set_text_color(212, 175, 55)
            self.cell(0, 8, "  UrbanBlade - Reporte de Big Data  |   UTVT IDGS-93", 0, 1, "L", fill=True)
            self.set_text_color(150, 150, 150)
            self.set_font("Helvetica", "", 8)
            self.cell(0, 5, f"  Prof. MGTI. Hector Velazquez Estrada  |  Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "L")
            self.ln(2)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(130, 130, 130)
            self.cell(0, 6, f"Extraccion del Conocimiento en BD  |  Pag. {self.page_no()}", 0, 0, "C")

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Portada / Título ──────────────────────────────────────
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(212, 175, 55)
    pdf.ln(8)
    pdf.cell(0, 12, _limpiar(titulo), 0, 1, "C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(0, 7, "UrbanBlade Big Data Module  |  Apache Spark 3.5.1 + MongoDB", 0, 1, "C")
    pdf.ln(6)
    pdf.set_draw_color(212, 175, 55)
    pdf.set_line_width(0.8)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)

    # ── Secciones ─────────────────────────────────────────────
    for sec in secciones:
        # Título de sección
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(212, 175, 55)
        pdf.cell(0, 8, _limpiar(sec.get("titulo", "")), 0, 1, "L")
        pdf.set_line_width(0.3)
        pdf.set_draw_color(80, 80, 80)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)

        # Texto descriptivo
        if sec.get("texto"):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(200, 200, 200)
            pdf.multi_cell(0, 6, _limpiar(sec["texto"]))
            pdf.ln(2)

        # KPIs en caja
        if sec.get("kpis"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(30, 30, 30)
            n = len(sec["kpis"])
            col_w = 180 / max(n, 1)
            for k, v in sec["kpis"].items():
                pdf.set_text_color(140, 140, 140)
                pdf.cell(col_w, 7, _limpiar(str(k)), 1, 0, "C", fill=True)
            pdf.ln()
            for k, v in sec["kpis"].items():
                pdf.set_text_color(212, 175, 55)
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(col_w, 9, _limpiar(str(v)), 1, 0, "C", fill=True)
            pdf.ln(6)

        # Tabla de DataFrame
        if sec.get("df") is not None:
            df = sec["df"].head(30)
            cols = list(df.columns)[:10]
            df   = df[cols]
            n_cols = len(cols)
            col_w  = 180 / n_cols

            # Encabezado
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(40, 40, 40)
            pdf.set_text_color(212, 175, 55)
            for c in cols:
                pdf.cell(col_w, 6, _limpiar(str(c)[:18]), 1, 0, "C", fill=True)
            pdf.ln()

            # Filas
            pdf.set_font("Helvetica", "", 8)
            for i, (_, row) in enumerate(df.iterrows()):
                pdf.set_fill_color(20, 20, 20) if i % 2 == 0 else pdf.set_fill_color(28, 28, 28)
                pdf.set_text_color(210, 210, 210)
                for c in cols:
                    val = _limpiar(str(row[c])[:20])
                    pdf.cell(col_w, 5, val, 1, 0, "C", fill=True)
                pdf.ln()
            pdf.ln(4)

        pdf.ln(4)

    return bytes(pdf.output())


# ─────────────────────────────────────────────────────────────
# PARQUET
# ─────────────────────────────────────────────────────────────
def a_parquet(df: pd.DataFrame) -> bytes:
    """Exporta a formato Parquet (columnar, ideal para Big Data)."""
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────
# SQL INSERT
# ─────────────────────────────────────────────────────────────
def a_sql(df: pd.DataFrame, tabla: str = "urbanblade_appointments") -> bytes:
    """Genera sentencias INSERT INTO compatibles con MySQL/PostgreSQL."""
    lines = [f"-- UrbanBlade Export – {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             f"-- Tabla: {tabla}",
             f"-- Registros: {len(df):,}",
             "",
             f"CREATE TABLE IF NOT EXISTS {tabla} ("]

    # Tipos básicos
    tipo_map = {"int64": "INT", "float64": "DECIMAL(12,2)",
                "object": "VARCHAR(255)", "bool": "BOOLEAN",
                "datetime64[ns]": "DATETIME"}
    cols_def = []
    for col, dtype in df.dtypes.items():
        sql_type = tipo_map.get(str(dtype), "VARCHAR(255)")
        cols_def.append(f"  `{col}` {sql_type}")
    lines.append(",\n".join(cols_def))
    lines.append(");\n")

    # INSERTs en lotes de 100
    cols_str = ", ".join([f"`{c}`" for c in df.columns])
    lines.append(f"INSERT INTO {tabla} ({cols_str}) VALUES")

    batch_size = 100
    rows = []
    for _, row in df.head(1000).iterrows():
        vals = []
        for v in row:
            if pd.isna(v):
                vals.append("NULL")
            elif isinstance(v, str):
                vals.append(f"'{v.replace(chr(39), chr(39)*2)}'")
            elif isinstance(v, bool):
                vals.append("1" if v else "0")
            else:
                vals.append(str(v))
        rows.append(f"  ({', '.join(vals)})")

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        lines.append(",\n".join(batch))
        if i + batch_size < len(rows):
            lines.append(";\n")
            lines.append(f"INSERT INTO {tabla} ({cols_str}) VALUES")

    lines.append(";")
    return "\n".join(lines).encode("utf-8")
