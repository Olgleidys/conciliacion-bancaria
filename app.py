import streamlit as st
import pandas as pd

st.set_page_config(page_title="Conciliación", layout="wide")

# CSS para Azul Rey y métricas grandes
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #0056b3; padding: 20px; border-radius: 10px; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: white !important; }
    h1, h2, h3 { color: #0056b3; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sistema de Conciliación Bancaria")

# --- PASO 1: Ingreso de información ---
with st.expander("🏢 Paso 1: Carga de Información (Configuración)", expanded=True):
    c1, c2 = st.columns(2)
    empresa = c1.selectbox("Empresa:", ["Thermo Group", "Mystic", "Keravital"])
    banco = c2.selectbox("Banco:", ["Banesco", "Venezuela", "Banplus"])
    
    col_up1, col_up2 = st.columns(2)
    banco_file = col_up1.file_uploader("Estado de Cuenta (.csv)", type=["csv"])
    profit_file = col_up2.file_uploader("Reporte Profit (.csv)", type=["csv"])

if banco_file and profit_file:
    # Procesamiento robusto
    def leer(f):
        df = pd.read_csv(f, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
        df.columns = [str(c).strip() for c in df.columns]
        while len(df.columns) < 5: df[f'Extra_{len(df.columns)}'] = ""
        # Mapeo posicional para evitar errores de nombres de columna
        df.columns = ['Fecha', 'Ref', 'Desc', 'Monto1', 'Monto2'] + list(df.columns[5:])
        df['Ref'] = df['Ref'].fillna('').astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
        return df

    df_b = leer(banco_file)
    df_p = leer(profit_file)

    # --- Pestaña de Ajustes (Input para persistencia) ---
    tabs = st.tabs(["📋 Resultados", "🛠️ Ajustes y Aclaraciones", "🔒 Cierre"])
    
    with tabs[1]:
        st.write("### 🛠️ Registro de Diferencias Aclaradas")
        refs_manuales = st.text_input("Ingresa referencias aclaradas (ej: 123, 456):", key="ajustes")
        ajustes_lista = [r.strip() for r in refs_manuales.split(",") if r.strip()]

    # Lógica de cálculo (considerando ajustes)
    refs_b = set(df_b['Ref'].unique())
    refs_p = set(df_p['Ref'].unique())
    refs_ajustadas = set(ajustes_lista)
    
    total_refs_p = refs_p.union(refs_ajustadas)
    
    cruces = df_b[df_b['Ref'].isin(total_refs_p)]
    solo_b = df_b[~df_b['Ref'].isin(total_refs_p)]
    solo_p = df_p[~df_p['Ref'].isin(refs_b)]

    # --- MÉTRICAS FIJAS (Se actualizan solas al escribir en ajustes) ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Cruces Exitosos", f"{len(cruces)} mov.")
    m2.metric("Pendientes Banco", f"{len(solo_b)} mov.")
    m3.metric("Pendientes Profit", f"{len(solo_p)} mov.")

    with tabs[0]:
        st.dataframe(cruces, use_container_width=True)
    
    with tabs[2]:
        st.write("### 🔒 Cierre")
        st.write("Total operaciones cuadradas:", len(cruces))
