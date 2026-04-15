import streamlit as st

# ==========================================
# Modo Comercial: solo editar cantidades + brief + descripción + comentarios
# - Bloquea (disabled) el resto de widgets del motor
# ==========================================

ALLOWED_KEYS = {
    "brf",
    "desc",
    "notas",
    "cants_str_saved",
}

def _should_enable_widget(kwargs: dict) -> bool:
    k = kwargs.get("key", None)
    if k is None:
        # Si no hay key, por seguridad lo dejamos editable SOLO en widgets de texto del modo comercial?
        # -> Mejor bloquear (así no hay vías de edición no controladas).
        return False
    return str(k) in ALLOWED_KEYS

def _wrap_widget(fn):
    def _inner(*args, **kwargs):
        if not _should_enable_widget(kwargs):
            # No permitimos interacción salvo los campos autorizados.
            kwargs["disabled"] = True
        return fn(*args, **kwargs)
    return _inner

# Wrap de inputs típicos
st.text_input = _wrap_widget(st.text_input)
st.text_area = _wrap_widget(st.text_area)
st.number_input = _wrap_widget(st.number_input)
st.selectbox = _wrap_widget(st.selectbox)
st.multiselect = _wrap_widget(st.multiselect)
st.radio = _wrap_widget(st.radio)
st.checkbox = _wrap_widget(st.checkbox)
st.slider = _wrap_widget(st.slider)

# Botones: solo dejamos activos Import/Export/Descargar (por label o key)
_orig_button = st.button
def _button(*args, **kwargs):
    label = str(args[0]) if args else str(kwargs.get("label", ""))
    k = str(kwargs.get("key", "") or "")
    allow = any(x in label.lower() for x in ["import", "export", "descargar", "download"]) or any(
        x in k.lower() for x in ["import", "export", "download", "oferta", "json"]
    )
    if not allow:
        kwargs["disabled"] = True
    return _orig_button(*args, **kwargs)
st.button = _button

# Download buttons siempre permitidos (es salida, no edición)
# File uploader permitido (para importar JSON)
# -> No tocamos st.download_button / st.file_uploader

# Importa el motor completo (UI + cálculo). Con los wraps anteriores,
# el usuario solo podrá editar los campos permitidos.
import ventas_core  # noqa: F401
