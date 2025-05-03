import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import base64
import io
from funciones_analisis_sismico import *



# Configuración de la página
st.set_page_config(
    page_title="Análisis Sísmico Dinámico Modal Espectral",
    page_icon="🏢",
    layout="wide"
)

# Título y descripción
st.title("Análisis Sísmico Dinámico Modal Espectral")
st.markdown("""
Esta aplicación realiza un análisis sísmico dinámico modal espectral para estructuras de edificación.
Ingrese los parámetros solicitados y cargue los datos de modos y masas para obtener los resultados.
""")

# Sidebar para parámetros generales
st.sidebar.header("Parámetros de la Estructura")

# Parámetros de la estructura
num_pisos = st.sidebar.slider("Número de pisos", 1, 20, 5)
h = st.sidebar.number_input("Altura de pisos (m)", min_value=2.0, max_value=5.0, value=3.0, step=0.1)

# Parámetros para el cálculo del periodo fundamental
st.sidebar.subheader("Parámetros para Periodo Fundamental")
tipo_estructura = st.sidebar.selectbox(
    "Tipo de Estructura",
    [
        "Pórticos de concreto armado sin muros de corte",
        "Pórticos de concreto armado con muros en cajas de ascensores",
        "Edificios de albañilería y para concreto armado duales"
    ]
)

# Asignar valor de Ct según el tipo de estructura
if tipo_estructura == "Pórticos de concreto armado sin muros de corte":
    Ct = 35
elif tipo_estructura == "Pórticos de concreto armado con muros en cajas de ascensores":
    Ct = 45
else:  # Edificios de albañilería y para concreto armado duales
    Ct = 60

st.sidebar.text(f"Coeficiente Ct: {Ct}")

# Parámetros sísmicos
st.sidebar.subheader("Parámetros Sísmicos")
Z = st.sidebar.selectbox("Factor de Zona (Z)", [0.10, 0.25, 0.35, 0.45], index=3)
uso = st.sidebar.selectbox("Factor de Uso (U)", [1.0, 1.3, 1.5], index=0)
S = st.sidebar.selectbox("Factor de Suelo (S)", [0.8, 1.0, 1.05, 1.1, 1.4], index=1)
R = st.sidebar.slider("Factor de Reducción (R)", 1, 8, 8)

# Parámetros para el cálculo del factor de amplificación
Tp = st.sidebar.number_input("Periodo de plataforma Tp (s)", min_value=0.1, max_value=1.0, value=0.4, step=0.1)
Tl = st.sidebar.number_input("Periodo límite Tl (s)", min_value=0.5, max_value=10.0, value=2.5, step=0.1)

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["Entrada de datos", "Resultados", "Reportes"])

with tab1:
    st.header("Entrada de datos")
    
    # Opción para cargar datos de ejemplo o ingresar datos manualmente
    data_option = st.radio(
        "Seleccionar método de entrada de datos:",
        ["Usar datos de ejemplo", "Cargar archivo Excel", "Ingresar datos manualmente"]
    )
    
    if data_option == "Usar datos de ejemplo":
        # Datos de ejemplo para modos y masas
        st.subheader("Datos de ejemplo")
        
        # Modos y masas de ejemplo (para 5 pisos)
        ejemplo_modos_masas = pd.DataFrame({
            "Piso": [5, 4, 3, 2, 1],
            "Modo 1": [1.000, 0.766, 0.500, 0.259, 0.085],
            "Modo 2": [0.000, -0.643, -1.000, -0.766, -0.259],
            "Modo 3": [0.000, 1.000, 0.000, -1.000, 0.000],
            "Masa (ton)": [25, 25, 25, 25, 25]
        })
        
        st.write("Datos de modos y masas:")
        st.dataframe(ejemplo_modos_masas)
        
        # Periodos de ejemplo
        ejemplo_periodos = pd.DataFrame({
            "Modo": [1, 2, 3],
            "Periodo (s)": [0.82, 0.27, 0.16]
        })
        
        st.write("Datos de periodos:")
        st.dataframe(ejemplo_periodos)
        
        # Usar estos datos como entrada
        modosymasa = ejemplo_modos_masas
        periodos_data = ejemplo_periodos["Periodo (s)"].values
        
    elif data_option == "Cargar archivo Excel":
        st.subheader("Cargar archivo Excel")
        st.write("El archivo debe contener dos hojas: 'modosymasa_data' y 'periodos_data'.")
        
        uploaded_file = st.file_uploader("Seleccionar archivo Excel", type=["xlsx"])
        
        if uploaded_file is not None:
            try:
                modosymasa = pd.read_excel(uploaded_file, sheet_name="modosymasa_data")
                periodos_df = pd.read_excel(uploaded_file, sheet_name="periodos_data")
                
                st.write("Datos de modos y masas:")
                st.dataframe(modosymasa)
                
                st.write("Datos de periodos:")
                st.dataframe(periodos_df)
                
                # Extraer los periodos como un array numpy
                periodos_data = periodos_df.iloc[0, 1:].values
                
            except Exception as e:
                st.error(f"Error al cargar el archivo: {e}")
                st.stop()
        else:
            st.info("Por favor, cargue un archivo Excel.")
            st.stop()
    
    else:  # Ingresar datos manualmente
        st.subheader("Ingresar datos manualmente")
        
        # Crear un DataFrame vacío para modos y masas
        columnas = ["Piso"] + [f"Modo {i+1}" for i in range(3)] + ["Masa (ton)"]
        datos_vacios = {col: [0.0] * num_pisos for col in columnas}
        datos_vacios["Piso"] = list(range(num_pisos, 0, -1))
        
        modosymasa = pd.DataFrame(datos_vacios)
        
        # Widget para editar el DataFrame
        edited_modosymasa = st.data_editor(
            modosymasa,
            use_container_width=True,
            hide_index=True,
            disabled=["Piso"]
        )
        
        # Entrada para periodos
        st.subheader("Periodos por modo")
        periodos_dict = {}
        col1, col2, col3 = st.columns(3)
        
        with col1:
            periodo1 = st.number_input("Periodo Modo 1 (s)", min_value=0.1, max_value=5.0, value=0.82, step=0.01)
        with col2:
            periodo2 = st.number_input("Periodo Modo 2 (s)", min_value=0.1, max_value=5.0, value=0.27, step=0.01)
        with col3:
            periodo3 = st.number_input("Periodo Modo 3 (s)", min_value=0.1, max_value=5.0, value=0.16, step=0.01)
        
        periodos_data = np.array([periodo1, periodo2, periodo3])
        
        # Usar los datos editados
        modosymasa = edited_modosymasa

    # Botón para realizar el análisis
    if st.button("Realizar Análisis Sísmico", type="primary"):
        # Guardar los datos para uso en otras pestañas
        st.session_state['modosymasa'] = modosymasa
        st.session_state['periodos_data'] = periodos_data
        st.session_state['parametros'] = {
            'num_pisos': num_pisos,
            'h': h,
            'Ct': Ct,
            'Z': Z,
            'uso': uso,
            'S': S,
            'R': R,
            'Tp': Tp,
            'Tl': Tl
        }
        st.session_state['analisis_realizado'] = True
        st.success("Análisis realizado con éxito. Consulte la pestaña de Resultados.")

