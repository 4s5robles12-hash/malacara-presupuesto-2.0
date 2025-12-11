import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Presupuestador Malacara", page_icon="❄️")

# --- BASE DE DATOS DE PRECIOS Y HORARIOS ---
PRECIOS_ALQUILER = {
    "Esquís Gama Bronce": {
        "Equipo Completo": [21.00, 38.50, 49.00, 58.00, 67.50],
        "Equipo Completo + Casco": [27.50, 47.50, 62.00, 73.00, 83.50],
        "Esquís + Bastones": [18.50, 34.00, 46.00, 55.50, 63.50],
        "Botas Esquí": [9.00, 15.50, 21.00, 26.00, 28.00]
    },
    "Esquís Gama Plata": {
        "Equipo Completo": [26.00, 46.50, 66.00, 83.50, 99.50],
        "Equipo Completo + Casco": [32.00, 55.50, 78.50, 98.50, 114.50],
        "Esquís + Bastones": [23.50, 44.00, 63.50, 81.00, 97.00],
        "Botas Esquí": [13.00, 24.00, 34.50, 42.50, 49.00]
    },
    "Esquís Gama Oro": {
        "Equipo Completo": [35.50, 65.00, 92.00, 120.00, 138.00],
        "Equipo Completo + Casco": [42.00, 75.50, 106.00, 136.00, 155.50],
        "Esquís + Bastones": [31.50, 53.00, 72.00, 90.50, 107.50],
        "Botas Esquí": [14.50, 26.00, 36.00, 44.00, 50.50]
    },
    "Esquís de Travesía": {
        "Equipo Completo": [35.50, 65.00, 92.00, 120.00, 138.00],
        "Equipo Completo + Casco": [42.00, 75.50, 106.00, 136.00, 155.50],
        "Esquís + Bastones": [31.50, 53.00, 72.00, 90.50, 107.50],
        "Botas Travesía": [14.50, 26.00, 36.00, 44.00, 50.50]
    },
    "Esquís Infantil (<= 13 Años)": {
        "Equipo Completo": [17.00, 30.50, 38.50, 50.00, 54.50],
        "Equipo Completo + Casco": [23.50, 40.00, 51.50, 65.00, 71.50],
        "Esquís + Bastones": [14.50, 24.00, 34.00, 40.00, 45.00],
        "Botas Esquí": [7.50, 11.50, 14.50, 17.00, 19.50]
    },
    "Esquís Infantil Oro (<= 13 Años)": {
        "Equipo Completo": [23.50, 42.50, 54.00, 69.00, 76.00],
        "Equipo Completo + Casco": [29.00, 51.50, 66.00, 83.50, 92.00],
        "Esquís + Bastones": [22.00, 41.00, 52.00, 67.50, 74.50],
        "Botas Esquí": [10.00, 16.00, 22.00, 26.50, 30.50]
    },
    "Snowboard Progresión": {
        "Tabla + Botas": [27.50, 49.00, 68.00, 84.50, 98.00],
        "Tabla + Botas + Casco": [34.00, 58.50, 82.00, 100.00, 115.50],
        "Tabla Sola": [20.00, 36.00, 52.00, 66.00, 79.50],
        "Botas Snowboard": [10.50, 18.50, 26.00, 32.00, 38.50]
    },
    "Snowboard Experto": {
        "Tabla + Botas": [32.00, 58.50, 75.50, 93.00, 100.00],
        "Tabla + Botas + Casco": [37.00, 66.50, 86.00, 106.00, 114.00],
        "Tabla Sola": [27.50, 48.00, 66.50, 82.00, 87.50],
        "Botas Snowboard": [11.50, 19.50, 26.50, 33.00, 39.50]
    },
    "Snowboard Niño": {
        "Tabla + Botas": [22.00, 37.00, 51.50, 65.00, 74.50],
        "Tabla + Botas + Casco": [28.00, 46.00, 65.00, 80.00, 93.00],
        "Tabla Sola": [18.00, 32.00, 45.00, 57.00, 71.50],
        "Botas Snowboard": [7.50, 11.50, 14.50, 17.00, 19.50]
    }
}

NIVELES_ESQUI = [
    "NIVEL A - Nunca he esquiado",
    "NIVEL A+ - Nociones básicas de cuña",
    "NIVEL B - Giros en cuña, empiezo paralelo",
    "NIVEL C - Pistas azules y rojas en paralelo",
    "NIVEL D - Paralelo conducido perfeccionado"
]

