import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")
custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- INSTRUCCIONES DE USO ---
with st.expander("📖 Instrucciones de uso"):
  st.markdown("""
    1. **Configuración:** Seleccione la empresa, el banco, la frecuencia, el mes y el año correspondientes.
    2. **Carga de Archivos:** Suba el estado de cuenta bancario y el reporte de Profit Plus en formato `.csv`.
    3. **Procesamiento:** El sistema analizará automáticamente ambos archivos y validará los movimientos.
    4. **Resultados:** Revise las pestañas (Conciliados, Inversiones, Pendientes y Errores) para validar la información.
    5. **Exportación:** Haga clic en el botón de descarga al final para obtener el reporte completo en formato Excel.
    """)

# --- UI CONFIGURACIÓN ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox(
    "🏦 Banco:",
    ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"],
)
p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox(
    "📆 Mes:",
    [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ],
)
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028"])


# --- FUNCIONES DE PROCESAMIENTO ---
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


def normalizar(file):
  df = pd.read_csv(file, sep=None, engine="python", encoding="latin-1")
  col = next((c for c in df.columns if "referencia" in c.lower()), None)
  if col:
    df = df.rename(columns={col: "Ref"})
  else:
    if len(df.columns) > 1:
      df = df.rename(columns={df.columns[1]: "Ref"})
    else:
      df["Ref"] = ""
  df["Ref"] = (
      df["Ref"]
      .fillna("")
      .astype(str)
      .str.strip()
      .str.replace(r"\.0$", "", regex=True)
  )
  return df


# --- CARGA ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta", type=["csv"])
file_p = f_p.file_uploader("📥 Reporte Profit", type=["csv"])

