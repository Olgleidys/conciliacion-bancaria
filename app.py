import streamlit as st
import pandas as pd
import numpy as np
import re
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Sistema de Conciliación — Lic. Olgleidys")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    .footer { text-align: center; color: #bcbed8; padding: 20px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
""", unsafe_allow_html=True)

# --- TÍTULO E INSTRUCCIONES ---
st.title("📊 Sistema Automatizado de Conciliación Bancaria")
with st.expander("📖 Instrucciones de uso"):
    st.markdown("""
    1. Seleccione empresa, banco, frecuencia, mes y año.
    2. Cargue los archivos CSV del Banco y de Profit Plus. 
    3. La app ejecutará los cruces automáticos (Completos, 3 dígitos, Sumatorias) y la auditoría de duplicados y alertas rojas.
    4. Descargue el reporte completo en Excel con todas las pestañas organizadas. 
    """)

# --- CONFIGURACIÓN DE PARÁMETROS ---
col1, col2 = st.columns(2)
empresa = col1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = col2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])

c3, c4, c5 = st.columns(3)
frecuencia = c3.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = c4.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = c5.selectbox("📅 Año:", list(range(2026, 2030)))

st.divider()

# --- FUNCIONES DE APOYO ---
def limpiar_monto(val):
    if pd.isna(val) or val == "": return 0.0
    val_str = str(val).strip()
    val_str = re.sub(r'[^0-9,.-]', '', val_str)
    if ',' in val_str and '.' in val_str:
        if val_str.rfind(',') > val_str.rfind('.'):
            val_str = val_str.replace('.', '').replace(',', '.')
        else:
            val_str = val_str.replace(',', '')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except: return 0.0

def encontrar_columna(df, posibles):
    for col in df.columns:
        col_limpia = str(col).strip().lower()
        for p in posibles:
            if p in col_limpia:
                return col
    return None

def detectar_coincidencia_3_consecutivos(m1, m2):
    s1, s2 = str(abs(int(round(float(m1), 2)))), str(abs(int(round(float(m2), 2))))
    for i in range(len(s1) - 2):
        substring = s1[i:i+3]
        if substring in s2:
            return True
    return False

# --- CARGA DE ARCHIVOS ---
b1, b2 = st.columns(2)
file_banco = b1.file_uploader("📥 Estado de Cuenta Bancario (.csv)", type="csv")
file_profit = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type="csv")

if file_banco and file_profit:
    try:
        df_b = pd.read_csv(file_banco, encoding='latin-1', sep=None, engine='python')
        df_p = pd.read_csv(file_profit, encoding='latin-1', sep=None, engine='python')
        
        df_b.columns = df_b.columns.str.strip()
        df_p.columns = df_p.columns.str.strip()
        
        col_ref_b = encontrar_columna(df_b, ['referencia', 'ref', 'nro'])
        col_ref_p = encontrar_columna(df_p, ['referencia', 'ref', 'nro'])
        col_monto_b = encontrar_columna(df_b, ['credito', 'haber', 'monto', 'debito', 'debe'])
        col_monto_p = encontrar_columna(df_p, ['haber', 'credito', 'monto', 'debe', 'debito'])

        if not col_ref_b or not col_ref_p or not col_monto_b or not col_monto_p:
            st.error("⚠️ No se pudieron detectar automáticamente las columnas de Referencia o Monto. Verifique los nombres en sus CSV.")
        else:
            # Procesamiento de campos
            df_b['Ref_Procesada'] = df_b[col_ref_b].astype(str).str.strip()
            df_p['Ref_Procesada'] = df_p[col_ref_p].astype(str).str.strip()
            
            df_b['Ref_Corto'] = df_b['Ref_Procesada'].str[-3:]
            df_p['Ref_Corto'] = df_p['Ref_Procesada'].str[-3:]
            
            df_b['Monto_Num'] = df_b[col_monto_b].apply(limpiar_monto)
            df_p['Monto_Num'] = df_p[col_monto_p].apply(limpiar_monto)

            # --- CRUCES DE CONCILIACIÓN ---
            # A: Ref completa + Monto exacto
            cruce_A = pd.merge(df_b, df_p, on=['Ref_Procesada', 'Monto_Num'], how='inner', suffixes=('_Banco', '_Profit'))
            cruce_A['Tipo_Cruce'] = 'A: Ref Completa y Monto'

            # B: Ref corta (últimos 3 dígitos) + Monto exacto
            cruce_B = pd.merge(df_b, df_p, on=['Ref_Corto', 'Monto_Num'], how='inner', suffixes=('_Banco', '_Profit'))
            cruce_B = cruce_B[~cruce_B.index.isin(cruce_A.index)]
            cruce_B['Tipo_Cruce'] = 'B: Ref Corta (3 dig) y Monto'

            # C: Sumatoria de desgloses en Profit == Monto del Banco
            grupo_p = df_p.groupby('Ref_Corto')['Monto_Num'].sum().reset_index()
            cruce_C = pd.merge(df_b, grupo_p, on='Ref_Corto', suffixes=('', '_Sum'))
            cruce_C = cruce_C[cruce_C['Monto_Num'] == cruce_C['Monto_Num_Sum']]
            cruce_C['Tipo_Cruce'] = 'C: Sumatoria Desglose Profit'

            df_conciliados = pd.concat([cruce_A, cruce_B, cruce_C], ignore_index=True).drop_duplicates()
            
            # PENDIENTES
            refs_conciliadas_b = df_conciliados['Ref_Procesada_Banco'].unique() if 'Ref_Procesada_Banco' in df_conciliados.columns else df_conciliados.get('Ref_Procesada', []).unique()
            df_pend_banco = df_b[~df_b['Ref_Procesada'].isin(refs_conciliadas_b)]
            df_pend_profit = df_p[~df_p['Ref_Procesada'].isin(df_conciliados.get('Ref_Procesada_Profit', refs_conciliadas_b))]

            # --- AUDITORÍA DE DUPLICADOS Y ALERTAS ROJAS ---
            dups_exactos = df_p[df_p.duplicated(subset=['Ref_Procesada', 'Monto_Num'], keep=False)].copy()
            dups_exactos['Tipo_Error'] = 'Duplicado Exacto (Ref y Monto)'

            dups_corto = df_p[df_p.duplicated(subset=['Ref_Corto', 'Monto_Num'], keep=False)].copy()
            dups_corto['Tipo_Error'] = 'Duplicado por Ref Corta (3 dig) y Monto'

            alertas_rojas = []
            for idx, row in df_p.iterrows():
                coincidencias_ref = df_p[(df_p['Ref_Procesada'] == row['Ref_Procesada']) & (df_p['Monto_Num'] != row['Monto_Num'])]
                for _, match in coincidencias_ref.iterrows():
                    if detectar_coincidencia_3_consecutivos(row['Monto_Num'], match['Monto_Num']):
                        alertas_rojas.append(row)
            
            df_rojos = pd.DataFrame(alertas_rojas)
            if not df_rojos.empty:
                df_rojos = df_rojos.drop_duplicates()
                df_rojos['Tipo_Error'] = '🚨 ALERTA ROJA: Ref Igual con Montos Diferentes (3 dig consecutivos)'

            df_errores_totales = pd.concat([dups_exactos, dups_corto, df_rojos], ignore_index=True).drop_duplicates()
            df_inversiones = pd.DataFrame(columns=df_p.columns)

            # --- PESTAÑAS VISUALES ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
                "🔄 Inversiones", "⚠️ Duplicados/Errores"
            ])
            
            with tab1:
                st.subheader("Registros Conciliados Exitosamente (A, B y C)")
                st.dataframe(df_conciliados, use_container_width=True)
            with tab2:
                st.subheader("Movimientos en Banco sin conciliar")
                st.dataframe(df_pend_banco, use_container_width=True)
            with tab3:
                st.subheader("Movimientos en Profit sin conciliar")
                st.dataframe(df_pend_profit, use_container_width=True)
            with tab4:
                st.subheader("Análisis de Inversiones (Debe / Haber)")
                st.dataframe(df_inversiones, use_container_width=True)
            with tab5:
                st.subheader("Auditoría de Duplicados y Alertas Rojas")
                if not df_errores_totales.empty:
                    def estilizar_rojo(val):
                        return 'background-color: #8b0000; color: white;' if 'ALERTA ROJA' in str(val) else ''
                    st.dataframe(df_errores_totales.style.applymap(estilizar_rojo, subset=['Tipo_Error'] if 'Tipo_Error' in df_errores_totales.columns else None), use_container_width=True)
                else:
                    st.success("No se encontraron errores ni duplicados bajo los criterios evaluados.")

            # --- EXPORTACIÓN ---
            st.divider()
            st.subheader("📥 Exportación Final")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_conciliados.to_excel(writer, sheet_name="Conciliados", index=False)
                df_pend_banco.to_excel(writer, sheet_name="Pendientes_Banco", index=False)
                df_pend_profit.to_excel(writer, sheet_name="Pendientes_Profit", index=False)
                df_errores_totales.to_excel(writer, sheet_name="Duplicados_Errores", index=False)
            
            st.download_button(
                label="📥 Descargar Reporte Completo en Excel",
                data=output.getvalue(),
                file_name=f"Conciliacion_{empresa}_{banco}_{mes}_{ano}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Error procesando los archivos: {e}")

# --- FOOTER ---
st.markdown("<br><br><div class='footer'>© 2026 | Sistema Conciliación — Lic. Olgleidys Hernández ✨</div>", unsafe_allow_html=True)
