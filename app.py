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
    
    def limpiar_referencia(val):
        val = str(val).strip()
        if not val or val.lower() == "nan":
            return ""
        if 'e' in val.lower() or '.' in val:
            try:
                val = str(int(float(val)))
            except ValueError:
                pass
        return val.replace(".0", "").strip()

    df["Ref"] = df["Ref"].apply(limpiar_referencia)
    
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

def tres_digitos_consecutivos(m1, m2):
    """Verifica si dos montos comparten al menos 3 números consecutivos exactos."""
    s1 = str(abs(m1)).replace('.', '')
    s2 = str(abs(m2)).replace('.', '')
    if len(s1) < 3 or len(s2) < 3: return False
    for i in range(len(s1) - 2):
        if s1[i:i+3] in s2: return True
    return False

# --- CARGA DE ARCHIVOS ---
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
    
    # -------------------------------------------------------------
    # REGLA 1: Conciliar todo lo que cruza correctamente (Exacto)
    # -------------------------------------------------------------
    cruce_1 = pd.merge(b_valid, p_valid, left_on=["Ref", "Monto_Final"], right_on=["Ref", "Monto_Final"], suffixes=("_Banco", "_Profit"))
    if not cruce_1.empty:
        cruce_1["Tipo_Cruce"] = "1. Exacto (Ref y Monto)"
        conciliados = pd.concat([conciliados, cruce_1], ignore_index=True)
        b_valid = b_valid[~b_valid["ID_B"].isin(cruce_1["ID_B"])]
        p_valid = p_valid[~p_valid["ID_P"].isin(cruce_1["ID_P"])]

    # -------------------------------------------------------------
    # REGLA 2: Conciliar últimos 3 dígitos de referencia y monto iguales
    # -------------------------------------------------------------
    cruce_2 = pd.merge(b_valid, p_valid, left_on=["Ref_3", "Monto_Final"], right_on=["Ref_3", "Monto_Final"], suffixes=("_Banco", "_Profit"))
    if not cruce_2.empty:
        cruce_2 = cruce_2.drop_duplicates(subset=["ID_B"]).drop_duplicates(subset=["ID_P"])
        cruce_2["Tipo_Cruce"] = "2. Últimos 3 Dígitos y Monto"
        conciliados = pd.concat([conciliados, cruce_2], ignore_index=True)
        b_valid = b_valid[~b_valid["ID_B"].isin(cruce_2["ID_B"])]
        p_valid = p_valid[~p_valid["ID_P"].isin(cruce_2["ID_P"])]

    # -------------------------------------------------------------
    # REGLA 3: Sumatoria de Profit con mismos últimos 3 dígitos igual a Banco
    # -------------------------------------------------------------
    agrupado_p = p_valid.groupby("Ref_3")["Monto_Final"].sum().reset_index()
    cruce_3_banco = pd.merge(b_valid, agrupado_p, left_on=["Ref_3", "Monto_Final"], right_on=["Ref_3", "Monto_Final"])
    
    filas_cruce_3 = []
    ids_p_a_remover = []
    for _, row in cruce_3_banco.iterrows():
        filas_p = p_valid[p_valid["Ref_3"] == row["Ref_3"]]
        for _, fila_p in filas_p.iterrows():
            combinada = row.to_dict()
            combinada.update({k+"_Profit": v for k, v in fila_p.items()})
            combinada["Tipo_Cruce"] = "3. Sumatoria Profit (3 Dígitos)"
            filas_cruce_3.append(combinada)
            ids_p_a_remover.append(fila_p["ID_P"])
            
        b_valid = b_valid[b_valid["ID_B"] != row["ID_B"]]
        
    if filas_cruce_3:
        df_cruce_3 = pd.DataFrame(filas_cruce_3).drop_duplicates(subset=["ID_B"])
        conciliados = pd.concat([conciliados, df_cruce_3], ignore_index=True)
        p_valid = p_valid[~p_valid["ID_P"].isin(ids_p_a_remover)]

    # PENDIENTES
    pendientes_b = pd.concat([b_valid, df_b[df_b["Ref"] == ""]], ignore_index=True)
    pendientes_p = pd.concat([p_valid, df_p[df_p["Ref"] == ""]], ignore_index=True)

    # --- CRUCES DEBE / HABER ---
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

    # -------------------------------------------------------------
    # REGLAS 4, 5 y 6: DUPLICADOS Y ERRORES
    # -------------------------------------------------------------
    alertas = []
    
    df_b_chk = df_b.copy()
    df_p_chk = df_p.copy()
    df_b_chk["Monto_Abs"] = df_b_chk["Monto_Final"].abs()
    df_p_chk["Monto_Abs"] = df_p_chk["Monto_Final"].abs()

    # REGLA 4: Duplicados exactos (Mismo número de referencia y monto)
    dup_b_ex = df_b_chk[df_b_chk.duplicated(subset=["Ref", "Monto_Abs"], keep=False) & (df_b_chk["Ref"] != "")]
    if not dup_b_ex.empty: alertas.append(dup_b_ex.assign(Alerta="4. Duplicado Exacto (Banco)"))
    
    dup_p_ex = df_p_chk[df_p_chk.duplicated(subset=["Ref", "Monto_Abs"], keep=False) & (df_p_chk["Ref"] != "")]
    if not dup_p_ex.empty: alertas.append(dup_p_ex.assign(Alerta="4. Duplicado Exacto (Profit)"))

    # REGLA 5: Duplicados con mismos últimos 3 dígitos de referencia y monto iguales
    dup_b_3 = df_b_chk[df_b_chk.duplicated(subset=["Ref_3", "Monto_Abs"], keep=False) & (df_b_chk["Ref"] != "") & (~df_b_chk.index.isin(dup_b_ex.index))]
    if not dup_b_3.empty: alertas.append(dup_b_3.assign(Alerta="5. Duplicado por Últimos 3 Dígitos (Banco)"))
    
    dup_p_3 = df_p_chk[df_p_chk.duplicated(subset=["Ref_3", "Monto_Abs"], keep=False) & (df_p_chk["Ref"] != "") & (~df_p_chk.index.isin(dup_p_ex.index))]
    if not dup_p_3.empty: alertas.append(dup_p_3.assign(Alerta="5. Duplicado por Últimos 3 Dígitos (Profit)"))

    # REGLA 6: Misma referencia, montos diferentes pero con al menos 3 números consecutivos iguales (Marcado en Rojo)
    for name, group in df_b_chk[df_b_chk["Ref"] != ""].groupby("Ref"):
        if len(group) > 1:
            for idx1, idx2 in itertools.combinations(group.index, 2):
                m1, m2 = group.loc[idx1, "Monto_Abs"], group.loc[idx2, "Monto_Abs"]
                if m1 != m2 and tres_digitos_consecutivos(m1, m2):
                    alertas.append(group.loc[[idx1, idx2]].assign(Alerta="6. Error Digitación (Misma Ref, 3 Dígitos Consecutivos)"))

    for name, group in df_p_chk[df_p_chk["Ref"] != ""].groupby("Ref"):
        if len(group) > 1:
            for idx1, idx2 in itertools.combinations(group.index, 2):
                m1, m2 = group.loc[idx1, "Monto_Abs"], group.loc[idx2, "Monto_Abs"]
                if m1 != m2 and tres_digitos_consecutivos(m1, m2):
                    alertas.append(group.loc[[idx1, idx2]].assign(Alerta="6. Error Digitación (Misma Ref, 3 Dígitos Consecutivos)"))

    df_alertas = pd.concat(alertas).drop_duplicates() if alertas else pd.DataFrame()

    # --- RENDERIZADO DE PESTAÑAS ---
    tabs = st.tabs(["✅ Todo lo Conciliado", "🏦 Pendiente Banco", "💻 Pendiente Profit", "🔄 Cruces Debe/Haber", "⚠️ Duplicados y Errores"])
    
    with tabs[0]: st.dataframe(conciliados, use_container_width=True)
    with tabs[1]: st.dataframe(pendientes_b, use_container_width=True)
    with tabs[2]: st.dataframe(pendientes_p, use_container_width=True)
    with tabs[3]: 
        if not cruces_debe_haber.empty: st.dataframe(cruces_debe_haber, use_container_width=True)
        else: st.info("No se encontraron cruces directos Debe/Haber.")
    with tabs[4]: 
        if not df_alertas.empty:
            def highlight_rule6(val):
                return 'background-color: #780000; color: white' if '6.' in str(val) else 'background-color: #b7094c; color: white'
            
            if hasattr(df_alertas.style, 'map'):
                st.dataframe(df_alertas.style.map(highlight_rule6, subset=['Alerta']), use_container_width=True)
            else:
                st.dataframe(df_alertas.style.applymap(highlight_rule6, subset=['Alerta']), use_container_width=True)
        else:
            st.success("No se detectaron duplicados ni errores de digitación con los filtros actuales.")

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
