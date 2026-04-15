import streamlit as st
import pandas as pd
import json
import re
import html
import math
from copy import deepcopy
import hashlib

# =========================================================
# Helpers (mínimo)
# =========================================================
MARGEN_NORMAL = 2.2
MARGEN_ESPECIAL = 2.1
COMERCIALES_MARGEN_ESPECIAL = {52, 47, 46, 62}
CLIENTES_MARGEN_ESPECIAL = {"PLANETA", "ILIDIA"}


def _parse_comercial_num(value: str):
    """Devuelve el número de comercial si es interpretable, si no None."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    m = re.search(r"(\d+)", s)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _cliente_tiene_margen_especial(cliente: str) -> bool:
    if cliente is None:
        return False
    c = str(cliente).upper()
    return any(k in c for k in CLIENTES_MARGEN_ESPECIAL)


def _margen_por_comercial(n) -> float:
    if n is None:
        return MARGEN_NORMAL
    return MARGEN_ESPECIAL if n in COMERCIALES_MARGEN_ESPECIAL else MARGEN_NORMAL


def _margen_sugerido(com1: str, com2: str, cliente: str) -> float:
    # Si el cliente es especial, manda 2.1.
    if _cliente_tiene_margen_especial(cliente):
        return MARGEN_ESPECIAL

    n1 = _parse_comercial_num(com1)
    n2 = _parse_comercial_num(com2)
    return min(_margen_por_comercial(n1), _margen_por_comercial(n2))


def _aplicar_margen_auto_si_procede() -> None:
    """Actualiza st.session_state.margen solo si el usuario no lo ha sobreescrito."""
    sugerido = float(_margen_sugerido(st.session_state.comercial_1, st.session_state.comercial_2, st.session_state.cli))
    actual = float(st.session_state.margen)
    last_auto = float(st.session_state.last_auto_margen)

    # Si el margen actual coincide con el último auto, interpretamos que el usuario no lo tocó.
    if (actual == last_auto) and (sugerido != actual):
        st.session_state.margen = sugerido
        st.session_state.last_auto_margen = sugerido
    else:
        # Aun así guardamos el sugerido para la próxima comparación.
        st.session_state.last_auto_margen = sugerido

# =========================================================
# 1) CONFIGURACIÓN
# =========================================================
st.set_page_config(page_title="MAINSA ADMIN V44", layout="wide")

# =========================================================
# 2) FLEXICO (igual)
# =========================================================
PRODUCTOS_FLEXICO = {
    "172018": {"desc": "GANCHO EXTENSIBLE MAXI 0,5kg", "precio": 0.0397},
    "137018": {"desc": "PORTAETIQUETA GANCHO 28x30 mm", "precio": 0.0742},
    "142201": {"desc": "GANCHO PERFORANTE SIMPLE 200mm", "precio": 0.1480},
    "142203": {"desc": "GANCHO PERFORANTE SIMPLE 150mm", "precio": 0.1290},
    "142205": {"desc": "GANCHO PERFORANTE SIMPLE 100mm", "precio": 0.1080},
    "142206": {"desc": "GANCHO PERFORADOR SIMPLE 5 CM", "precio": 0.1530},
    "142412": {"desc": "GANCHO PERFORANTE DOBLE 100mm", "precio": 0.1260},
    "142413": {"desc": "GANCHO PERFORANTE DOBLE 150mm", "precio": 0.1280},
    "142414": {"desc": "PERFORANTE DOBLE 200mm GANCHO", "precio": 0.1710},
    "142415": {"desc": "PERFORANTE DOBLE 250mm GANCHO", "precio": 0.1800},
    "142422": {"desc": "GANCHO PERFO DOBLE NEGRO 100mm", "precio": 0.1020},
    "142424": {"desc": "GANCHO PERFO DOBLE NEGRO 200mm", "precio": 0.1880},
    "145104": {"desc": "TIRA CROSS MERCH METALICA", "precio": 3.1100},
    "145110": {"desc": "TIRA CROSS MERCH-740 MM", "precio": 0.3310},
    "145150": {"desc": "PINZA PARA CROSS-MERCHANDISING", "precio": 0.1072},
    "172594": {"desc": "ANILLA LLAVERO - 20 MM", "precio": 0.0600},
    "262041": {"desc": "SUJETADOR PERFIL PP 30-40mm", "precio": 0.0500},
    "752012": {"desc": "BISTUCADOR Ø12mm CIER14mm NEGR", "precio": 0.0400},
    "752013": {"desc": "BISTUCADOR Ø12mm CIER14mm TRSP", "precio": 0.0410},
    "752015": {"desc": "BISTUCADOR Ø12mm CIER7mm TRSP", "precio": 0.0370},
    "753007": {"desc": "SOP PORTACARTEL ADH TRSP 56X25", "precio": 0.1770},
    "792010": {"desc": "GANCHO SUSPENSION + HILO 1,2m", "precio": 0.1160},
    "792032": {"desc": "HILO NYLON- BOBINA 200M", "precio": 5.4800},
    "792071": {"desc": "TWISTER METAL 2 ADH 75mm", "precio": 0.0538},
    "792301": {"desc": "BASE DE PLAS EXPOSITOR TRSP", "precio": 0.1840},
    "792421": {"desc": "GANCHO S METAL 24MM DIAM 2MM", "precio": 0.0215},
    "792425": {"desc": "ESSE 32MM BOUCLE DIA 6 & 14MM", "precio": 0.0360},
    "792427": {"desc": "GANCHO S METAL30MM DIAM 2MM", "precio": 0.0267},
    "792432": {"desc": "GANCHO S 36 MM 014", "precio": 0.0300},
    "792436": {"desc": "GANCHO S METAL ASYMETRICO 45MM", "precio": 0.0394},
    "792437": {"desc": "GANCHO S METAL ASYMETRICO 40MM", "precio": 0.0428},
    "792451": {"desc": "GANCHO S METAL 59MM DIAM 2MM", "precio": 0.0365},
    "792452": {"desc": "GANCHO S METAL 65MM DIAM 2,5MM", "precio": 0.0540},
    "792542": {"desc": "TWISTER PET 75MM-2 ADHESIVOS", "precio": 0.0460},
    "792546": {"desc": "WOBBLER PET 150MM 2 ADH", "precio": 0.0411},
    "792550": {"desc": "WOBBLER PET 150MM 2 ADH REMOV", "precio": 0.0613},
    "792570": {"desc": "MEGA TWISTER METAL 2 ADH", "precio": 0.0897},
    "792571": {"desc": "TWISTER METAL 2 ADH", "precio": 0.0400},
    "792573": {"desc": "TWISTER METAL 3 ADH", "precio": 0.0543},
    "792582": {"desc": "TWISTER MET 75MM 2 ADH EN HOJA", "precio": 0.0600},
    "793075": {"desc": "TWISTER 2 ADH CLEAN", "precio": 0.0650},
    "793240": {"desc": "1100 ALMOH AUTOADH MACHO-19mm", "precio": 15.6000},
    "793242": {"desc": "1100 ALMOH AUTOADH HEMBRA-19mm", "precio": 15.6000},
    "793249": {"desc": "1500ALMOH AUTOAD HEMBR 13 NEGR", "precio": 11.8000},
    "793250": {"desc": "1500ALMOH AUTOAD MACH 13 NEGR", "precio": 11.8000},
    "793301": {"desc": "PLETINA PVC ADH 20X20mm", "precio": 0.0382},
    "793303": {"desc": "PLETINA PVC ADH 20X40mm", "precio": 0.0680},
    "796007": {"desc": "TORNILLO Ø15mm MAXI 9mm BLCO", "precio": 0.0299},
    "796043": {"desc": "TORNILLO Ø28mm MAXI 22mm BLCO", "precio": 0.0534},
    "796307": {"desc": "TORNILLO Ø 15mm MAXI 9mm NEGRO", "precio": 0.0300},
    "796309": {"desc": "TORNILLO Ø28mm MAXI 15mm NEGRO", "precio": 0.0320},
    "796343": {"desc": "TORNILLO Ø28mm MAXI 22mm NEGRO", "precio": 0.0525},
    "796407": {"desc": "TORNILLO Ø15mm MAXI 9mm TRSP", "precio": 0.0294},
    "796409": {"desc": "TORNILLO Ø28 mm MAXI15 mm TRSP", "precio": 0.0325},
    "796443": {"desc": "TORNILLO Ø 28mm MAXI 22mm TRSP", "precio": 0.0570},
    "796445": {"desc": "TORNILLO Ø 28mm MAXI 38mm TRSP", "precio": 0.0597},
    "797133": {"desc": "GRIPADOR 2 ENTRADAS EN L 25mm", "precio": 0.0579},
    "797148": {"desc": "GRIPADOR T13mm LG 76mm ADH", "precio": 0.0821},
    "797150": {"desc": "GRIPADOR T 28mm LG 25mm ADH", "precio": 0.0398},
    "797193": {"desc": "GRIPADOR 2 ENTRADAS EN J", "precio": 0.1080},
    "797786": {"desc": "PINZA MULTI ANGULO", "precio": 0.1460},
    "797885": {"desc": "BRIDA NYLON 300MM", "precio": 0.0434},
    "797910": {"desc": "PISTOLA", "precio": 10.5000},
    "797911": {"desc": "SET DE 5 AGUJERAS", "precio": 7.8000},
    "797915": {"desc": "ATADURAS NYLON 40MM", "precio": 0.0020},
    "797917": {"desc": "ATADURAS NYLON 65MM", "precio": 0.0024},
    "797921": {"desc": "ATADURAS EXTR ESTR 125mm", "precio": 0.0037},
    "841201": {"desc": "PESCANTE MULTIMAG", "precio": 1.8000},
    "841211": {"desc": "PESCANTE MULTIMAG PLUS", "precio": 1.9400},
    "950101": {"desc": "GANCHO FONDO PERF SIMPLE 50MM", "precio": 0.1384},
    "950235": {"desc": "CABLE ACIER ANTIRROBO PLACA", "precio": 2.6000},
    "950341": {"desc": "PORTA VISUAL BASE MADERA - A5", "precio": 5.5000},
    "950790": {"desc": "SUPER VENTOSA CON TORNILLON", "precio": 3.0100},
    "142002": {"desc": "GANCHO UNIVERSAL SIMPLE 100mm", "precio": 0.1101},
    "145101": {"desc": "TIRA CROSS MERCH DBLE FLJ 780", "precio": 0.4424},
    "145103": {"desc": "TIRA CROSS MERCH PNZA METL 790", "precio": 2.3700},
    "145111": {"desc": "TIRA CROSSMERCH 600 PE85X100mm", "precio": 0.2830},
    "163401": {"desc": "PINZA PORTA ETIQ ARTICUL TRSP", "precio": 0.3474},
    "172012": {"desc": "GANCHO SUSPENSION +HILO 1,2M", "precio": 0.1500},
    "172078": {"desc": "GANCHO DOBLE METALICO 300mm", "precio": 0.0690},
    "950221": {"desc": "BASE GIRATORIA Ø 150 MM", "precio": 1.9400}
}
OPCIONES_FLEXICO = [f"{k} - {v['desc']}" for k, v in PRODUCTOS_FLEXICO.items()]

# =========================================================
# 3) PRECIOS BASE + RÍGIDOS ACTUALIZADOS
# =========================================================
PRECIOS_BASE = {
    "cartoncillo": {
        "Ninguno": {"precio_kg": 0.0, "gramaje": 0},
        "Reverso Gris": {"precio_kg": 0.96, "gramaje": 220},
        "Zenith": {"precio_kg": 1.55, "gramaje": 350},
        "Reverso Madera": {"precio_kg": 0.975, "gramaje": 400},
        "Folding Kraft": {"precio_kg": 1.90, "gramaje": 340},
        "Folding Blanco": {"precio_kg": 1.82, "gramaje": 350},
    },
    "planchas": {
        "Ninguna": {"C/C": 0.0, "peg": 0.0},
        "Microcanal / Canal 3": {"C/C": 0.702, "B/C": 0.725, "B/B": 0.805, "peg": 0.217},
        "Doble Micro / Doble Doble": {"C/C": 1.128, "B/C": 1.187, "B/B": 1.378, "peg": 0.263},
        "AC (Cuero/Cuero)": {"C/C": 2.505, "peg": 0.217},
    },
    "rigidos": {
        "Ninguno": {"precio_ud": 0.0, "w": 0, "h": 0},
        "PVC TRANSPARENTE 300 MICRAS": {"precio_ud": 1.80, "w": 1000, "h": 700},
        "PVC TRANSPARENTE 500 MICRAS": {"precio_ud": 2.99, "w": 1000, "h": 700},
        "PVC TRANSPARENTE 700 MICRAS": {"precio_ud": 4.22, "w": 1000, "h": 700},
        "PVC BLANCO MATE 300 MICRAS": {"precio_ud": 1.76, "w": 1000, "h": 700},
        "PVC BLANCO MATE 500 MICRAS": {"precio_ud": 2.94, "w": 1000, "h": 700},
        "PVC BLANCO MATE 700 MICRAS": {"precio_ud": 4.11, "w": 1000, "h": 700},
        "APET 300 MICRAS": {"precio_ud": 1.35, "w": 1000, "h": 700},
        "APET 500 MICRAS": {"precio_ud": 2.25, "w": 1000, "h": 700},
        "PET G 0,5mm": {"precio_ud": 8.87, "w": 1250, "h": 2050},
        "PET G 0,7mm": {"precio_ud": 11.22, "w": 1250, "h": 2050},
        "PET G 1mm": {"precio_ud": 13.61, "w": 1250, "h": 2050},
        "POLIPROPILENO COMPACTO BLANCO/ NATURAL 300 MICRAS": {"precio_ud": 1.00, "w": 1000, "h": 700},
        "POLIPROPILENO COMPACTO BLANCO/ NATURAL 500 MICRAS": {"precio_ud": 1.67, "w": 1000, "h": 700},
        "POLIPROPILENO COMPACTO BLANCO/ NATURAL 800 MICRAS": {"precio_ud": 2.67, "w": 1000, "h": 700},
        "COMPACTO 1,5 MM": {"precio_ud": 1.80, "w": 1050, "h": 750},
        "COMPACTO 2 MM": {"precio_ud": 2.15, "w": 1050, "h": 750},
        "COMPACTO 3 MM": {"precio_ud": 3.00, "w": 1050, "h": 750},
        "POLIPROPILENO CELULAR 3,5 MM": {"precio_ud": 15.00, "w": 3050, "h": 2050},
    },
    "peliculado": {
        "Sin Peliculado": 0.0,
        "Polipropileno": 0.26,
        "Poliéster brillo": 0.38,
        "Poliéster mate": 0.64,
    },
    "laminado_digital": 3.5,
    "extras_base": {
        "CINTA D/CARA": 0.26, "CINTA LOHMAN": 0.49, "CINTA GEL": 1.2,
        "GOMA TERMINALES": 0.079, "IMAN 20x2mm": 1.145, "TUBOS": 1.06,
        "REMACHES": 0.049, "VELCRO": 0.43, "PUNTO ADHESIVO": 0.08,
        "Soporte Balda Blanco": 0.08, "Soporte Balda Negro": 0.10
    },
    "troquelado": {
        "Pequeño (< 1000x700)": {"arranque": 48.19, "tiro": 0.06},
        "Mediano (Estándar)": {"arranque": 80.77, "tiro": 0.09},
        "Grande (> 1000x700)": {"arranque": 107.80, "tiro": 0.135}
    },
    # Stamping (película + calor). Similar a troquelado pero con consumible de película por superficie.
    "stamping": {"arreglo": 168.0, "pisada": 0.21, "pelicula_m2": 0.39},
    # Flexografía (coste fijo por plancha)
    "flexografia": {"arreglo": 180.0},
    "plotter": {"precio_hoja": 2.03}
}

FORMATOS_STD = {
    "Personalizado": (0, 0), "1600x1200": (1600, 1200), "1600x1100": (1600, 1100),
    "1400x1000": (1400, 1000), "1300x900": (1300, 900), "1200x800": (1200, 800),
    "1100x800": (1100, 800), "1000x700": (1000, 700), "900x650": (900, 650),
    "800x550": (800, 550), "700x500": (700, 500)
}

# =========================================================
# MERMAS (AUTO)
# =========================================================
def _tabla_merma_procesos_offset(hojas_netas: float) -> int:
    """Merma de procesos en OFFSET según tabla del cliente.

    IMPORTANTE:
    - La tabla se aplica sobre *hojas/pliegos netos* (ya ajustados por formato: Pliegos/Ud).
    - Redondea hacia arriba a hoja entera.
    """
    n = int(math.ceil(max(0.0, float(hojas_netas))))
    # Tabla (Desde incl., Hasta incl., Merma)
    tramos = [
        (0, 99, 20),
        (100, 149, 30),
        (150, 200, 40),
        (201, 600, 40),
        (601, 1000, 60),
        (1001, 1500, 60),
        (1501, 2000, 80),
        (2001, 3000, 80),
        (3001, 3500, 100),
        (3501, 5000, 100),
        (5001, 8000, 120),
        (8001, 10000, 120),
        (10001, 13000, 140),
        (13001, 15000, 140),
    ]
    for a, b, merma in tramos:
        if a <= n <= b:
            return int(merma)
    # A partir de 15001
    return 150


def _merma_impresion_offset_por_pasadas(n_tintas: int, barniz: bool) -> int:
    """Merma de impresión OFFSET por pasadas.

    Regla:
    - Base: 100 hojas (arranque mínimo).
    - Máquina 4 cuerpos: nº pasadas = ceil((tintas + (barniz?1:0)) / 4).
    - Merma = 100 + 50*(pasadas-1)

    Nota importante:
    - Si por UI/JSON llega n_tintas vacío/0, igualmente aplicamos el mínimo de 100 hojas.
    """
    # Robustez ante valores vacíos/None/strings
    try:
        tintas = int(n_tintas)
    except Exception:
        tintas = 0

    tintas = max(0, tintas)
    apps = max(1, tintas) + (1 if bool(barniz) else 0)  # mínimo 1 aplicación para garantizar arranque
    pasadas = int(math.ceil(apps / 4.0))
    return int(100 + 50 * max(0, pasadas - 1))


def calcular_mermas_estandar(n_uds: int, pliegos_por_ud: float = 1.0, es_digital: bool = False,
                            n_tintas: int = 4, barniz: bool = False) -> tuple[int, int]:
    """Devuelve (merma_proceso_hojas, merma_impresion_hojas).

    - Proceso (OFFSET): según tabla del cliente, aplicada a hojas netas = uds * pliegos_por_ud.
    - Impresión:
        * Offset: 100 + 50*(pasadas-1), con pasadas por (tintas + barniz) en grupos de 4.
        * Digital: mantiene comportamiento anterior (10 hojas) salvo que se fuerce manualmente.
    """
    uds = max(0, int(n_uds))
    pl = float(pliegos_por_ud) if pliegos_por_ud is not None else 1.0
    hojas_netas = uds * pl

    if es_digital:
        merma_proc = min(int(math.ceil(hojas_netas * 0.02)), 150)
        return int(merma_proc), 10

    merma_proc = _tabla_merma_procesos_offset(hojas_netas)
    merma_imp = _merma_impresion_offset_por_pasadas(n_tintas=n_tintas, barniz=barniz)
    return int(merma_proc), int(merma_imp)



# =========================================================
# MERMAS (AUTO TRACKERS) - para actualizar defaults cuando cambian tintas/formato
# =========================================================
def _ss_autoref_init() -> None:
    # Trackers para saber si el usuario ha sobreescrito un valor o sigue en automático
    if "mermas_proc_auto_ref" not in st.session_state or not isinstance(st.session_state.get("mermas_proc_auto_ref"), dict):
        st.session_state.mermas_proc_auto_ref = {}
    if "mermas_imp_auto_ref" not in st.session_state or not isinstance(st.session_state.get("mermas_imp_auto_ref"), dict):
        st.session_state.mermas_imp_auto_ref = {}

def _ss_autoupdate_merma_proc(pid: int, qty: int, new_default: int) -> None:
    """Si la merma de proceso actual coincide con el último default auto guardado, se actualiza al nuevo default."""
    _ss_autoref_init()
    pid_k = str(pid); qty_k = str(int(qty))
    cur = _ss_get_merma_proc(pid, qty, new_default)
    auto_pid = st.session_state.mermas_proc_auto_ref.setdefault(pid_k, {})
    old_auto = int(auto_pid.get(qty_k, new_default))
    # Solo actualizamos si el usuario no ha tocado (cur==old_auto) o si cur<=0 (legacy)
    if int(cur) <= 0 or int(cur) == int(old_auto):
        st.session_state.mermas_proc_manual.setdefault(pid_k, {})
        st.session_state.mermas_proc_manual[pid_k][qty_k] = int(new_default)
        auto_pid[qty_k] = int(new_default)

def _ss_autoupdate_merma_imp(pid: int, qty: int, lado: str, new_default: int) -> None:
    """Auto-update para merma de impresión por lado (cara/dorso)."""
    _ss_autoref_init()
    pid_k = str(pid); qty_k = str(int(qty)); lado_k = str(lado)
    cur = _ss_get_merma_imp(pid, qty, lado_k, new_default)
    auto_pid = st.session_state.mermas_imp_auto_ref.setdefault(pid_k, {})
    auto_qty = auto_pid.setdefault(qty_k, {})
    old_auto = int(auto_qty.get(lado_k, new_default))
    if int(cur) <= 0 or int(cur) == int(old_auto):
        st.session_state.mermas_imp_manual.setdefault(pid_k, {})
        st.session_state.mermas_imp_manual[pid_k].setdefault(qty_k, {"cara": 0, "dorso": 0})
        st.session_state.mermas_imp_manual[pid_k][qty_k][lado_k] = int(new_default)
        auto_qty[lado_k] = int(new_default)


def _ss_sync_merma_imp_widget(pid: int, qty: int, lado: str, widget_key: str, new_default: int) -> None:
    """Sincroniza la merma de impresión (cara/dorso) con el default calculado,
    respetando si el usuario la ha editado manualmente.

    Problema que resuelve:
    - Streamlit mantiene el valor del widget en session_state. Si el usuario cambia tintas/barniz,
      queremos recalcular el default (100+50*(pasadas-1)) y reflejarlo automáticamente *solo*
      si el usuario no había sobreescrito ese campo.

    Criterio de 'no sobreescrito':
    - El valor actual del widget o el valor almacenado coincide con el último default auto, o es <=0 (legacy).
    """
    _ss_autoref_init()
    pid_k = str(pid)
    qty_k = str(int(qty))
    lado_k = str(lado)

    auto_pid = st.session_state.mermas_imp_auto_ref.setdefault(pid_k, {})
    auto_qty = auto_pid.setdefault(qty_k, {})
    old_auto = int(auto_qty.get(lado_k, int(new_default)))

    try:
        cur_widget = int(st.session_state.get(widget_key, 0) or 0)
    except Exception:
        cur_widget = 0

    try:
        cur_stored = int(_ss_get_merma_imp(pid, int(qty), lado_k, int(new_default)) or 0)
    except Exception:
        cur_stored = 0

    # Si el usuario no ha tocado, actualizamos a new_default y guardamos la referencia auto
    if (cur_widget <= 0) or (cur_widget == old_auto) or (cur_stored <= 0) or (cur_stored == old_auto):
        st.session_state[widget_key] = int(new_default)
        st.session_state.mermas_imp_manual.setdefault(pid_k, {})
        st.session_state.mermas_imp_manual[pid_k].setdefault(qty_k, {"cara": 0, "dorso": 0})
        st.session_state.mermas_imp_manual[pid_k][qty_k][lado_k] = int(new_default)
        auto_qty[lado_k] = int(new_default)
# =========================================================
# MERMAS (SESSION HELPERS - compat JSON antiguo/nuevo)
# =========================================================
def _ss_get_merma_proc(pid: int, qty: int, default: int = 0) -> int:
    """Obtiene merma de procesos por forma+cantidad.
    Compatibilidad:
    - Nuevo: mermas_proc_manual = {pid: {qty: val}}
    - Antiguo: mermas_proc_manual = {qty: val}
    """
    d = st.session_state.get("mermas_proc_manual", {})
    try:
        pid_k = str(pid)
        qty_k = str(int(qty))
        if isinstance(d, dict):
            if pid_k in d and isinstance(d.get(pid_k), dict):
                sub = d[pid_k]
                return int(sub.get(qty_k, sub.get(int(qty), default)))
            if pid in d and isinstance(d.get(pid), dict):
                sub = d[pid]
                return int(sub.get(qty_k, sub.get(int(qty), default)))
            # legacy
            return int(d.get(qty_k, d.get(int(qty), default)))
    except Exception:
        pass
    return int(default)


def _ss_setdefault_merma_proc(pid: int, qty: int, value: int) -> None:
    d = st.session_state.get("mermas_proc_manual", {})
    if not isinstance(d, dict):
        d = {}
        st.session_state.mermas_proc_manual = d
    pid_k = str(pid)
    qty_k = str(int(qty))
    if pid_k not in d or not isinstance(d.get(pid_k), dict):
        d[pid_k] = {}
    sub = d[pid_k]
    if qty_k not in sub and int(qty) not in sub:
        sub[qty_k] = int(value)


def _ss_get_merma_imp(pid: int, qty: int, lado: str, default: int = 0) -> int:
    """Merma de impresión OFFSET por forma+cantidad+lado ('cara'/'dorso').

    Compatibilidad:
    - Nuevo: mermas_imp_manual = {pid: {qty: {'cara': x, 'dorso': y}}}
    - Intermedio: {pid: {qty: x}} -> aplica a ambos lados
    - Antiguo: {qty: x} -> aplica a ambos lados

    Nota:
    - Para evitar arrastres de proyectos antiguos, si hay un valor guardado <= 0 y el
      default calculado es > 0, se considera "no inicializado" y se devuelve el default.
      Además se actualiza en session_state para que el usuario lo vea/editable.
    """
    d = st.session_state.get("mermas_imp_manual", {})

    def _sanitize(v: object) -> int | None:
        try:
            iv = int(v)  # type: ignore[arg-type]
        except Exception:
            return None
        # Si está a 0/negativo y tenemos default > 0, lo tratamos como no inicializado
        if iv <= 0 and int(default) > 0:
            return None
        return iv

    try:
        pid_k = str(pid)
        qty_i = int(qty)
        qty_k = str(qty_i)

        # Intentamos leer en orden: nuevo -> intermedio -> legacy
        if isinstance(d, dict):
            # NUEVO / INTERMEDIO por pid
            for pk in (pid_k, pid):
                if pk in d and isinstance(d.get(pk), dict):
                    sub = d[pk]
                    v = sub.get(qty_k, sub.get(qty_i, None))
                    if isinstance(v, dict):
                        vv = _sanitize(v.get(lado, None))
                        if vv is not None:
                            return vv
                    else:
                        vv = _sanitize(v)
                        if vv is not None:
                            return vv

            # LEGACY global por cantidad
            v = d.get(qty_k, d.get(qty_i, None))
            if isinstance(v, dict):
                vv = _sanitize(v.get(lado, None))
                if vv is not None:
                    return vv
            else:
                vv = _sanitize(v)
                if vv is not None:
                    return vv
    except Exception:
        pass

    # Si llegamos aquí, devolvemos default y, si aplica, lo persistimos para que no quede a 0.
    try:
        if int(default) > 0:
            _ss_setdefault_merma_imp(int(pid), int(qty), str(lado), int(default))
    except Exception:
        pass
    return int(default)


def _ss_setdefault_merma_imp(pid: int, qty: int, lado: str, value: int) -> None:
    """Inicializa merma de impresión si no existe o si está a 0 en proyectos antiguos."""
    d = st.session_state.get("mermas_imp_manual", {})
    if not isinstance(d, dict):
        d = {}
        st.session_state.mermas_imp_manual = d
    pid_k = str(pid)
    qty_i = int(qty)
    qty_k = str(qty_i)
    if pid_k not in d or not isinstance(d.get(pid_k), dict):
        d[pid_k] = {}
    sub = d[pid_k]

    # Normalizamos a dict por lado ('cara'/'dorso')
    v = sub.get(qty_k, sub.get(qty_i, None))
    if not isinstance(v, dict):
        # Si no existe o venía como entero legacy, lo convertimos.
        if v is None:
            v = {"cara": 0, "dorso": 0}
        else:
            try:
                iv = int(v)
            except Exception:
                iv = 0
            v = {"cara": iv, "dorso": iv}
        sub[qty_k] = v

    # Si el valor actual está vacío/0/negativo, escribimos el default calculado
    try:
        current = v.get(lado, 0)
        current_i = int(current) if current not in (None, "") else 0
    except Exception:
        current_i = 0
    if current_i <= 0:
        v[lado] = int(value)
def parse_cantidades(s: str):
    if not s:
        return []
    out = []
    for x in s.split(","):
        x = x.strip()
        if x.isdigit() and int(x) > 0:
            out.append(int(x))
    return out


# =========================================================
# IMPRESIONES POR CANTIDAD (multi-tirada)
# =========================================================
def _split_equal(total: int, n: int) -> list:
    """Reparte 'total' en 'n' partes lo más igualadas posible."""
    if n <= 1 or total <= 0:
        return [int(total)] if total > 0 else []
    base = total // n
    rem = total % n
    partes = [base + (1 if i < rem else 0) for i in range(n)]
    return [p for p in partes if p > 0]

def _parse_partes_str(s: str) -> list:
    """Parsea '100+400+500' o '100, 400, 500' -> [100,400,500]."""
    if not s:
        return []
    nums = re.split(r"[,+\s]+", str(s).strip())
    out = []
    for x in nums:
        x = x.strip()
        if x.isdigit():
            v = int(x)
            if v > 0:
                out.append(v)
    return out

def obtener_partes_impresion_por_cantidad(q_total: int) -> list:
    """Devuelve el desglose de impresiones para una cantidad concreta.

    Regla:
    - Si no hay configuración: 1 impresión con q_total.
    - Si hay N impresiones: se reparte igual o se usa el desglose manual.
    - Siempre normaliza para que la suma sea q_total (fallback a reparto igual).
    """
    if q_total <= 0:
        return []
    cfg_all = st.session_state.get("impresiones_by_qty", {})
    if not isinstance(cfg_all, dict):
        return [int(q_total)]
    cfg = cfg_all.get(str(int(q_total)), None)
    if not isinstance(cfg, dict):
        return [int(q_total)]

    try:
        n = int(cfg.get("n", 1))
    except Exception:
        n = 1
    n = max(1, n)
    modo = str(cfg.get("modo", "igual")).lower().strip()
    partes = cfg.get("partes", [])
    if isinstance(partes, list):
        try:
            partes = [int(x) for x in partes if int(x) > 0]
        except Exception:
            partes = []
    else:
        partes = []

    if n == 1:
        return [int(q_total)]
    if modo == "manual" and partes and sum(partes) == int(q_total) and len(partes) == n:
        return partes

    # Fallback: reparto igual
    return _split_equal(int(q_total), int(n))


def obtener_partes_impresion_por_formato(pid: int, q_total: int) -> list:
    """Devuelve el desglose de impresiones para una cantidad concreta, PERO por formato (forma).

    - Se activa solo si el TIC (checkbox) del formato está activo.
    - Si no está activo, devuelve 1 impresión con q_total.
    - Si existe configuración por formato, la aplica.
    - Fallback de compatibilidad: si no hay cfg por formato, usa 'impresiones_by_qty' (global legacy).
    """
    if q_total <= 0:
        return []
    pid_key = str(int(pid))

    enabled_all = st.session_state.get("impresiones_by_qty_fmt_enabled", {})
    enabled = False
    if isinstance(enabled_all, dict):
        enabled = bool(enabled_all.get(pid_key, False))
    if not enabled:
        return [int(q_total)]

    cfg_fmt_all = st.session_state.get("impresiones_by_qty_fmt", {})
    if isinstance(cfg_fmt_all, dict):
        cfg_all = cfg_fmt_all.get(pid_key, {})
        if isinstance(cfg_all, dict):
            cfg = cfg_all.get(str(int(q_total)), None)
            if isinstance(cfg, dict):
                try:
                    n = int(cfg.get("n", 1))
                except Exception:
                    n = 1
                n = max(1, n)
                modo = str(cfg.get("modo", "igual")).lower().strip()
                partes = cfg.get("partes", [])
                if isinstance(partes, list):
                    try:
                        partes = [int(x) for x in partes if int(x) > 0]
                    except Exception:
                        partes = []
                else:
                    partes = []

                if n == 1:
                    return [int(q_total)]
                if modo == "manual" and partes and sum(partes) == int(q_total) and len(partes) == n:
                    return partes
                return _split_equal(int(q_total), int(n))

    # Legacy global (por si venimos de JSON antiguo)
    return obtener_partes_impresion_por_cantidad(int(q_total))
# =========================================================
# EMBALAJES (múltiples)
# =========================================================
TIPOS_EMB = ["Manual", "Embalaje Guaina (Automático)", "Embalaje en Plano", "Embalaje en Volumen"]
EMB_MATS = ["Canal 5", "D/D"]

def emb_mult(material: str) -> float:
    return 1.5 if material == "D/D" else 1.0

def embalaje_plano_unit(L_mm, W_mm, H_mm, Q):
    if Q <= 0 or L_mm <= 0 or W_mm <= 0 or H_mm <= 0:
        return 0.0, 0.0
    L = L_mm / 1000.0
    W = W_mm / 1000.0
    H = H_mm / 1000.0
    S = (L * W) + 2.0 * H * (L + W)
    P = ((152.0 + (20.0 * S)) / float(Q)) + 0.15 + (1.02 * S)
    return float(P), float(S)

def embalaje_volumen_unit(L_mm, A_mm, H_mm, Q):
    if Q <= 0 or L_mm <= 0 or A_mm <= 0 or H_mm <= 0:
        return 0.0, 0.0
    L = L_mm / 1000.0
    A = A_mm / 1000.0
    H = H_mm / 1000.0
    S = (2.0 * L + 2.0 * A + 0.05) * (H + A)
    P = ((20.0 + (8.0 * S)) / float(Q)) + (0.64 * S)
    return float(P), float(S)

def crear_embalaje_vacio(idx):
    return {
        "id": f"emb_{idx}",
        "nombre": f"Embalaje {idx+1}",
        "tipo": "Manual",
        "material": "Canal 5",
        "dims": {"L": 0.0, "W": 0.0, "H": 0.0},
        "costes": {}
    }

# =========================================================
# EXTERNOS (PROVEEDORES ESPORÁDICOS)
# =========================================================
EXT_TIPOS_COSTE = ["Unitario (€/ud)", "Total (€)"]

def crear_externo_vacio(idx: int):
    return {
        "id": f"ext_{idx}",
        "concepto": f"Externo {idx+1}",
        "modo": "Unitario (€/ud)",
        "costes": {}  # por cantidad -> float (€/ud o € total)
    }

# =========================================================
# RÍGIDOS - MERMA FIJA (si NO hay contracolado)
# =========================================================
def merma_rigido_fija(hojas_netas: int) -> int:
    if hojas_netas <= 10:
        return 0
    if hojas_netas <= 50:
        return 1
    if hojas_netas <= 100:
        return 2
    if hojas_netas <= 300:
        return 3
    if hojas_netas <= 500:
        return 5
    if hojas_netas <= 750:
        return 7
    return 10

# =========================================================
# IMPRESIÓN OFFSET - NUEVA TARIFA
# =========================================================
def coste_offset_por_tinta(n_hojas: int) -> float:
    """
    Regla verificada con ejemplo:
    - Mínimo 85€ por tinta.
    - Hojas extra hasta 500: 0,0875€/hoja/tinta (contando desde hoja 101).
    - A partir de 501: 120€/tinta (mantiene el comportamiento anterior base).
    - A partir de 2001: +0,015€/hoja/tinta (permite cuadrar 2500 → 510 con 4 tintas)
    """
    n = max(0, int(round(n_hojas)))
    if n <= 100:
        return 85.0
    if n <= 500:
        extra = (n - 100) * 0.0875
        return 85.0 + extra
    base = 120.0
    if n > 2000:
        base += (n - 2000) * 0.015
    return base

# =========================================================
# FORMAS
# =========================================================
def crear_forma_vacia(index):
    # ✅ Formas 1..n (no 0)
    return {
        "nombre": f"Forma {index}",
        "pliegos": 1.0,
        "w": 0, "h": 0,
        "pf": "Ninguno", "gf": 0,
        "pd": "Ninguno", "gd": 0,
        "tipo_base": "Ondulado/Cartón",
        "pl": "Ninguna", "ap": "B/C",
        "pl_dif": False, "pl_h": 0, "pl_w": 0,
        "mat_rigido": "Ninguno",
        "rig_manual": False,
        "rig_w": 0, "rig_h": 0, "rig_precio_ud": 0.0,
        "im": "No", "nt": 0, "ba": False,
        "im_d": "No", "nt_d": 0, "ba_d": False,
        "pel": "Sin Peliculado",
        "pel_d": "Sin Peliculado",
        "ld": False, "ld_d": False,
        "fr24": False,
        "fr24_rate": 0.05,
        "cor_default": "Troquelado",
        "cor_by_qty": {},
        "cobrar_arreglo": True,
        "pv_troquel": 0.0,
        "troquel_piezas": 0,
        "stamping": False,
        "stamping_w": 0,
        "stamping_h": 0,
        "stamping_cobrar_arreglo": True,
        "flexografia": False,
    }

def es_digital_en_proyecto(piezas_dict):
    for p in piezas_dict.values():
        if p.get("im") == "Digital" or p.get("im_d") == "Digital":
            return True
    return False

# =========================================================
# SESSION STATE INIT
# =========================================================
if "db_precios" not in st.session_state: st.session_state.db_precios = deepcopy(PRECIOS_BASE)

# =========================================================
# TARIFA MATERIA PRIMA (comparación vs proyectos importados)
# =========================================================
_TARIFA_MATERIA_PRIMA_CATS = ("cartoncillo", "planchas", "rigidos", "peliculado")

def _subset_materia_prima(db: dict) -> dict:
    """Devuelve un subconjunto estable de db_precios para comparar tarifas de materia prima.
    Solo incluye categorías de materia prima (no procesos).
    """
    out: dict = {}
    if not isinstance(db, dict):
        return out
    for cat in _TARIFA_MATERIA_PRIMA_CATS:
        v = db.get(cat, None)
        if isinstance(v, dict):
            out[cat] = deepcopy(v)
    return out


def _normalizar_mp_para_hash(v: object) -> object:
    """Normaliza valores para comparar tarifas con tolerancia a floats."""
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, (int, bool)) or v is None:
        return v
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return [_normalizar_mp_para_hash(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _normalizar_mp_para_hash(val) for k, val in v.items()}
    try:
        return round(float(v), 6)
    except Exception:
        return str(v)


def _hash_materia_prima(db: dict) -> str:
    """Hash estable (ordenado) del subconjunto de materia prima."""
    subset_norm = _normalizar_mp_para_hash(_subset_materia_prima(db))
    try:
        blob = json.dumps(subset_norm, sort_keys=True, ensure_ascii=False)
    except Exception:
        blob = str(subset_norm)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

def _aplicar_tarifa_actual_materia_prima() -> None:
    """Actualiza SOLO materia prima (cartoncillo/planchas/rigidos/peliculado) a la tarifa actual (PRECIOS_BASE).

    Importante:
    - NO reinicia el proyecto ni toca piezas/cantidades/extras/embalajes/externos.
    - Actualiza EN SITIO (in-place) para minimizar efectos colaterales en widgets que lean de db_precios.
    - Mantiene cualquier material "custom" que ya existiese en el proyecto.
    """
    db = st.session_state.get("db_precios")
    if not isinstance(db, dict):
        # Si por algún motivo viene corrupto, creamos un dict basado en lo actual para no perder claves.
        db = deepcopy(PRECIOS_BASE)
        st.session_state.db_precios = db

    base = PRECIOS_BASE  # referencia (no mutar)

    for cat in _TARIFA_MATERIA_PRIMA_CATS:
        base_cat = base.get(cat)
        if not isinstance(base_cat, dict):
            continue

        cur_cat = db.get(cat)
        if not isinstance(cur_cat, dict):
            cur_cat = {}
            db[cat] = cur_cat

        # Reemplazamos/actualizamos solo las entradas de la tarifa actual (manteniendo posibles claves extra del proyecto)
        for k, v in base_cat.items():
            cur_cat[k] = deepcopy(v)

    # Dejamos constancia de que ya está actualizado respecto a la tarifa actual
    st.session_state._tarifa_mp_import_hash = _hash_materia_prima(st.session_state.db_precios)
    st.session_state._tarifa_mp_mismatch = False

if "piezas_dict" not in st.session_state: st.session_state.piezas_dict = {1: crear_forma_vacia(1)}
if "lista_extras_grabados" not in st.session_state: st.session_state.lista_extras_grabados = []
if "embalajes" not in st.session_state: st.session_state.embalajes = [crear_embalaje_vacio(0)]
if "externos" not in st.session_state: st.session_state.externos = [crear_externo_vacio(0)]
if "mermas_imp_manual" not in st.session_state: st.session_state.mermas_imp_manual = {}
if "mermas_imp_digital_manual" not in st.session_state: st.session_state.mermas_imp_digital_manual = {}
if "mermas_proc_manual" not in st.session_state: st.session_state.mermas_proc_manual = {}
if "impresiones_by_qty" not in st.session_state: st.session_state.impresiones_by_qty = {}  # {str(cantidad): {"n": int, "modo": "igual"|"manual", "partes": [int,...]}}
if "impresiones_by_qty_fmt" not in st.session_state: st.session_state.impresiones_by_qty_fmt = {}  # {str(pid): {str(cantidad): {"n": int, "modo": "igual"|"manual", "partes": [int,...]}}}
if "impresiones_by_qty_fmt_enabled" not in st.session_state: st.session_state.impresiones_by_qty_fmt_enabled = {}  # {str(pid): bool}

if "brf" not in st.session_state: st.session_state.brf = ""
if "cli" not in st.session_state: st.session_state.cli = ""
if "desc" not in st.session_state: st.session_state.desc = ""
if "notas" not in st.session_state: st.session_state.notas = ""
if "cants_str_saved" not in st.session_state: st.session_state.cants_str_saved = ""

if "unidad_t" not in st.session_state: st.session_state.unidad_t = "Segundos"
if "t_input" not in st.session_state: st.session_state.t_input = 0.0

if "rell_enabled" not in st.session_state: st.session_state.rell_enabled = False
if "rell_t_input" not in st.session_state: st.session_state.rell_t_input = 0.0
if "arm_enabled" not in st.session_state: st.session_state.arm_enabled = False
if "arm_t_input" not in st.session_state: st.session_state.arm_t_input = 0.0

if "dif_ud" not in st.session_state: st.session_state.dif_ud = 0.091
if "dif_preset_sel" not in st.session_state: st.session_state.dif_preset_sel = "0,091 (standard)"
if "imp_fijo_pvp" not in st.session_state: st.session_state.imp_fijo_pvp = 500.0
if "repeticion_proyecto" not in st.session_state: st.session_state.repeticion_proyecto = False
if "imp_fijo_pvp_prev" not in st.session_state: st.session_state.imp_fijo_pvp_prev = None
if "margen" not in st.session_state: st.session_state.margen = 2.2
if "comercial_1" not in st.session_state: st.session_state.comercial_1 = ""
if "comercial_2" not in st.session_state: st.session_state.comercial_2 = ""
if "last_auto_margen" not in st.session_state: st.session_state.last_auto_margen = float(st.session_state.margen)


if "descuento_procesos" not in st.session_state: st.session_state.descuento_procesos = 0.0
if "margen_extras" not in st.session_state: st.session_state.margen_extras = 1.4
if "margen_embalajes" not in st.session_state: st.session_state.margen_embalajes = 1.4

if "db_descuentos" not in st.session_state:
    # Descuentos de compra por bloque (en %). Se aplican a los costes en cálculo.
    st.session_state.db_descuentos = {
        "cartoncillo": 0.0,
        "ondulado_rigidos": 0.0,
        "narba": 0.0,
    }


if "_last_import_hash" not in st.session_state: st.session_state._last_import_hash = None
if "_tarifa_mp_import_hash" not in st.session_state: st.session_state._tarifa_mp_import_hash = None
if "_tarifa_mp_mismatch" not in st.session_state: st.session_state._tarifa_mp_mismatch = False
if "_export_blob" not in st.session_state: st.session_state._export_blob = None
if "_export_filename" not in st.session_state: st.session_state._export_filename = "oferta.json"
if "_imported_compras_legible" not in st.session_state: st.session_state._imported_compras_legible = None
if "_imported_resumen_costes" not in st.session_state: st.session_state._imported_resumen_costes = None
if "_json_downloaded" not in st.session_state: st.session_state._json_downloaded = False
if "_json_downloaded_filename" not in st.session_state: st.session_state._json_downloaded_filename = ""

# =========================================================
# FIX IMPORT: PURGE KEYS DE WIDGETS
# =========================================================
def purge_widget_keys_for_import(lista_cants=None, piezas_ids=None, externos_len=0, embalajes_len=0, extras_len=0):
    """
    Streamlit prioriza st.session_state[widget_key] sobre value=.
    Al importar, limpiamos claves de widgets para que se recarguen desde el JSON.
    """
    if piezas_ids is None:
        piezas_ids = []
    if lista_cants is None:
        lista_cants = []

    base_prefixes = [
        "n_", "p_", "std_", "h_", "w_", "im_", "nt_", "ba_", "ld_", "pel_",
        "pf_", "gf_", "tb_", "pl_", "pldif_", "plh_", "plw_", "ap_",
        "rigman_", "rigwman_", "righman_", "rigpman_", "mrig_",
        "pd_", "gd_", "cor_def_", "arr_", "pvt_", "trqp_", "stamp_", "stampw_", "stamph_", "stamparr_", "flexo_", "im_d_", "nt_d_", "ba_d_", "ld_d_", "pel_d_"
    ]

    for pid in piezas_ids:
        for pref in base_prefixes:
            k = f"{pref}{pid}"
            if k in st.session_state:
                del st.session_state[k]

        for q in lista_cants:
            kq = f"cor_qty_{pid}_{q}"
            if kq in st.session_state:
                del st.session_state[kq]

        kdel = f"del_{pid}"
        if kdel in st.session_state:
            del st.session_state[kdel]

    for q in lista_cants:
        for k in [f"mi_{q}", f"mp_{q}"]:
            if k in st.session_state:
                del st.session_state[k]


    # Impresiones por cantidad (multi-tirada)
    for q in lista_cants:
        for k in [f"impn_{q}", f"impigual_{q}", f"impman_{q}"]:
            if k in st.session_state:
                del st.session_state[k]

    # Impresiones por cantidad (multi-tirada) - POR FORMATO
    for pid in list(st.session_state.get("piezas_dict", {}).keys()):
        for q in lista_cants:
            for k in [f"impact_{pid}", f"impn_{pid}_{q}", f"impigual_{pid}_{q}", f"impman_{pid}_{q}"]:
                if k in st.session_state:
                    del st.session_state[k]

    for i in range(max(0, extras_len)):
        for k in [f"exc_{i}", f"exq_{i}", f"exd_{i}"]:
            if k in st.session_state:
                del st.session_state[k]

    for ei in range(max(0, embalajes_len)):
        for k in [f"emb_name_{ei}", f"emb_tipo_{ei}", f"emb_mat_{ei}", f"embL_{ei}", f"embW_{ei}", f"embH_{ei}", f"emb_del_{ei}"]:
            if k in st.session_state:
                del st.session_state[k]
        for q in lista_cants:
            kq = f"embMan_{ei}_{q}"
            if kq in st.session_state:
                del st.session_state[kq]

    for xi in range(max(0, externos_len)):
        for k in [f"ext_con_{xi}", f"ext_modo_{xi}", f"ext_del_{xi}"]:
            if k in st.session_state:
                del st.session_state[k]
        for q in lista_cants:
            kq = f"ext_{xi}_{q}"
            if kq in st.session_state:
                del st.session_state[kq]

# =========================================================
# FIX IMPORT: SEED KEYS DE WIDGETS CON LO IMPORTADO (TODAS LAS FORMAS)
# =========================================================
def seed_widget_keys_from_import(lista_cants, piezas_dict):
    """
    Streamlit prioriza st.session_state[widget_key] sobre value=.
    Sembramos las keys de widgets con los valores importados para que NO se pierdan.
    """
    for pid, p in piezas_dict.items():
        st.session_state[f"n_{pid}"] = p.get("nombre", f"Forma {pid}")
        st.session_state[f"p_{pid}"] = float(p.get("pliegos", 1.0))

        st.session_state[f"h_{pid}"] = int(p.get("h", 0))
        st.session_state[f"w_{pid}"] = int(p.get("w", 0))

        st.session_state[f"im_{pid}"] = p.get("im", "No")
        st.session_state[f"nt_{pid}"] = int(p.get("nt", 0))
        st.session_state[f"ba_{pid}"] = bool(p.get("ba", False))
        st.session_state[f"ld_{pid}"] = bool(p.get("ld", False))
        st.session_state[f"pel_{pid}"] = p.get("pel", "Sin Peliculado")

        st.session_state[f"pf_{pid}"] = p.get("pf", "Ninguno")
        st.session_state[f"gf_{pid}"] = int(p.get("gf", 0))

        st.session_state[f"tb_{pid}"] = p.get("tipo_base", "Ondulado/Cartón")
        st.session_state[f"pl_{pid}"] = p.get("pl", "Ninguna")
        st.session_state[f"ap_{pid}"] = p.get("ap", "B/C")
        st.session_state[f"pldif_{pid}"] = bool(p.get("pl_dif", False))
        st.session_state[f"plh_{pid}"] = int(p.get("pl_h", p.get("h", 0)))
        st.session_state[f"plw_{pid}"] = int(p.get("pl_w", p.get("w", 0)))

        st.session_state[f"mrig_{pid}"] = p.get("mat_rigido", "Ninguno")
        st.session_state[f"rigman_{pid}"] = bool(p.get("rig_manual", False))
        st.session_state[f"rigwman_{pid}"] = int(p.get("rig_w", 0))
        st.session_state[f"righman_{pid}"] = int(p.get("rig_h", 0))
        st.session_state[f"rigpman_{pid}"] = float(p.get("rig_precio_ud", 0.0))

        st.session_state[f"pd_{pid}"] = p.get("pd", "Ninguno")
        st.session_state[f"gd_{pid}"] = int(p.get("gd", 0))

        st.session_state[f"cor_def_{pid}"] = p.get("cor_default", "Troquelado")
        if isinstance(p.get("cor_by_qty", {}), dict):
            for q in lista_cants:
                st.session_state[f"cor_qty_{pid}_{q}"] = p["cor_by_qty"].get(str(q), p.get("cor_default", "Troquelado"))

        st.session_state[f"arr_{pid}"] = bool(p.get("cobrar_arreglo", True))
        st.session_state[f"pvt_{pid}"] = float(p.get("pv_troquel", 0.0))
        st.session_state[f"stamp_{pid}"] = bool(p.get("stamping", False))
        st.session_state[f"stampw_{pid}"] = int(p.get("stamping_w", 0))
        st.session_state[f"stamph_{pid}"] = int(p.get("stamping_h", 0))
        st.session_state[f"stamparr_{pid}"] = bool(p.get("stamping_cobrar_arreglo", True))
        st.session_state[f"flexo_{pid}"] = bool(p.get("flexografia", False))
        st.session_state[f"trqp_{pid}"] = int(p.get("troquel_piezas", 0) or 0)

        st.session_state[f"im_d_{pid}"] = p.get("im_d", "No")
        st.session_state[f"nt_d_{pid}"] = int(p.get("nt_d", 0))
        st.session_state[f"ba_d_{pid}"] = bool(p.get("ba_d", False))
        st.session_state[f"ld_d_{pid}"] = bool(p.get("ld_d", False))
        st.session_state[f"pel_d_{pid}"] = p.get("pel_d", "Sin Peliculado")
    # Impresiones por cantidad (multi-tirada)
    cfg_all = st.session_state.get("impresiones_by_qty", {})
    if not isinstance(cfg_all, dict):
        cfg_all = {}
    for q in lista_cants:
        cfg = cfg_all.get(str(int(q)), {}) if isinstance(cfg_all.get(str(int(q)), {}), dict) else {}
        try:
            n = int(cfg.get("n", 1))
        except Exception:
            n = 1
        n = max(1, n)
        modo = str(cfg.get("modo", "igual")).lower().strip()
        partes = cfg.get("partes", [])
        if not isinstance(partes, list):
            partes = []
        st.session_state[f"impn_{q}"] = n
        st.session_state[f"impigual_{q}"] = (modo != "manual")
        if modo == "manual" and partes:
            try:
                st.session_state[f"impman_{q}"] = "+".join(str(int(x)) for x in partes)
            except Exception:
                st.session_state[f"impman_{q}"] = ""
        else:
            st.session_state.setdefault(f"impman_{q}", "")

    # Impresiones por cantidad (multi-tirada) - POR FORMATO (si viene en JSON)
    cfg_fmt_all = st.session_state.get("impresiones_by_qty_fmt", {})
    en_all = st.session_state.get("impresiones_by_qty_fmt_enabled", {})
    if isinstance(cfg_fmt_all, dict) and isinstance(en_all, dict):
        for pid, _p in piezas_dict.items():
            pid_key = str(int(pid))
            st.session_state[f"impact_{pid}"] = bool(en_all.get(pid_key, False))
            cfg_fmt = cfg_fmt_all.get(pid_key, {}) if isinstance(cfg_fmt_all.get(pid_key, {}), dict) else {}
            for q in lista_cants:
                cfg = cfg_fmt.get(str(int(q)), {}) if isinstance(cfg_fmt.get(str(int(q)), {}), dict) else {}
                try:
                    n = int(cfg.get("n", 1))
                except Exception:
                    n = 1
                n = max(1, n)
                modo = str(cfg.get("modo", "igual")).lower().strip()
                partes = cfg.get("partes", [])
                if not isinstance(partes, list):
                    partes = []
                st.session_state[f"impn_{pid}_{q}"] = n
                st.session_state[f"impigual_{pid}_{q}"] = (modo != "manual")
                if modo == "manual" and partes:
                    try:
                        st.session_state[f"impman_{pid}_{q}"] = "+".join(str(int(x)) for x in partes)
                    except Exception:
                        st.session_state[f"impman_{pid}_{q}"] = ""
                else:
                    st.session_state.setdefault(f"impman_{pid}_{q}", "")


# =========================================================
# IMPORT NORMALIZADO (ROBUSTO): GARANTIZA QUE SE CARGAN TODOS LOS CAMPOS
# =========================================================
def _coerce_bool(x, default=False):
    try:
        return bool(x)
    except:
        return default

def _coerce_int(x, default=0):
    try:
        return int(float(x))
    except:
        return default

def _coerce_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default

def _normalizar_pieza_dict(pid: int, v: dict):
    base = crear_forma_vacia(pid)
    if isinstance(v, dict):
        base.update(v)

    base["nombre"] = str(base.get("nombre", f"Forma {pid}"))
    base["pliegos"] = _coerce_float(base.get("pliegos", 1.0), 1.0)

    base["w"] = _coerce_int(base.get("w", 0), 0)
    base["h"] = _coerce_int(base.get("h", 0), 0)

    base["pf"] = str(base.get("pf", "Ninguno"))
    base["gf"] = _coerce_int(base.get("gf", 0), 0)
    base["pd"] = str(base.get("pd", "Ninguno"))
    base["gd"] = _coerce_int(base.get("gd", 0), 0)

    base["tipo_base"] = str(base.get("tipo_base", "Ondulado/Cartón"))

    # ✅ blindaje plancha / calidad
    base["pl"] = str(base.get("pl", "Ninguna"))
    base["ap"] = str(base.get("ap", "B/C"))
    base["pl_dif"] = _coerce_bool(base.get("pl_dif", False), False)
    base["pl_h"] = _coerce_int(base.get("pl_h", base.get("h", 0)), 0)
    base["pl_w"] = _coerce_int(base.get("pl_w", base.get("w", 0)), 0)

    base["mat_rigido"] = str(base.get("mat_rigido", "Ninguno"))
    base["rig_manual"] = _coerce_bool(base.get("rig_manual", False), False)
    base["rig_w"] = _coerce_int(base.get("rig_w", 0), 0)
    base["rig_h"] = _coerce_int(base.get("rig_h", 0), 0)
    base["rig_precio_ud"] = _coerce_float(base.get("rig_precio_ud", 0.0), 0.0)

    base["im"] = str(base.get("im", "No"))
    base["nt"] = _coerce_int(base.get("nt", 0), 0)
    base["ba"] = _coerce_bool(base.get("ba", False), False)
    base["ld"] = _coerce_bool(base.get("ld", False), False)
    base["pel"] = str(base.get("pel", "Sin Peliculado"))

    base["im_d"] = str(base.get("im_d", "No"))
    base["nt_d"] = _coerce_int(base.get("nt_d", 0), 0)
    base["ba_d"] = _coerce_bool(base.get("ba_d", False), False)
    base["ld_d"] = _coerce_bool(base.get("ld_d", False), False)
    base["pel_d"] = str(base.get("pel_d", "Sin Peliculado"))

    base["cor_default"] = str(base.get("cor_default", "Troquelado"))
    _allowed_cor = {"Troquelado", "Plotter", "Sin corte"}
    if base["cor_default"] not in _allowed_cor:
        base["cor_default"] = "Troquelado"
    if not isinstance(base.get("cor_by_qty", {}), dict):
        base["cor_by_qty"] = {}
    else:
        base["cor_by_qty"] = {
            str(k): (str(vv) if str(vv) in _allowed_cor else base["cor_default"])
            for k, vv in base["cor_by_qty"].items()
        }
    base["cobrar_arreglo"] = _coerce_bool(base.get("cobrar_arreglo", True), True)
    base["pv_troquel"] = _coerce_float(base.get("pv_troquel", 0.0), 0.0)
    base["stamping"] = _coerce_bool(base.get("stamping", False), False)
    base["stamping_w"] = _coerce_int(base.get("stamping_w", 0), 0)
    base["stamping_h"] = _coerce_int(base.get("stamping_h", 0), 0)
    base["stamping_cobrar_arreglo"] = _coerce_bool(base.get("stamping_cobrar_arreglo", True), True)

    base["flexografia"] = _coerce_bool(base.get("flexografia", False), False)

    base["troquel_piezas"] = max(0, _coerce_int(base.get("troquel_piezas", 0), 0))

    return base

def normalizar_import(di: dict):
    prev_cants = parse_cantidades(st.session_state.get("cants_str_saved", ""))
    prev_piezas_ids = list(st.session_state.get("piezas_dict", {}).keys()) if isinstance(st.session_state.get("piezas_dict", None), dict) else []
    prev_extras_len = len(st.session_state.get("lista_extras_grabados", [])) if isinstance(st.session_state.get("lista_extras_grabados", None), list) else 0
    prev_emb_len = len(st.session_state.get("embalajes", [])) if isinstance(st.session_state.get("embalajes", None), list) else 0
    prev_ext_len = len(st.session_state.get("externos", [])) if isinstance(st.session_state.get("externos", None), list) else 0

    st.session_state.brf = str(di.get("brf", st.session_state.brf))
    st.session_state.comercial_1 = str(di.get("comercial_1", st.session_state.get("comercial_1", "")))
    st.session_state.comercial_2 = str(di.get("comercial_2", st.session_state.get("comercial_2", "")))
    st.session_state.cli = str(di.get("cli", st.session_state.cli))
    st.session_state.desc = str(di.get("desc", st.session_state.desc))
    st.session_state.notas = str(di.get("notas", st.session_state.get("notas","")))
    if isinstance(di.get("cants_str", None), str):
        st.session_state.cants_str_saved = di["cants_str"]

    manip = di.get("manip", {})
    if isinstance(manip, dict):
        if "unidad_t" in manip:
            st.session_state.unidad_t = str(manip["unidad_t"])
        if "t_input" in manip:
            st.session_state.t_input = float(manip["t_input"])

        # ✅ Opcionales (compatibles hacia atrás)
        rell = manip.get("rellenado", {})
        if isinstance(rell, dict):
            if "enabled" in rell:
                st.session_state.rell_enabled = bool(rell.get("enabled", False))
            if "t_input" in rell:
                st.session_state.rell_t_input = float(rell.get("t_input", 0.0))
        arm = manip.get("armado", {})
        if isinstance(arm, dict):
            if "enabled" in arm:
                st.session_state.arm_enabled = bool(arm.get("enabled", False))
            if "t_input" in arm:
                st.session_state.arm_t_input = float(arm.get("t_input", 0.0))

    # ✅ FIX: al importar, limpiamos keys de widgets globales para que Streamlit no
    # fuerce valores antiguos (p.ej. preset dificultad "standard").
    for _k in ("dif_preset_sel", "dif_ud", "repeticion_proyecto", "imp_fijo_pvp"):
        if _k in st.session_state:
            del st.session_state[_k]

    params = di.get("params", {})
    if isinstance(params, dict):
        if "dif_ud" in params: st.session_state.dif_ud = float(params["dif_ud"])
        # ✅ Importar también el preset visible (para que no vuelva a "standard" por culpa del widget)
        if "dif_preset_sel" in params:
            st.session_state.dif_preset_sel = str(params.get("dif_preset_sel", ""))
        else:
            # Compat: si no viene, intentamos inferirlo a partir de dif_ud
            try:
                _v = float(st.session_state.dif_ud)
            except Exception:
                _v = 0.091
            _presets = [("0,000", 0.0), ("0,020", 0.02), ("0,050", 0.05), ("0,091 (standard)", 0.091), ("0,120", 0.12), ("0,150", 0.15)]
            _label = "Personalizado"
            for _l, _vv in _presets:
                if abs(float(_vv) - float(_v)) < 1e-9:
                    _label = _l
                    break
            st.session_state.dif_preset_sel = _label

        if "repeticion_proyecto" in params:
            st.session_state.repeticion_proyecto = bool(params.get("repeticion_proyecto", False))
        if "imp_fijo_pvp" in params: st.session_state.imp_fijo_pvp = float(params["imp_fijo_pvp"])
        # Si es repetición de proyecto, el desarrollo se anula.
        if bool(st.session_state.get("repeticion_proyecto", False)):
            st.session_state.imp_fijo_pvp = 0.0
        if "margen" in params: st.session_state.margen = float(params["margen"])
        # ✅ Nuevos (compatibles hacia atrás)
        if "descuento_procesos" in params: st.session_state.descuento_procesos = float(params["descuento_procesos"])
        if "margen_extras" in params: st.session_state.margen_extras = float(params["margen_extras"])
        if "margen_embalajes" in params: st.session_state.margen_embalajes = float(params["margen_embalajes"])


    if isinstance(di.get("db_precios", None), dict):
        # Importamos SIEMPRE la base de precios del proyecto (compatibilidad hacia atrás)
        st.session_state.db_precios = di["db_precios"]

        # ✅ Aviso de tarifa: si el proyecto importado trae materia prima distinta a la tarifa actual
        try:
            st.session_state._tarifa_mp_import_hash = _hash_materia_prima(st.session_state.db_precios)
            st.session_state._tarifa_mp_mismatch = (st.session_state._tarifa_mp_import_hash != _hash_materia_prima(PRECIOS_BASE))
        except Exception:
            st.session_state._tarifa_mp_import_hash = None
            st.session_state._tarifa_mp_mismatch = False
    else:
        # JSON antiguo sin db_precios: usamos la tarifa actual, pero dejamos flags coherentes
        st.session_state._tarifa_mp_import_hash = None
        st.session_state._tarifa_mp_mismatch = False

    # ✅ Descuentos por bloque (si vienen en el JSON)
    if isinstance(di.get("db_descuentos", None), dict):
        cur = st.session_state.get("db_descuentos", {})
        if not isinstance(cur, dict):
            cur = {}
        for k, v in di["db_descuentos"].items():
            try:
                cur[str(k)] = float(v)
            except Exception:
                pass
        for k0 in ["cartoncillo", "ondulado_rigidos", "narba"]:
            cur.setdefault(k0, 0.0)
        st.session_state.db_descuentos = cur

    lista_cants_import = parse_cantidades(st.session_state.cants_str_saved)
    cants_all = sorted(set(prev_cants + lista_cants_import))

    raw = []
    piezas_in = di.get("piezas", None)

    # ✅ Import robusto:
    # - Si el JSON trae piezas como dict ({"1": {...}, "6": {...}}), mantenemos SUS IDs
    #   para que "Forma 6" siga siendo la 6 (y no se renumere).
    # - Si viene como lista, seguimos usando 1..n.
    if isinstance(piezas_in, dict):
        for k, v in piezas_in.items():
            try:
                ik = int(k)
            except:
                continue
            if isinstance(v, dict):
                raw.append((ik, v))
        raw.sort(key=lambda x: x[0])
    elif isinstance(piezas_in, list):
        for idx, v in enumerate(piezas_in, start=1):
            if isinstance(v, dict):
                raw.append((idx, v))

    new_piezas = {1: crear_forma_vacia(1)}
    new_ids = [1]
    if raw:
        new_piezas = {}
        new_ids = []
        for pid, v in raw:
            new_piezas[pid] = _normalizar_pieza_dict(pid, v)
            new_ids.append(pid)

    piezas_all = sorted(set(prev_piezas_ids + new_ids))

    # ✅ Snapshots de costes (para preservar proyectos antiguos con precios vendidos)
    if isinstance(di.get("compras_legible", None), dict):
        st.session_state._imported_compras_legible = di["compras_legible"]
    if isinstance(di.get("resumen_costes", None), dict):
        st.session_state._imported_resumen_costes = di["resumen_costes"]


    purge_widget_keys_for_import(
        lista_cants=cants_all,
        piezas_ids=piezas_all,
        externos_len=max(prev_ext_len, len(di.get("externos", []) if isinstance(di.get("externos", None), list) else []), 1),
        embalajes_len=max(prev_emb_len, len(di.get("embalajes", []) if isinstance(di.get("embalajes", None), list) else []), 1),
        extras_len=max(prev_extras_len, len(di.get("extras", []) if isinstance(di.get("extras", None), list) else []), 0),
    )

    st.session_state.piezas_dict = new_piezas if new_piezas else {1: crear_forma_vacia(1)}

    if isinstance(di.get("extras", None), list):
        st.session_state.lista_extras_grabados = di["extras"]

    if isinstance(di.get("mermas_imp", None), dict):
        # Compatibilidad:
        # - Nuevo: {pid: {qty: {'cara':x,'dorso':y}}}
        # - Antiguo: {qty: x}
        mi = di.get("mermas_imp", {})
        if mi and all(isinstance(v, dict) for v in mi.values()):
            # asumimos nuevo por forma
            out = {}
            for pid_k, sub in mi.items():
                if not isinstance(sub, dict):
                    continue
                out[str(pid_k)] = {}
                for qk, vv in sub.items():
                    if isinstance(vv, dict):
                        out[str(pid_k)][str(qk)] = {
                            "cara": int(vv.get("cara", 0)),
                            "dorso": int(vv.get("dorso", 0)),
                        }
                    else:
                        # valor único -> ambos lados
                        out[str(pid_k)][str(qk)] = {"cara": int(vv), "dorso": int(vv)}
            st.session_state.mermas_imp_manual = out
        else:
            # legacy por cantidad
            st.session_state.mermas_imp_manual = {int(k): int(v) for k, v in mi.items() if str(k).isdigit()}

    if isinstance(di.get("mermas_imp_digital", None), dict):
        st.session_state.mermas_imp_digital_manual = {int(k): int(v) for k, v in di["mermas_imp_digital"].items()}
    if isinstance(di.get("mermas_proc", None), dict):
        # Compatibilidad:
        # - Nuevo: {pid: {qty: val}}
        # - Antiguo: {qty: val}
        mp = di.get("mermas_proc", {})
        if mp and all(isinstance(v, dict) for v in mp.values()):
            out = {}
            for pid_k, sub in mp.items():
                if not isinstance(sub, dict):
                    continue
                out[str(pid_k)] = {str(qk): int(vv) for qk, vv in sub.items()}
            st.session_state.mermas_proc_manual = out
        else:
            st.session_state.mermas_proc_manual = {int(k): int(v) for k, v in mp.items() if str(k).isdigit()}
# Impresiones por cantidad (multi-tirada) - opcional en JSON
    if isinstance(di.get("impresiones_by_qty", None), dict):
        cfg_new = {}
        for k, v in di["impresiones_by_qty"].items():
            try:
                qk = int(k)
            except Exception:
                continue
            if not isinstance(v, dict):
                continue
            try:
                n = int(v.get("n", 1))
            except Exception:
                n = 1
            n = max(1, n)
            modo = str(v.get("modo", "igual")).lower().strip()
            partes = v.get("partes", [])
            if isinstance(partes, list):
                try:
                    partes = [int(x) for x in partes if int(x) > 0]
                except Exception:
                    partes = []
            else:
                partes = []
            if n == 1:
                modo = "igual"
                partes = [qk]
            elif modo == "manual" and (not partes or sum(partes) != qk or len(partes) != n):
                # Normalizamos a reparto igual si el manual no cuadra
                modo = "igual"
                partes = _split_equal(qk, n)
            elif modo != "manual":
                partes = _split_equal(qk, n)
            cfg_new[str(qk)] = {"n": n, "modo": modo, "partes": partes}
        st.session_state.impresiones_by_qty = cfg_new


    # Impresiones por cantidad (multi-tirada) - POR FORMATO (nuevo, opcional en JSON)
    if isinstance(di.get("impresiones_by_qty_fmt", None), dict):
        cfg_fmt_new = {}
        for pid_k, cfg_pid in di["impresiones_by_qty_fmt"].items():
            try:
                pid_int = int(pid_k)
            except Exception:
                continue
            if not isinstance(cfg_pid, dict):
                continue
            cfg_q_new = {}
            for k, v in cfg_pid.items():
                try:
                    qk = int(k)
                except Exception:
                    continue
                if not isinstance(v, dict):
                    continue
                try:
                    n = int(v.get("n", 1))
                except Exception:
                    n = 1
                n = max(1, n)
                modo = str(v.get("modo", "igual")).lower().strip()
                partes = v.get("partes", [])
                if isinstance(partes, list):
                    try:
                        partes = [int(x) for x in partes if int(x) > 0]
                    except Exception:
                        partes = []
                else:
                    partes = []
                if n == 1:
                    modo = "igual"
                    partes = [qk]
                elif modo == "manual" and (not partes or sum(partes) != qk or len(partes) != n):
                    modo = "igual"
                    partes = _split_equal(qk, n)
                elif modo != "manual":
                    partes = _split_equal(qk, n)
                cfg_q_new[str(qk)] = {"n": n, "modo": modo, "partes": partes}
            cfg_fmt_new[str(pid_int)] = cfg_q_new
        st.session_state.impresiones_by_qty_fmt = cfg_fmt_new

    if isinstance(di.get("impresiones_by_qty_fmt_enabled", None), dict):
        en_new = {}
        for k, v in di["impresiones_by_qty_fmt_enabled"].items():
            try:
                pid_int = int(k)
            except Exception:
                continue
            en_new[str(pid_int)] = bool(v)
        st.session_state.impresiones_by_qty_fmt_enabled = en_new

    emb = di.get("embalajes", None)
    if isinstance(emb, list) and len(emb) > 0:
        new_list = []
        for idx, e in enumerate(emb):
            if not isinstance(e, dict):
                continue
            base = crear_embalaje_vacio(idx)
            base["id"] = str(e.get("id", base["id"]))
            base["nombre"] = str(e.get("nombre", base["nombre"]))
            base["tipo"] = str(e.get("tipo", base["tipo"]))
            base["material"] = str(e.get("material", base["material"]))
            dims_in = e.get("dims", {}) if isinstance(e.get("dims", None), dict) else {}
            base["dims"] = {
                "L": _coerce_float(dims_in.get("L", 0.0), 0.0),
                "W": _coerce_float(dims_in.get("W", 0.0), 0.0),
                "H": _coerce_float(dims_in.get("H", 0.0), 0.0),
            }
            if isinstance(e.get("costes", None), dict):
                costes_new = {}
                for k, v in e["costes"].items():
                    try:
                        kk = int(float(k))
                    except Exception:
                        continue
                    try:
                        vv = float(v)
                    except Exception:
                        vv = 0.0
                    costes_new[kk] = vv
                base["costes"] = costes_new
            new_list.append(base)
        st.session_state.embalajes = new_list if new_list else [crear_embalaje_vacio(0)]
    else:
        st.session_state.embalajes = [crear_embalaje_vacio(0)]

    ext = di.get("externos", None)
    if isinstance(ext, list) and len(ext) > 0:
        new_ext = []
        for idx, e in enumerate(ext):
            if not isinstance(e, dict):
                continue
            base = crear_externo_vacio(idx)
            base["id"] = str(e.get("id", base["id"]))
            base["concepto"] = str(e.get("concepto", base["concepto"]))
            base["modo"] = str(e.get("modo", base["modo"]))
            if isinstance(e.get("costes", None), dict):
                base["costes"] = {int(k): float(v) for k, v in e["costes"].items()}
            new_ext.append(base)
        st.session_state.externos = new_ext if new_ext else [crear_externo_vacio(0)]
    else:
        if "externos" not in st.session_state or not st.session_state.externos:
            st.session_state.externos = [crear_externo_vacio(0)]

    purge_widget_keys_for_import(
        lista_cants=lista_cants_import,
        piezas_ids=list(st.session_state.piezas_dict.keys()),
        externos_len=len(st.session_state.externos),
        embalajes_len=len(st.session_state.embalajes),
        extras_len=len(st.session_state.lista_extras_grabados),
    )

    seed_widget_keys_from_import(
        lista_cants=lista_cants_import,
        piezas_dict=st.session_state.piezas_dict
    )

# =========================================================
# EXPORT ROBUSTO
# =========================================================
def construir_export(resumen_compra=None, resumen_costes=None):
    piezas_out = {}
    for pid, p in st.session_state.piezas_dict.items():
        piezas_out[str(int(pid))] = deepcopy(p)

    # Comercial: exportamos el número si es interpretable (p.ej. "Comercial 52" -> "52").
    # Mantiene compatibilidad: si no se puede interpretar, se exporta el texto tal cual.
    _c1_raw = st.session_state.get("comercial_1", "")
    _c2_raw = st.session_state.get("comercial_2", "")
    _c1_num = _parse_comercial_num(_c1_raw)
    _c2_num = _parse_comercial_num(_c2_raw)

    c1_out = (str(_c1_num) if _c1_num is not None else str(_c1_raw or ""))
    c2_out = (str(_c2_num) if _c2_num is not None else str(_c2_raw or ""))

    data = {
        "brf": st.session_state.brf,
        "comercial_1": c1_out,
        "comercial_2": c2_out,
        "cli": st.session_state.cli,
        "desc": st.session_state.desc,
        "notas": st.session_state.get("notas",""),
        "_schema": {"app": "MAINSA ADMIN V44", "piezas_index_base": 1},
        "cants_str": st.session_state.cants_str_saved,
        "manip": {"unidad_t": st.session_state.unidad_t, "t_input": float(st.session_state.t_input), "rellenado": {"enabled": bool(st.session_state.rell_enabled), "t_input": float(st.session_state.rell_t_input)}, "armado": {"enabled": bool(st.session_state.arm_enabled), "t_input": float(st.session_state.arm_t_input)}},
        "params": {"dif_ud": float(st.session_state.dif_ud), "dif_preset_sel": str(st.session_state.get("dif_preset_sel","")), "repeticion_proyecto": bool(st.session_state.get("repeticion_proyecto", False)), "imp_fijo_pvp": float(st.session_state.imp_fijo_pvp), "margen": float(st.session_state.margen), "descuento_procesos": float(st.session_state.descuento_procesos), "margen_extras": float(st.session_state.margen_extras), "margen_embalajes": float(st.session_state.margen_embalajes)},
        "db_precios": deepcopy(st.session_state.db_precios),
        "db_descuentos": deepcopy(st.session_state.db_descuentos),
        "piezas": piezas_out,
        "extras": deepcopy(st.session_state.lista_extras_grabados),
        "embalajes": deepcopy(st.session_state.embalajes),
        "externos": deepcopy(st.session_state.externos),
        "mermas_imp": deepcopy(st.session_state.mermas_imp_manual),
        "mermas_imp_digital": deepcopy(st.session_state.mermas_imp_digital_manual),
        "mermas_proc": deepcopy(st.session_state.mermas_proc_manual),
        "impresiones_by_qty": deepcopy(st.session_state.get("impresiones_by_qty", {})),
        "impresiones_by_qty_fmt": deepcopy(st.session_state.get("impresiones_by_qty_fmt", {})),
        "impresiones_by_qty_fmt_enabled": deepcopy(st.session_state.get("impresiones_by_qty_fmt_enabled", {})),
    }
    if resumen_compra is not None:
        data["compras_legible"] = resumen_compra
    if resumen_costes is not None:
        data["resumen_costes"] = resumen_costes
    return data
# =========================================================
# CSS
# =========================================================
CSS_COMERCIAL = """
<style>
    .comercial-box { background-color: white; padding: 26px; border: 2px solid #1E88E5; border-radius: 12px; color: #222; }
    .comercial-header { color: #1E88E5; text-align: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 12px; font-weight: 800; letter-spacing: .5px;}
    .comercial-ref { text-align: center; color: #555; font-size: 1.0em; margin-bottom: 18px; font-weight: 600; }
    .comercial-table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 1.02em; }
    .comercial-table th { background-color: #1E88E5; color: white; padding: 10px; text-align: left; }
    .comercial-table td { padding: 10px; border: 1px solid #e1e1e1; text-align: left; vertical-align: top;}
    .tag {display:inline-block; padding:2px 8px; border-radius: 999px; font-size:.88em; background:#f2f6ff; border:1px solid #dbe6ff; color:#1E88E5; margin-right:6px;}
    .sec-title{margin-top:14px; font-weight:800; color:#1E88E5;}
    .small{font-size:.92em; color:#555;}
    .muted{color:#666;}
    .grid2{display:grid; grid-template-columns: 1fr 1fr; gap:10px;}
    .card{border:1px solid #eee; border-radius:10px; padding:12px; background:#fff;}
    .warn{background:#fff7e6;border:1px solid #ffe0a3;padding:10px;border-radius:10px;}
</style>
"""
st.markdown(CSS_COMERCIAL, unsafe_allow_html=True)

st.title("🛡️ PANEL ADMIN - ESCANDALLO")

# =========================================================
# SIDEBAR (visualización + import/export)
# =========================================================

def _mark_json_download():
    """Marca en session_state que el JSON se ha descargado (para no olvidarse)."""
    st.session_state._json_downloaded = True
    st.session_state._json_downloaded_filename = st.session_state.get("_export_filename", "")

with st.sidebar:
    st.header("📦 JSON / Visualización")
    # 🌟 VISTA OFERTA siempre activa (sin toggle)
    st.session_state["modo_oferta"] = True
    modo_comercial = True
    st.caption("🌟 VISTA OFERTA activa")

    st.divider()

    # =========================================================
    # Aviso + botón (sidebar) sobre materia prima importada vs tarifa actual
    # =========================================================
    if bool(st.session_state.get("_tarifa_mp_mismatch", False)):
        st.warning(
            "⚠️ Materia prima del proyecto ≠ tarifa actual. "
            "Puedes mantenerla (si ya enviaste oferta) o actualizar a tarifa vigente."
        )
        if st.button("🔁 Actualizar materia prima a tarifa actual", use_container_width=True, key="btn_update_mp_sidebar"):
            _aplicar_tarifa_actual_materia_prima()
            st.success("Materia prima actualizada a tarifa actual.")
        st.caption("Actualiza SOLO: Cartoncillo, Planchas, Rígidos y Peliculado.")

    with st.expander("📥 Importar JSON", expanded=False):
        uploaded = st.file_uploader("Subir JSON", type=["json"], key="uploader_json")
        if uploaded is not None:
            try:
                raw = uploaded.getvalue()
                h = hashlib.sha256(raw).hexdigest()
                if st.session_state._last_import_hash != h:
                    di = json.loads(raw.decode("utf-8"))
                    normalizar_import(di)
                    st.session_state._last_import_hash = h
                    st.success("Importación completa OK")
                    st.rerun()
                else:
                    st.caption("Este JSON ya se importó (evitado bucle).")
            except Exception as e:
                st.error(f"Error importando JSON: {e}")

        if st.button("🧹 Permitir re-importar el mismo JSON", key="reset_import"):
            st.session_state._last_import_hash = None
            st.success("Listo.")

    with st.expander("📤 Exportar JSON", expanded=True):
        if st.session_state._export_blob:
            st.download_button(
                "💾 Descargar JSON",
                data=st.session_state._export_blob,
                file_name=st.session_state._export_filename,
                mime="application/json",
                on_click=_mark_json_download,
                key="dl_json_sidebar"
            )
            if st.session_state.get("_json_downloaded", False):
                st.success(f"✅ JSON descargado: {st.session_state.get('_json_downloaded_filename', '') or st.session_state._export_filename}")
        else:
            st.caption("Calcula una vez para habilitar la exportación.")

# =========================================================
# PESTAÑAS (SIEMPRE ADMIN)
# =========================================================
tab_calculadora, tab_costes, tab_auditoria, tab_debug = st.tabs(["🧮 Calculadora", "💰 Base de Datos", "🧾 Auditoría cálculos", "🔍 Desglose"])

# =========================================================
# TAB COSTES (siempre visible)
# =========================================================
with tab_costes:
    col_c1, col_c2 = st.columns(2)
    db = st.session_state.db_precios


    # defaults descuentos (por si vienen viejos)
    if "db_descuentos" not in st.session_state or not isinstance(st.session_state.db_descuentos, dict):
        st.session_state.db_descuentos = {"cartoncillo": 0.0, "ondulado_rigidos": 0.0, "narba": 0.0}
    for _k0 in ["cartoncillo", "ondulado_rigidos", "narba"]:
        st.session_state.db_descuentos.setdefault(_k0, 0.0)

    with col_c1:
        with st.expander("📄 Cartoncillo (€/Kg)", expanded=True):
            st.session_state.db_descuentos["cartoncillo"] = st.number_input(
                "Descuento bloque Cartoncillo (%)",
                min_value=0.0, max_value=100.0, step=0.5,
                value=float(st.session_state.db_descuentos.get("cartoncillo", 0.0)),
                key="db_desc_cart"
            )
            for k, v in db["cartoncillo"].items():
                if k != "Ninguno":
                    db["cartoncillo"][k]["precio_kg"] = st.number_input(
                        f"{k} (€/kg)", value=float(v["precio_kg"]), key=f"cost_cart_{k}"
                    )

        with st.expander("🧱 Ondulado y Rígidos (€/hoja)", expanded=True):
            st.session_state.db_descuentos["ondulado_rigidos"] = st.number_input(
                "Descuento bloque Ondulado + Rígidos (%)",
                min_value=0.0, max_value=100.0, step=0.5,
                value=float(st.session_state.db_descuentos.get("ondulado_rigidos", 0.0)),
                key="db_desc_or"
            )

            st.markdown("##### Ondulado")
            for k, v in db["planchas"].items():
                if k != "Ninguna":
                    st.markdown(f"**{k}**")
                    # ✅ 'peg' se gestiona en NARBA, aquí solo calidades de plancha
                    vv = {kk: sv for kk, sv in v.items() if kk != "peg"}
                    cols = st.columns(len(vv)) if vv else st.columns(1)
                    for idx, (sk, sv) in enumerate(vv.items()):
                        db["planchas"][k][sk] = cols[idx].number_input(
                            sk, value=float(sv), key=f"cost_pl_{k}_{sk}"
                        )

            st.markdown("---")
            st.markdown("##### Rígidos (Precio Hoja + Tamaño)")
            for k, v in db["rigidos"].items():
                if k != "Ninguno":
                    c1, c2, c3 = st.columns([3, 1, 1])
                    db["rigidos"][k]["precio_ud"] = c1.number_input(
                        f"{k} (€/hoja)", value=float(v["precio_ud"]), key=f"cost_rig_{k}"
                    )
                    db["rigidos"][k]["w"] = int(c2.number_input("w", value=int(v["w"]), key=f"rigw_{k}"))
                    db["rigidos"][k]["h"] = int(c3.number_input("h", value=int(v["h"]), key=f"righ_{k}"))

    with col_c2:
        with st.expander("✨ Acabados (otros)", expanded=True):
            # Laminado digital se mantiene aquí (no NARBA)
            db["laminado_digital"] = st.number_input(
                "Laminado Digital", value=float(db.get("laminado_digital", 3.5)), key="cost_lam_dig"
            )

        with st.expander("🧩 NARBA (Procesos: Contracolado · Peliculado · Troquelado)", expanded=True):
            st.session_state.db_descuentos["narba"] = st.number_input(
                "Descuento bloque NARBA (%)",
                min_value=0.0, max_value=100.0, step=0.5,
                value=float(st.session_state.db_descuentos.get("narba", 0.0)),
                key="db_desc_narba"
            )

            st.markdown("##### Contracolado (€/m² por capa)")
            for k, v in db["planchas"].items():
                if k != "Ninguna":
                    if "peg" in v:
                        db["planchas"][k]["peg"] = st.number_input(
                            f"{k} · peg", value=float(v["peg"]), key=f"cost_peg_{k}", format="%.4f"
                        )

            st.markdown("---")
            st.markdown("##### Peliculado (€/m²)")
            for k, v in db["peliculado"].items():
                if k != "Sin Peliculado":
                    db["peliculado"][k] = st.number_input(f"{k}", value=float(v), key=f"cost_pel_{k}")

            st.markdown("---")
            st.markdown("##### Troquelado")
            for k, v in db["troquelado"].items():
                st.markdown(f"**{k}**")
                c_arr, c_tir = st.columns(2)
                db["troquelado"][k]["arranque"] = c_arr.number_input(
                    "Arranque (€)", value=float(v["arranque"]), key=f"trq_arr_{k}"
                )
                db["troquelado"][k]["tiro"] = c_tir.number_input(
                    "Tiro (€/h)", value=float(v["tiro"]), format="%.4f", key=f"trq_tir_{k}"
                )

        with st.expander("✂️ Plotter", expanded=True):
            db["plotter"]["precio_hoja"] = st.number_input(
                "Corte Plotter (€/hoja)", value=float(db["plotter"]["precio_hoja"]), key="plotter_precio"
            )

        with st.expander("🖨️ Impresión Offset (info)", expanded=True):
            st.markdown(
                """
<div class="warn">
<b>Nueva regla Offset</b><br>
• Mínimo: <b>85€ por tinta</b> (hasta 100 hojas)<br>
• Hojas extra (101..500): <b>0,0875€ / hoja / tinta</b><br>
• 501..2000: <b>120€ por tinta</b><br>
• &gt;2000: <b>+0,015€ / hoja / tinta</b><br>
</div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# TAB CALCULADORA
# =========================================================
with tab_calculadora:
    db = st.session_state.db_precios

    st.header("Paso 1 · Datos de oferta")

    cA, cB, cC = st.columns([2, 2, 3])
    with cA:
        st.text_input("Nº Briefing", key="brf")
        st.text_input("Nº Comercial 1", key="comercial_1")
        st.text_input("Nº Comercial 2 (opcional)", key="comercial_2")
        st.text_input("Cliente", key="cli")
        st.text_area("Notas / Comentarios", key="notas", height=180, placeholder="Escribe aquí notas internas o comentarios para incluir en la oferta comercial...")
        _aplicar_margen_auto_si_procede()
    with cB:
        st.text_input("Descripción", key="desc")
        st.text_input("Cantidades (ej: 500, 1000)", key="cants_str_saved")
    with cC:
        st.radio("Manipulación", ["Segundos", "Minutos"], horizontal=True, key="unidad_t")
        st.number_input("Tiempo/ud", min_value=0.0, value=float(st.session_state.t_input), step=1.0, key="t_input")

        st.markdown("**Opcionales (a parte)**")
        st.checkbox("Rellenado", value=bool(st.session_state.rell_enabled), key="rell_enabled")
        st.number_input("Tiempo/ud Rellenado", min_value=0.0, value=float(st.session_state.rell_t_input), step=1.0, key="rell_t_input", disabled=not bool(st.session_state.rell_enabled))
        st.checkbox("Armado", value=bool(st.session_state.arm_enabled), key="arm_enabled")
        st.number_input("Tiempo/ud Armado", min_value=0.0, value=float(st.session_state.arm_t_input), step=1.0, key="arm_t_input", disabled=not bool(st.session_state.arm_enabled))

        st.markdown("**Dificultad**")
        # Desplegable + editable: el desplegable aplica un valor rápido y el input permite afinarlo.
        _dif_presets = [
            ("0,000", 0.0),
            ("0,020", 0.02),
            ("0,050", 0.05),
            ("0,091 (standard)", 0.091),
            ("0,120", 0.12),
            ("0,150", 0.15),
            ("Personalizado", None),
        ]

        # Inicializa selección en base al valor actual si coincide con un preset
        _dif_actual = float(st.session_state.dif_ud)
        _dif_labels = [p[0] for p in _dif_presets]
        _dif_values = [p[1] for p in _dif_presets]

        _idx = None
        for i, v in enumerate(_dif_values):
            if v is None:
                continue
            if abs(float(v) - _dif_actual) < 1e-9:
                _idx = i
                break
        if _idx is None:
            _idx = _dif_labels.index("Personalizado")

        sel = st.selectbox("Preset dificultad", _dif_labels, index=_idx, key="dif_preset_sel")
        sel_val = _dif_presets[_dif_labels.index(sel)][1]
        if sel_val is not None:
            # Si eliges un preset, se aplica automáticamente
            st.session_state.dif_ud = float(sel_val)

        # Editable siempre (si está en preset, puedes ajustarlo manualmente igualmente)
        st.number_input("Dificultad (€/ud)", min_value=0.0, step=0.001, value=float(st.session_state.dif_ud), key="dif_ud")

        # Repetición de proyecto (fuera de Finanzas)
        st.checkbox("🔁 Repetición de proyecto", value=bool(st.session_state.get("repeticion_proyecto", False)), key="repeticion_proyecto")

    lista_cants = parse_cantidades(st.session_state.cants_str_saved)

    unidad_t = st.session_state.unidad_t
    t_input = float(st.session_state.t_input)
    seg_man_total = t_input * 60 if unidad_t == "Minutos" else t_input


    # Opcionales (a parte): mismas unidades que manipulación
    rell_t_input = float(st.session_state.rell_t_input)
    arm_t_input = float(st.session_state.arm_t_input)
    seg_rell_total = (rell_t_input * 60) if unidad_t == "Minutos" else rell_t_input
    seg_arm_total = (arm_t_input * 60) if unidad_t == "Minutos" else arm_t_input

    with st.expander("💰 Finanzas", expanded=False):
        # Si es repetición de proyecto, el importe de desarrollo debe ser 0€.
        if bool(st.session_state.get("repeticion_proyecto", False)):
            # Guardamos el último valor no-cero para poder recuperarlo si se desactiva.
            if st.session_state.get("imp_fijo_pvp_prev") in (None, ""):
                try:
                    st.session_state.imp_fijo_pvp_prev = float(st.session_state.get("imp_fijo_pvp", 0.0) or 0.0)
                except Exception:
                    st.session_state.imp_fijo_pvp_prev = 0.0
            st.session_state.imp_fijo_pvp = 0.0
            st.number_input("Importe de desarrollo de proyecto (€)", value=0.0, key="imp_fijo_pvp", disabled=True)
        else:
            # Si venimos de repetición y estaba a 0, restauramos el último valor guardado.
            try:
                cur = float(st.session_state.get("imp_fijo_pvp", 0.0) or 0.0)
            except Exception:
                cur = 0.0
            if cur == 0.0 and st.session_state.get("imp_fijo_pvp_prev") not in (None, ""):
                try:
                    st.session_state.imp_fijo_pvp = float(st.session_state.get("imp_fijo_pvp_prev") or 0.0)
                except Exception:
                    pass
            st.number_input("Importe de desarrollo de proyecto (€)", value=float(st.session_state.imp_fijo_pvp), key="imp_fijo_pvp")

        st.number_input("Multiplicador", step=0.1, value=float(st.session_state.margen), key="margen")

        st.markdown("---")
        st.number_input("Descuento sobre PROCESOS (%)", min_value=0.0, max_value=100.0, step=0.5, value=float(st.session_state.descuento_procesos), key="descuento_procesos")
        st.number_input("Margen materiales EXTRA", min_value=1.0, step=0.05, value=float(st.session_state.margen_extras), key="margen_extras")
        st.number_input("Margen EMBALAJES", min_value=1.0, step=0.05, value=float(st.session_state.margen_embalajes), key="margen_embalajes")

    dif_ud = float(st.session_state.dif_ud)
    imp_fijo_pvp = float(st.session_state.imp_fijo_pvp)
    if bool(st.session_state.get("repeticion_proyecto", False)):
        imp_fijo_pvp = 0.0
    margen = float(st.session_state.margen)
    descuento_procesos = float(st.session_state.descuento_procesos)
    margen_extras = float(st.session_state.margen_extras)
    margen_embalajes = float(st.session_state.margen_embalajes)

    st.divider()

    if lista_cants:
        # Mermas por defecto (por FORMA + cantidad):
        # - Procesos: tabla aplicada a hojas netas = uds * (pliegos/ud)
        # - Impresión offset: 100 + 50*(pasadas-1) con pasadas = ceil((tintas + barniz)/4)
        # Nota: siempre es editable en 'Gestión de Mermas'.
        piezas = st.session_state.get("piezas_dict", {})
        if isinstance(piezas, dict):
            for pid, p in piezas.items():
                pl = float(p.get("pliegos", 1.0))
                # Defaults impresión (por lado) según configuración de la forma
                im_c = p.get("im", "No")
                nt_c = int(p.get("nt", 4))
                ba_c = bool(p.get("ba", False))

                im_d = p.get("im_d", "No")
                nt_d = int(p.get("nt_d", 4))
                ba_d = bool(p.get("ba_d", False))

                for q in lista_cants:
                    mp_off, _mi_ign = calcular_mermas_estandar(q, pliegos_por_ud=pl, es_digital=False, n_tintas=4, barniz=False)
                    _ss_autoupdate_merma_proc(int(pid), int(q), int(mp_off))

                    # Merma impresión por lado (solo OFFSET)
                    if im_c == "Offset":
                        mi_c = _merma_impresion_offset_por_pasadas(nt_c, ba_c)
                        _ss_autoupdate_merma_imp(int(pid), int(q), "cara", int(mi_c))
                    if im_d == "Offset":
                        mi_d = _merma_impresion_offset_por_pasadas(nt_d, ba_d)
                        _ss_autoupdate_merma_imp(int(pid), int(q), "dorso", int(mi_d))

        # Digital (global por cantidad, como hasta ahora)
        for q in lista_cants:
            _mp_dig, mi_dig = calcular_mermas_estandar(q, pliegos_por_ud=1.0, es_digital=True)
            if q not in st.session_state.mermas_imp_digital_manual and str(q) not in st.session_state.mermas_imp_digital_manual:
                st.session_state.mermas_imp_digital_manual[q] = int(mi_dig)
# -----------------------------------------------------
    # PASO 2: TÉCNICO
    # -----------------------------------------------------
    st.header("Paso 2 · Datos técnicos")

    c_btns = st.columns([1, 4])
    with c_btns[0]:
        dup_prev = st.checkbox("Repetir datos de la anterior", key="dup_prev_forma", value=False)
        if st.button("➕ Forma", key="btn_add_forma"):
            last_id = max(st.session_state.piezas_dict.keys())
            nid = int(last_id) + 1

            if dup_prev and last_id in st.session_state.piezas_dict:
                # Copiamos la forma anterior (inputs técnicos) y ajustamos el nombre
                st.session_state.piezas_dict[nid] = deepcopy(st.session_state.piezas_dict[last_id])
                st.session_state.piezas_dict[nid]["nombre"] = f"Forma {nid}"

                # Duplicamos también configuraciones asociadas al formato (si existen)
                for kdict in ["mermas_proc_manual", "mermas_imp_manual", "mermas_imp_digital_manual"]:
                    d = st.session_state.get(kdict, {})
                    if isinstance(d, dict):
                        # Aceptamos claves int o str (compatibilidad)
                        if str(last_id) in d:
                            d[str(nid)] = deepcopy(d[str(last_id)])
                        elif last_id in d:
                            d[str(nid)] = deepcopy(d[last_id])

                # Impresiones por cantidad por formato
                en = st.session_state.get("impresiones_by_qty_fmt_enabled", {})
                if isinstance(en, dict):
                    if str(last_id) in en:
                        en[str(nid)] = bool(en.get(str(last_id), False))
                    elif last_id in en:
                        en[str(nid)] = bool(en.get(last_id, False))

                cfg_fmt = st.session_state.get("impresiones_by_qty_fmt", {})
                if isinstance(cfg_fmt, dict):
                    if str(last_id) in cfg_fmt:
                        cfg_fmt[str(nid)] = deepcopy(cfg_fmt[str(last_id)])
                    elif last_id in cfg_fmt:
                        cfg_fmt[str(nid)] = deepcopy(cfg_fmt[last_id])

            else:
                st.session_state.piezas_dict[nid] = crear_forma_vacia(nid)

            st.rerun()
    if c_btns[1].button("🗑 Reiniciar"):

        st.session_state.piezas_dict = {1: crear_forma_vacia(1)}
        st.session_state.lista_extras_grabados = []
        st.session_state.embalajes = [crear_embalaje_vacio(0)]
        st.session_state.externos = [crear_externo_vacio(0)]
        st.session_state.mermas_imp_manual = {}
        st.session_state.mermas_proc_manual = {}
        st.rerun()

    def callback_cambio_frontal(pid):
        new_mat = st.session_state[f"pf_{pid}"]
        if new_mat != "Ninguno":
            st.session_state[f"gf_{pid}"] = st.session_state.db_precios["cartoncillo"][new_mat]["gramaje"]
            st.session_state[f"im_{pid}"] = "Offset"
            st.session_state[f"nt_{pid}"] = 4
        else:
            st.session_state[f"im_{pid}"] = "No"
            st.session_state[f"nt_{pid}"] = 0

    def callback_cambio_dorso(pid):
        new_mat = st.session_state[f"pd_{pid}"]
        if new_mat != "Ninguno":
            st.session_state[f"gd_{pid}"] = st.session_state.db_precios["cartoncillo"][new_mat]["gramaje"]
            if st.session_state.get(f"im_d_{pid}", "No") == "No":
                st.session_state[f"im_d_{pid}"] = "No"
        else:
            st.session_state[f"im_d_{pid}"] = "No"
            st.session_state[f"nt_d_{pid}"] = 0

    def callback_medida_estandar(pid):
        fmt = st.session_state[f"std_{pid}"]
        if fmt != "Personalizado":
            nh, nw = FORMATOS_STD[fmt]
            st.session_state[f"h_{pid}"] = nh
            st.session_state[f"w_{pid}"] = nw
            if not st.session_state.get(f"pldif_{pid}", False):
                st.session_state[f"plh_{pid}"] = nh
                st.session_state[f"plw_{pid}"] = nw

    def callback_rigido(pid):
        mat = st.session_state.get(f"mrig_{pid}", "Ninguno")
        if mat != "Ninguno":
            info = st.session_state.db_precios["rigidos"][mat]
            st.session_state[f"w_{pid}"] = int(info["w"])
            st.session_state[f"h_{pid}"] = int(info["h"])


    def callback_corte_default(pid, cants):
        """Sincroniza el corte por cantidad con el corte por defecto."""
        new_val = st.session_state.get(f"cor_def_{pid}", "Troquelado")
        # Actualiza widgets por cantidad
        for q in cants:
            st.session_state[f"cor_qty_{pid}_{q}"] = new_val
        # Actualiza estructura en memoria (por si se usa en cálculos sin rerun completo)
        try:
            pieza = st.session_state.piezas_dict.get(pid, None)
            if isinstance(pieza, dict):
                pieza["cor_default"] = new_val
                if not isinstance(pieza.get("cor_by_qty", {}), dict):
                    pieza["cor_by_qty"] = {}
                for q in cants:
                    pieza["cor_by_qty"][str(q)] = new_val
        except Exception:
            pass

    for p_id, p in st.session_state.piezas_dict.items():
        with st.expander(f"🛠 {p.get('nombre','Forma')} - {p.get('h',0)}x{p.get('w',0)} mm", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                p["nombre"] = st.text_input("Etiqueta", p.get("nombre", f"Forma {p_id}"), key=f"n_{p_id}")
                p["pliegos"] = st.number_input("Pliegos/Ud", 0.0, 100.0, float(p.get("pliegos", 1.0)), format="%.4f", key=f"p_{p_id}")

                st.selectbox("Medidas Estándar", list(FORMATOS_STD.keys()), key=f"std_{p_id}",
                             on_change=callback_medida_estandar, args=(p_id,))

                c_h, c_w = st.columns(2)
                p["h"] = c_h.number_input("Largo Papel (mm)", 0, 5000, value=int(p.get("h", 0)), key=f"h_{p_id}")
                p["w"] = c_w.number_input("Ancho Papel (mm)", 0, 5000, value=int(p.get("w", 0)), key=f"w_{p_id}")

                opts_im = ["Offset", "Digital", "No"]
                val_im_raw = p.get("im", "No")
                val_im_norm = str(val_im_raw).strip().lower()
                if val_im_norm in ("offset", "off"):
                    val_im = "Offset"
                elif val_im_norm in ("digital", "dig"):
                    val_im = "Digital"
                elif val_im_norm in ("no", "ninguno", "none", ""):
                    val_im = "No"
                else:
                    # Compatibilidad: si viene algo raro de JSON antiguo, mantenemos "No"
                    val_im = "No"
                idx_im = opts_im.index(val_im)
                p["im"] = st.selectbox("Impresión Cara", opts_im, index=idx_im, key=f"im_{p_id}")

                if p["im"] == "Offset":
                    p["nt"] = st.number_input("Tintas Cara", 0, 12, int(p.get("nt", 4)), key=f"nt_{p_id}")
                    p["ba"] = st.checkbox("Barniz Cara", value=bool(p.get("ba", False)), key=f"ba_{p_id}")
                elif p["im"] == "Digital":
                    p["ld"] = st.checkbox("Laminado Digital Cara", value=bool(p.get("ld", False)), key=f"ld_{p_id}")

                opts_pel = list(db["peliculado"].keys())
                val_pel = p.get("pel", "Sin Peliculado")
                idx_pel = opts_pel.index(val_pel) if val_pel in opts_pel else 0
                p["pel"] = st.selectbox("Peliculado Cara", opts_pel, index=idx_pel, key=f"pel_{p_id}")

                # -----------------------------------------------------
                # TINTA ESPECIAL FR24 (extra por m²)
                # -----------------------------------------------------
                p["fr24"] = st.checkbox("🧪 Tinta especial FR24 (extra €/m²)", value=bool(p.get("fr24", False)), key=f"fr24_{p_id}")
                if bool(p["fr24"]):
                    p["fr24_rate"] = float(st.number_input(
                        "Coste extra FR24 (€/m²)",
                        min_value=0.0,
                        max_value=999.0,
                        value=float(p.get("fr24_rate", 0.05)),
                        step=0.01,
                        key=f"fr24r_{p_id}",
                    ))
                else:
                    # Mantener el último valor configurado (si existe) para no perderlo al desactivar.
                    p["fr24_rate"] = float(p.get("fr24_rate", 0.05))

                # -----------------------------------------------------
                # STAMPING (película + calor) - proceso poco habitual
                # -----------------------------------------------------
                p["stamping"] = st.checkbox("✨ Stamping (película + pisada)", value=bool(p.get("stamping", False)), key=f"stamp_{p_id}")
                if bool(p["stamping"]):
                    col_s1, col_s2, col_s3 = st.columns([1, 1, 1])
                    with col_s1:
                        p["stamping_w"] = int(st.number_input("Ancho stamping (mm)", min_value=0, max_value=5000, value=int(p.get("stamping_w", 0)), step=1, key=f"stampw_{p_id}"))
                    with col_s2:
                        p["stamping_h"] = int(st.number_input("Alto stamping (mm)", min_value=0, max_value=5000, value=int(p.get("stamping_h", 0)), step=1, key=f"stamph_{p_id}"))
                    with col_s3:
                        p["stamping_cobrar_arreglo"] = bool(st.checkbox("Cobrar arreglo stamping", value=bool(p.get("stamping_cobrar_arreglo", True)), key=f"stamparr_{p_id}"))
                    st.caption("Tarifa: arreglo 168€ · pisada 0,21€/hoja · película 0,39€/m² (rectángulo) · hojas = hp_corte (ajustado por piezas por troquel).")
                else:
                    p["stamping_w"] = int(p.get("stamping_w", 0))
                    p["stamping_h"] = int(p.get("stamping_h", 0))
                    p["stamping_cobrar_arreglo"] = bool(p.get("stamping_cobrar_arreglo", True))

                # -----------------------------------------------------
                # IMPRESIONES POR CANTIDAD (multi-tirada) - POR FORMATO (TIC)
                # -----------------------------------------------------
                # Si una misma cantidad se imprime en varias tiradas (p.ej. 100+400+500) para ESTA forma,
                # indícalo aquí. Solo afecta a: (1) coste de impresión y (2) merma de cartoncillo (una merma extra por cada impresión).
                # El resto de procesos mantiene su merma habitual.
                pid_key = str(int(p_id))
                if "impresiones_by_qty_fmt_enabled" not in st.session_state:
                    st.session_state.impresiones_by_qty_fmt_enabled = {}
                if "impresiones_by_qty_fmt" not in st.session_state:
                    st.session_state.impresiones_by_qty_fmt = {}

                tic_def = bool(st.session_state.impresiones_by_qty_fmt_enabled.get(pid_key, False)) if isinstance(st.session_state.impresiones_by_qty_fmt_enabled, dict) else False
                tic = st.checkbox("🖨️ Varias impresiones por cantidad (esta forma)", value=bool(st.session_state.get(f"impact_{p_id}", tic_def)), key=f"impact_{p_id}")
                if isinstance(st.session_state.impresiones_by_qty_fmt_enabled, dict):
                    st.session_state.impresiones_by_qty_fmt_enabled[pid_key] = bool(tic)

                if bool(tic) and lista_cants:
                    with st.expander("🖨️ Desglose de impresiones por cantidad (esta forma)", expanded=False):
                        st.caption("Ejemplo: 1000 uds -> 3 impresiones: 100+400+500. "
                                   "Solo afecta a coste de impresión y merma extra de cartoncillo por impresión.")
                        cfg_fmt_all = st.session_state.impresiones_by_qty_fmt if isinstance(st.session_state.impresiones_by_qty_fmt, dict) else {}
                        cfg_fmt = cfg_fmt_all.get(pid_key, {}) if isinstance(cfg_fmt_all.get(pid_key, {}), dict) else {}

                        for q in lista_cants:
                            cfg = cfg_fmt.get(str(int(q)), {}) if isinstance(cfg_fmt.get(str(int(q)), {}), dict) else {}
                            try:
                                n_def = int(cfg.get("n", 1))
                            except Exception:
                                n_def = 1
                            n_def = max(1, n_def)
                            modo_def = str(cfg.get("modo", "igual")).lower().strip()
                            igual_def = (modo_def != "manual")
                            partes_def = cfg.get("partes", []) if isinstance(cfg.get("partes", []), list) else []
                            try:
                                partes_def_str = "+".join(str(int(x)) for x in partes_def) if partes_def else ""
                            except Exception:
                                partes_def_str = ""

                            c1i, c2i = st.columns([1, 3])
                            with c1i:
                                n_imp = st.number_input(
                                    f"{q} uds · Nº impresiones",
                                    min_value=1,
                                    step=1,
                                    value=int(st.session_state.get(f"impn_{p_id}_{q}", n_def)),
                                    key=f"impn_{p_id}_{q}",
                                )
                            with c2i:
                                igual = st.checkbox(
                                    "Repartir a partes iguales",
                                    value=bool(st.session_state.get(f"impigual_{p_id}_{q}", igual_def)),
                                    key=f"impigual_{p_id}_{q}",
                                )

                            partes = []
                            if int(n_imp) <= 1:
                                partes = [int(q)]
                                cfg_fmt[str(int(q))] = {"n": 1, "modo": "igual", "partes": partes}
                                st.caption("Tirada única.")
                                continue

                            if bool(igual):
                                partes = _split_equal(int(q), int(n_imp))
                                cfg_fmt[str(int(q))] = {"n": int(n_imp), "modo": "igual", "partes": partes}
                                st.caption(f"Tiradas: {partes} (suma {sum(partes)})")
                            else:
                                txt = st.text_input(
                                    "Desglose (ej: 100+400+500)",
                                    value=str(st.session_state.get(f"impman_{p_id}_{q}", partes_def_str)),
                                    key=f"impman_{p_id}_{q}",
                                )
                                partes_manual = _parse_partes_str(txt)
                                if partes_manual and len(partes_manual) == int(n_imp) and sum(partes_manual) == int(q):
                                    partes = partes_manual
                                    cfg_fmt[str(int(q))] = {"n": int(n_imp), "modo": "manual", "partes": partes}
                                    st.caption(f"Tiradas: {partes} (suma {sum(partes)})")
                                else:
                                    partes = _split_equal(int(q), int(n_imp))
                                    cfg_fmt[str(int(q))] = {"n": int(n_imp), "modo": "igual", "partes": partes}
                                    st.warning("El desglose manual no cuadra (nº partes o suma). Se ha aplicado reparto igual.")
                                    st.caption(f"Tiradas: {partes} (suma {sum(partes)})")

                        cfg_fmt_all[pid_key] = cfg_fmt
                        st.session_state.impresiones_by_qty_fmt = cfg_fmt_all


            with col2:
                opts_pf = list(db["cartoncillo"].keys())
                val_pf = p.get("pf", "Ninguno")
                idx_pf = opts_pf.index(val_pf) if val_pf in opts_pf else 0
                p["pf"] = st.selectbox("Cartoncillo Cara", opts_pf, index=idx_pf, key=f"pf_{p_id}",
                                       on_change=callback_cambio_frontal, args=(p_id,))
                p["gf"] = st.number_input("Gramaje Cara (g)", value=int(p.get("gf", 0)), key=f"gf_{p_id}")

                st.divider()

                opts_base = ["Ondulado/Cartón", "Material Rígido"]
                idx_base = opts_base.index(p.get("tipo_base", "Ondulado/Cartón")) if p.get("tipo_base") in opts_base else 0
                p["tipo_base"] = st.selectbox("Tipo Soporte", opts_base, index=idx_base, key=f"tb_{p_id}")

                if p["tipo_base"] == "Ondulado/Cartón":
                    opts_pl = list(db["planchas"].keys())
                    val_pl = p.get("pl", "Ninguna")
                    idx_pl = opts_pl.index(val_pl) if val_pl in opts_pl else 0
                    p["pl"] = st.selectbox("Plancha Base", opts_pl, index=idx_pl, key=f"pl_{p_id}")

                    if p["pl"] != "Ninguna":
                        p["pl_dif"] = st.checkbox("📏 Medida Plancha Diferente", value=bool(p.get("pl_dif", False)), key=f"pldif_{p_id}")
                        if p["pl_dif"]:
                            c_ph, c_pw = st.columns(2)
                            p["pl_h"] = c_ph.number_input("Alto Plancha", 0, 5000, value=int(p.get("pl_h", p["h"])), key=f"plh_{p_id}")
                            p["pl_w"] = c_pw.number_input("Ancho Plancha", 0, 5000, value=int(p.get("pl_w", p["w"])), key=f"plw_{p_id}")
                        else:
                            p["pl_h"] = p["h"]
                            p["pl_w"] = p["w"]

                    opts_ap = ["C/C", "B/C", "B/B"]
                    val_ap = p.get("ap", "B/C")
                    idx_ap = opts_ap.index(val_ap) if val_ap in opts_ap else 1
                    p["ap"] = st.selectbox("Calidad Ondulado", opts_ap, index=idx_ap, key=f"ap_{p_id}")

                    p["flexografia"] = st.checkbox("🟪 Flexografía (coste fijo por plancha)", value=bool(p.get("flexografia", False)), key=f"flexo_{p_id}")

                else:
                    p["rig_manual"] = st.checkbox("🧩 Rígido Manual (tamaño + precio)", value=bool(p.get("rig_manual", False)), key=f"rigman_{p_id}")

                    if p["rig_manual"]:
                        c_rw, c_rh, c_rp = st.columns(3)
                        p["rig_w"] = int(c_rw.number_input("Hoja w (mm)", 0, 10000, value=int(p.get("rig_w", 0)), key=f"rigwman_{p_id}"))
                        p["rig_h"] = int(c_rh.number_input("Hoja h (mm)", 0, 10000, value=int(p.get("rig_h", 0)), key=f"righman_{p_id}"))
                        p["rig_precio_ud"] = float(c_rp.number_input("Precio hoja (€)", 0.0, 999999.0, value=float(p.get("rig_precio_ud", 0.0)), step=0.01, key=f"rigpman_{p_id}"))
                        st.caption("Este rígido manual se usa SOLO en esta pieza.")
                        p["mat_rigido"] = "MANUAL"
                    else:
                        opts_rig = list(db["rigidos"].keys())
                        val_rig = p.get("mat_rigido", "Ninguno")
                        idx_rig = opts_rig.index(val_rig) if val_rig in opts_rig else 0
                        p["mat_rigido"] = st.selectbox("Material Rígido (hoja)", opts_rig, index=idx_rig, key=f"mrig_{p_id}",
                                                       on_change=callback_rigido, args=(p_id,))
                        if p["mat_rigido"] != "Ninguno":
                            info = db["rigidos"][p["mat_rigido"]]
                            st.info(f"Tamaño hoja: {info['w']}x{info['h']} mm | Precio: {info['precio_ud']:.2f}€/hoja")

                st.divider()

                opts_pd = list(db["cartoncillo"].keys())
                val_pd = p.get("pd", "Ninguno")
                idx_pd = opts_pd.index(val_pd) if val_pd in opts_pd else 0
                p["pd"] = st.selectbox("Cartoncillo Dorso", opts_pd, index=idx_pd, key=f"pd_{p_id}",
                                       on_change=callback_cambio_dorso, args=(p_id,))
                if p["pd"] != "Ninguno":
                    p["gd"] = st.number_input("Gramaje Dorso (g)", value=int(p.get("gd", 0)), key=f"gd_{p_id}")
                else:
                    p["gd"] = 0

            with col3:
                st.markdown("##### Corte")
                opts_cor = ["Sin corte", "Troquelado", "Plotter"]
                val_cor = p.get("cor_default", p.get("cor", "Troquelado"))
                idx_troq = opts_cor.index("Troquelado")
                idx_cor = opts_cor.index(val_cor) if val_cor in opts_cor else idx_troq
                p["cor_default"] = st.selectbox(
                    "Corte (por defecto)", opts_cor, index=idx_cor, key=f"cor_def_{p_id}",
                    on_change=callback_corte_default, args=(p_id, lista_cants,)
                )

                if lista_cants:
                    st.caption("Corte por cantidad (opcional):")
                    if not isinstance(p.get("cor_by_qty", {}), dict):
                        p["cor_by_qty"] = {}
                    for q in lista_cants:
                        cur = p["cor_by_qty"].get(str(q), p["cor_default"])
                        idxq = opts_cor.index(cur) if cur in opts_cor else idx_cor
                        p["cor_by_qty"][str(q)] = st.selectbox(
                            f"{q} uds", opts_cor, index=idxq, key=f"cor_qty_{p_id}_{q}"
                        )

                st.divider()

                p["cobrar_arreglo"] = st.checkbox("¿Cobrar Arreglo?", value=bool(p.get("cobrar_arreglo", True)), key=f"arr_{p_id}")
                p["pv_troquel"] = st.number_input("Precio Venta Troquel (€) (si aplica)", value=float(p.get("pv_troquel", 0.0)), key=f"pvt_{p_id}")

                # ✅ Troquelado: permitir forzar manualmente cuántas piezas salen por golpe de troquel.
                # 0 = automático (se asume 1/pliegos_por_ud cuando pliegos<1).
                p["troquel_piezas"] = int(st.number_input(
                    "Piezas por troquel (0 = automático)",
                    min_value=0,
                    step=1,
                    value=int(p.get("troquel_piezas", 0) or 0),
                    key=f"trqp_{p_id}",
                ))

                if p.get("pd", "Ninguno") != "Ninguno":
                    opts_imd = ["Offset", "Digital", "No"]
                    val_imd_raw = p.get("im_d", "No")
                    val_imd_norm = str(val_imd_raw).strip().lower()
                    if val_imd_norm in ("offset", "off"):
                        val_imd = "Offset"
                    elif val_imd_norm in ("digital", "dig"):
                        val_imd = "Digital"
                    elif val_imd_norm in ("no", "ninguno", "none", ""):
                        val_imd = "No"
                    else:
                        val_imd = "No"
                    idx_imd = opts_imd.index(val_imd)
                    p["im_d"] = st.selectbox("Impresión Dorso", opts_imd, index=idx_imd, key=f"im_d_{p_id}")

                    if p["im_d"] == "Offset":
                        p["nt_d"] = st.number_input("Tintas Dorso", 0, 12, int(p.get("nt_d", 0)), key=f"nt_d_{p_id}")
                        p["ba_d"] = st.checkbox("Barniz Dorso", value=bool(p.get("ba_d", False)), key=f"ba_d_{p_id}")
                    elif p["im_d"] == "Digital":
                        p["ld_d"] = st.checkbox("Laminado Digital Dorso", value=bool(p.get("ld_d", False)), key=f"ld_d_{p_id}")
                    else:
                        p["nt_d"] = 0
                        p["ba_d"] = False
                        p["ld_d"] = False

                    opts_pel = list(db["peliculado"].keys())
                    val_peld = p.get("pel_d", "Sin Peliculado")
                    idx_peld = opts_pel.index(val_peld) if val_peld in opts_pel else 0
                    p["pel_d"] = st.selectbox("Peliculado Dorso", opts_pel, index=idx_peld, key=f"pel_d_{p_id}")
                else:
                    p["im_d"] = "No"
                    p["nt_d"] = 0
                    p["ba_d"] = False
                    p["ld_d"] = False
                    p["pel_d"] = "Sin Peliculado"

                if st.button("🗑 Borrar Forma", key=f"del_{p_id}"):
                    del st.session_state.piezas_dict[p_id]
                    st.rerun()

    st.divider()
    st.subheader("📦 2. Materiales extra")

    c_add_main, c_add_flex, c_add_manual = st.columns(3)

    with c_add_main:
        st.markdown("**Extras Mainsa**")
        opts_extra = ["---"] + list(db["extras_base"].keys())
        ex_sel = st.selectbox("Añadir extra estándar:", opts_extra, key="sel_extra_mainsa")
        if st.button("➕ Añadir Mainsa", key="btn_add_mainsa") and ex_sel != "---":
            coste_actual = db["extras_base"][ex_sel]
            st.session_state.lista_extras_grabados.append({"nombre": ex_sel, "coste": float(coste_actual), "cantidad": 1.0, "tipo": "mainsa"})
            st.rerun()

    with c_add_flex:
        st.markdown("**Catálogo FLEXICO**")
        flx_sel = st.selectbox("Buscar Ref/Desc:", ["---"] + OPCIONES_FLEXICO, key="sel_extra_flexico")
        if st.button("➕ Añadir Flexico", key="btn_add_flexico") and flx_sel != "---":
            cod = flx_sel.split(" - ")[0]
            prod = PRODUCTOS_FLEXICO[cod]
            st.session_state.lista_extras_grabados.append({"nombre": f"FLEXICO: {prod['desc']}", "coste": float(prod["precio"]), "cantidad": 1.0, "tipo": "flexico"})
            st.rerun()

    with c_add_manual:
        st.markdown("**Extra manual**")
        m_name = st.text_input("Nombre", key="manual_ex_name")
        m_cost = st.number_input("Precio unitario", min_value=0.0, value=0.0, step=0.01, key="manual_ex_cost")
        m_qty = st.number_input("Cantidad/ud prod", min_value=0.0, value=1.0, step=0.1, key="manual_ex_qty")
        if st.button("➕ Añadir Manual", key="btn_add_manual"):
            if m_name.strip():
                st.session_state.lista_extras_grabados.append({"nombre": m_name.strip(), "coste": float(m_cost), "cantidad": float(m_qty), "tipo": "manual"})
                st.rerun()
            else:
                st.warning("Pon un nombre para el extra manual.")

    for i, ex in enumerate(st.session_state.lista_extras_grabados):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.write(f"**{ex['nombre']}**")
        ex["coste"] = c2.number_input("€/ud compra", value=float(ex.get("coste", 0.0)), key=f"exc_{i}", format="%.4f")
        ex["cantidad"] = c3.number_input("Cant/Ud prod", value=float(ex.get("cantidad", 1.0)), key=f"exq_{i}")
        if c4.button("🗑", key=f"exd_{i}"):
            st.session_state.lista_extras_grabados.pop(i)
            st.rerun()

    st.divider()
    st.subheader("📦 3. Embalajes (múltiples)")

    cE1, cE2 = st.columns([1, 4])
    if cE1.button("➕ Añadir embalaje"):
        if len(st.session_state.embalajes) < 5:
            st.session_state.embalajes.append(crear_embalaje_vacio(len(st.session_state.embalajes)))
            st.rerun()
        else:
            st.warning("Máximo 5 embalajes.")

    if cE2.button("🗑 Reset embalajes"):
        st.session_state.embalajes = [crear_embalaje_vacio(0)]
        st.rerun()

    if not lista_cants:
        st.warning("Define cantidades en Paso 1.")
    else:
        for ei, emb in enumerate(st.session_state.embalajes):
            with st.expander(f"📦 {emb.get('nombre', f'Embalaje {ei+1}')}", expanded=True):
                c0, c1, c2, c3 = st.columns([2, 2, 2, 1])
                emb["nombre"] = c0.text_input("Nombre", value=emb.get("nombre", f"Embalaje {ei+1}"), key=f"emb_name_{ei}")
                emb["tipo"] = c1.selectbox("Tipo", TIPOS_EMB, index=TIPOS_EMB.index(emb.get("tipo", "Manual")) if emb.get("tipo","Manual") in TIPOS_EMB else 0, key=f"emb_tipo_{ei}")
                emb["material"] = c2.selectbox("Material", EMB_MATS, index=EMB_MATS.index(emb.get("material","Canal 5")) if emb.get("material","Canal 5") in EMB_MATS else 0, key=f"emb_mat_{ei}")
                if c3.button("🗑", key=f"emb_del_{ei}"):
                    if len(st.session_state.embalajes) > 1:
                        st.session_state.embalajes.pop(ei)
                        st.rerun()
                    else:
                        st.warning("Debe existir al menos 1 embalaje.")

                d1, d2, d3 = st.columns(3)
                emb["dims"]["L"] = float(d1.number_input("Largo mm", value=float(emb["dims"].get("L",0.0)), key=f"embL_{ei}"))
                emb["dims"]["W"] = float(d2.number_input("Ancho mm", value=float(emb["dims"].get("W",0.0)), key=f"embW_{ei}"))
                emb["dims"]["H"] = float(d3.number_input("Alto mm", value=float(emb["dims"].get("H",0.0)), key=f"embH_{ei}"))

                mult = emb_mult(emb["material"])
                cols = st.columns(len(lista_cants))

                for idx, q in enumerate(lista_cants):
                    if emb["tipo"] == "Manual":
                        emb["costes"][q] = float(cols[idx].number_input(f"Coste compra {q}", value=float(emb["costes"].get(q, 0.0)), key=f"embMan_{ei}_{q}"))
                    elif emb["tipo"] == "Embalaje Guaina (Automático)":
                        L, W, H = emb["dims"]["L"], emb["dims"]["W"], emb["dims"]["H"]
                        sup_m2 = ((2*(L+W)*H) + (L*W)) / 1_000_000 if (L>0 and W>0 and H>0) else 0.0
                        coste_auto = (sup_m2 * 0.70) + (30 / q) if q>0 else 0.0
                        coste_auto *= mult
                        emb["costes"][q] = float(coste_auto)
                        cols[idx].metric(f"{q} uds", f"{coste_auto:.3f}€")
                    elif emb["tipo"] == "Embalaje en Plano":
                        L, W, H = emb["dims"]["L"], emb["dims"]["W"], emb["dims"]["H"]
                        c_plano, _S = embalaje_plano_unit(L, W, H, q)
                        c_plano *= mult
                        emb["costes"][q] = float(c_plano)
                        cols[idx].metric(f"{q} uds", f"{c_plano:.3f}€")
                    elif emb["tipo"] == "Embalaje en Volumen":
                        L, W, H = emb["dims"]["L"], emb["dims"]["W"], emb["dims"]["H"]
                        c_vol, _S = embalaje_volumen_unit(L, W, H, q)
                        c_vol *= mult
                        emb["costes"][q] = float(c_vol)
                        cols[idx].metric(f"{q} uds", f"{c_vol:.3f}€")

    st.divider()
    st.subheader("📌 4. Externos (proveedores / procesos esporádicos)")

    cX1, cX2 = st.columns([1, 4])
    if cX1.button("➕ Añadir externo"):
        if len(st.session_state.externos) < 10:
            st.session_state.externos.append(crear_externo_vacio(len(st.session_state.externos)))
            st.rerun()
        else:
            st.warning("Máximo 10 externos.")

    if cX2.button("🗑 Reset externos"):
        st.session_state.externos = [crear_externo_vacio(0)]
        st.rerun()

    if not lista_cants:
        st.warning("Define cantidades en Paso 1 para poder asignar costes por cantidad.")
    else:
        for xi, ext in enumerate(st.session_state.externos):
            with st.expander(f"📌 {ext.get('concepto', f'Externo {xi+1}')}", expanded=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                ext["concepto"] = c1.text_input("Concepto", value=ext.get("concepto", f"Externo {xi+1}"), key=f"ext_con_{xi}")
                ext["modo"] = c2.selectbox("Modo coste", EXT_TIPOS_COSTE, index=EXT_TIPOS_COSTE.index(ext.get("modo","Unitario (€/ud)")) if ext.get("modo","Unitario (€/ud)") in EXT_TIPOS_COSTE else 0, key=f"ext_modo_{xi}")
                if c3.button("🗑", key=f"ext_del_{xi}"):
                    if len(st.session_state.externos) > 1:
                        st.session_state.externos.pop(xi)
                        st.rerun()
                    else:
                        st.warning("Debe existir al menos 1 externo.")

                cols = st.columns(len(lista_cants))
                for idx, q in enumerate(lista_cants):
                    label = f"{q} uds (€ / ud)" if ext["modo"] == "Unitario (€/ud)" else f"{q} uds (Total €)"
                    ext["costes"][q] = float(cols[idx].number_input(label, value=float(ext.get("costes", {}).get(q, 0.0)), step=0.01, key=f"ext_{xi}_{q}"))

    st.divider()
    st.subheader("⚙️ 5. Gestión de Mermas (auto-relleno)")
    if not lista_cants:
        st.warning("Define cantidades en Paso 1.")
    else:
        # Digital se mantiene global por cantidad (como estaba)
        st.markdown("**Impresión DIGITAL (global por cantidad)**")
        for q in lista_cants:
            c1, c2 = st.columns([1, 3])
            c1.markdown(f"**{q} uds**")
            st.session_state.mermas_imp_digital_manual[q] = int(
                c2.number_input(
                    "Arranque impresión DIGITAL (hojas)",
                    value=int(st.session_state.mermas_imp_digital_manual.get(q, 0)),
                    key=f"mid_{q}",
                )
            )

        st.markdown("**OFFSET / Procesos (por Forma y cantidad)**")
        piezas = st.session_state.get("piezas_dict", {})
        if not isinstance(piezas, dict) or not piezas:
            st.info("No hay formas definidas.")
        else:
            for pid, p in piezas.items():
                nombre = p.get("nombre", f"Forma {pid}")
                with st.expander(f"🧾 Mermas - {nombre}", expanded=False):
                    # Cabecera
                    for q in lista_cants:
                        pl = float(p.get("pliegos", 1.0))
                        mp_def, _ = calcular_mermas_estandar(int(q), pliegos_por_ud=pl, es_digital=False, n_tintas=4, barniz=False)

                        # Defaults impresión por lado
                        is_offset_c = str(p.get("im", "No")).strip().lower() == "offset"
                        is_offset_d = str(p.get("im_d", "No")).strip().lower() == "offset"
                        mi_def_c = _merma_impresion_offset_por_pasadas(int(p.get("nt", 4)), bool(p.get("ba", False))) if is_offset_c else 0
                        mi_def_d = _merma_impresion_offset_por_pasadas(int(p.get("nt_d", 4)), bool(p.get("ba_d", False))) if is_offset_d else 0

                        c0, c1, c2, c3 = st.columns([1, 2, 2, 2])
                        c0.markdown(f"**{q} uds**")

                        # Proceso
                        _ss_autoupdate_merma_proc(int(pid), int(q), int(mp_def))
                        v_proc = int(_ss_get_merma_proc(int(pid), int(q), int(mp_def)))
                        # Guardamos la edición (si cambia)
                        st.session_state.mermas_proc_manual.setdefault(str(pid), {})
                        st.session_state.mermas_proc_manual[str(pid)][str(int(q))] = int(
                            c1.number_input(
                                "Rodaje proceso (hojas)",
                                value=v_proc,
                                key=f"mp_{pid}_{q}",
                            )
                        )

                        # Impresión cara/dorso (OFFSET)
                        st.session_state.mermas_imp_manual.setdefault(str(pid), {})
                        qk = str(int(q))
                        if qk not in st.session_state.mermas_imp_manual[str(pid)] or not isinstance(st.session_state.mermas_imp_manual[str(pid)][qk], dict):
                            st.session_state.mermas_imp_manual[str(pid)][qk] = {"cara": 0, "dorso": 0}

                        # Cara
                        mi_key_c = f"mi_c_{pid}_{q}"
                        if is_offset_c:
                            # Default auto según tintas/barniz (se recalcula si cambian y el usuario no lo ha tocado)
                            _ss_sync_merma_imp_widget(int(pid), int(q), "cara", mi_key_c, int(mi_def_c))
                            v_c_auto = int(_ss_get_merma_imp(int(pid), int(q), "cara", int(mi_def_c)))
                            if mi_key_c not in st.session_state:
                                st.session_state[mi_key_c] = int(v_c_auto)

                            v_c = int(st.session_state.get(mi_key_c, int(v_c_auto)))
                            v_c = int(st.session_state.get(mi_key_c, int(v_c_auto)))
                            v_c_in = int(
                                c2.number_input(
                                    "Merma impresión OFFSET (cara)",
                                    value=v_c,
                                    key=mi_key_c,
                                )
                            )
                            st.session_state.mermas_imp_manual[str(pid)][qk]["cara"] = v_c_in
                        else:
                            # Si no es Offset, no aplicamos merma de impresión
                            if mi_key_c not in st.session_state:
                                st.session_state[mi_key_c] = 0
                            c2.number_input(
                                "Merma impresión OFFSET (cara)",
                                value=0,
                                key=mi_key_c,
                                disabled=True,
                            )
                            st.session_state.mermas_imp_manual[str(pid)][qk]["cara"] = 0

                        # Dorso
                        mi_key_d = f"mi_d_{pid}_{q}"
                        if is_offset_d:
                            # Default auto según tintas/barniz (se recalcula si cambian y el usuario no lo ha tocado)
                            _ss_sync_merma_imp_widget(int(pid), int(q), "dorso", mi_key_d, int(mi_def_d))
                            v_d_auto = int(_ss_get_merma_imp(int(pid), int(q), "dorso", int(mi_def_d)))
                            if mi_key_d not in st.session_state:
                                st.session_state[mi_key_d] = int(v_d_auto)

                            v_d = int(st.session_state.get(mi_key_d, int(v_d_auto)))
                            v_d = int(st.session_state.get(mi_key_d, int(v_d_auto)))
                            v_d_in = int(
                                c3.number_input(
                                    "Merma impresión OFFSET (dorso)",
                                    value=v_d,
                                    key=mi_key_d,
                                )
                            )
                            st.session_state.mermas_imp_manual[str(pid)][qk]["dorso"] = v_d_in
                        else:
                            if mi_key_d not in st.session_state:
                                st.session_state[mi_key_d] = 0
                            c3.number_input(
                                "Merma impresión OFFSET (dorso)",
                                value=0,
                                key=mi_key_d,
                                disabled=True,
                            )
                            st.session_state.mermas_imp_manual[str(pid)][qk]["dorso"] = 0
# =========================================================
# MOTOR DE CÁLCULO + DESGLOSE + COMPRAS
# =========================================================
res_final = []
desc_full = {}
compras_legible = {}
resumen_costes_export = {}

if lista_cants and st.session_state.piezas_dict and sum(lista_cants) > 0:
    tot_pv_trq = sum(float(pz.get("pv_troquel", 0.0)) for pz in st.session_state.piezas_dict.values())

    for q_n in lista_cants:
        # Mermas:
        # - Digital: mermas_imp_digital_manual (fallback a regla digital si no existe)
        # - Procesos e impresión OFFSET: por forma+cantidad (ver _ss_get_* en helpers)
        merma_imp_digital_hojas = int(
            st.session_state.mermas_imp_digital_manual.get(
                q_n, calcular_mermas_estandar(q_n, es_digital=True)[1]
            )
        )

        coste_f = 0.0
        det_f = []
        debug_log = []


        tot_cat = {
            "materiales": {
                "cartoncillo": 0.0,
                "ondulado": 0.0,
                "rigidos": 0.0,
                "extras": 0.0,
                "embalajes_compra": 0.0
            },
            "procesos": {
                "contracolado": 0.0,
                "impresion": 0.0,
                "peliculado": 0.0,
                "corte": 0.0,
                "stamping": 0.0,
                "manipulacion": 0.0,
                "dificultad": 0.0,
                "externos": 0.0,
            },
            "embalajes_venta": []
        }

        # Descuentos de compra por bloque (BD)
        db_desc = st.session_state.get("db_descuentos", {}) if isinstance(st.session_state.get("db_descuentos", None), dict) else {}
        f_cart = 1.0 - (float(db_desc.get("cartoncillo", 0.0)) / 100.0)
        f_or = 1.0 - (float(db_desc.get("ondulado_rigidos", 0.0)) / 100.0)
        f_narba = 1.0 - (float(db_desc.get("narba", 0.0)) / 100.0)

        for pid, p in st.session_state.piezas_dict.items():
            c_cart_cara = c_cart_dorso = 0.0
            c_ondulado = 0.0
            c_rigido = 0.0
            c_contracolado = 0.0
            c_imp_total = 0.0
            c_pel_total = 0.0
            c_troquel_taller = 0.0
            c_plotter = 0.0
            c_stamping = 0.0

            # Impresiones por cantidad (multi-tirada) - POR FORMATO:
            # Solo afecta a coste de impresión y a la merma extra de cartoncillo por impresión.
            partes_imp_units = obtener_partes_impresion_por_formato(int(pid), int(q_n))
            n_impresiones_qty = len(partes_imp_units) if partes_imp_units else 1

            pl = float(p.get("pliegos", 1.0))
            nb = int(math.ceil(q_n * pl))
            mp_def, _mi_ign = calcular_mermas_estandar(q_n, pliegos_por_ud=pl, es_digital=False, n_tintas=4, barniz=False)
            _ss_autoupdate_merma_proc(int(pid), int(q_n), int(mp_def))
            merma_proc_hojas = _ss_get_merma_proc(int(pid), int(q_n), int(mp_def))
            hp_produccion = nb + int(merma_proc_hojas)

            im_cara = p.get("im", "No")
            im_dorso = p.get("im_d", "No")

            imprime_cara = (im_cara != "No")
            imprime_dorso = (p.get("pd", "Ninguno") != "Ninguno" and im_dorso != "No")

            # 👇 Merma de impresión depende del tipo (Offset vs Digital)
            # Multi-tirada: la merma extra de cartoncillo se cuenta 1 vez por impresión.
            if imprime_cara:
                if im_cara == "Digital":
                    merma_cara = int(merma_imp_digital_hojas)
                elif im_cara == "Offset":
                    mi_def_c = _merma_impresion_offset_por_pasadas(int(p.get("nt", 4)), bool(p.get("ba", False)))
                    _ss_autoupdate_merma_imp(int(pid), int(q_n), "cara", int(mi_def_c))
                    merma_cara = int(_ss_get_merma_imp(int(pid), int(q_n), "cara", int(mi_def_c)))
                else:
                    merma_cara = 0
                hp_papel_f = hp_produccion + (merma_cara * int(n_impresiones_qty))
            else:
                hp_papel_f = hp_produccion

            if imprime_dorso:
                if im_dorso == "Digital":
                    merma_d = int(merma_imp_digital_hojas)
                elif im_dorso == "Offset":
                    mi_def_d = _merma_impresion_offset_por_pasadas(int(p.get("nt_d", 4)), bool(p.get("ba_d", False)))
                    _ss_autoupdate_merma_imp(int(pid), int(q_n), "dorso", int(mi_def_d))
                    merma_d = int(_ss_get_merma_imp(int(pid), int(q_n), "dorso", int(mi_def_d)))
                else:
                    merma_d = 0
                hp_papel_d = hp_produccion + (merma_d * int(n_impresiones_qty))
            else:
                hp_papel_d = hp_produccion

            w = float(p.get("w", 0))
            h = float(p.get("h", 0))
            m2_papel = (w * h) / 1_000_000 if (w > 0 and h > 0) else 0.0

            # Capas de cartoncillo seleccionadas (cara/dorso)
            has_cart_cara = (p.get("pf", "Ninguno") != "Ninguno")
            has_cart_dorso = (p.get("pd", "Ninguno") != "Ninguno")
            capas_cartoncillo = (1 if has_cart_cara else 0) + (1 if has_cart_dorso else 0)

            # ✅ Reglas de CONTRACOLADO:
            # - Solo se contracola si hay que pegar capas entre sí.
            # - Si hay base (plancha ondulado o rígido) + cartoncillo: 1 contracolado por cada cara con cartoncillo.
            # - Si NO hay base (solo cartoncillo):
            #     · 1 cara: NO hay contracolado
            #     · cara + dorso: 1 contracolado (pegarlos entre sí)
            has_base_ondulado = (p.get("tipo_base") == "Ondulado/Cartón" and p.get("pl", "Ninguna") != "Ninguna")
            has_base_rigido = (p.get("tipo_base") == "Material Rígido" and (
                bool(p.get("rig_manual", False)) or p.get("mat_rigido", "Ninguno") != "Ninguno"
            ))
            has_base = (has_base_ondulado or has_base_rigido)

            if has_base:
                capas_contracolado = (1 if has_cart_cara else 0) + (1 if has_cart_dorso else 0)
            else:
                capas_contracolado = 1 if (has_cart_cara and has_cart_dorso) else 0

            if p.get("tipo_base") == "Material Rígido":
                if bool(p.get("rig_manual", False)):
                    mw, mh = float(p.get("rig_w", 0)), float(p.get("rig_h", 0))
                    precio_hoja = float(p.get("rig_precio_ud", 0.0))
                else:
                    if p.get("mat_rigido") != "Ninguno":
                        info = db["rigidos"][p["mat_rigido"]]
                        mw, mh = float(info["w"]), float(info["h"])
                        precio_hoja = float(info["precio_ud"]) * f_or
                    else:
                        mw = mh = precio_hoja = 0.0

                if w > 0 and h > 0 and mw > 0 and mh > 0:
                    y1 = int(mw // w) * int(mh // h)
                    y2 = int(mw // h) * int(mh // w)
                    by = max(y1, y2)
                else:
                    by = 0

                if by > 0:
                    n_net = math.ceil(hp_produccion / by)
                    if capas_contracolado == 0:
                        n_pl = n_net + merma_rigido_fija(n_net)
                    else:
                        n_pl = math.ceil(n_net * 1.02)
                    c_rigido = n_pl * precio_hoja

                    debug_log.append({
                        "qty": q_n,
                        "pieza": p.get("nombre",""),
                        "tipo": "rigido",
                        "by": by,
                        "hojas_netas": n_net,
                        "hojas_total": n_pl,
                        "precio_hoja": precio_hoja,
                        "coste": c_rigido,
                        "merma_regla": "fija" if capas_contracolado == 0 else "2%"
                    })
            else:
                if p.get("pl", "Ninguna") != "Ninguna":
                    if bool(p.get("pl_dif", False)) and float(p.get("pl_h", 0)) > 0 and float(p.get("pl_w", 0)) > 0:
                        m2_plancha = (float(p["pl_w"]) * float(p["pl_h"])) / 1_000_000
                    else:
                        m2_plancha = m2_papel
                    c_ondulado = hp_produccion * m2_plancha * float(db["planchas"][p["pl"]][p.get("ap","B/C")]) * f_or
                    # Flexografía: coste fijo por plancha (no depende de cantidad)
                    if bool(p.get("flexografia", False)):
                        c_ondulado += float(db.get("flexografia", {}).get("arreglo", 180.0))

            if p.get("pf", "Ninguno") != "Ninguno" and m2_papel > 0:
                c_cart_cara = hp_papel_f * m2_papel * (float(p.get("gf", 0))/1000.0) * float(db["cartoncillo"][p["pf"]]["precio_kg"]) * f_cart
            if p.get("pd", "Ninguno") != "Ninguno" and m2_papel > 0:
                c_cart_dorso = hp_papel_d * m2_papel * (float(p.get("gd", 0))/1000.0) * float(db["cartoncillo"][p["pd"]]["precio_kg"]) * f_cart

            peg_rate = float(db["planchas"]["Microcanal / Canal 3"]["peg"]) * f_narba
            if capas_contracolado > 0 and m2_papel > 0:
                c_contracolado = hp_produccion * m2_papel * peg_rate * capas_contracolado

            c_imp_cara = 0.0
            c_imp_dorso = 0.0

            # FR24: tinta especial con coste extra por m² impreso.
            fr24_enabled = bool(p.get("fr24", False))
            try:
                fr24_rate = float(p.get("fr24_rate", 0.05))
            except Exception:
                fr24_rate = 0.05
            fr24_m2_total = 0.0

            # Impresión (multi-tirada): el coste se calcula por cada impresión (tirada).
            # La merma de impresión se aplica por tirada según la cantidad seleccionada.
            if p.get("im","No") == "Digital":
                for q_run in (partes_imp_units if partes_imp_units else [int(q_n)]):
                    nb_run = int(q_run) * float(p.get("pliegos", 1.0))
                    hp_imp_run = nb_run + merma_imp_digital_hojas
                    c_imp_cara += hp_imp_run * m2_papel * 6.5
                    if fr24_enabled and m2_papel > 0:
                        fr24_m2_total += hp_imp_run * m2_papel
                    if bool(p.get("ld", False)):
                        c_pel_total += hp_imp_run * m2_papel * float(db.get("laminado_digital", 3.5))
            elif p.get("im","No") == "Offset":
                tintas_cara = int(p.get("nt",0)) + (1 if bool(p.get("ba",False)) else 0)
                for q_run in (partes_imp_units if partes_imp_units else [int(q_n)]):
                    nb_run = int(round(int(q_run) * float(p.get("pliegos", 1.0))))
                    c_imp_cara += coste_offset_por_tinta(int(nb_run)) * tintas_cara
                    if fr24_enabled and m2_papel > 0:
                        fr24_m2_total += nb_run * m2_papel

            if p.get("im_d","No") == "Digital":
                for q_run in (partes_imp_units if partes_imp_units else [int(q_n)]):
                    nb_run = int(q_run) * float(p.get("pliegos", 1.0))
                    hp_imp_run = nb_run + merma_imp_digital_hojas
                    c_imp_dorso += hp_imp_run * m2_papel * 6.5
                    if fr24_enabled and m2_papel > 0:
                        fr24_m2_total += hp_imp_run * m2_papel
                    if bool(p.get("ld_d", False)):
                        c_pel_total += hp_imp_run * m2_papel * float(db.get("laminado_digital", 3.5))
            elif p.get("im_d","No") == "Offset":
                tintas_dorso = int(p.get("nt_d",0)) + (1 if bool(p.get("ba_d",False)) else 0)
                for q_run in (partes_imp_units if partes_imp_units else [int(q_n)]):
                    nb_run = int(round(int(q_run) * float(p.get("pliegos", 1.0))))
                    c_imp_dorso += coste_offset_por_tinta(int(nb_run)) * tintas_dorso
                    if fr24_enabled and m2_papel > 0:
                        fr24_m2_total += nb_run * m2_papel

            c_imp_total = c_imp_cara + c_imp_dorso

            c_fr24 = 0.0
            if fr24_enabled and fr24_rate > 0 and fr24_m2_total > 0:
                c_fr24 = fr24_m2_total * fr24_rate
                c_imp_total += c_fr24

            c_pel_cara = 0.0
            c_pel_dorso = 0.0
            if p.get("pel","Sin Peliculado") != "Sin Peliculado":
                c_pel_cara = hp_produccion * m2_papel * float(db["peliculado"][p["pel"]]) * f_narba
            if p.get("pd","Ninguno") != "Ninguno" and p.get("pel_d","Sin Peliculado") != "Sin Peliculado":
                c_pel_dorso = hp_produccion * m2_papel * float(db["peliculado"][p["pel_d"]]) * f_narba
            c_pel_total += (c_pel_cara + c_pel_dorso)

            cor_sel = p.get("cor_default", "Troquelado")
            if isinstance(p.get("cor_by_qty", {}), dict):
                cor_sel = p["cor_by_qty"].get(str(q_n), cor_sel)

            cat = "Grande (> 1000x700)" if (h>1000 or w>700) else ("Pequeño (< 1000x700)" if (h<1000 and w<700) else "Mediano (Estándar)")
            c_troquel_taller = 0.0
            c_plotter = 0.0

            # Pre-cálculo para corte (Troquelado/Plotter):
            # - Evita NameError (hp_corte siempre definido).
            # - Aplica el ajuste manual "piezas por troquel" también al Plotter.
            hp_corte = int(math.ceil(float(hp_produccion)))
            auto_piezas = 1
            troquel_piezas_manual = int(p.get("troquel_piezas", 0) or 0)
            stamping_enabled = bool(p.get("stamping", False))
            if cor_sel in ("Troquelado", "Plotter") or stamping_enabled:
                try:
                    _pl_tmp = float(p.get("pliegos", 1.0) or 1.0)
                    if _pl_tmp > 0 and _pl_tmp < 1.0:
                        auto_piezas = max(1, int(round(1.0 / _pl_tmp)))
                except Exception:
                    auto_piezas = 1
                if troquel_piezas_manual <= 0:
                    troquel_piezas_manual = auto_piezas
                troquel_factor = float(auto_piezas) / float(max(1, troquel_piezas_manual))
                hp_corte = int(math.ceil(float(hp_produccion) * troquel_factor))

            if cor_sel == "Troquelado":
                arr = float(db["troquelado"][cat]["arranque"]) * f_narba if bool(p.get("cobrar_arreglo", True)) else 0.0
                tiro = float(db["troquelado"][cat]["tiro"]) * f_narba
                c_troquel_taller = arr + (hp_corte * tiro)
            elif cor_sel == "Plotter":
                c_plotter = hp_corte * float(db["plotter"]["precio_hoja"])
            else:
                # "Sin corte": no suma coste de troquel ni plotter
                pass

            # Stamping (si aplica): arreglo + pisadas + película (m²)
            if bool(p.get("stamping", False)):
                try:
                    sw = float(p.get("stamping_w", 0) or 0)
                    sh = float(p.get("stamping_h", 0) or 0)
                except Exception:
                    sw, sh = 0.0, 0.0
                area_m2 = max(0.0, (sw/1000.0) * (sh/1000.0))
                arr_s = float(db.get("stamping", {}).get("arreglo", 168.0)) if bool(p.get("stamping_cobrar_arreglo", True)) else 0.0
                pisada = float(db.get("stamping", {}).get("pisada", 0.21))
                peli = float(db.get("stamping", {}).get("pelicula_m2", 0.39))
                c_stamping = arr_s + (hp_corte * pisada) + (hp_corte * area_m2 * peli)

            sub = c_cart_cara + c_cart_dorso + c_ondulado + c_rigido + c_contracolado + c_imp_total + c_pel_total + c_troquel_taller + c_plotter + c_stamping
            coste_f += sub

            det_f.append({
                "Pieza": p.get("nombre",""),
                "Cartoncillo Cara": c_cart_cara,
                "Cartoncillo Dorso": c_cart_dorso,
                "Plancha Ondulado": c_ondulado,
                "Material Rígido": c_rigido,
                "Contracolado": c_contracolado,
                "Impresión": c_imp_total,
                "Peliculado": c_pel_total,
                "Corte (Troquel/Plotter)": c_troquel_taller + c_plotter,
                "Stamping": c_stamping,
                "Subtotal Pieza": sub,
                "Corte Seleccionado": cor_sel
            })

            tot_cat["materiales"]["cartoncillo"] += (c_cart_cara + c_cart_dorso)
            tot_cat["materiales"]["ondulado"] += c_ondulado
            tot_cat["materiales"]["rigidos"] += c_rigido
            tot_cat["procesos"]["contracolado"] += c_contracolado
            tot_cat["procesos"]["impresion"] += c_imp_total
            tot_cat["procesos"]["peliculado"] += c_pel_total
            tot_cat["procesos"]["corte"] += (c_troquel_taller + c_plotter)
            tot_cat["procesos"]["stamping"] += c_stamping

        c_ext = sum(float(e.get("coste",0.0)) * float(e.get("cantidad",1.0)) * q_n for e in st.session_state.lista_extras_grabados)
        tot_cat["materiales"]["extras"] += c_ext

        c_mo_man = (seg_man_total/3600.0)*18.0*q_n
        c_mo_dif = (q_n * float(dif_ud))
        c_mo = c_mo_man + c_mo_dif
        tot_cat["procesos"]["manipulacion"] += c_mo_man
        tot_cat["procesos"]["dificultad"] += c_mo_dif

        # Opcionales (a parte): Rellenado + Armado (se muestran como opción al cliente)
        # Se calcula un PVP opcional aplicando el mismo margen de trabajo (st.session_state.margen).
        # Se guardan también los costes base sin margen para uso interno / compatibilidad.
        margen_trabajo = float(st.session_state.margen) if "margen" in st.session_state else 1.0

        c_opt_rell_coste = (seg_rell_total/3600.0)*18.0*q_n if bool(st.session_state.rell_enabled) else 0.0
        c_opt_arm_coste = (seg_arm_total/3600.0)*18.0*q_n if bool(st.session_state.arm_enabled) else 0.0

        c_opt_rell_pvp = c_opt_rell_coste * margen_trabajo
        c_opt_arm_pvp = c_opt_arm_coste * margen_trabajo

        opcionales_cost = {
            # Valores que se muestran al cliente (con margen)
            "rellenado_total": float(c_opt_rell_pvp),
            "armado_total": float(c_opt_arm_pvp),
            "rellenado_unit": float(c_opt_rell_pvp / q_n) if q_n > 0 else 0.0,
            "armado_unit": float(c_opt_arm_pvp / q_n) if q_n > 0 else 0.0,
            # Costes internos sin margen
            "rellenado_total_coste": float(c_opt_rell_coste),
            "armado_total_coste": float(c_opt_arm_coste),
            "rellenado_unit_coste": float(c_opt_rell_coste / q_n) if q_n > 0 else 0.0,
            "armado_unit_coste": float(c_opt_arm_coste / q_n) if q_n > 0 else 0.0,
            "margen_aplicado": float(margen_trabajo),
        }

        emb_compra_total = 0.0
        emb_det = []
        for emb in st.session_state.embalajes:
            cu = float(emb.get("costes", {}).get(q_n, 0.0))
            emb_compra_total += cu * q_n
            emb_det.append({"nombre": emb.get("nombre",""), "tipo": emb.get("tipo",""), "material": emb.get("material",""), "coste_unit_compra": cu})

        # ✅ Venta de embalajes por opción (para mostrar en oferta si hay varias opciones)
        pv_emb_por_embalaje = []
        for j, emb in enumerate(st.session_state.embalajes):
            nombre_emb = str(emb.get("nombre", "")).strip() or f"EMB_{j+1}"
            cu_compra = float(emb.get("costes", {}).get(q_n, 0.0))
            pv_unit = cu_compra * margen_embalajes
            pv_tot = pv_unit * q_n
            nombre_key = re.sub(r"[\r\n\t]+", " ", nombre_emb)
            pv_emb_por_embalaje.append({
                "nombre": nombre_key,
                "unit": pv_unit,
                "total": pv_tot,
            })

        tot_cat["materiales"]["embalajes_compra"] += emb_compra_total

        ext_total = 0.0
        ext_det = []
        for ext in st.session_state.externos:
            val = float(ext.get("costes", {}).get(q_n, 0.0))
            if ext.get("modo", "Unitario (€/ud)") == "Unitario (€/ud)":
                coste = val * q_n
                tipo = "unitario"
            else:
                coste = val
                tipo = "total"
            ext_total += coste
            ext_det.append({"concepto": ext.get("concepto",""), "modo": ext.get("modo",""), "tipo_aplicado": tipo, "valor_input": val, "coste_total": coste})
        tot_cat["procesos"]["externos"] += ext_total

        pv_emb_total = (emb_compra_total * margen_embalajes)

        # Venta producido (excluye extras, embalajes y troquel)
        materiales_cost = float(
            tot_cat["materiales"]["cartoncillo"]
            + tot_cat["materiales"]["ondulado"]
            + tot_cat["materiales"]["rigidos"]
        )

        # Procesos incluye "externos" en el desglose de costes, pero comercialmente los queremos tratar como "Extras".
        procesos_cost_total = float(sum(tot_cat["procesos"].values()))  # incluye externos, manipulación y dificultad
        procesos_cost_sin_externos = float(procesos_cost_total - ext_total)

        pv_materiales_total = materiales_cost * margen
        pv_procesos_total = (procesos_cost_sin_externos * margen) + imp_fijo_pvp

        # ✅ Descuento SOLO sobre procesos (no afecta extras, embalajes ni troqueles).
        # Al mover "externos" a extras, tampoco se les aplica este descuento.
        pv_procesos_total = pv_procesos_total * (1.0 - (descuento_procesos / 100.0))

        pv_producido_total = pv_materiales_total + pv_procesos_total
        pv_material_unit = pv_producido_total / q_n

        # Extras comerciales = extras grabados + procesos externos
        pv_extras_total = ((c_ext + ext_total) * margen_extras)
        pv_extras_unit = pv_extras_total / q_n if q_n > 0 else 0.0

        # ✅ PV troquel (venta): solo debe imputarse a las cantidades que realmente van a TROQUELADO.
        # Si una cantidad va a Plotter (o Sin corte), NO debe cargar el coste del troquel en el sumatorio.
        tot_pv_trq = 0.0
        for _pid, _pz in st.session_state.piezas_dict.items():
            _cor_sel = _pz.get("cor_default", "Troquelado")
            if isinstance(_pz.get("cor_by_qty", {}), dict):
                _cor_sel = _pz["cor_by_qty"].get(str(q_n), _cor_sel)
            if str(_cor_sel) == "Troquelado":
                try:
                    tot_pv_trq += float(_pz.get("pv_troquel", 0.0) or 0.0)
                except Exception:
                    pass

        pvp_total_todo = pv_producido_total + pv_extras_total + pv_emb_total + tot_pv_trq
        unit_todo = pvp_total_todo / q_n

        # Unitario sin troquel: producido + embalaje + extras
        pvp_prod_emb_extras = pv_producido_total + pv_emb_total + pv_extras_total
        unit_prod_emb_extras = pvp_prod_emb_extras / q_n if q_n > 0 else 0.0

        res_final.append({
            "Cantidad": q_n,
            "Precio venta material (unitario)": f"{pv_material_unit:.3f}€",
            "Precio venta extras (unitario)": f"{pv_extras_unit:.3f}€",
            "Precio venta embalaje (unitario)": f"{(pv_emb_total/q_n):.3f}€",
            "Precio venta troquel (TOTAL)": f"{tot_pv_trq:.2f}€",
            "Precio venta unitario (prod+emb+extras)": f"{unit_prod_emb_extras:.3f}€",
            "Precio venta unitario (todo)": f"{unit_todo:.3f}€",
            "Precio venta total": f"{pvp_total_todo:.2f}€"
        })

        desc_full[q_n] = {
            "det_piezas": det_f,
            "embalajes": emb_det,
            "externos": ext_det,
            "mermas": {"impresion_digital_hojas": merma_imp_digital_hojas, "procesos_por_forma": deepcopy(st.session_state.get("mermas_proc_manual", {})), "impresion_offset_por_forma": deepcopy(st.session_state.get("mermas_imp_manual", {}))},
            "debug": debug_log
        }

        compras_legible[q_n] = {
            "Cantidad": q_n,
            "Materiales": tot_cat["materiales"],
            "Procesos": tot_cat["procesos"],
            "Detalle piezas": det_f,
            "Detalle embalajes": emb_det,
            "Detalle externos": ext_det,
            "Extras (detalle)": st.session_state.lista_extras_grabados,
            "Opcionales (a parte)": opcionales_cost
        }

        resumen_costes_export[q_n] = {
            "Cantidad": q_n,
            "materiales": {k: round(v, 4) for k, v in tot_cat["materiales"].items()},
            "procesos": {k: round(v, 4) for k, v in tot_cat["procesos"].items()},
            "totales": {
                "materiales_total": round(sum(tot_cat["materiales"].values()), 4),
                "procesos_total": round(sum(tot_cat["procesos"].values()), 4),
                "coste_total_compra_estimado": round(sum(tot_cat["materiales"].values()) + sum(tot_cat["procesos"].values()), 4)
            },
            "opcionales_a_parte": {
                # Valores mostrados al cliente (con margen)
                "rellenado_total": round(opcionales_cost.get("rellenado_total", 0.0), 4),
                "armado_total": round(opcionales_cost.get("armado_total", 0.0), 4),
                "rellenado_unit": round(opcionales_cost.get("rellenado_unit", 0.0), 6),
                "armado_unit": round(opcionales_cost.get("armado_unit", 0.0), 6),
                # Costes internos sin margen
                "rellenado_total_coste": round(opcionales_cost.get("rellenado_total_coste", 0.0), 4),
                "armado_total_coste": round(opcionales_cost.get("armado_total_coste", 0.0), 4),
                "rellenado_unit_coste": round(opcionales_cost.get("rellenado_unit_coste", 0.0), 6),
                "armado_unit_coste": round(opcionales_cost.get("armado_unit_coste", 0.0), 6),
                "margen_aplicado": round(opcionales_cost.get("margen_aplicado", float(st.session_state.margen)), 4)
            },
            "embalajes_venta_por_opcion": [
                {
                    "nombre": e.get("nombre",""),
                    "unit": round(float(e.get("unit", 0.0)), 6),
                    "total": round(float(e.get("total", 0.0)), 4),
                }
                for e in (pv_emb_por_embalaje if isinstance(pv_emb_por_embalaje, list) else [])
            ]
        }

safe_brf = re.sub(r'[\/*?:"<>|]', "", st.session_state.brf or "Ref").replace(" ", "_")
safe_cli = re.sub(r'[\/*?:"<>|]', "", st.session_state.cli or "Cli").replace(" ", "_")
safe_desc = re.sub(r'[\/*?:"<>|]', "", st.session_state.desc or "Oferta").replace(" ", "_")
# Incluir nº(s) de comercial en el nombre de archivo (si están informados)
c1_num = _parse_comercial_num(st.session_state.get('comercial_1', ''))
c2_num = _parse_comercial_num(st.session_state.get('comercial_2', ''))
com_parts = []
if c1_num is not None:
    com_parts.append(f"C{c1_num}")
if c2_num is not None:
    com_parts.append(f"C{c2_num}")
com_tag = "_".join(com_parts)
if com_tag:
    st.session_state._export_filename = f"{safe_brf}_{com_tag}_{safe_cli}_{safe_desc}.json"
else:
    st.session_state._export_filename = f"{safe_brf}_{safe_cli}_{safe_desc}.json"

resumen_compra_to_export = compras_legible if isinstance(compras_legible, dict) and len(compras_legible) > 0 else st.session_state.get("_imported_compras_legible")
resumen_costes_to_export = resumen_costes_export if isinstance(resumen_costes_export, dict) and len(resumen_costes_export) > 0 else st.session_state.get("_imported_resumen_costes")

export_data = construir_export(
    resumen_compra=resumen_compra_to_export,
    resumen_costes=resumen_costes_to_export
)
st.session_state._export_blob = json.dumps(export_data, indent=4, ensure_ascii=False)
st.session_state._json_downloaded = False
st.session_state._json_downloaded_filename = ""

# =========================================================
# SALIDAS
# =========================================================
def build_comercial_html(res_final_rows, desc_html, extras_html, emb_html, ext_html, tabla_html):
    return f"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Oferta - {st.session_state.cli or 'CLIENTE'}</title>
{CSS_COMERCIAL}
</head>
<body>
<div class='comercial-box'>
  <div class='comercial-header'>OFERTA COMERCIAL - {st.session_state.cli or 'CLIENTE'}</div>
  <div class='comercial-ref'>Ref. Briefing: {st.session_state.brf or '-'}</div>
  {desc_html}
  {extras_html}
  {emb_html}
  {ext_html}
  {tabla_html}
</div>
</body>
</html>
"""

if modo_comercial and res_final:
    manip_unit_txt = f"{t_input:g} {('min' if unidad_t=='Minutos' else 'seg')}/ud"
    manip_seg_txt = f"{seg_man_total:g} seg/ud"

    desc_html = "<div class='sec-title'>📋 Especificaciones del Proyecto</div>"
    desc_html += "<div class='card'>"
    desc_html += (
        "<div style='margin-bottom:10px;'>"
        "<span class='tag'>Manipulación</span>"
        f"<span class='small muted'><b>Tiempo/ud:</b> {manip_unit_txt} &nbsp;|&nbsp; <b>Equivalente:</b> {manip_seg_txt}</span>"
        "</div>"
    )

    # Opcionales (a parte)
    if bool(st.session_state.rell_enabled) or bool(st.session_state.arm_enabled):
        opt_lines = []
        if bool(st.session_state.rell_enabled):
            opt_lines.append(f"<span class='tag'>Rellenado</span><span class='small muted'>+ {seg_rell_total:g} seg/ud</span>")
        if bool(st.session_state.arm_enabled):
            opt_lines.append(f"<span class='tag'>Armado</span><span class='small muted'>+ {seg_arm_total:g} seg/ud</span>")
        desc_html += "<div style='margin-bottom:10px;'>"
        desc_html += "<span class='tag'>Opcionales</span> "
        desc_html += " &nbsp; ".join(opt_lines)
        desc_html += "</div>"


    # Notas / comentarios (solo si hay texto)
    _notas_txt = (st.session_state.get("notas", "") or "").strip()
    if _notas_txt:
        _notas_html = html.escape(_notas_txt).replace("\n", "<br>")
        desc_html += "<div style='margin-top:10px;'><span class='tag'>Notas</span></div>"
        desc_html += f"<div class='small' style='margin-top:6px; line-height:1.35;'>{_notas_html}</div>"

    for pid, p in st.session_state.piezas_dict.items():
        base_info = ""
        if p.get("tipo_base") == "Material Rígido":
            if bool(p.get("rig_manual", False)):
                base_info = f"Rígido Manual: {int(p.get('rig_w',0))}×{int(p.get('rig_h',0))} mm | {float(p.get('rig_precio_ud',0.0)):.2f}€/hoja"
            else:
                base_info = f"Rígido: {p.get('mat_rigido','')}"
        else:
            base_info = f"Ondulado: {p.get('pl','')} ({p.get('ap','')})"

        cara = f"{p.get('pf','')} ({p.get('gf',0)}g)"
        dorso = f"{p.get('pd','')} ({p.get('gd',0)}g)"
        imp_c = f"{p.get('im','No')}"
        imp_d = f"{p.get('im_d','No')}"
        pel_c = f"{p.get('pel','Sin Peliculado')}"
        pel_d = f"{p.get('pel_d','Sin Peliculado')}"

        tintas_c = ""
        if p.get("im","No") == "Offset":
            tintas_c = f" | <b>Tintas:</b> {int(p.get('nt',0))}" + (" + Barniz" if bool(p.get("ba",False)) else "")
        elif p.get("im","No") == "Digital":
            tintas_c = " | <b>Laminado:</b> " + ("Sí" if bool(p.get("ld",False)) else "No")

        tintas_d = ""
        if p.get("im_d","No") == "Offset":
            tintas_d = f" | <b>Tintas:</b> {int(p.get('nt_d',0))}" + (" + Barniz" if bool(p.get("ba_d",False)) else "")
        elif p.get("im_d","No") == "Digital":
            tintas_d = " | <b>Laminado:</b> " + ("Sí" if bool(p.get("ld_d",False)) else "No")

        corte = p.get("cor_default","Troquelado")
        trq = f"{float(p.get('pv_troquel',0.0)):.2f}€"

        # Varias impresiones (solo si está activado para esta forma) -> mostrar en oferta
        impresiones_info_html = ""
        enabled_all = st.session_state.get("impresiones_by_qty_fmt_enabled", {})
        enabled_fmt = False
        if isinstance(enabled_all, dict):
            enabled_fmt = bool(enabled_all.get(str(int(pid)), False))
        if enabled_fmt:
            q_list = []
            try:
                q_list = [int(r.get("Cantidad", 0)) for r in res_final if int(r.get("Cantidad", 0)) > 0]
            except Exception:
                q_list = []
            lines = []
            for qv in q_list:
                partes = obtener_partes_impresion_por_formato(int(pid), int(qv))
                if isinstance(partes, list) and len(partes) > 1:
                    try:
                        parts_txt = "+".join(str(int(x)) for x in partes)
                    except Exception:
                        parts_txt = "+".join(str(x) for x in partes)
                    lines.append(f"{int(qv)} uds → {parts_txt}")
            if lines:
                impresiones_info_html = "<br><b>Varias impresiones:</b> " + " &nbsp;|&nbsp; ".join(lines)


        desc_html += (
            "<div style='margin-bottom:8px;'>"
            f"<span class='tag'>{p.get('nombre','')}</span>"
            f"<span class='small muted'>{int(p.get('h',0))}×{int(p.get('w',0))} mm | Pliegos/ud: {float(p.get('pliegos',1.0)):.4f}</span>"
            "<div class='small'>"
            f"<b>Soporte:</b> {base_info}<br>"
            f"<b>Cara:</b> {cara} | <b>Imp:</b> {imp_c}{tintas_c} | <b>Pel:</b> {pel_c}<br>"
            f"<b>Dorso:</b> {dorso} | <b>Imp:</b> {imp_d}{tintas_d} | <b>Pel:</b> {pel_d}<br>"
            f"<b>Corte (def):</b> {corte} | <b>Troquel (venta):</b> {trq}" + impresiones_info_html + "</div></div>"
        )
    desc_html += "</div>"

    extras_html = "<div class='sec-title'>➕ Materiales extra</div><div class='card'>"
    if st.session_state.lista_extras_grabados:
        for e in st.session_state.lista_extras_grabados:
            extras_html += f"<div class='small'>• <b>{e.get('nombre','')}</b> — {float(e.get('cantidad',1.0))} /ud — {float(e.get('coste',0.0)):.4f}€ compra</div>"
    else:
        extras_html += "<div class='small muted'>Sin extras.</div>"
    extras_html += "</div>"

    emb_html = "<div class='sec-title'>📦 Embalajes</div><div class='card'>"
    for emb in st.session_state.embalajes:
        L, W, H = emb["dims"].get("L",0), emb["dims"].get("W",0), emb["dims"].get("H",0)
        emb_html += f"<div class='small'>• <b>{emb.get('nombre','')}</b> — {emb.get('tipo','')} — {emb.get('material','')} — {L:.0f}×{W:.0f}×{H:.0f} mm</div>"
    emb_html += "</div>"

    ext_html = "<div class='sec-title'>📌 Externos</div><div class='card'>"
    if st.session_state.externos:
        for ext in st.session_state.externos:
            ext_html += f"<div class='small'>• <b>{ext.get('concepto','')}</b> — {ext.get('modo','')}</div>"
    else:
        ext_html += "<div class='small muted'>Sin externos.</div>"
    ext_html += "</div>"

    rows_list = []
    for r in res_final:
        rows_list.append(
            "<tr>"
            f"<td><b>{r['Cantidad']}</b></td>"
            f"<td>{r['Precio venta material (unitario)']}</td>"
            f"<td>{r.get('Precio venta extras (unitario)', '0.000€')}</td>"
            f"<td>{r['Precio venta embalaje (unitario)']}</td>"
            f"<td>{r['Precio venta troquel (TOTAL)']}</td>"
            f"<td>{r.get('Precio venta unitario (prod+emb+extras)', '0.000€')}</td>"
            f"<td><b style='color:#1E88E5;'>{r['Precio venta unitario (todo)']}</b></td>"
            f"<td>{r['Precio venta total']}</td>"
            "</tr>"
        )
    rows = "".join(rows_list)

    tabla = (
        "<div class='sec-title'>€ Precios de venta</div>"
        "<table class='comercial-table'>"
        "<tr>"
        "<th>Cantidad</th>"
        "<th>Venta material (unit)</th>"
        "<th>Venta extras+externos (unit)</th>"
        "<th>Venta embalaje (unit)</th>"
        "<th>Troquel (TOTAL)</th>"
        "<th>Unitario (prod+emb+extras)</th>"
        "<th>UNITARIO (TODO)</th>"
        "<th>VENTA TOTAL</th>"
        "</tr>"
        f"{rows}"
        "</table>"
        "<div class='small muted' style='margin-top:10px;'>"
        "* &quot;Venta material&quot; incluye el producido (materiales + procesos internos) excluyendo extras, procesos externos, embalajes y troqueles. &quot;Extras+externos&quot; incluye extras grabados y procesos externos. IVA no incluido."
        "</div>"
    )


    # Opciones de embalaje (si hay más de 1)
    emb_opts_html = ""
    try:
        if isinstance(st.session_state.embalajes, list) and len(st.session_state.embalajes) > 1:
            emb_opts_html += "<div class='sec-title'>📦 Opciones de embalaje</div>"
            emb_opts_html += "<div class='card'>"
            emb_opts_html += "<div class='small muted'>Precios de embalaje por opción (no altera el precio principal mostrado arriba).</div>"
            for q in sorted(resumen_costes_export.keys()):
                emb_opts_html += f"<div style='margin-top:10px; font-weight:700;'>Cantidad: {int(q)} uds</div>"
                emb_opts_html += "<table class='comercial-table' style='margin-top:6px;'>"
                emb_opts_html += "<tr><th>Embalaje</th><th>€/ud</th><th>Total</th></tr>"
                opts = (resumen_costes_export.get(q, {}) or {}).get("embalajes_venta_por_opcion", [])
                if isinstance(opts, list) and opts:
                    for opt in opts:
                        emb_opts_html += f"<tr><td>{opt.get('nombre','')}</td><td>{float(opt.get('unit',0.0)):.3f}€</td><td>{float(opt.get('total',0.0)):.2f}€</td></tr>"
                emb_opts_html += "</table>"
            emb_opts_html += "</div>"
    except Exception:
        emb_opts_html = ""

        # Opcionales (a parte) - tabla
    opc_html = ""
    if bool(st.session_state.rell_enabled) or bool(st.session_state.arm_enabled):
        opc_html += "<div class='sec-title'>🧩 Opcionales (a parte)</div>"
        opc_html += "<div class='card'>"
        opc_html += f"<div class='small muted'>Precios opcionales NO incluidos en el precio mostrado.</div>"
        opc_html += "<table class='comercial-table' style='margin-top:10px;'>" \
                   "<tr><th>Cantidad</th><th>Rellenado (€/ud)</th><th>Rellenado (TOTAL)</th><th>Armado (€/ud)</th><th>Armado (TOTAL)</th></tr>"
        for row in resumen_costes_export.values():
            q = int(row.get("Cantidad", 0))
            op = row.get("opcionales_a_parte", {}) or {}
            opc_html += f"<tr><td>{q}</td><td>{float(op.get('rellenado_unit',0.0)):.3f}€</td><td>{float(op.get('rellenado_total',0.0)):.2f}€</td><td>{float(op.get('armado_unit',0.0)):.3f}€</td><td>{float(op.get('armado_total',0.0)):.2f}€</td></tr>"
        opc_html += "</table></div>"

    oferta_html = build_comercial_html(res_final, desc_html, extras_html, emb_html, (ext_html + emb_opts_html + opc_html), tabla)
    safe_desc = re.sub(r'[\/*?:"<>|]', "", st.session_state.desc or "Oferta").replace(" ", "_")
    # Incluir nº(s) de comercial en el nombre de archivo (si están informados)
    c1_num = _parse_comercial_num(st.session_state.get('comercial_1', ''))
    c2_num = _parse_comercial_num(st.session_state.get('comercial_2', ''))
    com_parts = []
    if c1_num is not None:
        com_parts.append(f"C{c1_num}")
    if c2_num is not None:
        com_parts.append(f"C{c2_num}")
    com_tag = "_".join(com_parts)
    if com_tag:
        fname_html = f"OFERTA_{safe_brf}_{com_tag}_{safe_cli}_{safe_desc}.html"
    else:
        fname_html = f"OFERTA_{safe_brf}_{safe_cli}_{safe_desc}.html"

    # Acceso rápido también en el panel lateral (sin quitar el botón de arriba)
    with st.sidebar:
        st.divider()
        st.subheader("📄 Oferta comercial")
        st.download_button(
            "⬇️ Descargar OFERTA (HTML)",
            data=oferta_html.encode("utf-8"),
            file_name=fname_html,
            mime="text/html",
            use_container_width=True,
            key="dl_oferta_html_sidebar"
        )


    st.download_button(
        "⬇️ Descargar VISTA OFERTA (HTML)",
        data=oferta_html.encode("utf-8"),
        file_name=fname_html,
        mime="text/html",
        use_container_width=True
    )

    st.markdown(
        "<div class='comercial-box'>"
        f"<div class='comercial-header'>OFERTA COMERCIAL - {st.session_state.cli or 'CLIENTE'}</div>"
        f"<div class='comercial-ref'>Ref. Briefing: {st.session_state.brf or '-'}</div>"
        f"{desc_html}{extras_html}{emb_html}{ext_html}{emb_opts_html}{opc_html}{tabla}"
        "</div>",
        unsafe_allow_html=True
    )
else:
    if res_final:
        st.header(f"📊 Resumen de Venta: {st.session_state.cli}")
        df = pd.DataFrame(res_final)[[
            "Cantidad",
            "Precio venta material (unitario)",
            "Precio venta extras (unitario)",
            "Precio venta embalaje (unitario)",
            "Precio venta troquel (TOTAL)",
            "Precio venta unitario (prod+emb+extras)",
            "Precio venta unitario (todo)",
            "Precio venta total"
        ]]
        st.dataframe(df, use_container_width=True)

# =========================================================

# =========================================================
# TAB AUDITORÍA (SIEMPRE)
# =========================================================
with tab_auditoria:
    st.subheader("🧾 Auditoría de cálculos (trazabilidad)")

    lista_cants_aud = parse_cantidades(st.session_state.cants_str_saved)

    if not lista_cants_aud:
        st.info("No hay cantidades definidas para auditar.")
    else:
        q_sel = st.selectbox("Cantidad a auditar:", lista_cants_aud, key="aud_sel_qty")

        # Resumen inputs principales
        with st.expander("🔎 Entradas principales del proyecto", expanded=False):
            st.write(
                {
                    "briefing": st.session_state.get("brief", ""),
                    "comercial_1": st.session_state.get("comercial_1", ""),
                    "comercial_2": st.session_state.get("comercial_2", ""),
                    "cliente": st.session_state.get("cli", ""),
                    "descripcion": st.session_state.get("desc", ""),
                    "margen": st.session_state.get("margen", None),
                }
            )

        piezas = st.session_state.get("piezas_dict", {}) or {}
        if not isinstance(piezas, dict) or not piezas:
            st.info("No hay formas definidas.")
        else:
            # Tabla: por forma, mostrar matemáticamente hojas netas, mermas y pasadas
            rows = []
            for pid, p in piezas.items():
                try:
                    pid_i = int(pid)
                except Exception:
                    pid_i = int(str(pid)) if str(pid).isdigit() else 0

                nombre = p.get("nombre", f"Forma {pid}")

                # Formato (pliegos por unidad)
                try:
                    pliegos_por_ud = float(p.get("pliegos", 1.0))
                except Exception:
                    pliegos_por_ud = 1.0

                # Hojas netas reales (ajustadas por formato)
                try:
                    hojas_netas = int(math.ceil(float(q_sel) * float(pliegos_por_ud)))
                except Exception:
                    hojas_netas = int(q_sel)

                # Merma procesos (tabla) y valor final (editable)
                mp_tabla = int(_tabla_merma_procesos_offset(hojas_netas))
                mp_final = int(_ss_get_merma_proc(int(pid_i), int(q_sel), int(mp_tabla)))

                mp_manual = False
                try:
                    mp_manual = str(pid) in st.session_state.get("mermas_proc_manual", {}) and str(int(q_sel)) in st.session_state.mermas_proc_manual.get(str(pid), {})
                except Exception:
                    mp_manual = False

                # Impresión (cara)
                im_c = str(p.get("im", "No")).strip()
                is_offset_c = im_c.lower() == "offset"
                try:
                    nt_c = int(p.get("nt", 4))
                except Exception:
                    nt_c = 0
                ba_c = bool(p.get("ba", False))
                apps_c = (max(1, max(0, nt_c)) + (1 if ba_c else 0)) if is_offset_c else 0
                pasadas_c = int(math.ceil(apps_c / 4.0)) if is_offset_c else 0
                mi_def_c = int(_merma_impresion_offset_por_pasadas(nt_c, ba_c)) if is_offset_c else 0
                mi_final_c = int(_ss_get_merma_imp(int(pid_i), int(q_sel), "cara", int(mi_def_c))) if is_offset_c else 0

                mi_manual_c = False
                try:
                    mi_manual_c = (
                        str(pid) in st.session_state.get("mermas_imp_manual", {})
                        and str(int(q_sel)) in st.session_state.mermas_imp_manual.get(str(pid), {})
                        and isinstance(st.session_state.mermas_imp_manual[str(pid)][str(int(q_sel))], dict)
                        and "cara" in st.session_state.mermas_imp_manual[str(pid)][str(int(q_sel))]
                    )
                except Exception:
                    mi_manual_c = False

                # Impresión (dorso)
                im_d = str(p.get("im_d", "No")).strip()
                is_offset_d = im_d.lower() == "offset"
                try:
                    nt_d = int(p.get("nt_d", 4))
                except Exception:
                    nt_d = 0
                ba_d = bool(p.get("ba_d", False))
                apps_d = (max(1, max(0, nt_d)) + (1 if ba_d else 0)) if is_offset_d else 0
                pasadas_d = int(math.ceil(apps_d / 4.0)) if is_offset_d else 0
                mi_def_d = int(_merma_impresion_offset_por_pasadas(nt_d, ba_d)) if is_offset_d else 0
                mi_final_d = int(_ss_get_merma_imp(int(pid_i), int(q_sel), "dorso", int(mi_def_d))) if is_offset_d else 0

                mi_manual_d = False
                try:
                    mi_manual_d = (
                        str(pid) in st.session_state.get("mermas_imp_manual", {})
                        and str(int(q_sel)) in st.session_state.mermas_imp_manual.get(str(pid), {})
                        and isinstance(st.session_state.mermas_imp_manual[str(pid)][str(int(q_sel))], dict)
                        and "dorso" in st.session_state.mermas_imp_manual[str(pid)][str(int(q_sel))]
                    )
                except Exception:
                    mi_manual_d = False

                # FR24 (si aplica)
                fr24_on = bool(p.get("fr24_on", False))
                try:
                    fr24_eur_m2 = float(p.get("fr24_eur_m2", 0.05))
                except Exception:
                    fr24_eur_m2 = 0.05

                rows.append(
                    {
                        "Forma": nombre,
                        "Pliegos/Ud": pliegos_por_ud,
                        "Uds": int(q_sel),
                        "Hojas netas": hojas_netas,
                        "Merma proceso (tabla)": mp_tabla,
                        "Merma proceso (final)": mp_final,
                        "Merma proc editada": "Sí" if mp_manual else "No",
                        "Impr. cara": im_c,
                        "Tintas cara": nt_c if is_offset_c else "",
                        "Barniz cara": "Sí" if (is_offset_c and ba_c) else ("No" if is_offset_c else ""),
                        "Apps cara": apps_c if is_offset_c else "",
                        "Pasadas cara": pasadas_c if is_offset_c else "",
                        "Merma imp cara (def)": mi_def_c if is_offset_c else "",
                        "Merma imp cara (final)": mi_final_c if is_offset_c else "",
                        "Merma imp cara editada": "Sí" if mi_manual_c else ("No" if is_offset_c else ""),
                        "Impr. dorso": im_d,
                        "Tintas dorso": nt_d if is_offset_d else "",
                        "Barniz dorso": "Sí" if (is_offset_d and ba_d) else ("No" if is_offset_d else ""),
                        "Apps dorso": apps_d if is_offset_d else "",
                        "Pasadas dorso": pasadas_d if is_offset_d else "",
                        "Merma imp dorso (def)": mi_def_d if is_offset_d else "",
                        "Merma imp dorso (final)": mi_final_d if is_offset_d else "",
                        "Merma imp dorso editada": "Sí" if mi_manual_d else ("No" if is_offset_d else ""),
                        "FR24": "Sí" if fr24_on else "No",
                        "FR24 €/m²": fr24_eur_m2 if fr24_on else "",
                    }
                )

            df_aud = pd.DataFrame(rows)
            st.dataframe(df_aud, use_container_width=True)

            # Fórmulas (explicación matemática) para el usuario
            with st.expander("📐 Fórmulas aplicadas (esta cantidad)", expanded=False):
                st.markdown(
                    "- **Hojas netas reales (por forma y cantidad)**  \n"
                    "  `hojas_netas = ceil(uds * pliegos_por_ud)`\n\n"
                    "- **Merma procesos (OFFSET)** (según tabla)  \n"
                    "  Se evalúa la tabla con `hojas_netas` y devuelve la merma correspondiente (editable).\n\n"
                    "- **Merma impresión OFFSET (por lado)**  \n"
                    "  `apps = max(1, tintas) + (1 si barniz else 0)`  \n"
                    "  `pasadas = ceil(apps / 4)`  \n"
                    "  `merma_imp = 100 + 50 * (pasadas - 1)`  (editable)\n\n"
                    "> Nota: si has editado manualmente una merma, la app ya no la sobreescribe automáticamente."
                )

        # =========================================================
        # Costes de materiales y procesos (con fórmulas matemáticas)
        # =========================================================
        comp_aud = compras_legible.get(q_sel, {}) if isinstance(compras_legible, dict) else {}
        if comp_aud:
            with st.expander("💶 Costes de materiales y procesos (con fórmulas)", expanded=False):
                # 1) Totales por categoría (lo que realmente se está usando en el cálculo)
                st.markdown("### Totales por categoría (esta cantidad)")
                materiales_tot = (resumen_costes_export.get(q_sel, {}).get("materiales", {}) if isinstance(resumen_costes_export, dict) else {}) or {}
                procesos_tot = (resumen_costes_export.get(q_sel, {}).get("procesos", {}) if isinstance(resumen_costes_export, dict) else {}) or {}
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Materiales**")
                    if materiales_tot:
                        st.dataframe(pd.DataFrame([materiales_tot]), use_container_width=True)
                    else:
                        st.caption("Sin materiales.")
                with c2:
                    st.markdown("**Procesos**")
                    if procesos_tot:
                        st.dataframe(pd.DataFrame([procesos_tot]), use_container_width=True)
                    else:
                        st.caption("Sin procesos.")

                st.markdown("### Fórmulas aplicadas por proceso/material")
                st.markdown("""- **Cartoncillo (cara/dorso)**:  
  `coste = hp_papel * m2_papel * (gramaje_g_m2/1000) * precio_kg * f_cart`  
  donde `hp_papel = hp_produccion + (merma_impresión * nº_impresiones)`

- **Contracolado**:  
  `coste = hp_produccion * m2_papel * peg_rate * capas_contracolado`

- **Impresión DIGITAL** (por tirada):  
  `coste = (nb_run + merma_digital) * m2_papel * 6.5`  
  y si hay laminado digital: `+ (nb_run + merma_digital) * m2_papel * precio_laminado_digital`

- **Impresión OFFSET** (por tirada):  
  `coste = coste_offset_por_tinta(nb_run) * (tintas + barniz)`

- **FR24** (si está activado):  
  `extra_FR24 = (m2_impresos_totales) * eur_m2`

- **Peliculado (OFFSET)**:  
  `coste = hp_produccion * m2_papel * precio_peliculado * f_narba`

- **Corte / Troquelado**:  
  `coste = arranque + (hp_produccion * tiro)`  (si se cobra arreglo)

- **Corte / Plotter**:  
  `coste = hp_produccion * precio_hoja_plotter`

> En Auditoría se muestran también las **sustituciones numéricas** para cada forma.
""")
                # 2) Detalle por forma con sustitución numérica (lo que ayuda a validar matemáticamente)
                piezas_aud = st.session_state.get("piezas_dict", {}) or {}
                lista_det = comp_aud.get("Detalle piezas", []) or []

                # Mapear costes ya calculados por nombre de pieza (para comparar)
                map_det = {}
                for d in lista_det:
                    try:
                        map_det[str(d.get("Pieza",""))] = d
                    except Exception:
                        pass

                def _ceil_int(x: float) -> int:
                    try:
                        return int(math.ceil(float(x)))
                    except Exception:
                        return int(x) if str(x).isdigit() else 0

                for pid, p in piezas_aud.items():
                    nombre = p.get("nombre", f"Forma {pid}")
                    det_row = map_det.get(str(nombre), {})

                    with st.expander(f"🧩 {nombre} · detalle matemático", expanded=False):
                        # Datos base
                        try:
                            pl = float(p.get("pliegos", 1.0))
                        except Exception:
                            pl = 1.0
                        uds = int(q_sel)
                        nb = _ceil_int(uds * pl)  # pliegos netos reales

                        # Mermas (proceso + impresión por lado) usando los mismos helpers que el motor
                        mp_def = int(_tabla_merma_procesos_offset(int(nb)))
                        mp_final = int(_ss_get_merma_proc(int(pid), int(q_sel), int(mp_def)))
                        hp_produccion = int(nb) + int(mp_final)

                        # Ajuste por "piezas por troquel" manual (solo corte)
                        troquel_piezas_manual = int(p.get("troquel_piezas", 0) or 0)
                        auto_piezas = 1
                        try:
                            if pl > 0 and pl < 1.0:
                                auto_piezas = max(1, int(round(1.0 / pl)))
                        except Exception:
                            auto_piezas = 1
                        if troquel_piezas_manual <= 0:
                            troquel_piezas_manual = auto_piezas
                        troquel_factor = float(auto_piezas) / float(max(1, troquel_piezas_manual))
                        hp_corte = int(math.ceil(float(hp_produccion) * troquel_factor))

                        partes_imp_units = obtener_partes_impresion_por_formato(int(pid), int(q_sel))
                        n_impresiones_qty = len(partes_imp_units) if partes_imp_units else 1

                        im_c = str(p.get("im", "No"))
                        im_d = str(p.get("im_d", "No"))

                        # Merma impresión (cara)
                        merma_cara = 0
                        if im_c == "Digital":
                            merma_cara = int(merma_imp_digital_hojas)
                        elif im_c == "Offset":
                            mi_def_c = int(_merma_impresion_offset_por_pasadas(int(p.get("nt", 0)), bool(p.get("ba", False))))
                            mi_final_c = int(_ss_get_merma_imp(int(pid), int(q_sel), "cara", int(mi_def_c)))
                            merma_cara = mi_final_c
                        # Merma impresión (dorso)
                        merma_dorso = 0
                        if im_d == "Digital":
                            merma_dorso = int(merma_imp_digital_hojas)
                        elif im_d == "Offset":
                            mi_def_d = int(_merma_impresion_offset_por_pasadas(int(p.get("nt_d", 0)), bool(p.get("ba_d", False))))
                            mi_final_d = int(_ss_get_merma_imp(int(pid), int(q_sel), "dorso", int(mi_def_d)))
                            merma_dorso = mi_final_d

                        hp_papel_f = hp_produccion + int(merma_cara) * int(n_impresiones_qty)
                        hp_papel_d = hp_produccion + int(merma_dorso) * int(n_impresiones_qty)

                        # Superficie (m2) del papel
                        try:
                            w = float(p.get("w", 0.0))
                            h = float(p.get("h", 0.0))
                            m2_papel = (w * h) / 1_000_000.0 if (w > 0 and h > 0) else 0.0
                        except Exception:
                            m2_papel = 0.0

                        st.markdown("**Pliegos netos reales**")
                        st.code(f"nb = ceil(uds * pliegos_por_ud) = ceil({uds} * {pl}) = {nb}")

                        st.markdown("**Merma de procesos (tabla + final editable)**")
                        st.code(
                            f"mp_def = tabla(nb={nb}) = {mp_def}\n"
                            f"mp_final = {mp_final}\n"
                            f"hp_produccion = nb + mp_final = {nb} + {mp_final} = {hp_produccion}\n"
                            f"hp_corte = ceil(hp_produccion * auto_piezas/troquel_piezas) = ceil({hp_produccion} * {auto_piezas}/{troquel_piezas_manual}) = {hp_corte}"
                        )

                        st.markdown("**Mermas de impresión y papel (por lado)**")
                        st.code(
                            f"n_impresiones = {n_impresiones_qty}\n"
                            f"hp_papel_cara = hp_produccion + merma_cara*n_impresiones = {hp_produccion} + {merma_cara}*{n_impresiones_qty} = {hp_papel_f}\n"
                            f"hp_papel_dorso = hp_produccion + merma_dorso*n_impresiones = {hp_produccion} + {merma_dorso}*{n_impresiones_qty} = {hp_papel_d}"
                        )

                        st.markdown("**Costes (resultado + fórmula con sustitución)**")

                        # Factores de descuento (compra) por bloque
                        try:
                            _dd = st.session_state.get("db_descuentos", {}) if isinstance(st.session_state.get("db_descuentos", {}), dict) else {}
                            f_cart = 1.0 - (float(_dd.get("cartoncillo", 0.0)) / 100.0)
                            f_or = 1.0 - (float(_dd.get("ondulado_rigidos", 0.0)) / 100.0)
                            f_narba = 1.0 - (float(_dd.get("narba", 0.0)) / 100.0)
                        except Exception:
                            f_cart, f_or, f_narba = 1.0, 1.0, 1.0

                        # Cartoncillo
                        try:
                            pf = p.get("pf", "Ninguno")
                            gf = float(p.get("gf", 0.0))
                            precio_pf = float(db["cartoncillo"][pf]["precio_kg"]) if (pf != "Ninguno") else 0.0
                        except Exception:
                            pf, gf, precio_pf = "Ninguno", 0.0, 0.0

                        try:
                            pd_ = p.get("pd", "Ninguno")
                            gd = float(p.get("gd", 0.0))
                            precio_pd = float(db["cartoncillo"][pd_]["precio_kg"]) if (pd_ != "Ninguno") else 0.0
                        except Exception:
                            pd_, gd, precio_pd = "Ninguno", 0.0, 0.0

                        if pf != "Ninguno" and m2_papel > 0 and gf > 0 and precio_pf > 0:
                            calc = hp_papel_f * m2_papel * (gf/1000.0) * precio_pf * f_cart
                            st.write(f"Cartoncillo Cara: {float(det_row.get('Cartoncillo Cara', 0.0)):.4f} €")
                            st.code(f"= {hp_papel_f} * {m2_papel:.6f} * ({gf}/1000) * {precio_pf} * {f_cart} = {calc:.4f}")
                        if pd_ != "Ninguno" and m2_papel > 0 and gd > 0 and precio_pd > 0:
                            calc = hp_papel_d * m2_papel * (gd/1000.0) * precio_pd * f_cart
                            st.write(f"Cartoncillo Dorso: {float(det_row.get('Cartoncillo Dorso', 0.0)):.4f} €")
                            st.code(f"= {hp_papel_d} * {m2_papel:.6f} * ({gd}/1000) * {precio_pd} * {f_cart} = {calc:.4f}")

                        # Plancha Ondulado
                        st.write(f"Plancha Ondulado: {float(det_row.get('Plancha Ondulado', 0.0)):.4f} €")
                        try:
                            if str(p.get("tipo_base","Ondulado/Cartón")) == "Ondulado/Cartón" and str(p.get("pl","Ninguna")) != "Ninguna" and m2_papel > 0:
                                pl_name = str(p.get("pl","Ninguna"))
                                ap = str(p.get("ap","B/C"))
                                if bool(p.get("pl_dif", False)) and float(p.get("pl_h", 0)) > 0 and float(p.get("pl_w", 0)) > 0:
                                    m2_plancha = (float(p.get("pl_w",0)) * float(p.get("pl_h",0))) / 1_000_000.0
                                    st.code(f"m2_plancha = (pl_w*pl_h)/1e6 = ({float(p.get('pl_w',0))}*{float(p.get('pl_h',0))})/1e6 = {m2_plancha:.6f}")
                                else:
                                    m2_plancha = m2_papel
                                    st.code(f"m2_plancha = m2_papel = {m2_plancha:.6f}")
                                precio_m2 = float(db["planchas"][pl_name][ap])
                                calc = hp_produccion * m2_plancha * precio_m2 * f_or
                                st.code(f"= {hp_produccion} * {m2_plancha:.6f} * {precio_m2} * {f_or} = {calc:.4f}")
                                if bool(p.get("flexografia", False)):
                                    flexo = float(db.get("flexografia", {}).get("arreglo", 180.0))
                                    st.code(f"Flexografía (fijo) = {flexo}")
                                    st.code(f"Total plancha = {calc:.4f} + {flexo} = {(calc+flexo):.4f}")
                            else:
                                st.caption("— (No aplica: base no es ondulado o no hay plancha seleccionada)")
                        except Exception:
                            st.caption("— (No se ha podido desglosar la plancha ondulado)")

                        # Material Rígido
                        st.write(f"Material Rígido: {float(det_row.get('Material Rígido', 0.0)):.4f} €")
                        try:
                            if str(p.get("tipo_base","Ondulado/Cartón")) == "Material Rígido":
                                if bool(p.get("rig_manual", False)):
                                    mw, mh = float(p.get("rig_w", 0)), float(p.get("rig_h", 0))
                                    precio_hoja = float(p.get("rig_precio_ud", 0.0))
                                    st.code(f"hoja_rigida = {mw}x{mh} mm (manual) · precio_hoja = {precio_hoja}")
                                else:
                                    mat = str(p.get("mat_rigido","Ninguno"))
                                    if mat != "Ninguno":
                                        info = db["rigidos"][mat]
                                        mw, mh = float(info.get("w",0)), float(info.get("h",0))
                                        precio_hoja = float(info.get("precio_ud",0.0)) * f_or
                                        st.code(f"hoja_rigida = {mw}x{mh} mm · precio_hoja = {float(info.get('precio_ud',0.0))} * {f_or} = {precio_hoja}")
                                    else:
                                        mw = mh = precio_hoja = 0.0
                                by = 0
                                if w > 0 and h > 0 and mw > 0 and mh > 0:
                                    y1 = int(mw // w) * int(mh // h)
                                    y2 = int(mw // h) * int(mh // w)
                                    by = max(y1, y2)
                                st.code(f"aprovechamiento_by = max(floor({mw}/{w})*floor({mh}/{h}), floor({mw}/{h})*floor({mh}/{w})) = {by}")
                                if by > 0:
                                    n_net = math.ceil(hp_produccion / by)
                                    if capas_contracolado == 0:
                                        merma_fija = merma_rigido_fija(int(n_net))
                                        n_pl = int(n_net) + int(merma_fija)
                                        st.code(f"hojas_netas = ceil({hp_produccion}/{by}) = {n_net} · merma_fija = {merma_fija} · hojas_total = {n_pl}")
                                    else:
                                        n_pl = int(math.ceil(float(n_net) * 1.02))
                                        st.code(f"hojas_netas = ceil({hp_produccion}/{by}) = {n_net} · hojas_total = ceil({n_net}*1.02) = {n_pl}")
                                    calc = float(n_pl) * float(precio_hoja)
                                    st.code(f"= {n_pl} * {precio_hoja} = {calc:.4f}")
                                else:
                                    st.caption("— (No aplica: no se puede encajar la pieza en la hoja rígida)")
                            else:
                                st.caption("— (No aplica: la base no es material rígido)")
                        except Exception:
                            st.caption("— (No se ha podido desglosar el material rígido)")

                        # Contracolado
                        st.write(f"Contracolado: {float(det_row.get('Contracolado', 0.0)):.4f} €")
                        try:
                            peg_rate = float(db["planchas"]["Microcanal / Canal 3"]["peg"]) * f_narba
                        except Exception:
                            peg_rate = 0.0
                        if capas_contracolado > 0 and m2_papel > 0 and peg_rate > 0:
                            calc = hp_produccion * m2_papel * peg_rate * capas_contracolado
                            st.code(f"= {hp_produccion} * {m2_papel:.6f} * {peg_rate:.6f} * {capas_contracolado} = {calc:.4f}")
                        else:
                            st.caption("— (No aplica: capas_contracolado=0 o faltan datos)")

                        # Impresión (incl. FR24 si aplica)
                        st.write(f"Impresión: {float(det_row.get('Impresión', 0.0)):.4f} €")
                        try:
                            merma_imp_digital_hojas_local = int(globals().get("merma_imp_digital_hojas", 10) or 10)
                        except Exception:
                            merma_imp_digital_hojas_local = 10
                        fr24_enabled = bool(p.get("fr24", False))
                        try:
                            fr24_rate = float(p.get("fr24_rate", 0.05))
                        except Exception:
                            fr24_rate = 0.05
                        fr24_m2_total = 0.0
                        imp_total_calc = 0.0
                        det_lines = []
                        partes = partes_imp_units if partes_imp_units else [int(q_sel)]
                        # Cara
                        if im_c == "Digital":
                            for q_run in partes:
                                nb_run = float(int(q_run)) * float(pl)
                                hp_run = float(nb_run) + float(merma_imp_digital_hojas_local)
                                c = hp_run * m2_papel * 6.5
                                imp_total_calc += c
                                det_lines.append(f"cara DIGITAL: (nb_run+merma) * m2 * 6.5 = ({nb_run:.0f}+{merma_imp_digital_hojas_local})*{m2_papel:.6f}*6.5 = {c:.4f}")
                                if fr24_enabled and m2_papel > 0:
                                    fr24_m2_total += hp_run * m2_papel
                        elif im_c == "Offset":
                            tintas = int(p.get("nt", 0)) + (1 if bool(p.get("ba", False)) else 0)
                            for q_run in partes:
                                nb_run = int(round(int(q_run) * float(pl)))
                                c_t = coste_offset_por_tinta(int(nb_run))
                                c = c_t * int(tintas)
                                imp_total_calc += c
                                det_lines.append(f"cara OFFSET: coste_offset_por_tinta({nb_run})*tintas = {c_t:.4f}*{tintas} = {c:.4f}")
                                if fr24_enabled and m2_papel > 0:
                                    fr24_m2_total += float(nb_run) * m2_papel
                        # Dorso
                        if im_d == "Digital":
                            for q_run in partes:
                                nb_run = float(int(q_run)) * float(pl)
                                hp_run = float(nb_run) + float(merma_imp_digital_hojas_local)
                                c = hp_run * m2_papel * 6.5
                                imp_total_calc += c
                                det_lines.append(f"dorso DIGITAL: ({nb_run:.0f}+{merma_imp_digital_hojas_local})*{m2_papel:.6f}*6.5 = {c:.4f}")
                                if fr24_enabled and m2_papel > 0:
                                    fr24_m2_total += hp_run * m2_papel
                        elif im_d == "Offset":
                            tintas = int(p.get("nt_d", 0)) + (1 if bool(p.get("ba_d", False)) else 0)
                            for q_run in partes:
                                nb_run = int(round(int(q_run) * float(pl)))
                                c_t = coste_offset_por_tinta(int(nb_run))
                                c = c_t * int(tintas)
                                imp_total_calc += c
                                det_lines.append(f"dorso OFFSET: coste_offset_por_tinta({nb_run})*tintas = {c_t:.4f}*{tintas} = {c:.4f}")
                                if fr24_enabled and m2_papel > 0:
                                    fr24_m2_total += float(nb_run) * m2_papel
                        c_fr24 = 0.0
                        if fr24_enabled and fr24_rate > 0 and fr24_m2_total > 0:
                            c_fr24 = fr24_m2_total * fr24_rate
                            imp_total_calc += c_fr24
                            det_lines.append(f"FR24: m2_total*rate = {fr24_m2_total:.6f}*{fr24_rate} = {c_fr24:.4f}")
                        if det_lines:
                            st.code("\n".join(det_lines))
                        else:
                            st.caption("— (No aplica: no hay impresión)")

                        # Peliculado (incl. Laminado digital si aplica)
                        st.write(f"Peliculado: {float(det_row.get('Peliculado', 0.0)):.4f} €")
                        pel_lines = []
                        pel_total_calc = 0.0
                        # Peliculado offset (por lado)
                        try:
                            if str(p.get("pel","Sin Peliculado")) != "Sin Peliculado":
                                precio_pel = float(db["peliculado"][str(p.get("pel"))])
                                c = hp_produccion * m2_papel * precio_pel * f_narba
                                pel_total_calc += c
                                pel_lines.append(f"pel_cara OFFSET: {hp_produccion}*{m2_papel:.6f}*{precio_pel}*{f_narba} = {c:.4f}")
                        except Exception:
                            pass
                        try:
                            if str(p.get("pd","Ninguno")) != "Ninguno" and str(p.get("pel_d","Sin Peliculado")) != "Sin Peliculado":
                                precio_pel = float(db["peliculado"][str(p.get("pel_d"))])
                                c = hp_produccion * m2_papel * precio_pel * f_narba
                                pel_total_calc += c
                                pel_lines.append(f"pel_dorso OFFSET: {hp_produccion}*{m2_papel:.6f}*{precio_pel}*{f_narba} = {c:.4f}")
                        except Exception:
                            pass
                        # Laminado digital (por tirada y lado)
                        try:
                            lam_rate = float(db.get("laminado_digital", 3.5))
                        except Exception:
                            lam_rate = 3.5
                        if bool(p.get("ld", False)) and im_c == "Digital":
                            for q_run in partes:
                                nb_run = float(int(q_run)) * float(pl)
                                hp_run = float(nb_run) + float(merma_imp_digital_hojas_local)
                                c = hp_run * m2_papel * lam_rate
                                pel_total_calc += c
                                pel_lines.append(f"laminado_digital CARA: ({nb_run:.0f}+{merma_imp_digital_hojas_local})*{m2_papel:.6f}*{lam_rate} = {c:.4f}")
                        if bool(p.get("ld_d", False)) and im_d == "Digital":
                            for q_run in partes:
                                nb_run = float(int(q_run)) * float(pl)
                                hp_run = float(nb_run) + float(merma_imp_digital_hojas_local)
                                c = hp_run * m2_papel * lam_rate
                                pel_total_calc += c
                                pel_lines.append(f"laminado_digital DORSO: ({nb_run:.0f}+{merma_imp_digital_hojas_local})*{m2_papel:.6f}*{lam_rate} = {c:.4f}")
                        if pel_lines:
                            st.code("\n".join(pel_lines))
                        else:
                            st.caption("— (No aplica: sin peliculado ni laminado digital)")

                        # Corte
                        st.write(f"Corte (Troquel/Plotter): {float(det_row.get('Corte (Troquel/Plotter)', 0.0)):.4f} €")
                        st.code(
                            f"hp_corte = ceil(hp_produccion * auto_piezas/troquel_piezas) = ceil({hp_produccion} * {auto_piezas}/{troquel_piezas_manual}) = {hp_corte}\n"
                            f"Troquelado: arranque + hp_corte*tiro · Plotter: hp_corte*precio_hoja"
                        )
                        st.markdown("""**Troquelado**: `arranque + hp_corte * tiro`  (hp_corte = ceil(hp_produccion * auto_piezas/troquel_piezas)`
**Plotter**: `hp_corte * precio_hoja_plotter`
**Sin corte**: `0`""")


                                                # Stamping
                        st.write(f"Stamping: {float(det_row.get('Stamping', 0.0)):.4f} €")
                        if bool(p.get("stamping", False)):
                            try:
                                sw = float(p.get("stamping_w", 0) or 0)
                                sh = float(p.get("stamping_h", 0) or 0)
                            except Exception:
                                sw, sh = 0.0, 0.0
                            area_m2 = max(0.0, (sw/1000.0) * (sh/1000.0))
                            arr_s = float(db.get("stamping", {}).get("arreglo", 168.0)) if bool(p.get("stamping_cobrar_arreglo", True)) else 0.0
                            pisada = float(db.get("stamping", {}).get("pisada", 0.21))
                            peli = float(db.get("stamping", {}).get("pelicula_m2", 0.39))
                            st.code(
                                f"area_m2 = (w/1000)*(h/1000) = ({sw}/1000)*({sh}/1000) = {area_m2:.6f}\n"
                                f"coste = arreglo + hp_corte*pisada + hp_corte*area_m2*pelicula\n"
                                f"= {arr_s} + {hp_corte}*{pisada} + {hp_corte}*{area_m2:.6f}*{peli} = {(arr_s + hp_corte*pisada + hp_corte*area_m2*peli):.4f}"
                            )
                        else:
                            st.caption("— (No aplica)")

# Subtotal
                        st.write(f"Subtotal Pieza: {float(det_row.get('Subtotal Pieza', 0.0)):.4f} €")

        # Mostrar (si existe) el desglose interno ya calculado para esta cantidad
        if lista_cants_aud and desc_full:
            with st.expander("🧩 Datos internos: desc_full / compras_legible / resumen_costes", expanded=False):
                st.markdown("**desc_full (por cantidad)**")
                st.json(desc_full.get(q_sel, {}))

                st.markdown("**compras_legible (por cantidad)**")
                st.json(compras_legible.get(q_sel, {}))

                st.markdown("**resumen_costes (por cantidad)**")
                resumen_costes_por_cantidad = st.session_state.get("resumen_costes", {})
                # Compatibilidad hacia atrás: algunos JSON antiguos pueden guardarlo con otras claves
                if not isinstance(resumen_costes_por_cantidad, dict):
                    resumen_costes_por_cantidad = {}
                st.json(resumen_costes_por_cantidad.get(q_sel, {}))


# TAB DEBUG (SIEMPRE)
# =========================================================
with tab_debug:
    lista_cants_dbg = parse_cantidades(st.session_state.cants_str_saved)

    if lista_cants_dbg and desc_full:
        sq = st.selectbox("Ver detalle por cantidad:", lista_cants_dbg, key="dbg_sel")

        st.subheader("Desglose por pieza")
        det = desc_full.get(sq, {}).get("det_piezas", [])
        if det:
            st.dataframe(pd.DataFrame(det), use_container_width=True)
        else:
            st.info("No hay detalle de piezas para esta cantidad.")

        st.subheader("Resumen compras (materiales y procesos)")
        comp = compras_legible.get(sq, {})
        if comp:
            materiales = comp.get("Materiales", {}) or {}
            procesos = comp.get("Procesos", {}) or {}

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Materiales (compra estimada)**")
                st.dataframe(pd.DataFrame([materiales]), use_container_width=True)
            with c2:
                st.markdown("**Procesos (coste estimado)**")
                st.dataframe(pd.DataFrame([procesos]), use_container_width=True)

            total_materiales = sum(float(v or 0.0) for v in materiales.values())
            total_procesos = sum(float(v or 0.0) for v in procesos.values())
            total_compra = total_materiales + total_procesos

            st.metric("TOTAL COSTE (compra) · Materiales + Procesos", f"{total_compra:,.2f}€")

        st.subheader("Externos (detalle)")
        exd = desc_full.get(sq, {}).get("externos", [])
        if exd:
            st.dataframe(pd.DataFrame(exd), use_container_width=True)
        else:
            st.caption("Sin externos para esta cantidad.")

        st.subheader("Debug log (técnico)")
        dbg = desc_full.get(sq, {}).get("debug", [])
        if dbg:
            st.dataframe(pd.DataFrame(dbg), use_container_width=True)
        else:
            st.caption("Sin entradas debug (solo se rellenan algunas líneas, p.ej. rígidos).")
    else:
        st.info("No hay desglose aún. Define cantidades y calcula.")