EDADES_ALUMNOS = ["5-8 años", "9-12 años", "Adulto (>13 años)"]
HORARIOS_COLECTIVAS = ["10:00 - 13:00", "13:00 - 16:00"]
HORARIOS_PARTICULARES = [f"{h}:00" for h in range(9, 18)]

# --- FUNCIONES AUXILIARES ---
def calcular_precio_bloque(tipo, alumnos, duracion):
    num_personas = len(alumnos)
    if num_personas == 0: return 0, 0
    
    if tipo == "Colectiva (3h/día)":
        precio_unitario = 55
        # En colectivas, la duración es el número de días
        total = precio_unitario * num_personas * duracion
        return total, precio_unitario
    else: # Particular
        # En particular, la duración son Horas Totales, independiente de los días seleccionados
        precio_hora = 50 + (max(0, num_personas - 1) * 5)
        total = precio_hora * duracion
        return total, precio_hora

def calcular_precio_alquiler(gama, equipo, dias):
    if dias < 1: return 0
    if dias > 5: dias = 5
    try:
        precio = PRECIOS_ALQUILER[gama][equipo][dias-1]
        return precio
    except:
        return 0

def get_date_range(start, end):
    return [start + timedelta(days=x) for x in range((end - start).days + 1)]

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image('logo.png', 10, 8, 50)
            self.ln(25)
        else:
            self.set_font('Arial', 'B', 24)
            self.set_text_color(220, 50, 50) 
            self.cell(0, 10, 'Presupuesto', 0, 1, 'C')
            self.set_text_color(50, 50, 100)
            self.cell(0, 10, 'Malacara Esquí - Snowboard', 0, 1, 'C')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Malacara Esquí y Snowboard - www.malacaraesqui.es', 0, 0, 'C')

# --- INTERFAZ STREAMLIT ---
st.title("⛷️ Presupuestador Malacara Pro")

id_presupuesto = "MAL-" + datetime.now().strftime("%Y%m%d-%H%M")
fecha_solicitud = datetime.now().strftime("%d/%m/%Y")

# 1. DATOS DEL CLIENTE Y FECHAS
with st.container():
    st.markdown("### 1. Detalles del Cliente y Fechas")
    col1, col2 = st.columns(2)
    cliente_nombre = col1.text_input("Nombre del Titular", "Iván Fernández")
    cliente_dni = col2.text_input("DNI / Pasaporte")
    col3, col4 = st.columns(2)
    cliente_telefono = col3.text_input("Teléfono")
    cliente_email = col4.text_input("Email")
    
    st.divider()
    st.markdown("#### 📅 Selección de Días de Esquí")
    
    cd1, cd2 = st.columns(2)
    f_inicio = cd1.date_input("Fecha Llegada", datetime.now())
    f_fin = cd2.date_input("Fecha Salida", datetime.now() + timedelta(days=2))
    
    # Generar rango de fechas
    if f_fin >= f_inicio:
        dias_posibles = get_date_range(f_inicio, f_fin)
        dias_formateados = [d.strftime("%d/%m") for d in dias_posibles]
        
        # Multiselect para elegir días específicos
        st.info("Desmarca los días que NO se vaya a esquiar:")
        dias_seleccionados = st.multiselect(
            "Días Activos de Esquí", 
            dias_posibles, 
            default=dias_posibles,
            format_func=lambda x: x.strftime("%d/%m/%Y")
        )
        
        cantidad_dias_esqui = len(dias_seleccionados)
        texto_fechas_pdf = ", ".join([d.strftime("%d/%m") for d in dias_seleccionados])
        
        if cantidad_dias_esqui > 0:
            st.success(f"🗓️ Total días efectivos para cálculo: **{cantidad_dias_esqui} días**")
        else:
            st.warning("No hay días seleccionados.")
            cantidad_dias_esqui = 0
            texto_fechas_pdf = "Sin fechas seleccionadas"
    else:
        st.error("La fecha de salida debe ser posterior a la de llegada.")
        cantidad_dias_esqui = 0
        texto_fechas_pdf = "Error en fechas"

    st.caption(f"🆔 Ref: **{id_presupuesto}**")

# 2. GESTIÓN DE CLASES
st.divider()
st.markdown("### 2. Clases de Esquí / Snowboard")

if 'carrito_clases' not in st.session_state:
    st.session_state['carrito_clases'] = []
    
