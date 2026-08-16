import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Sistema de Conciliación Bancaria", layout="wide")
custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; font-weight: bold; width: 100%; padding: 10px; border-radius: 8px;}
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; z-index: 100; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- INSTRUCCIONES DE USO ---
with st.expander("📝 Instrucciones de uso"):
    st.markdown("""
    Siga estos sencillos pasos para realizar su conciliación:
    
    1. **Configuración**: Seleccione la empresa, el banco y el periodo correspondiente.
    2. **Carga de Archivos**: Suba el Estado de Cuenta del Banco y el Reporte de Profit Plus.
    3. **Revisión**: El sistema aplicará las reglas de conciliación (1-3) y validará posibles errores (4-6).
    4. **Descarga**: Haga clic en el botón inferior para descargar el reporte consolidado.
    """)

# --- FUNCIONES ---
def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0.0).round(2)

def estandarizar_columnas(df, tipo):
    # Estandarizar nombres a minúsculas para mapeo
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Mapeo a los nombres exactos que requiere el sistema
    if tipo == "banco":
        # Aseguramos nombres exactos internos
        # Si la columna existe en el archivo, se usa.
        df["debito"] = limpiar_monto(df.get("debito", 0))
        df["credito"] = limpiar_monto(df.get("credito", 0))
        df["monto_final"] = df["credito"] - df["debito"]
    else:
        df["debe"] = limpiar_monto(df.get("debe", 0))
        df["haber"] = limpiar_monto(df.get("haber", 0))
        df["monto_final"] = df["debe"] - df["haber"]

    # Normalizar Referencia
    df["referencia"] = df["referencia"].astype(str).str.strip().replace("nan", "")
    df["ref_3"] = df["referencia"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    return df

def check_4_digits(m1, m2):
    s1 = f"{abs(float(m1)):.2f}".replace('.', '')
    s2 = f"{abs(float(m2)):.2f}".replace('.', '')
    if len(s1) < 4 or len(s2) < 4: return False
    for i in range(len(s1) - 3):
        if s1[i:i+4] in s2: return True
    return False

# --- UI ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta (Banco)", type=["xlsx"])
file_p = f_p.file_uploader("📥 Reporte Profit", type=["xlsx"])

if file_b and file_p:
    df_b = estandarizar_columnas(pd.read_excel(file_b), "banco")
    df_p = estandarizar_columnas(pd.read_excel(file_p), "profit")
    
    pend_b, pend_p = df_b.copy(), df_p.copy()
    conciliados = pd.DataFrame()
    alertas = pd.DataFrame()

    # --- PUNTOS 1 AL 3: CONCILIACIÓN ---
    m1 = pd.merge(pend_b, pend_p, on=["referencia", "monto_final"], suffixes=("_B", "_P"))
    if not m1.empty:
        m1["regla"] = "1. Exacto"
        conciliados = pd.concat([conciliados, m1])
        pend_b = pend_b[~pend_b.index.isin(m1.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m1.index.get_level_values(0))]

    m2 = pd.merge(pend_b, pend_p, on=["ref_3", "monto_final"], suffixes=("_B", "_P"))
    if not m2.empty:
        m2["regla"] = "2. Ref 3 Digitos + Monto"
        conciliados = pd.concat([conciliados, m2])
        pend_b = pend_b[~pend_b.index.isin(m2.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m2.index.get_level_values(0))]

    df_p_sum = pend_p.groupby(["ref_3", "monto_final"])["monto_final"].sum().reset_index(name="suma_profit")
    m3 = pd.merge(pend_b, df_p_sum, on=["ref_3", "monto_final"])
    if not m3.empty:
        m3["regla"] = "3. Sumatoria Profit"
        conciliados = pd.concat([conciliados, m3])

    # --- CRUCES (Exclusivo: Debe Banco vs Haber Profit) ---
    cruce_dh = pd.merge(df_b[df_b["debito"] != 0], df_p[df_p["haber"] != 0], on="referencia")
    cruce_dh = cruce_dh[cruce_dh["debito"] == cruce_dh["haber"]]
    cruce_dh["regla"] = "Cruce Debe Banco vs Haber Profit"

    # --- PUNTOS 4 AL 6: DETECCIÓN DE DUPLICADOS ---
    # 4. Duplicado Exacto
    dup_4 = df_b[df_b.duplicated(subset=["referencia", "monto_final"], keep=False) & (df_b["referencia"] != "")]
    if not dup_4.empty:
        dup_4["alerta"] = "4. Duplicado Exacto"
        alertas = pd.concat([alertas, dup_4])
    
    # 5. Duplicado 3 dígitos
    dup_5 = df_b[df_b.duplicated(subset=["ref_3", "monto_final"], keep=False) & (df_b["referencia"] != "")]
    if not dup_5.empty:
        dup_5["alerta"] = "5. Duplicado 3 Digitos"
        alertas = pd.concat([alertas, dup_5])
    
    # 6. Error 4 dígitos
    for ref, group in df_b[df_b["referencia"] != ""].groupby("referencia"):
        if len(group) > 1:
            for i, row1 in group.iterrows():
                for j, row2 in group.iterrows():
                    if i < j and check_4_digits(row1["monto_final"], row2["monto_final"]):
                        err = pd.DataFrame([row1, row2])
                        err["alerta"] = "6. Error 4 Digitos Consecutivos"
                        alertas = pd.concat([alertas, err])

    # --- PESTAÑAS ---
    tabs = st.tabs(["✅ Conciliado", "🏦 Pendiente Banco", "💻 Pendiente Profit", "🔄 Cruces (Debe/Haber)", "⚠️ Alertas (Duplicados)"])
    tabs[0].dataframe(conciliados, use_container_width=True)
    tabs[1].dataframe(pend_b, use_container_width=True)
    tabs[2].dataframe(pend_p, use_container_width=True)
    tabs[3].dataframe(cruce_dh, use_container_width=True)
    tabs[4].dataframe(alertas.drop_duplicates(), use_container_width=True)

# --- FOOTER ---
st.markdown('<br><br><div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)
