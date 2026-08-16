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
    1. **Configuración:** Seleccione la empresa, el banco, la frecuencia, el mes y el año.
    2. **Carga de Archivos:** Suba el estado de cuenta bancario y el reporte de Profit Plus en formato `.xlsx`.
    3. **Procesamiento:** El sistema analizará los datos conservando la exactitud de los montos y las referencias largas.
    4. **Resultados:** Revise las pestañas de Conciliados, Cruces, Pendientes y Duplicados.
    5. **Exportación:** Descargue el resultado final en Excel.
    """)

# --- UI CONFIGURACIÓN ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])
p1, p2, p3 = st.columns(3)
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
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
      .fillna(0.0)
      .round(2)
  )

def normalizar(file):
  # Lectura directa de Excel conservando formatos originales
  df = pd.read_excel(file, dtype=str)
  col = next(
      (c for c in df.columns if any(k in c.lower() for k in ["referencia", "ref", "documento", "doc", "nro"])),
      None,
  )
  if col:
    df = df.rename(columns={col: "Ref"})
  else:
    if len(df.columns) > 1:
      df = df.rename(columns={df.columns[1]: "Ref"})
    else:
      df["Ref"] = ""
  df["Ref"] = df["Ref"].fillna("").astype(str).str.replace(".0", "", regex=False).str.strip()
  return df

def comparte_3_digitos_consecutivos(val1, val2):
  s1 = f"{val1:.2f}".replace(".", "")
  s2 = f"{val2:.2f}".replace(".", "")
  if len(s1) < 3 or len(s2) < 3: return False
  for i in range(len(s1) - 2):
    sub = s1[i : i + 3]
    if sub in s2: return True
  return False

# --- CARGA ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta (Excel)", type=["xlsx", "xls"])
file_p = f_p.file_uploader("📥 Reporte Profit (Excel)", type=["xlsx", "xls"])

if file_b and file_p:
  df_b = normalizar(file_b)
  df_p = normalizar(file_p)

  df_b_proc = df_b.copy()
  df_p_proc = df_p.copy()

  cols_b, cols_p = list(df_b_proc.columns), list(df_p_proc.columns)
  deb_b_col = next((c for c in cols_b if "deb" in c.lower()), cols_b[3] if len(cols_b)>3 else None)
  cred_b_col = next((c for c in cols_b if "cred" in c.lower()), cols_b[4] if len(cols_b)>4 else None)
  deb_p_col = next((c for c in cols_p if "deb" in c.lower()), cols_p[3] if len(cols_p)>3 else None)
  cred_p_col = next((c for c in cols_p if "hab" in c.lower()), cols_p[4] if len(cols_p)>4 else None)

  df_b_proc["Debito"] = limpiar_monto(df_b_proc[deb_b_col]) if deb_b_col else 0.0
  df_b_proc["Credito"] = limpiar_monto(df_b_proc[cred_b_col]) if cred_b_col else 0.0
  df_p_proc["Debe"] = limpiar_monto(df_p_proc[deb_p_col]) if deb_p_col else 0.0
  df_p_proc["Haber"] = limpiar_monto(df_p_proc[cred_p_col]) if cred_p_col else 0.0

  df_b_proc["Ref3"], df_p_proc["Ref3"] = df_b_proc["Ref"].str[-3:], df_p_proc["Ref"].str[-3:]
  df_b_proc["orig_idx"], df_p_proc["orig_idx"] = df_b_proc.index, df_p_proc.index

  # --- CRUCES ---
  b_cred, p_debe = df_b_proc[df_b_proc["Credito"] > 0].copy(), df_p_proc[df_p_proc["Debe"] > 0].copy()
  b_cred["Monto"], p_debe["Monto"] = b_cred["Credito"], p_debe["Debe"]
  
  cruce_exacto = pd.merge(b_cred, p_debe, on=["Ref", "Monto"], suffixes=("_B", "_P"))
  
  idx_b_conc = set(cruce_exacto.get("orig_idx_B", []))
  idx_p_conc = set(cruce_exacto.get("orig_idx_P", []))

  # --- DUPLICADOS/ERRORES ---
  df_p_proc["Monto_Total"] = (df_p_proc["Debe"] + df_p_proc["Haber"]).round(2)
  dup = df_p_proc[df_p_proc.duplicated(subset=["Ref", "Monto_Total"], keep=False)].copy()
  dup["Alerta"] = "⚠️ Duplicado"

  # --- PESTAÑAS ---
  t1, t2, t3 = st.tabs(["✅ Conciliados", "💻 Pendientes Profit", "⚠️ Duplicados"])
  with t1: st.dataframe(cruce_exacto, use_container_width=True)
  with t2: st.dataframe(df_p_proc[~df_p_proc["orig_idx"].isin(idx_p_conc)], use_container_width=True)
  with t3: st.dataframe(dup, use_container_width=True)

# --- FOOTER ---
st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria</p></div>', unsafe_allow_html=True)