with st.container():
    st.markdown("#### 🛠️ Configurar Nuevo Grupo de Clase")
    
    c_conf1, c_conf2 = st.columns(2)
    new_estacion = c_conf1.selectbox("Estación", ["Astún", "Candanchú"], key="new_est")
    new_tipo = c_conf2.selectbox("Tipo de Clase", ["Colectiva (3h/día)", "Particular"], key="new_tipo")
    
    c_conf3, c_conf4 = st.columns(2)
    
    # Lógica de días/horas según tipo
    if new_tipo == "Colectiva (3h/día)":
        # Bloqueamos el input y usamos la cantidad calculada arriba
        st.caption(f"ℹ️ Duración automática basada en calendario: {cantidad_dias_esqui} días")
        new_duracion = cantidad_dias_esqui
        new_horario = c_conf4.selectbox("Horario Turno", HORARIOS_COLECTIVAS, key="new_hor")
        lbl_dur = "días"
    else:
        # Particulares: Horas totales manuales
        new_duracion = c_conf3.number_input("Horas Totales (Indep. días)", 1, 20, 2, key="new_dur")
        new_horario = c_conf4.selectbox("Hora Inicio", HORARIOS_PARTICULARES, key="new_hor")
        lbl_dur = "horas"

    # Alumnos provisionales
    if 'temp_alumnos' not in st.session_state:
        st.session_state['temp_alumnos'] = []
        
    with st.expander("Añadir Alumnos a este grupo", expanded=True):
        ca1, ca2 = st.columns(2)
        n_nombre = ca1.text_input("Nombre Alumno", key="n_nom")
        n_edad = ca2.selectbox("Edad", EDADES_ALUMNOS, key="n_ed")
        ca3, ca4 = st.columns(2)
        n_mod = ca3.radio("Modalidad", ["Esquí", "Snowboard"], horizontal=True, key="n_mod")
        n_niv = ca4.selectbox("Nivel", NIVELES_ESQUI, key="n_niv")
        
        if st.button("➕ Añadir Alumno"):
            if n_nombre:
                st.session_state['temp_alumnos'].append({
                    "nombre": n_nombre,
                    "edad": n_edad,
                    "modalidad": n_mod,
                    "nivel": n_niv
                })
            else:
                st.error("Falta el nombre")

    if len(st.session_state['temp_alumnos']) > 0:
        st.table(pd.DataFrame(st.session_state['temp_alumnos']))
        
        # Validar antes de añadir
        bloquear_btn = (new_tipo == "Colectiva (3h/día)" and cantidad_dias_esqui == 0)
        
        if bloquear_btn:
            st.error("⚠️ No puedes añadir clase colectiva con 0 días seleccionados en el calendario.")
        else:
            if st.button("✅ Confirmar y Añadir Grupo", type="primary"):
                precio_bloque, precio_unit = calcular_precio_bloque(new_tipo, st.session_state['temp_alumnos'], new_duracion)
                
                st.session_state['carrito_clases'].append({
                    "estacion": new_estacion,
                    "tipo": new_tipo,
                    "duracion": new_duracion,
                    "lbl_dur": lbl_dur,
                    "horario": new_horario,
                    "alumnos": st.session_state['temp_alumnos'],
                    "precio_total": precio_bloque,
                    "precio_unit": precio_unit
                })
                st.session_state['temp_alumnos'] = []
                st.rerun()
            
        if st.button("Cancelar Lista"):
            st.session_state['temp_alumnos'] = []
            st.rerun()

# --- RESUMEN CLASES ---
st.divider()
st.subheader("📦 Resumen de Clases Añadidas")
total_clases_global = 0

if len(st.session_state['carrito_clases']) > 0:
    for idx, grupo in enumerate(st.session_state['carrito_clases']):
        with st.container():
            st.markdown(f"**Grupo {idx+1}: {grupo['tipo']} en {grupo['estacion']}**")
            st.markdown(f"🗓️ {grupo['duracion']} {grupo['lbl_dur']} | ⏰ {grupo['horario']} | 💶 **Subtotal: {grupo['precio_total']}€**")
            df_g = pd.DataFrame(grupo['alumnos'])
            st.dataframe(df_g[["nombre", "edad", "nivel"]], use_container_width=True, hide_index=True)
            total_clases_global += grupo['precio_total']
            st.divider()
            
    if st.button("🗑️ Borrar TODAS las clases"):
        st.session_state['carrito_clases'] = []
        st.rerun()
