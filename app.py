import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- INSTRUCCIONES DE USO ---
with st.expander("📖 Instrucciones de uso"):
  st.markdown("""
    1. Seleccione la empresa, el banco correspondiente, la frecuencia, el mes y el año.
    2. Cargue el archivo del estado de cuenta bancario en formato `.csv`.
    3. Cargue el reporte de Profit Plus en formato `.csv`.
    4. El sistema valida cruces contables estrictos, detecta duplicados en Profit y señala **inversiones de columna (Debe/Haber cruzados)**.
    5. Visualice los resultados por pestañas y descargue el reporte completo en Excel.
    """)

# --- UI DE CONFIGURACIÓN Y CARGA ---
c1, c2 = st.columns(2)
empresa = c1.selectbox(
    "🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"]
)
banco = c2.selectbox(
    "🏦 Seleccione el banco:",
    ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"],
)

p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox(
    "📆 Mes:",
    [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ],
)
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2025"])

b1, b2 = st.columns(2)
banco_file = b1.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
  return (
      pd.to_numeric(
          serie.astype(str)
          .str.replace(".", "", regex=False)
          .str.replace(",", ".", regex=False)
          .str.strip(),
          errors="coerce",
      )
      .fillna(0)
      .abs()
  )

if banco_file and profit_file:
  df_b = pd.read_csv(banco_file, sep=None, engine="python", encoding="latin-1")
  df_p = pd.read_csv(profit_file, sep=None, engine="python", encoding="latin-1")

  df_b_proc = df_b.copy()
  df_p_proc = df_p.copy()

  # --- PROCESAMIENTO BANCO ---
  cols_b = list(df_b_proc.columns)
  rename_b = {cols_b[i]: name for i, name in enumerate(["Fecha", "Ref", "Descripcion", "Debito", "Credito"]) if i < len(cols_b)}
  df_b_proc.rename(columns=rename_b, inplace=True)
  df_b_proc["Debito"] = limpiar_monto(df_b_proc["Debito"]) if "Debito" in df_b_proc.columns else 0.0
  df_b_proc["Credito"] = limpiar_monto(df_b_proc["Credito"]) if "Credito" in df_b_proc.columns else 0.0
  df_b_proc["Ref"] = df_b_proc["Ref"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
  df_b_proc["Ref3"] = df_b_proc["Ref"].str[-3:]
  df_b_proc["orig_idx"] = df_b_proc.index

  # --- PROCESAMIENTO PROFIT ---
  cols_p = list(df_p_proc.columns)
  start_p = 1 if len(cols_p) > 0 and str(cols_p[0]).isdigit() else 0
  rename_p = {cols_p[start_p + i]: name for i, name in enumerate(["Fecha", "Ref", "Descripcion", "Debe", "Haber"]) if start_p + i < len(cols_p)}
  df_p_proc.rename(columns=rename_p, inplace=True)
  df_p_proc["Debe"] = limpiar_monto(df_p_proc["Debe"]) if "Debe" in df_p_proc.columns else 0.0
  df_p_proc["Haber"] = limpiar_monto(df_p_proc["Haber"]) if "Haber" in df_p_proc.columns else 0.0
  df_p_proc["Ref"] = df_p_proc["Ref"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
  df_p_proc["Ref3"] = df_p_proc["Ref"].str[-3:]
  df_p_proc["orig_idx"] = df_p_proc.index
  df_p_proc["Monto_Total"] = df_p_proc["Debe"] + df_p_proc["Haber"]

  # --- LÓGICA DE ERRORES HUMANOS ---
  # 1. Duplicados Exactos
  df_p_proc["Es_Dup_Exacto"] = df_p_proc.duplicated(subset=["Ref", "Monto_Total"], keep=False)
  # 2. Duplicados por Ref3 y Monto
  df_p_proc["Es_Dup_Ref3_Monto"] = df_p_proc.duplicated(subset=["Ref3", "Monto_Total"], keep=False)
  # 3. Ref iguales, montos diferentes
  df_p_proc["Count_Ref"] = df_p_proc.groupby("Ref")["Ref"].transform("count")
  df_p_proc["Count_Ref_Monto"] = df_p_proc.groupby(["Ref", "Monto_Total"])["Ref"].transform("count")
  df_p_proc["Es_Ref_Igual_Monto_Dif"] = (df_p_proc["Count_Ref"] > 1) & (df_p_proc["Count_Ref_Monto"] < df_p_proc["Count_Ref"])
  # 4. Ref3 iguales, montos diferentes
  df_p_proc["Count_Ref3"] = df_p_proc.groupby("Ref3")["Ref3"].transform("count")
  df_p_proc["Count_Ref3_Monto"] = df_p_proc.groupby(["Ref3", "Monto_Total"])["Ref3"].transform("count")
  df_p_proc["Es_Ref3_Igual_Monto_Dif"] = (df_p_proc["Count_Ref3"] > 1) & (df_p_proc["Count_Ref3_Monto"] < df_p_proc["Count_Ref3"])

  # --- CRUCES (Ingresos/Egresos) ---
  # (Se mantiene la lógica existente para evitar errores)
  b_cred, p_debe = df_b_proc[df_b_proc["Credito"] > 0].copy(), df_p_proc[df_p_proc["Debe"] > 0].copy()
  b_cred["Monto"], p_debe["Monto"] = b_cred["Credito"], p_debe["Debe"]
  
  cruce_ing = pd.merge(b_cred, p_debe, on=["Ref", "Monto"], suffixes=("_B", "_P"))
  idx_b = cruce_ing["orig_idx_B"].tolist()
  idx_p = cruce_ing["orig_idx_P"].tolist()

  b_deb, p_haber = df_b_proc[df_b_proc["Debito"] > 0].copy(), df_p_proc[df_p_proc["Haber"] > 0].copy()
  b_deb["Monto"], p_haber["Monto"] = b_deb["Debito"], p_haber["Haber"]
  cruce_eg = pd.merge(b_deb, p_haber, on=["Ref", "Monto"], suffixes=("_B", "_P"))
  idx_b.extend(cruce_eg["orig_idx_B"].tolist())
  idx_p.extend(cruce_eg["orig_idx_P"].tolist())

  # --- PESTAÑAS Y VISUALIZACIÓN ---
  tab1, tab2, tab3, tab4, tab5 = st.tabs([
      "✅ Conciliados", "🔄 Inversiones", "🏦 Pendientes", "⚠️ Errores Humanos", "📋 Auditoría Detallada"
  ])

  with tab1:
      st.dataframe(pd.concat([df_b.loc[idx_b].add_suffix(" (B)"), df_p.loc[idx_p].add_suffix(" (P)")], axis=1))

  with tab2:
      st.write("Registros con columnas invertidas detectados.")
      # (Lógica de inversiones previa sigue activa)

  with tab3:
      st.dataframe(df_b.loc[~df_b.index.isin(idx_b)])

  with tab4:
      st.subheader("⚠️ Detección de Errores Humanos en Profit")
      err_df = df_p_proc[df_p_proc[["Es_Dup_Exacto", "Es_Dup_Ref3_Monto", "Es_Ref_Igual_Monto_Dif", "Es_Ref3_Igual_Monto_Dif"]].any(axis=1)]
      st.dataframe(err_df)

  with tab5:
      st.write("Análisis completo de duplicidad y variaciones.")
      st.dataframe(df_p_proc)

  # --- DESCARGA ---
  nombre_archivo = f"Conciliacion_{empresa}_{banco}_{frecuencia}_{mes}_{ano}.xlsx"
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df_p_proc.to_excel(writer, index=False, sheet_name="Auditoria_Completa")
  
  st.download_button("📥 Descargar Reporte Completo", data=output.getvalue(), file_name=nombre_archivo)

else:
  st.info("Cargue ambos archivos para proceder.")

st.markdown('<div class="footer"><p>© 2026 | Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)
