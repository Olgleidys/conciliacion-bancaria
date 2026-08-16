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
    3. **Procesamiento:** El sistema cruza por referencia exacta, por los últimos 3 dígitos, sumatorias y cruces Debe/Haber.
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
    if serie is None:
        return pd.Series(0.0, index=range(len(serie))) if hasattr(serie, '__len__') else 0.0
    return pd.to_numeric(
        serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), 
        errors="coerce"
    ).fillna(0.0).round(2)

def normalizar_archivo(file, tipo):
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.astype(str).str.strip().str.lower()
    
    col_ref = next((c for c in df.columns if any(k in c for k in ["referencia", "ref", "documento", "doc", "nro"])), None)
    if not col_ref:
        col_ref = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    df = df.rename(columns={col_ref: "Ref"})
    df["Ref"] = df["Ref"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    
    # Blanquear si tiene 2 dígitos o menos (error de dedo)
    df["Ref"] = df["Ref"].apply(lambda x: "" if len(x) <= 2 else x)
    df["Ref_3"] = df["Ref"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    if tipo == "banco":
        c_deb = next((c for c in df.columns if "deb" in c), None)
        c_cred = next((c for c in df.columns if "cred" in c), None)
        
        val_deb = limpiar_monto(df[c_deb]) if c_deb else 0.0
        val_cred = limpiar_monto(df[c_cred]) if c_cred else 0.0
        
        df["Debito_Lim"] = val_deb
        df["Credito_Lim"] = val_cred
        df["Monto_Final"] = val_cred - val_deb 
    else: 
        c_deb = next((c for c in df.columns if "debe" in c), None)
        c_hab = next((c for c in df.columns if "haber" in c), None)
        
        val_debe = limpiar_monto(df[c_deb]) if c_deb else 0.0
        val_hab = limpiar_monto(df[c_hab]) if c_hab else 0.0
        
        df["Debe_Lim"] = val_debe
        df["Haber_Lim"] = val_hab
        df["Monto_Final"] = val_debe - val_hab 

    return df

def cuatro_digitos_consecutivos(m1, m2):
    """Verifica si dos montos comparten al menos 4 números consecutivos exactos."""
    s1 = str(abs(m1)).replace('.', '')
    s2 = str(abs(m2)).replace('.', '')
    if len(s1) < 4 or len(s2) < 4: return False
    for i in range(len(s1) - 3):
        if s1[i:i+4] in s2: return True
    return False

# --- CARGA ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta (Banco)", type=["xlsx", "xls"])
file_p = f_p.file_uploader("📥 Reporte Profit", type=["xlsx", "xls"])

if file_b and file_p:
    df_b = normalizar_archivo(file_b, "banco")
    df_p = normalizar_archivo(file_p, "profit")
    
    df_b["ID_B"] = df_b.index.astype(str) + "_B"
    df_p["ID_P"] = df_p.index.astype(str) + "_P"
    
    b_valid = df_b[df_b["Ref"] != ""].copy()
    p_valid = df_p[df_p["Ref"] != ""].copy()
    
    conciliados = pd.DataFrame()
    
    # 1. CRUCE EXACTO
    cruce_1 = pd.merge(b_valid, p_valid, left_on=["Ref", "Monto_Final"], right_on=["Ref", "Monto_Final"], suffixes=("_Banco", "_Profit"))
    if not cruce_1.empty:
        cruce_1["Tipo_Cruce"] = "Exacto"
        conciliados = pd.concat([conciliados, cruce_1], ignore_index=True)
        b_valid = b_valid[~b_valid["ID_B"].isin(cruce_1["ID_B"])]
        p_valid = p_valid[~p_valid["ID_P"].isin(cruce_1["ID_P"])]

    # 2. CRUCE ÚLTIMOS 3 DÍGITOS
    cruce_2 = pd.merge(b_valid, p_valid, left_on=["Ref_3", "Monto_Final"], right_on=["Ref_3", "Monto_Final"], suffixes=("_Banco", "_Profit"))
    if not cruce_2.empty:
        cruce_2 = cruce_2.drop_duplicates(subset=["ID_B"]).drop_duplicates(subset=["ID_P"])
        cruce_2["Tipo_Cruce"] = "Últimos 3 Dígitos"
        conciliados = pd.concat([conciliados, cruce_2], ignore_index=True)
        b_valid = b_valid[~b_valid["ID_B"].isin(cruce_2["ID_B"])]
        p_valid = p_valid[~p_valid["ID_P"].isin(cruce_2["ID_P"])]

    # 3. CRUCE POR SUMATORIA DE PROFIT
    agrupado_p = p_valid.groupby("Ref_3")["Monto_Final"].sum().reset_index()
    cruce_3_banco = pd.merge(b_valid, agrupado_p, left_on=["Ref_3", "Monto_Final"], right_on=["Ref_3", "Monto_Final"])
    
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
        conciliados = pd.concat([conciliados, df_cruce_3], ignore_index=True)

    # PENDIENTES
    pendientes_b = pd.concat([b_valid, df_b[df_b["Ref"] == ""]], ignore_index=True)
    pendientes_p = pd.concat([p_valid, df_p[df_p["Ref"] == ""]], ignore_index=True)

    # --- CRUCES DEBE / HABER (Específico: Debe en Profit con Débito en Banco o Haber con Crédito) ---
    cruce_dh_merge = pd.merge(df_b[df_b["Ref"] != ""], df_p[df_p["Ref"] != ""], on="Ref", suffixes=("_Banco", "_Profit"))
    if not cruce_dh_merge.empty:
        mask_dh = (
            ((cruce_dh_merge["Debito_Lim"] > 0) & (cruce_dh_merge["Debe_Lim"] > 0) & (cruce_dh_merge["Debito_Lim"] == cruce_dh_merge["Debe_Lim"])) |
            ((cruce_dh_merge["Credito_Lim"] > 0) & (cruce_dh_merge["Haber_Lim"] > 0) & (cruce_dh_merge["Credito_Lim"] == cruce_dh_merge["Haber_Lim"]))
        )
        cruces_debe_haber = cruce_dh_merge[mask_dh].copy()
        cruces_debe_haber["Tipo_Alerta"] = "Cruce Debe/Débito o Haber/Crédito"
    else:
        cruces_debe_haber = pd.DataFrame()

    # --- DUPLICADOS Y ERRORES ---
    alertas = []
    df_b_chk = df_b.copy()
    df_p_chk = df_p.copy()
    df_b_chk["Monto_Abs"] = df_b_chk["Monto_Final"].abs()
    df_p_chk["Monto_Abs"] = df_p_chk["Monto_Final"].abs()

    # 4. Duplicados exactos
    dup_b_exact = df_b_chk[df_b_chk.duplicated(subset=["Ref", "Monto_Abs"], keep=False) & (df_b_chk["Ref"] != "")]
    if not dup_b_exact.empty: alertas.append(dup_b_exact.assign(Alerta="Duplicado Exacto Banco"))
    
    dup_p_exact = df_p_chk[df_p_chk.duplicated(subset=["Ref", "Monto_Abs"], keep=False) & (df_p_chk["Ref"] != "")]
    if not dup_p_exact.empty: alertas.append(dup_p_exact.assign(Alerta="Duplicado Exacto Profit"))

    # 5. Duplicados por últimos 3 dígitos
    dup_b_3 = df_b_chk[df_b_chk.duplicated(subset=["Ref_3", "Monto_Abs"], keep=False) & (df_b_chk["Ref"] != "") & (~df_b_chk.index.isin(dup_b_exact.index))]
    if not dup_b_3.empty: alertas.append(dup_b_3.assign(Alerta="Duplicado 3 Dígitos Banco"))
    
    dup_p_3 = df_p_chk[df_p_chk.duplicated(subset=["Ref_3", "Monto_Abs"], keep=False) & (df_p_chk["Ref"] != "") & (~df_p_chk.index.isin(dup_p_exact.index))]
    if not dup_p_3.empty: alertas.append(dup_p_3.assign(Alerta="Duplicado 3 Dígitos Profit"))

    # 6. Errores de digitación (consecutivos)
    for name, group in df_b_chk[df_b_chk["Ref"] != ""].groupby("Ref"):
        if len(group) > 1:
            for idx1, idx2 in itertools.combinations(group.index, 2):
                if cuatro_digitos_consecutivos(group.loc[idx1, "Monto_Abs"], group.loc[idx2, "Monto_Abs"]):
                    alertas.append(group.loc[[idx1, idx2]].assign(Alerta="Error Digitacion Banco (Consecutivos)"))

    for name, group in df_p_chk[df_p_chk["Ref"] != ""].groupby("Ref"):
        if len(group) > 1:
            for idx1, idx2 in itertools.combinations(group.index, 2):
                if cuatro_digitos_consecutivos(group.loc[idx1, "Monto_Abs"], group.loc[idx2, "Monto_Abs"]):
                    alertas.append(group.loc[[idx1, idx2]].assign(Alerta="Error Digitacion Profit (Consecutivos)"))

    df_alertas = pd.concat(alertas).drop_duplicates() if alertas else pd.DataFrame()

    # --- RENDERIZADO DE PESTAÑAS ---
    tabs = st.tabs(["✅ Todo lo Conciliado", "🏦 Pendiente Banco", "💻 Pendiente Profit", "🔄 Cruces Debe/Haber", "⚠️ Duplicados y Errores"])
    
    with tabs[0]: st.dataframe(conciliados, use_container_width=True)
    with tabs[1]: st.dataframe(pendientes_b, use_container_width=True)
    with tabs[2]: st.dataframe(pendientes_p, use_container_width=True)
    with tabs[3]: 
        if not cruces_debe_haber.empty:
            st.dataframe(cruces_debe_haber, use_container_width=True)
        else:
            st.info("No se encontraron cruces directos entre Debe/Débito o Haber/Crédito con los filtros actuales.")
    with tabs[4]: 
        if not df_alertas.empty:
            def highlight_errors(val):
                return 'background-color: #780000; color: white' if 'Error Digitacion' in str(val) else ''
            
            if hasattr(df_alertas.style, 'map'):
                st.dataframe(df_alertas.style.map(highlight_errors, subset=['Alerta']), use_container_width=True)
            else:
                st.dataframe(df_alertas.style.applymap(highlight_errors, subset=['Alerta']), use_container_width=True)
        else:
            st.success("No se detectaron duplicados ni errores con los filtros actuales.")

    # --- BOTÓN DE DESCARGA EN EXCEL ---
    st.markdown("---")
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
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
