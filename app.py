import io
import pandas as pd
import streamlit as st
import itertools

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
    
    1. **Configuración**: Seleccione la empresa, el banco y el periodo correspondiente (frecuencia, mes y año).
    2. **Carga de Archivos**: Suba el Estado de Cuenta del Banco y el Reporte de Profit Plus en formato Excel.
    3. **Revisión**: El sistema procesará y organizará la información automáticamente. Verifique los resultados en las pestañas dispuestas para ello.
    4. **Descarga**: Haga clic en el botón inferior para descargar el archivo Excel consolidado con todo el reporte listo.
    """)

# --- UI CONFIGURACIÓN ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])
p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028"])

# --- FUNCIONES ---
def limpiar_monto(serie):
    if serie is None or not hasattr(serie, 'astype'):
        return pd.Series(0.0, index=range(len(serie))) if hasattr(serie, '__len__') else 0.0
    return pd.to_numeric(
        serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), 
        errors="coerce"
    ).fillna(0.0).round(2)

def normalizar_archivo(file, tipo):
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.astype(str).str.strip()
    
    # Mapeo insensible a mayúsculas/minúsculas pero exigiendo los nombres exactos requeridos
    cols_lower = {c.lower(): c for c in df.columns}
    
    if tipo == "banco":
        esperadas = ["fecha", "referencia", "descripcion", "debito", "credito"]
    else:
        esperadas = ["fecha", "referencia", "descripcion", "debe", "haber"]
        
    mapeo = {}
    for esp in esperadas:
        match = next((cols_lower[c] for c in cols_lower if c == esp), None)
        if match:
            mapeo[match] = esp
            
    df = df.rename(columns=mapeo)
    
    # Definir columna de referencia estándar para el sistema
    col_ref = "referencia" if "referencia" in df.columns else df.columns[0]
    df = df.rename(columns={col_ref: "Ref"})
    df["Ref"] = df["Ref"].apply(lambda x: str(x).strip().replace(".0", ""))
    df["Ref"] = df["Ref"].apply(lambda x: "" if x.lower() == "nan" else x)
    df["Ref_3"] = df["Ref"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    if tipo == "banco":
        val_deb = limpiar_monto(df["debito"]) if "debito" in df.columns else 0.0
        val_cred = limpiar_monto(df["credito"]) if "credito" in df.columns else 0.0
        df["Monto_Final"] = val_cred - val_deb
    else:
        val_debe = limpiar_monto(df["debe"]) if "debe" in df.columns else 0.0
        val_haber = limpiar_monto(df["haber"]) if "haber" in df.columns else 0.0
        df["Monto_Final"] = val_debe - val_haber
        
    return df

def check_4_digits(m1, m2):
    s1 = f"{abs(float(m1)):.2f}".replace('.', '')
    s2 = f"{abs(float(m2)):.2f}".replace('.', '')
    if len(s1) < 4 or len(s2) < 4: return False
    for i in range(len(s1) - 3):
        if s1[i:i+4] in s2: return True
    return False

# --- PROCESAMIENTO ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta (Banco)", type=["xlsx"])
file_p = f_p.file_uploader("📥 Reporte Profit", type=["xlsx"])

if file_b and file_p:
    df_b = normalizar_archivo(file_b, "banco")
    df_p = normalizar_archivo(file_p, "profit")
    
    pend_b, pend_p = df_b.copy(), df_p.copy()
    conciliados = pd.DataFrame()
    alertas = pd.DataFrame()

    # REGLA 1, 2, 3 (Conciliación)
    m1 = pd.merge(pend_b, pend_p, on=["Ref", "Monto_Final"], suffixes=("_B", "_P"))
    if not m1.empty:
        m1["Regla"] = "1. Exacto"
        conciliados = pd.concat([conciliados, m1])
        pend_b = pend_b[~pend_b.index.isin(m1.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m1.index.get_level_values(0))]

    m2 = pd.merge(pend_b, pend_p, on=["Ref_3", "Monto_Final"], suffixes=("_B", "_P"))
    if not m2.empty:
        m2["Regla"] = "2. Ref 3 Digitos + Monto"
        conciliados = pd.concat([conciliados, m2])
        pend_b = pend_b[~pend_b.index.isin(m2.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m2.index.get_level_values(0))]

    sumatoria = pend_p.groupby("Ref_3")["Monto_Final"].sum().reset_index()
    m3 = pd.merge(pend_b, sumatoria, on=["Ref_3", "Monto_Final"], suffixes=("_B", "_P"))
    if not m3.empty:
        m3["Regla"] = "3. Sumatoria Profit"
        conciliados = pd.concat([conciliados, m3])
        pend_b = pend_b[~pend_b.index.isin(m3.index.get_level_values(0))]

    # CRUCE DEBE/HABER
    cruce_dh = pd.merge(df_b, df_p, on="Ref", suffixes=("_B", "_P"))
    if not cruce_dh.empty:
        cruce_dh = cruce_dh[(cruce_dh["Monto_Final_B"] == cruce_dh["Monto_Final_P"])]
        cruce_dh["Regla"] = "Cruce Debe/Haber"
    else:
        cruce_dh = pd.DataFrame()

    # ALERTAS (4, 5, 6)
    dup_ex = df_b[df_b.duplicated(subset=["Ref", "Monto_Final"], keep=False) & (df_b["Ref"] != "")]
    if not dup_ex.empty:
        dup_ex["Alerta"] = "4. Duplicado Exacto"
        alertas = pd.concat([alertas, dup_ex])

    dup_3 = df_b[df_b.duplicated(subset=["Ref_3", "Monto_Final"], keep=False) & (df_b["Ref"] != "")]
    if not dup_3.empty:
        dup_3["Alerta"] = "5. Duplicado 3 Digitos"
        alertas = pd.concat([alertas, dup_3])

    alertas_lista = []
    for ref, group in df_b[df_b["Ref"] != ""].groupby("Ref"):
        if len(group) > 1:
            for i, row1 in group.iterrows():
                for j, row2 in group.iterrows():
                    if i < j and check_4_digits(row1["Monto_Final"], row2["Monto_Final"]):
                        err = pd.DataFrame([row1, row2])
                        err["Alerta"] = "6. Error 4 Digitos Consecutivos"
                        alertas_lista.append(err)
                        
    if alertas_lista:
        df_errs = pd.concat(alertas_lista)
        alertas = pd.concat([alertas, df_errs])

    # --- PESTAÑAS (5 en total) ---
    tabs = st.tabs(["✅ Conciliado", "🏦 Pendiente Banco", "💻 Pendiente Profit", "🔄 Cruces Debe/Haber", "⚠️ Duplicados y Errores"])
    tabs[0].dataframe(conciliados, use_container_width=True)
    tabs[1].dataframe(pend_b, use_container_width=True)
    tabs[2].dataframe(pend_p, use_container_width=True)
    tabs[3].dataframe(cruce_dh, use_container_width=True)
    tabs[4].dataframe(alertas.drop_duplicates() if not alertas.empty else pd.DataFrame(), use_container_width=True)

    # --- DESCARGA ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not conciliados.empty: conciliados.to_excel(writer, sheet_name="Conciliado", index=False)
        pend_b.to_excel(writer, sheet_name="Pendiente Banco", index=False)
        pend_p.to_excel(writer, sheet_name="Pendiente Profit", index=False)
        if not cruce_dh.empty: cruce_dh.to_excel(writer, sheet_name="Cruces DH", index=False)
        if not alertas.empty: alertas.drop_duplicates().to_excel(writer, sheet_name="Alertas", index=False)
    st.download_button("📥 DESCARGAR REPORTE", output.getvalue(), f"Conciliacion_{empresa}_{mes}_{ano}.xlsx")

# --- FOOTER ---
st.markdown('<br><br><div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)
