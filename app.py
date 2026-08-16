import io
import pandas as pd
import streamlit as st
import itertools

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")
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
with st.expander("📖 Instrucciones de uso"):
    st.markdown("""
    1. **Configuración:** Selecciona la empresa, el banco, la frecuencia, el mes y el año.
    2. **Carga de Archivos:** Sube el estado de cuenta bancario y el reporte de Profit Plus en `.xlsx`.
    3. **Procesamiento:** El sistema cruza por referencia exacta, por los últimos 3 dígitos y por sumatorias agrupadas.
    4. **Resultados:** Navega por las 5 pestañas: Todo lo Conciliado, Pendiente Banco, Pendiente Profit, Cruces Debe/Haber, Duplicados y Errores.
    5. **Exportación:** Al final de la página, usa el botón para descargar toda la conciliación en un solo Excel.
    """)

# --- UI CONFIGURACIÓN ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])
p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028"])

# --- FUNCIONES DE LIMPIEZA Y LÓGICA ---
def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0.0).round(2)

def normalizar(file):
    df = pd.read_excel(file, dtype=str)
    col = next((c for c in df.columns if any(k in c.lower() for k in ["referencia", "ref", "documento", "doc", "nro"])), None)
    if col: df = df.rename(columns={col: "Ref"})
    else: df = df.rename(columns={df.columns[1]: "Ref"}) if len(df.columns) > 1 else df
    
    df["Ref"] = df["Ref"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    # Blanquear si tiene 2 dígitos o menos (error de dedo) para no conciliar ni duplicar
    df["Ref"] = df["Ref"].apply(lambda x: "" if len(x) <= 2 else x)
    df["Ref_3"] = df["Ref"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    return df

def cuatro_digitos_consecutivos(m1, m2):
    """Verifica si dos montos comparten al menos 4 números consecutivos exactos."""
    s1 = str(m1).replace('.', '').replace('-', '')
    s2 = str(m2).replace('.', '').replace('-', '')
    if len(s1) < 4 or len(s2) < 4: return False
    for i in range(len(s1) - 3):
        if s1[i:i+4] in s2: return True
    return False

# --- CARGA ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta (Banco)", type=["xlsx", "xls"])
file_p = f_p.file_uploader("📥 Reporte Profit", type=["xlsx", "xls"])

if file_b and file_p:
    df_b = normalizar(file_b)
    df_p = normalizar(file_p)
    
    deb_b, cred_b = df_b.columns[3], df_b.columns[4]
    deb_p, cred_p = df_p.columns[3], df_p.columns[4]
    
    df_b["Monto_B"] = limpiar_monto(df_b[cred_b]) - limpiar_monto(df_b[deb_b]) # Positivo = Abono, Negativo = Cargo
    df_p["Monto_P"] = limpiar_monto(df_p[deb_p]) - limpiar_monto(df_p[cred_p]) # Positivo = Debe, Negativo = Haber
    
    df_b["ID_B"] = df_b.index.astype(str) + "_B"
    df_p["ID_P"] = df_p.index.astype(str) + "_P"
    
    # Separar datos con referencia válida de los vacíos
    b_valid = df_b[df_b["Ref"] != ""].copy()
    p_valid = df_p[df_p["Ref"] != ""].copy()
    
    conciliados = pd.DataFrame()
    
    # 1. CRUCE EXACTO (Ref y Monto)
    cruce_1 = pd.merge(b_valid, p_valid, left_on=["Ref", "Monto_B"], right_on=["Ref", "Monto_P"], suffixes=("_Banco", "_Profit"))
    if not cruce_1.empty:
        cruce_1["Tipo_Cruce"] = "Exacto"
        conciliados = pd.concat([conciliados, cruce_1])
        b_valid = b_valid[~b_valid["ID_B"].isin(cruce_1["ID_B"])]
        p_valid = p_valid[~p_valid["ID_P"].isin(cruce_1["ID_P"])]

    # 2. CRUCE ÚLTIMOS 3 DÍGITOS (Ref_3 y Monto)
    cruce_2 = pd.merge(b_valid, p_valid, left_on=["Ref_3", "Monto_B"], right_on=["Ref_3", "Monto_P"], suffixes=("_Banco", "_Profit"))
    if not cruce_2.empty:
        cruce_2 = cruce_2.drop_duplicates(subset=["ID_B"]).drop_duplicates(subset=["ID_P"])
        cruce_2["Tipo_Cruce"] = "Últimos 3 Dígitos"
        conciliados = pd.concat([conciliados, cruce_2])
        b_valid = b_valid[~b_valid["ID_B"].isin(cruce_2["ID_B"])]
        p_valid = p_valid[~p_valid["ID_P"].isin(cruce_2["ID_P"])]

    # 3. CRUCE POR SUMATORIA DE PROFIT (Mismos 3 dígitos, suma exacta en Profit)
    agrupado_p = p_valid.groupby("Ref_3")["Monto_P"].sum().reset_index()
    cruce_3_banco = pd.merge(b_valid, agrupado_p, left_on=["Ref_3", "Monto_B"], right_on=["Ref_3", "Monto_P"])
    
    filas_cruce_3 = []
    for _, row in cruce_3_banco.iterrows():
        filas_p = p_valid[p_valid["Ref_3"] == row["Ref_3"]]
        for _, fila_p in filas_p.iterrows():
            combinada = row.to_dict()
            combinada.update({k+"_Profit": v for k, v in fila_p.items()})
            combinada["Tipo_Cruce"] = "Sumatoria 3 Dígitos"
            filas_cruce_3.append(combinada)
            
        b_valid = b_valid[b_valid["ID_B"] != row["ID_B"]]
        p_valid = p_valid[p_valid["Ref_3"] != row["Ref_3"]]
        
    if filas_cruce_3:
        df_cruce_3 = pd.DataFrame(filas_cruce_3)
        conciliados = pd.concat([conciliados, df_cruce_3])

    # PENDIENTES
    pendientes_b = pd.concat([b_valid, df_b[df_b["Ref"] == ""]])
    pendientes_p = pd.concat([p_valid, df_p[df_p["Ref"] == ""]])

    # --- DUPLICADOS Y ERRORES ---
    alertas = []

    # 4. Duplicados exactos (Ref y Monto)
    dup_b_exact = df_b[df_b.duplicated(subset=["Ref", "Monto_B"], keep=False) & (df_b["Ref"] != "")]
    if not dup_b_exact.empty: alertas.append(dup_b_exact.assign(Alerta="Duplicado Exacto Banco"))
    
    dup_p_exact = df_p[df_p.duplicated(subset=["Ref", "Monto_P"], keep=False) & (df_p["Ref"] != "")]
    if not dup_p_exact.empty: alertas.append(dup_p_exact.assign(Alerta="Duplicado Exacto Profit"))

    # 5. Duplicados por últimos 3 dígitos y Monto
    dup_b_3 = df_b[df_b.duplicated(subset=["Ref_3", "Monto_B"], keep=False) & (df_b["Ref"] != "") & (~df_b.index.isin(dup_b_exact.index))]
    if not dup_b_3.empty: alertas.append(dup_b_3.assign(Alerta="Duplicado 3 Dígitos Banco"))
    
    dup_p_3 = df_p[df_p.duplicated(subset=["Ref_3", "Monto_P"], keep=False) & (df_p["Ref"] != "") & (~df_p.index.isin(dup_p_exact.index))]
    if not dup_p_3.empty: alertas.append(dup_p_3.assign(Alerta="Duplicado 3 Dígitos Profit"))

    # 6. Misma referencia, distinto monto, pero con 4 números consecutivos iguales
    for name, group in df_b[df_b["Ref"] != ""].groupby("Ref"):
        if len(group) > 1:
            for idx1, idx2 in itertools.combinations(group.index, 2):
                if cuatro_digitos_consecutivos(group.loc[idx1, "Monto_B"], group.loc[idx2, "Monto_B"]):
                    alertas.append(group.loc[[idx1, idx2]].assign(Alerta="Error Digitacion Banco (Consecutivos)"))

    for name, group in df_p[df_p["Ref"] != ""].groupby("Ref"):
        if len(group) > 1:
            for idx1, idx2 in itertools.combinations(group.index, 2):
                if cuatro_digitos_consecutivos(group.loc[idx1, "Monto_P"], group.loc[idx2, "Monto_P"]):
                    alertas.append(group.loc[[idx1, idx2]].assign(Alerta="Error Digitacion Profit (Consecutivos)"))

    df_alertas = pd.concat(alertas).drop_duplicates(subset=["ID_B" if "ID_B" in df_alertas.columns else "ID_P", "Alerta"]) if alertas else pd.DataFrame()

    # Formatear Pestaña Debe/Haber
    cruces_debe_haber = conciliados[["Ref", "Ref_3", "Monto_B", "Monto_P", "Tipo_Cruce"]].copy() if not conciliados.empty else pd.DataFrame()

    # --- RENDERIZADO DE PESTAÑAS ---
    tabs = st.tabs(["✅ Todo lo Conciliado", "🏦 Pendiente Banco", "💻 Pendiente Profit", "🔄 Cruces Debe/Haber", "⚠️ Duplicados y Errores"])
    
    with tabs[0]: st.dataframe(conciliados, use_container_width=True)
    with tabs[1]: st.dataframe(pendientes_b, use_container_width=True)
    with tabs[2]: st.dataframe(pendientes_p, use_container_width=True)
    with tabs[3]: st.dataframe(cruces_debe_haber, use_container_width=True)
    with tabs[4]: 
        if not df_alertas.empty:
            # Resaltar en rojo los errores de digitación
            def highlight_errors(val):
                return 'background-color: #780000; color: white' if 'Error Digitacion' in str(val) else ''
            st.dataframe(df_alertas.style.applymap(highlight_errors, subset=['Alerta']), use_container_width=True)
        else:
            st.success("No se detectaron duplicados ni errores de digitación.")

    # --- BOTÓN DE DESCARGA EN EXCEL ---
    st.markdown("---")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if not conciliados.empty: conciliados.to_excel(writer, sheet_name="Conciliado", index=False)
        pendientes_b.to_excel(writer, sheet_name="Pendiente Banco", index=False)
        pendientes_p.to_excel(writer, sheet_name="Pendiente Profit", index=False)
        if not cruces_debe_haber.empty: cruces_debe_haber.to_excel(writer, sheet_name="Cruces Debe Haber", index=False)
        if not df_alertas.empty: df_alertas.to_excel(writer, sheet_name="Duplicados y Errores", index=False)
    
    excel_data = output.getvalue()
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.download_button(
            label="📥 DESCARGAR CONCILIACIÓN COMPLETA EN EXCEL",
            data=excel_data,
            file_name=f"Conciliacion_{empresa}_{banco}_{mes}_{ano}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- FOOTER ---
st.markdown('<br><br>', unsafe_allow_html=True)
st.markdown(
    '<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — '
    'Creado por Lic. Olgleidys Hernández ✨</p></div>',
    unsafe_allow_html=True,
)
