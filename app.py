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

# --- UI DE CONFIGURACIÓN Y CARGA ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Seleccione el banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])

b1, b2 = st.columns(2)
banco_file = b1.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0).abs()

if banco_file and profit_file:
    df_b = pd.read_csv(banco_file, sep=None, engine="python", encoding="latin-1")
    df_p = pd.read_csv(profit_file, sep=None, engine="python", encoding="latin-1")

    # --- VALIDACIÓN DE COLUMNA "Referencia" ---
    if "Referencia" not in df_b.columns or "Referencia" not in df_p.columns:
        st.error("Error: Ambos archivos deben contener una columna llamada exactamente 'Referencia'.")
        st.stop()

    df_b_proc = df_b.copy()
    df_p_proc = df_p.copy()

    # Procesamiento Banco
    df_b_proc["Debito"] = limpiar_monto(df_b_proc.iloc[:, 3] if df_b_proc.shape[1] > 3 else 0)
    df_b_proc["Credito"] = limpiar_monto(df_b_proc.iloc[:, 4] if df_b_proc.shape[1] > 4 else 0)
    df_b_proc["Ref"] = df_b_proc["Referencia"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df_b_proc["Ref3"] = df_b_proc["Ref"].str[-3:]
    df_b_proc["orig_idx"] = df_b_proc.index

    # Procesamiento Profit
    df_p_proc["Debe"] = limpiar_monto(df_p_proc.iloc[:, 3] if df_p_proc.shape[1] > 3 else 0)
    df_p_proc["Haber"] = limpiar_monto(df_p_proc.iloc[:, 4] if df_p_proc.shape[1] > 4 else 0)
    df_p_proc["Ref"] = df_p_proc["Referencia"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df_p_proc["Ref3"] = df_p_proc["Ref"].str[-3:]
    df_p_proc["orig_idx"] = df_p_proc.index

    # --- CRUCES (Ahora usamos 'Ref' que viene de 'Referencia') ---
    b_cred = df_b_proc[df_b_proc["Credito"] > 0].copy()
    b_cred["Monto"] = b_cred["Credito"]
    p_debe = df_p_proc[df_p_proc["Debe"] > 0].copy()
    p_debe["Monto"] = p_debe["Debe"]

    cruce_ing_1 = pd.merge(b_cred, p_debe, on=["Ref", "Monto"], suffixes=("_B", "_P"))
    
    # ... (El resto de la lógica de cruces y visualización permanece igual)
    
    st.success("Archivos procesados correctamente usando la columna 'Referencia'.")
    # (Aquí iría el resto de tu lógica de visualización de pestañas...)

else:
    st.info("Cargue ambos archivos para proceder.")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)
