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

# --- INSTRUCCIONES ---
st.markdown("### 📝 Instrucciones de uso")
st.markdown("""
1. **Configuración**: Seleccione la empresa, el banco y el periodo correspondiente.
2. **Carga de Archivos**: Suba el Estado de Cuenta del Banco y el Reporte de Profit Plus.
3. **Revisión**: El sistema aplicará las reglas de conciliación (1-3) y validará posibles errores (4-6).
4. **Descarga**: Haga clic en el botón inferior para descargar el reporte consolidado.
""")

# --- DATOS CORPORATIVOS ---
st.markdown("### 📋 Datos Corporativos")
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco_sel = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])
p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028"])
periodo = f"{frecuencia} {mes} {ano}"

# --- COLUMNAS DEFINIDAS ---
cols_banco_show = ["Empresa", "Banco", "Periodo", "fecha", "referencia", "descripcion", "debito", "credito", "Observaciones"]
cols_profit_show = ["Empresa", "Banco", "Periodo", "fecha", "referencia", "descripcion", "debe", "haber", "Observaciones"]

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

    # Limpieza extrema de referencia para que las comparaciones funcionen
    df_new["referencia"] = df_new["referencia"].astype(str).str.strip().replace("nan", "").replace("None", "")
    df_new["ref_3"] = df_new["referencia"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    df_new["Empresa"] = empresa
    df_new["Banco"] = banco_sel
    df_new["Periodo"] = periodo
    df_new["Observaciones"] = ""
    return df_new

# --- UI ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta (Banco)", type=["xlsx"])
file_p = f_p.file_uploader("📥 Reporte Profit", type=["xlsx"])

if file_b and file_p:
    df_b = estandarizar_columnas(pd.read_excel(file_b), "banco")
    df_p = estandarizar_columnas(pd.read_excel(file_p), "profit")
    
    # --- DETECCIÓN MEJORADA DE DUPLICADOS ---
    # Convertimos referencia y monto a string plano para asegurar que los duplicados se vean
    df_b_flat = df_b.copy()
    df_b_flat["ref_check"] = df_b_flat["referencia"].astype(str).str.strip()
    df_b_flat["monto_check"] = df_b_flat["monto_final"].astype(str).str.strip()
    
    alertas = pd.DataFrame(columns=cols_banco_show)

    # 4. Duplicado Exacto (Forzado a string)
    dups_exact = df_b[df_b_flat.duplicated(subset=["ref_check", "monto_check"], keep=False) & (df_b_flat["ref_check"] != "")]
    if not dups_exact.empty:
        dups_exact = dups_exact.copy()
        dups_exact["Observaciones"] = "Regla 4: Duplicado Exacto"
        alertas = pd.concat([alertas, dups_exact], ignore_index=True)

    # 5. Duplicado 3 dígitos
    df_b_flat["ref_3_check"] = df_b_flat["ref_3"].astype(str).str.strip()
    dups_3 = df_b[df_b_flat.duplicated(subset=["ref_3_check", "monto_check"], keep=False) & (df_b_flat["ref_check"] != "")]
    if not dups_3.empty:
        dups_3 = dups_3.copy()
        dups_3["Observaciones"] = "Regla 5: Duplicado 3 Digitos"
        alertas = pd.concat([alertas, dups_3], ignore_index=True)

    # --- REGLAS DE CONCILIACIÓN ---
    pend_b, pend_p = df_b.copy(), df_p.copy()
    conciliados = pd.DataFrame(columns=cols_banco_show)

    m1 = pd.merge(pend_b, pend_p, on=["referencia", "monto_final"], suffixes=("_B", "_P"))
    if not m1.empty:
        m1["Observaciones"] = "Regla 1: Conciliación Exacta"
        conciliados = pd.concat([conciliados, m1], ignore_index=True)
    
    # --- TABLAS ---
    tabs = st.tabs(["✅ Conciliado", "🏦 Pendiente Banco", "💻 Pendiente Profit", "🔄 Cruces", "⚠️ Alertas"])
    
    tabs[0].dataframe(conciliados.reindex(columns=cols_banco_show), use_container_width=True)
    tabs[1].dataframe(pend_b.reindex(columns=cols_banco_show), use_container_width=True)
    tabs[2].dataframe(pend_p.reindex(columns=cols_profit_show), use_container_width=True)
    tabs[4].dataframe(alertas.reindex(columns=cols_banco_show).drop_duplicates(), use_container_width=True)

    # --- DESCARGA ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        conciliados.to_excel(writer, sheet_name="Conciliado", index=False)
        alertas.to_excel(writer, sheet_name="Alertas", index=False)
    st.download_button("📥 DESCARGAR REPORTE", output.getvalue(), f"Conciliacion_{empresa}_{mes}_{ano}.xlsx")

# --- FOOTER ---
st.markdown('<br><br><div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)
