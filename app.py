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

# --- INSTRUCCIONES (VISIBLES) ---
st.markdown("### 📝 Instrucciones de uso")
st.markdown("""
1. **Configuración**: Seleccione la empresa, el banco y el periodo correspondiente.
2. **Carga de Archivos**: Suba el Estado de Cuenta del Banco y el Reporte de Profit Plus.
3. **Revisión**: El sistema aplicará las reglas de conciliación (1-3) y validará posibles errores (4-6).
4. **Descarga**: Haga clic en el botón inferior para descargar el reporte consolidado.
""")

# --- DATOS CORPORATIVOS (VISIBLES) ---
st.markdown("### 📋 Datos Corporativos")
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco_sel = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])
p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028"])
periodo = f"{frecuencia} {mes} {ano}"

# --- FUNCIONES ---
def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0.0).round(2)

def estandarizar_columnas(df, tipo):
    df.columns = [c.lower().strip() for c in df.columns]
    df_new = pd.DataFrame()
    
    if tipo == "banco":
        cols_needed = ["fecha", "referencia", "descripcion", "debito", "credito"]
        for col in cols_needed:
            match = next((c for c in df.columns if col in c), None)
            df_new[col] = df[match] if match else 0.0
        df_new["debito"] = limpiar_monto(df_new["debito"])
        df_new["credito"] = limpiar_monto(df_new["credito"])
        df_new["monto_final"] = df_new["credito"] - df_new["debito"]
    else: # profit
        cols_needed = ["fecha", "referencia", "descripcion", "debe", "haber"]
        for col in cols_needed:
            match = next((c for c in df.columns if col in c), None)
            df_new[col] = df[match] if match else 0.0
        df_new["debe"] = limpiar_monto(df_new["debe"])
        df_new["haber"] = limpiar_monto(df_new["haber"])
        df_new["monto_final"] = df_new["debe"] - df_new["haber"]

    df_new["referencia"] = df_new["referencia"].astype(str).str.strip().replace("nan", "")
    df_new["ref_3"] = df_new["referencia"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    df_new["Empresa"] = empresa
    df_new["Banco"] = banco_sel
    df_new["Periodo"] = periodo
    df_new["Observaciones"] = ""
    return df_new

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

    # --- REGLAS ---
    m1 = pd.merge(pend_b, pend_p, on=["referencia", "monto_final"], suffixes=("_B", "_P"))
    if not m1.empty:
        m1["Observaciones"] = "Regla 1: Conciliación Exacta"
        conciliados = pd.concat([conciliados, m1])
        pend_b = pend_b[~pend_b.index.isin(m1.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m1.index.get_level_values(0))]

    m2 = pd.merge(pend_b, pend_p, on=["ref_3", "monto_final"], suffixes=("_B", "_P"))
    if not m2.empty:
        m2["Observaciones"] = "Regla 2: Ref 3 Digitos + Monto"
        conciliados = pd.concat([conciliados, m2])
        pend_b = pend_b[~pend_b.index.isin(m2.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m2.index.get_level_values(0))]

    # Sumatorias
    df_p_sum = pend_p.groupby(["ref_3", "monto_final"])["monto_final"].sum().reset_index(name="suma_profit")
    m3 = pd.merge(pend_b, df_p_sum, on=["ref_3", "monto_final"])
    if not m3.empty:
        m3["Observaciones"] = "Regla 3: Sumatoria Profit"
        conciliados = pd.concat([conciliados, m3])

    cruce_dh = pd.merge(df_b[df_b["debito"] != 0], df_p[df_p["haber"] != 0], on="referencia")
    cruce_dh = cruce_dh[cruce_dh["debito"] == cruce_dh["haber"]]
    cruce_dh["Observaciones"] = "Cruce: Debe Banco vs Haber Profit"

    dup_4 = df_b[df_b.duplicated(subset=["referencia", "monto_final"], keep=False) & (df_b["referencia"] != "")]
    if not dup_4.empty:
        dup_4["Observaciones"] = "Regla 4: Duplicado Exacto"
        alertas = pd.concat([alertas, dup_4])
    
    dup_5 = df_b[df_b.duplicated(subset=["ref_3", "monto_final"], keep=False) & (df_b["referencia"] != "")]
    if not dup_5.empty:
        dup_5["Observaciones"] = "Regla 5: Duplicado 3 Digitos"
        alertas = pd.concat([alertas, dup_5])

    # --- SELECCIÓN DE COLUMNAS (Corregido para no buscar 'regla') ---
    cols_banco_show = ["Empresa", "Banco", "Periodo", "fecha", "referencia", "descripcion", "debito", "credito", "Observaciones"]
    cols_profit_show = ["Empresa", "Banco", "Periodo", "fecha", "referencia", "descripcion", "debe", "haber", "Observaciones"]

    # --- TABLAS ---
    tabs = st.tabs(["✅ Conciliado", "🏦 Pendiente Banco", "💻 Pendiente Profit", "🔄 Cruces", "⚠️ Alertas"])
    
    # Conciliado tiene columnas mezcladas por el merge, visualizamos sin filtro de columnas estrictas para evitar KeyErrors
    tabs[0].dataframe(conciliados, use_container_width=True)
    tabs[1].dataframe(pend_b[cols_banco_show], use_container_width=True)
    tabs[2].dataframe(pend_p[cols_profit_show], use_container_width=True)
    tabs[3].dataframe(cruce_dh, use_container_width=True)
    tabs[4].dataframe(alertas[cols_banco_show].drop_duplicates(), use_container_width=True)

    # --- DESCARGA ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        conciliados.to_excel(writer, sheet_name="Conciliado", index=False)
        pend_b.to_excel(writer, sheet_name="Pendiente Banco", index=False)
        pend_p.to_excel(writer, sheet_name="Pendiente Profit", index=False)
        cruce_dh.to_excel(writer, sheet_name="Cruces DH", index=False)
        alertas.to_excel(writer, sheet_name="Alertas", index=False)
    st.download_button("📥 DESCARGAR REPORTE", output.getvalue(), f"Conciliacion_{empresa}_{mes}_{ano}.xlsx")

# --- FOOTER ---
st.markdown('<br><br><div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)