else:
    st.info("No hay clases añadidas.")

st.success(f"**Total Clases: {total_clases_global}€**")


# 3. ALQUILER DE MATERIAL
st.markdown("### 3. Alquiler de Material")

if 'alquileres' not in st.session_state:
    st.session_state['alquileres'] = []

with st.expander("Añadir Equipo de Alquiler"):
    c1, c2 = st.columns(2)
    cat_select = c1.selectbox("Gama", list(PRECIOS_ALQUILER.keys()))
    equip_options = list(PRECIOS_ALQUILER[cat_select].keys())
    equip_select = c2.selectbox("Equipo", equip_options)
    
    # Aquí usamos automáticamente los días del calendario
    c3, c4 = st.columns(2)
    st.caption(f"Días de alquiler calculados: {cantidad_dias_esqui}")
    cant_equip = c4.number_input("Cantidad", 1, 10, 1)
    
    if st.button("Añadir Equipo"):
        if cantidad_dias_esqui > 0:
            precio_unit = calcular_precio_alquiler(cat_select, equip_select, cantidad_dias_esqui)
            subtotal_linea = precio_unit * cant_equip
            st.session_state['alquileres'].append({
                "gama": cat_select,
                "tipo": equip_select,
                "dias": cantidad_dias_esqui,
                "cantidad": cant_equip,
                "precio_unit": precio_unit,
                "subtotal": subtotal_linea
            })
        else:
            st.error("Selecciona días en el calendario primero.")

total_alquiler = 0
if len(st.session_state['alquileres']) > 0:
    df_alq = pd.DataFrame(st.session_state['alquileres'])
    st.dataframe(df_alq[["gama", "tipo", "dias", "cantidad", "subtotal"]], use_container_width=True)
    total_alquiler = df_alq["subtotal"].sum()
    if st.button("Borrar Alquileres"):
        st.session_state['alquileres'] = []
        st.rerun()

st.write(f"**Subtotal Alquiler: {total_alquiler}€**")

# 4. TOTALES
st.divider()
st.markdown("### 4. Resumen Final")

subtotal_general = total_clases_global + total_alquiler

col_d1, col_d2 = st.columns(2)
aplicar_descuento = col_d1.checkbox("¿Aplicar Descuento?")
tipo_desc = col_d2.radio("Tipo", ["Porcentaje (%)", "Cantidad Fija (€)"], disabled=not aplicar_descuento, horizontal=True)
valor_desc = col_d1.number_input("Valor", min_value=0.0, value=0.0, disabled=not aplicar_descuento)
concepto_desc = col_d2.text_input("Concepto", "Descuento Especial", disabled=not aplicar_descuento)

descuento_total = 0
if aplicar_descuento:
    if tipo_desc == "Porcentaje (%)":
        descuento_total = subtotal_general * (valor_desc / 100)
    else:
        descuento_total = valor_desc

total_final = subtotal_general - descuento_total

st.metric(label="TOTAL A PAGAR", value=f"{total_final:.2f}€", delta=f"-{descuento_total:.2f}€" if descuento_total > 0 else None)