with tab2:
    st.header("Resultados del Análisis")
    
    if 'analisis_realizado' not in st.session_state or not st.session_state['analisis_realizado']:
        st.info("Realice el análisis en la pestaña 'Entrada de datos' primero.")
        st.stop()
    else:
        # Recuperar datos guardados
        modosymasa = st.session_state['modosymasa']
        periodos_data = st.session_state['periodos_data']
        params = st.session_state['parametros']
        
        # Crear columnas para mostrar parámetros principales
        col1, col2, col3, col4 = st.columns(4)
        
        # Calcular el periodo fundamental
        T = calcular_periodo_fundamental(params['num_pisos'], params['h'], params['Ct'])
        
        # Calcular el factor de amplificación
        C = calcular_factor_amplificacion(T, params['Tp'], params['Tl'])
        
        # Calcular la pseudo-aceleración
        Sa = calcular_pseudo_aceleracion(params['Z'], params['uso'], C, params['S'], params['R'])
        
        with col1:
            st.metric("Periodo Fundamental (T)", f"{T:.4f} s")
        
        with col2:
            st.metric("Factor de Amplificación (C)", f"{C:.4f}")
        
        with col3:
            st.metric("Pseudo-aceleración (Sa)", f"{Sa:.4f} g")
        
        with col4:
            st.metric("Factor de Reducción (R)", f"{params['R']}")
        
        # Preparar los datos para el análisis
        masas = modosymasa["Masa (ton)"].values[::-1]  # Invertir para que sea de abajo hacia arriba
        
        # Extraer modos de vibración
        modos_cols = [col for col in modosymasa.columns if "Modo" in col]
        X = modosymasa[modos_cols].values
        X = X[::-1].T  # Invertir filas y transponer
        
        # Calcular frecuencias estructurales
        W_matriz = calcular_frecuencias_estructurales(periodos_data)
        
        # Calcular desplazamientos espectrales
        Sd = calcular_desplazamientos_espectrales(Sa, W_matriz)
        
        # Calcular participación de masa
        r, M = calcular_participacion_masa(X, masas)
        
        # Calcular aceleración por piso
        U = calcular_aceleracion_por_piso(X, r, Sa)
        
        # Calcular fuerzas sísmicas
        F = calcular_fuerzas_sismicas(M, U)
        
        # Calcular cortante sísmica
        V = calcular_cortante_sismica(F)
        
        # Calcular cortante de la suma de valores absolutos
        V_sum_abs = calcular_cortante_suma_absolutos(V)
        
        # Calcular cortante raíz cuadrada de la suma de los cuadrados
        V_rcsc = calcular_cortante_rcsc(V)
        
        # Calcular cortante de respuesta máxima
        Vrnc_h = calcular_cortante_respuesta_maxima(V_sum_abs, V_rcsc)
        
        # Calcular cortante real
        Vreal = calcular_cortante_real(Vrnc_h, params['R'])
        
        # Nombres de pisos
        pisos_nombres = [f"Piso {i+1}" for i in range(params['num_pisos'])]
        
        # Mostrar resultados en pestañas
        res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs([
            "Modos y Participación", 
            "Fuerzas y Cortantes", 
            "Cortantes por Métodos", 
            "Cortante Real"
        ])
        
        with res_tab1:
            st.subheader("Modos de Vibración y Participación de Masa")
            
            # Mostrar periodos y frecuencias
            col1, col2 = st.columns(2)
            
            with col1:
                df_periodos = pd.DataFrame({
                    "Modo": [f"Modo {i+1}" for i in range(len(periodos_data))],
                    "Periodo (s)": periodos_data,
                    "Frecuencia (Hz)": [1/p for p in periodos_data],
                    "Frecuencia angular (rad/s)": W_matriz
                })
                st.write("Periodos y Frecuencias:")
                st.dataframe(df_periodos, hide_index=True)
            
            with col2:
                df_participacion = pd.DataFrame({
                    "Modo": [f"Modo {i+1}" for i in range(len(r))],
                    "Participación de Masa": r
                })
                st.write("Participación de Masa:")
                st.dataframe(df_participacion, hide_index=True)
            
            # Mostrar desplazamientos espectrales
            df_sd = pd.DataFrame({
                "Modo": [f"Modo {i+1}" for i in range(len(Sd))],
                "Desplazamiento Espectral (Sd)": Sd
            })
            st.write("Desplazamientos Espectrales:")
            st.dataframe(df_sd, hide_index=True)
        
        with res_tab2:
            st.subheader("Fuerzas y Cortantes Sísmicas por Modo")
            
            # Mostrar gráfico de fuerzas y cortantes
            fig_fuerzas_cortantes = generar_grafico_fuerzas_cortantes(F, V, pisos_nombres)
            st.plotly_chart(fig_fuerzas_cortantes, use_container_width=True)
            
            # Mostrar datos en tablas
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Aceleraciones por Piso (U):")
                df_u = pd.DataFrame({
                    "Piso": pisos_nombres
                })
                for i, u_modo in enumerate(U):
                    df_u[f"Modo {i+1}"] = u_modo
                st.dataframe(df_u, hide_index=True)
            
            with col2:
                st.write("Fuerzas Sísmicas por Piso (F):")
                df_f = pd.DataFrame({
                    "Piso": pisos_nombres
                })
                for i, f_modo in enumerate(F):
                    df_f[f"Modo {i+1}"] = f_modo
                st.dataframe(df_f, hide_index=True)
            
            st.write("Cortantes Sísmicas por Piso (V):")
            df_v = pd.DataFrame({
                "Piso": pisos_nombres
            })
            for i, v_modo in enumerate(V):
                df_v[f"Modo {i+1}"] = v_modo
            st.dataframe(df_v, hide_index=True)
        
        with res_tab3:
            st.subheader("Cortantes por Diferentes Métodos")
            
            # Mostrar gráfico de cortantes
            fig_cortantes = generar_grafico_cortantes(V_sum_abs, V_rcsc, Vrnc_h, Vreal, pisos_nombres)
            st.plotly_chart(fig_cortantes, use_container_width=True)
            
            # Mostrar datos en tabla
            df_cortantes = pd.DataFrame({
                "Piso": pisos_nombres,
                "Suma de Valores Absolutos": V_sum_abs,
                "Raíz Cuadrada de la Suma de Cuadrados": V_rcsc,
                "Respuesta Máxima": Vrnc_h,
                "Cortante Real": Vreal
            })
            st.dataframe(df_cortantes, hide_index=True)
        
        with res_tab4:
            st.subheader("Cortante Real por Piso")
            
            # Mostrar gráfico de cortante real
            fig_cortante_real = generar_grafico_cortante_real(Vreal, pisos_nombres)
            st.plotly_chart(fig_cortante_real, use_container_width=True)
            
            # Mostrar datos en tabla
            df_vreal = pd.DataFrame({
                "Piso": pisos_nombres,
                "Cortante Real (Tonf)": Vreal
            })
            st.dataframe(df_vreal, hide_index=True)
            
            # Guardar resultados para el reporte
            st.session_state['resultados'] = {
                'T': T,
                'C': C,
                'Sa': Sa,
                'W_matriz': W_matriz,
                'Sd': Sd,
                'r': r,
                'U': U,
                'F': F,
                'V': V,
                'V_sum_abs': V_sum_abs,
                'V_rcsc': V_rcsc,
                'Vrnc_h': Vrnc_h,
                'Vreal': Vreal,
                'pisos_nombres': pisos_nombres,
                'fig_fuerzas_cortantes': fig_fuerzas_cortantes,
                'fig_cortantes': fig_cortantes,
                'fig_cortante_real': fig_cortante_real,
                'periodos_data': periodos_data
            }