if file_b and file_p:
  df_b = normalizar(file_b)
  df_p = normalizar(file_p)

  df_b_proc = df_b.copy()
  df_p_proc = df_p.copy()

  cols_b = list(df_b_proc.columns)
  cols_p = list(df_p_proc.columns)

  deb_b_col = next(
      (c for c in cols_b if any(k in c.lower() for k in ["deb", "debe"])),
      cols_b[3] if len(cols_b) > 3 else None,
  )
  cred_b_col = next(
      (c for c in cols_b if any(k in c.lower() for k in ["cred", "haber"])),
      cols_b[4] if len(cols_b) > 4 else None,
  )

  deb_p_col = next(
      (c for c in cols_p if any(k in c.lower() for k in ["deb", "debe"])),
      cols_p[3] if len(cols_p) > 3 else None,
  )
  cred_p_col = next(
      (c for c in cols_p if any(k in c.lower() for k in ["cred", "haber"])),
      cols_p[4] if len(cols_p) > 4 else None,
  )

  df_b_proc["Debito"] = (
      limpiar_monto(df_b_proc[deb_b_col]) if deb_b_col else 0.0
  )
  df_b_proc["Credito"] = (
      limpiar_monto(df_b_proc[cred_b_col]) if cred_b_col else 0.0
  )

  df_p_proc["Debe"] = limpiar_monto(df_p_proc[deb_p_col]) if deb_p_col else 0.0
  df_p_proc["Haber"] = (
      limpiar_monto(df_p_proc[cred_p_col]) if cred_p_col else 0.0
  )

  df_b_proc["Ref3"] = df_b_proc["Ref"].str[-3:]
  df_p_proc["Ref3"] = df_p_proc["Ref"].str[-3:]
  df_b_proc["orig_idx"] = df_b_proc.index
  df_p_proc["orig_idx"] = df_p_proc.index

  # --- CRUCES Y VALIDACIONES ---
  b_cred = df_b_proc[df_b_proc["Credito"] > 0].copy()
  b_cred["Monto"] = b_cred["Credito"]
  p_debe = df_p_proc[df_p_proc["Debe"] > 0].copy()
  p_debe["Monto"] = p_debe["Debe"]

  cruce_ing_1 = pd.merge(
      b_cred, p_debe, on=["Ref", "Monto"], suffixes=("_B", "_P")
  )

  b_deb = df_b_proc[df_b_proc["Debito"] > 0].copy()
  b_deb["Monto"] = b_deb["Debito"]
  p_haber = df_p_proc[df_p_proc["Haber"] > 0].copy()
  p_haber["Monto"] = p_haber["Haber"]

  cruce_eg_1 = pd.merge(
      b_deb, p_haber, on=["Ref", "Monto"], suffixes=("_B", "_P")
  )

  conciliados = pd.concat([cruce_ing_1, cruce_eg_1], ignore_index=True)

  idx_b_conc = pd.concat([
      cruce_ing_1.get("orig_idx_B", pd.Series(dtype=int)),
      cruce_eg_1.get("orig_idx_B", pd.Series(dtype=int)),
  ]).unique()
  idx_p_conc = pd.concat([
      cruce_ing_1.get("orig_idx_P", pd.Series(dtype=int)),
      cruce_eg_1.get("orig_idx_P", pd.Series(dtype=int)),
  ]).unique()

  df_b_pend = df_b_proc[~df_b_proc["orig_idx"].isin(idx_b_conc)].copy()
  df_p_pend = df_p_proc[~df_p_proc["orig_idx"].isin(idx_p_conc)].copy()

  inv_ing = pd.merge(
      b_cred[~b_cred["orig_idx"].isin(idx_b_conc)],
      p_haber[~p_haber["orig_idx"].isin(idx_p_conc)],
      on=["Ref", "Monto"],
      suffixes=("_B", "_P"),
  )
  inv_eg = pd.merge(
      b_deb[~b_deb["orig_idx"].isin(idx_b_conc)],
      p_debe[~p_debe["orig_idx"].isin(idx_p_conc)],
      on=["Ref", "Monto"],
      suffixes=("_B", "_P"),
  )
  df_inversiones = pd.concat([inv_ing, inv_eg], ignore_index=True)

  df_p_proc["Monto_Total"] = df_p_proc["Debe"] + df_p_proc["Haber"]
  df_duplicados = df_p_proc[
      (df_p_proc["Ref"] != "")
      & (
          df_p_proc.duplicated(subset=["Ref"], keep=False)
          | df_p_proc.duplicated(subset=["Ref", "Monto_Total"], keep=False)
      )
  ].copy()

  # --- PESTAÑAS ---
  t1, t2, t3, t4, t5 = st.tabs([
      "✅ Conciliados",
      "🔄 Inversiones",
      "🏦 Pendientes Banco",
      "💻 Pendientes Profit",
      "⚠️ Duplicados/Errores",
  ])

  with t1:
    st.dataframe(conciliados, use_container_width=True)
  with t2:
    st.dataframe(df_inversiones, use_container_width=True)
  with t3:
    st.dataframe(df_b_pend, use_container_width=True)
  with t4:
    st.dataframe(df_p_pend, use_container_width=True)
  with t5:
    st.dataframe(df_duplicados, use_container_width=True)

  # --- DESCARGA ---
  buffer = io.BytesIO()
  with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    conciliados.to_excel(writer, index=False, sheet_name="Conciliados")
    df_inversiones.to_excel(
        writer, index=False, sheet_name="Inversiones_DebeHaber"
    )
    df_b_pend.to_excel(writer, index=False, sheet_name="Pendientes_Banco")
    df_p_pend.to_excel(writer, index=False, sheet_name="Pendientes_Profit")
    df_duplicados.to_excel(writer, index=False, sheet_name="Duplicados")

  st.download_button(
      "📥 Descargar Conciliación Completa",
      data=buffer.getvalue(),
      file_name=f"Conciliacion_{empresa}_{mes}_{ano}.xlsx",
  )

# --- FOOTER ---
st.markdown(
    '<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación'
    " Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>",
    unsafe_allow_html=True,
)