# 5. PDF
def create_pdf():
    pdf = PDF()
    pdf.add_page()
    blue_header = (230, 240, 255)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Fecha: {fecha_solicitud} | Ref: {id_presupuesto}", 0, 1, 'R')
    pdf.ln(5)
    
    pdf.multi_cell(0, 5, "Gracias por contactar con Malacara Esquí y Snowboard. A continuación, encontrará su presupuesto detallado.")
    pdf.ln(5)
    
    # BLOQUE CLIENTE
    pdf.set_fill_color(*blue_header)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Detalles del Cliente", 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 6, "Nombre:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 6, cliente_nombre, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 6, "DNI/Pass:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 6, cliente_dni, 0, 1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 6, "Teléfono:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 6, cliente_telefono, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 6, "Email:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 6, cliente_email, 0, 1)
    
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "Días seleccionados para esquí:", 0, 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 5, texto_fechas_pdf)
    pdf.ln(5)
    
    # BLOQUE CLASES
    if len(st.session_state['carrito_clases']) > 0:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Presupuesto de Clases", 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        for i, grupo in enumerate(st.session_state['carrito_clases']):
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(245, 245, 245)
            titulo_grupo = f"Grupo {i+1}: {grupo['tipo']} - {grupo['estacion']} ({grupo['horario']})"
            pdf.cell(0, 7, titulo_grupo, 0, 1, 'L', fill=True)
            
            pdf.set_font("Arial", 'B', 9)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(60, 6, "Alumno", 1, 0)
            pdf.cell(30, 6, "Edad", 1, 0, 'C')
            pdf.cell(30, 6, "Modalidad", 1, 0, 'C')
            pdf.cell(70, 6, "Nivel", 1, 1, 'C') 
            
            pdf.set_text_color(0)
            pdf.set_font("Arial", '', 8)
            for al in grupo['alumnos']:
                pdf.cell(60, 6, al['nombre'], 1, 0)
                pdf.cell(30, 6, al['edad'], 1, 0, 'C')
                pdf.cell(30, 6, al['modalidad'], 1, 0, 'C')
                nivel_corto = (al['nivel'][:35] + '..') if len(al['nivel']) > 35 else al['nivel']
                pdf.cell(70, 6, nivel_corto, 1, 1)
            
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(160, 6, f"Detalle: {len(grupo['alumnos'])} pax x {grupo['duracion']} {grupo['lbl_dur']} | Subtotal Grupo:", 0, 0, 'R')
            pdf.cell(30, 6, f"{grupo['precio_total']} eur", 0, 1, 'R')
            pdf.ln(3)

        pdf.ln(2)

    # BLOQUE ALQUILER
    if len(st.session_state['alquileres']) > 0:
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0)
        pdf.set_fill_color(*blue_header)
        pdf.cell(0, 8, "Presupuesto de Alquiler", 0, 1, 'L', fill=True)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(70, 8, "Equipo", 1, 0, 'C')
        pdf.cell(30, 8, "Duración", 1, 0, 'C')
        pdf.cell(30, 8, "Precio Unit.", 1, 0, 'C')
        pdf.cell(30, 8, "Cantidad", 1, 0, 'C')
        pdf.cell(30, 8, "Subtotal", 1, 1, 'C')
        
        pdf.set_text_color(0)
        pdf.set_font("Arial", '', 8)
        
        for item in st.session_state['alquileres']:
            desc_item = f"{item['gama']} - {item['tipo']}"
            pdf.cell(70, 8, desc_item[:40], 1, 0)
            pdf.cell(30, 8, f"{item['dias']} dias", 1, 0, 'C')
            pdf.cell(30, 8, f"{item['precio_unit']} eur", 1, 0, 'C')
            pdf.cell(30, 8, str(item['cantidad']), 1, 0, 'C')
            pdf.cell(30, 8, f"{item['subtotal']} eur", 1, 1, 'C')
        
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(160, 8, "Total Alquiler:", 0, 0, 'R')
        pdf.cell(30, 8, f"{total_alquiler:.2f} eur", 0, 1, 'R')
        pdf.ln(5)

    # RESUMEN FINAL
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "", 0, 1, fill=True)
    pdf.set_y(pdf.get_y() - 10)
    
    texto_total = f"TOTAL PRESUPUESTO: {total_final:.2f} eur"
    pdf.cell(0, 10, texto_total, 0, 1, 'R')
    
    if descuento_total > 0:
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 6, f"Incluye descuento de {descuento_total:.2f} eur ({concepto_desc})", 0, 1, 'R')
        pdf.set_text_color(0)
    
    pdf.ln(5)
    
    # CONDICIONES
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0)
    pdf.cell(0, 8, "Condiciones", 0, 1, 'L')
    pdf.set_font("Arial", '', 9)
    condiciones = (
        "- Este presupuesto tiene una validez de 15 días.\n"
        "- Para confirmar la reserva, contacte con nosotros.\n"
        "- Cancelaciones con menos de 48 horas conllevan cargo.\n"
        "- Los precios están sujetos a cambios según la temporada."
    )
    pdf.multi_cell(0, 5, condiciones)
    
    return pdf.output(dest='S').encode('latin-1')

st.divider()
if st.button("📄 CREAR PDF FINAL", type="primary"):
    pdf_bytes = create_pdf()
    nombre_archivo = f"Presupuesto_{id_presupuesto}_{cliente_nombre.split()[0]}.pdf"
    
    st.download_button(
        label="⬇️ Descargar PDF",
        data=pdf_bytes,
        file_name=nombre_archivo,
        mime='application/pdf'
    )
