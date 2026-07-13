import streamlit as st
import pandas as pd
import io
import re

# Configuración de la página
st.set_page_config(page_title="Conciliación Bancaria Profesional", page_icon="📊", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# Configuración de usuario
c1, c2 = st.columns(2)
with c1: empresa = st.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
with c2: banco = st.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])

col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader("📥 Estado de Cuenta (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader("📥 Reporte Profit (.csv)", type=["csv"])

# Lógica de procesamiento BLINDADA
def procesar_csv(file):
    try:
        # dtype=str impide que Excel corrompa los números largos (notación científica)
        df = pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip", dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error de lectura: {e}")
        return None

def limpiar_referencia(valor):
    if pd.isna(valor) or valor == '': return ""
    v = str(valor)
    # Si detecta notación científica (8.57E+10), la corrige a número real
    if 'E+' in v:
        try: return str(int(float(v)))
        except: pass
    # Deja solo los números
    return re.sub(r'[^0-9]', '', v)

def limpiar_monto(valor):
    # Asegura que el monto sea un número con 2 decimales
    s = str(valor).replace(',', '.')
    return pd.to_numeric(re.sub(r'[^0-9.]', '', s), errors='coerce')

if banco_file and profit_file:
    df_b = procesar_csv(banco_file)
    df_p = procesar_csv(profit_file)
    
    if df_b is not None and df_p is not None:
        try:
            # Seleccionar y renombrar columnas básicas (ajusta según tus nombres reales de columnas)
            # Asumimos: Fecha, Ref, Desc, Deb, Cred
            df_b = df_b.iloc[:, :5]; df_b.columns = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
            df_p = df_p.iloc[:, :5]; df_p.columns = ['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']
            
            # Limpieza profunda
            df_b['Ref_Limpia'] = df_b['Ref'].apply(limpiar_referencia)
            df_p['Ref_Limpia'] = df_p['Ref'].apply(limpiar_referencia)
            df_b['Monto_Num'] = df_b['Cred'].apply(limpiar_monto).fillna(0).round(2)
            df_p['Monto_Num'] = df_p['Haber'].apply(limpiar_monto).fillna(0).round(2)

            # Creación de llaves para el cruce
            df_b['Key'] = df_b['Ref_Limpia'] + "_" + df_b['Monto_Num'].astype(str)
            df_p['Key'] = df_p['Ref_Limpia'] + "_" + df_p['Monto_Num'].astype(str)
            
            # Conciliación
            cruces = df_b[df_b['Key'].isin(df_p['Key'])]
            solo_b = df_b[~df_b['Key'].isin(df_p['Key'])]
            solo_p = df_p[~df_p['Key'].isin(df_b['Key'])]
            
            # Visualización
            t1, t2, t3 = st.tabs(["✅ Cruces", "🏦 Solo Banco", "💻 Solo Profit"])
            t1.dataframe(cruces, use_container_width=True)
            t2.dataframe(solo_b, use_container_width=True)
            t3.dataframe(solo_p, use_container_width=True)
            
            # Exportación
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cruces.to_excel(writer, sheet_name='Cruces', index=False)
                solo_b.to_excel(writer, sheet_name='Solo_Banco', index=False)
                solo_p.to_excel(writer, sheet_name='Solo_Profit', index=False)
            st.download_button("📥 Descargar Conciliación", output.getvalue(), "Conciliacion_Final.xlsx")
            
        except Exception as e:
            st.error(f"Error en la conciliación: {e}")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación</p></div>', unsafe_allow_html=True)
