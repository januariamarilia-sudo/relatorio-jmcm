from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import streamlit as st

from app import generate_report, read_defaults


st.set_page_config(page_title="Gerador de Relatorios", layout="wide")

defaults = read_defaults()
BASE_URL = "https://relatorio-jmcm.streamlit.app/"
PROFILE_CODES = ["bx", "hjh", "k7m", "n4p", "v9r"]


def query_value(name, default=""):
    try:
        value = st.query_params.get(name, default)
    except Exception:
        value = st.experimental_get_query_params().get(name, [default])
    if isinstance(value, list):
        return value[0] if value else default
    return value or default


def safe_code(value):
    code = "".join(ch for ch in ("" if value is None else str(value)).lower() if ch.isalnum() or ch in ("-", "_"))
    return code[:24] or "principal"


DRAFT_CODE = safe_code(query_value("codigo", "principal"))
LOCAL_SAVE_DIR = Path(__file__).with_name("relatorios_salvos")

PRIORIDADES = ["", "Alta", "Media", "Baixa", "Urgente"]
STATUS = [
    "",
    "Nao iniciada",
    "Em andamento",
    "Paralisado",
    "Concluido",
    "Parcialmente concluido",
    "Aguardando outro setor",
    "Aguardando assinatura",
    "Aguardando documentos",
    "Aguardando publicacao",
]
PRODUTIVIDADE = ["Alto", "Medio", "Baixo"]
CUMPRIMENTO = ["Sim", "Parcialmente", "Nao"]
SIM_NAO = ["Sim", "Nao"]


def inject_design():
    st.markdown(
        """
        <style>
        :root {
            --icismep-blue: #2f39c0;
            --icismep-blue-dark: #202999;
            --icismep-red: #fa2946;
            --icismep-soft: #f4f6ff;
            --icismep-line: #dfe3f7;
            --icismep-ink: #172033;
            --icismep-muted: #5c6478;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(47, 57, 192, 0.11), transparent 30rem),
                linear-gradient(180deg, #f7f8ff 0%, #ffffff 34rem);
            color: var(--icismep-ink);
            -webkit-text-size-adjust: 100%;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
            padding-left: max(1rem, env(safe-area-inset-left));
            padding-right: max(1rem, env(safe-area-inset-right));
        }

        .jmcm-hero {
            position: relative;
            overflow: hidden;
            border-radius: 18px;
            padding: 26px 30px;
            margin-bottom: 22px;
            color: #ffffff;
            background: linear-gradient(135deg, var(--icismep-blue) 0%, var(--icismep-blue-dark) 100%);
            box-shadow: 0 18px 45px rgba(32, 41, 153, 0.22);
        }

        .jmcm-hero::after {
            content: "";
            position: absolute;
            right: -76px;
            top: -92px;
            width: 260px;
            height: 260px;
            background: rgba(255, 255, 255, 0.13);
            transform: rotate(45deg);
            border-radius: 20px;
        }

        .jmcm-brand {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            font-size: 0.92rem;
            letter-spacing: 0;
            margin-bottom: 18px;
            color: #ffffff;
        }

        .jmcm-logo-mark {
            display: inline-grid;
            grid-template-columns: 14px 24px 24px;
            gap: 4px;
            align-items: end;
            height: 24px;
        }

        .jmcm-logo-mark span {
            display: block;
            border-radius: 3px 3px 0 0;
            transform: skewX(28deg);
            background: #ffffff;
        }

        .jmcm-logo-mark span:first-child {
            height: 9px;
            background: var(--icismep-red);
        }

        .jmcm-logo-mark span:nth-child(2) { height: 18px; }
        .jmcm-logo-mark span:nth-child(3) { height: 24px; }

        .jmcm-hero h1 {
            margin: 0;
            font-size: clamp(2rem, 4vw, 3.35rem);
            line-height: 1.05;
            font-weight: 850;
            letter-spacing: 0;
        }

        .jmcm-hero p {
            max-width: 760px;
            margin: 12px 0 0;
            font-size: 1.02rem;
            line-height: 1.5;
            color: rgba(255, 255, 255, 0.9);
        }

        .jmcm-status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }

        .jmcm-pill {
            border: 1px solid rgba(255,255,255,0.28);
            background: rgba(255,255,255,0.13);
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 0.86rem;
            color: #ffffff;
        }

        h2, h3 {
            color: var(--icismep-ink);
            letter-spacing: 0;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0.8rem;
        }

        div[data-testid="stExpander"] details {
            border: 1px solid var(--icismep-line);
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 6px 20px rgba(47, 57, 192, 0.06);
            margin-bottom: 8px;
        }

        div[data-testid="stExpander"] summary {
            background: linear-gradient(90deg, #ffffff, var(--icismep-soft));
            border-radius: 12px;
            color: var(--icismep-blue-dark);
            font-weight: 700;
            min-height: 42px;
        }

        .stButton > button {
            border-radius: 10px;
            border-color: var(--icismep-line);
            font-weight: 700;
            min-height: 42px;
        }

        .stButton > button:hover {
            border-color: var(--icismep-blue);
            color: var(--icismep-blue-dark);
        }

        .stButton > button[kind="primary"],
        div[data-testid="stDownloadButton"] button[kind="primary"] {
            background: var(--icismep-blue);
            border-color: var(--icismep-blue);
            color: #ffffff;
        }

        .stButton > button[kind="primary"]:hover,
        div[data-testid="stDownloadButton"] button[kind="primary"]:hover {
            background: var(--icismep-blue-dark);
            border-color: var(--icismep-blue-dark);
            color: #ffffff;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] > div {
            border-radius: 10px;
            border-color: var(--icismep-line);
            background-color: #fbfcff;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: var(--icismep-blue);
            box-shadow: 0 0 0 1px var(--icismep-blue);
        }

        .stCaption, caption, small {
            color: var(--icismep-muted);
        }

        .iphone-card {
            border: 1px solid var(--icismep-line);
            border-radius: 14px;
            padding: 16px 18px;
            margin: -4px 0 22px;
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 10px 28px rgba(47, 57, 192, 0.07);
        }

        .iphone-card strong {
            color: var(--icismep-blue-dark);
        }

        .iphone-card p {
            margin: 6px 0 0;
            color: var(--icismep-muted);
            line-height: 1.45;
        }

        @media (max-width: 720px) {
            html {
                scroll-padding-top: 10px;
            }

            .block-container {
                padding-top: 0.7rem;
                padding-left: 0.85rem;
                padding-right: 0.85rem;
                padding-bottom: 1.8rem;
            }

            .jmcm-hero {
                border-radius: 14px;
                padding: 16px 16px;
                margin-bottom: 15px;
                box-shadow: 0 10px 24px rgba(32, 41, 153, 0.17);
            }

            .jmcm-hero::after {
                right: -120px;
                top: -138px;
                width: 220px;
                height: 220px;
            }

            .jmcm-brand {
                font-size: 0.76rem;
                margin-bottom: 8px;
                gap: 8px;
            }

            .jmcm-logo-mark {
                grid-template-columns: 10px 18px 18px;
                gap: 3px;
                height: 18px;
            }

            .jmcm-logo-mark span:first-child {
                height: 7px;
            }

            .jmcm-logo-mark span:nth-child(2) { height: 14px; }
            .jmcm-logo-mark span:nth-child(3) { height: 18px; }

            .jmcm-logo-mark span {
                border-radius: 2px 2px 0 0;
            }

            .jmcm-hero h1 {
                font-size: 1.55rem;
                line-height: 1.1;
            }

            .jmcm-hero p {
                font-size: 0.86rem;
                line-height: 1.35;
                margin-top: 8px;
            }

            .jmcm-status-strip {
                display: none;
            }

            h2, h3 {
                display: block !important;
                width: 100% !important;
                max-width: 100% !important;
                overflow: visible !important;
                white-space: normal !important;
                overflow-wrap: anywhere !important;
                text-overflow: clip !important;
                font-size: 1.28rem !important;
                line-height: 1.25 !important;
                margin-top: 0.85rem !important;
                margin-bottom: 0.55rem !important;
            }

            .stButton > button,
            div[data-testid="stDownloadButton"] button {
                width: 100%;
                min-height: 44px;
                padding: 0.45rem 0.7rem;
                border-radius: 9px;
            }

            div[data-testid="stTextInput"] input,
            div[data-testid="stTextArea"] textarea,
            div[data-baseweb="select"] > div {
                font-size: 16px;
                min-height: 42px;
                border-radius: 9px;
            }

            div[data-testid="stTextArea"] textarea {
                min-height: 88px;
            }

            label, div[data-testid="stWidgetLabel"] {
                font-size: 0.86rem !important;
                line-height: 1.25 !important;
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }

            div[data-testid="stExpander"] details {
                border-radius: 10px;
                margin-bottom: 7px;
                box-shadow: 0 4px 12px rgba(47, 57, 192, 0.045);
            }

            div[data-testid="stExpander"] summary {
                min-height: 44px;
                font-size: 0.94rem;
                line-height: 1.25;
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: clip !important;
                padding-top: 0.55rem !important;
                padding-bottom: 0.55rem !important;
            }

            .iphone-card {
                padding: 12px 13px;
                margin: -2px 0 12px;
                border-radius: 11px;
                font-size: 0.92rem;
            }

            div[data-testid="stVerticalBlock"] {
                gap: 0.62rem;
            }

            div[data-testid="stHorizontalBlock"] {
                gap: 0.62rem;
                flex-wrap: wrap;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    code_pill = "" if DRAFT_CODE == "principal" else f'<span class="jmcm-pill">Copia: {DRAFT_CODE}</span>'
    st.markdown(
        f"""
        <section class="jmcm-hero">
            <div class="jmcm-brand">
                <span class="jmcm-logo-mark"><span></span><span></span><span></span></span>
                Sistema de Relatorios
            </div>
            <h1>Gerador de Relatorios</h1>
            <p>Rascunho continuo para planejamento semanal, demandas extraordinarias e atividades executadas, com geracao em Word.</p>
            <div class="jmcm-status-strip">
                <span class="jmcm-pill">Rascunho salvo</span>
                <span class="jmcm-pill">Planejamento permanente</span>
                <span class="jmcm-pill">Atividades diarias protegidas</span>
                {code_pill}
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_profile_links():
    if DRAFT_CODE == "principal":
        return
    links = "\n".join(
        f"- [{code}]({BASE_URL}?codigo={code})"
        for code in PROFILE_CODES
    )
    with st.expander("Links separados", expanded=False):
        st.markdown(
            "Cada link abaixo tem rascunho separado. Envie um codigo para cada pessoa:\n\n"
            f"{links}\n\n"
            f"Link atual: `{BASE_URL}?codigo={DRAFT_CODE}`"
        )


def render_iphone_mode_hint():
    with st.expander("Usar no iPhone", expanded=False):
        st.markdown(
            """
            <div class="iphone-card">
                <strong>Para deixar como app na tela inicial:</strong>
                <p>Abra este link no Safari do iPhone, toque em Compartilhar e escolha Adicionar à Tela de Início.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def text_value(value=""):
    return "" if value is None else str(value)


def clean(rows):
    cleaned = []
    for row in rows:
        if any(str(value).strip() for value in row.values()):
            cleaned.append(row)
    return cleaned


def saved_now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def iso_now():
    return datetime.now().isoformat(timespec="seconds")


def report_date_key(value=""):
    value = " ".join(text_value(value).strip().split())
    if not value:
        return f"{DRAFT_CODE}:sem-data"
    return f"{DRAFT_CODE}:{value.lower()}"


def local_save_path(data_relatorio):
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in data_relatorio)
    return LOCAL_SAVE_DIR / f"{safe_name[:90] or 'sem-data'}.json"


def secret_value(*names):
    for name in names:
        try:
            value = st.secrets.get(name)
        except Exception:
            value = None
        if value:
            return str(value)
        try:
            section, key = name.split(".", 1)
            value = st.secrets.get(section, {}).get(key)
        except Exception:
            value = None
        if value:
            return str(value)
    return ""


def supabase_config():
    url = secret_value("SUPABASE_URL", "supabase.url").rstrip("/")
    key = secret_value("SUPABASE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY", "supabase.key", "supabase.anon_key")
    if not url or not key:
        return "", ""
    return url, key


def supabase_request(method, path, payload=None):
    url, key = supabase_config()
    if not url or not key:
        raise RuntimeError("Supabase nao configurado.")
    data = None
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    request = Request(f"{url}/rest/v1/{path}", data=data, headers=headers, method=method)
    with urlopen(request, timeout=12) as response:
        text = response.read().decode("utf-8")
    return json.loads(text) if text else None


def load_remote_draft(data_relatorio):
    encoded_date = quote(data_relatorio, safe="")
    rows = supabase_request(
        "GET",
        f"relatorios?data_relatorio=eq.{encoded_date}&select=conteudo_json,atualizado_em&limit=1",
    )
    if not rows:
        return None
    draft = rows[0].get("conteudo_json")
    if not isinstance(draft, dict):
        return None
    draft["saved_at"] = text_value(draft.get("saved_at") or rows[0].get("atualizado_em", ""))
    return draft


def save_remote_draft(data_relatorio, draft):
    payload = {
        "data_relatorio": data_relatorio,
        "conteudo_json": draft,
        "atualizado_em": iso_now(),
    }
    supabase_request("POST", "relatorios?on_conflict=data_relatorio", [payload])


def load_local_draft(data_relatorio):
    path = local_save_path(data_relatorio)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_local_draft(data_relatorio, draft):
    LOCAL_SAVE_DIR.mkdir(exist_ok=True)
    local_save_path(data_relatorio).write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")


def default_draft():
    return {
        "identity": defaults.get("identity", {}),
        "planning": defaults.get("planning", []) or [],
        "extra": [],
        "done": [],
        "indicators": defaults.get("indicators", {}),
        "observacoes": defaults.get("observacoes", ""),
        "validacao": "",
        "counts": {
            "planning_count": max(5, len(defaults.get("planning", []))),
            "extra_count": 3,
            "done_count": 3,
        },
        "saved_at": "",
    }


def blank_draft():
    return {
        "identity": {
            "data": "",
            "colaborador": "",
            "setor": "",
            "funcao": "",
            "horario": "",
            "responsavel": "",
        },
        "planning": [],
        "extra": [],
        "done": [],
        "indicators": {
            "produtividade": "Alto",
            "cumprimento": "Parcialmente",
            "urgente": "Nao",
            "dependencia": "Nao",
            "retrabalho": "Nao",
            "sobrecarga": "Nao",
            "acumulo": "Nao",
        },
        "observacoes": "",
        "validacao": "",
        "counts": {"planning_count": 3, "extra_count": 2, "done_count": 2},
        "saved_at": "",
    }


def load_draft(data_relatorio=None):
    data_relatorio = data_relatorio or report_date_key("")
    try:
        draft = load_remote_draft(data_relatorio)
    except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError, OSError):
        draft = load_local_draft(data_relatorio)
    if not isinstance(draft, dict):
        draft = default_draft()
    return draft


def save_draft(draft, data_relatorio=None):
    draft = dict(draft)
    draft["saved_at"] = saved_now()
    data_relatorio = data_relatorio or report_date_key(draft.get("identity", {}).get("data", ""))
    try:
        save_remote_draft(data_relatorio, draft)
        st.session_state["storage_mode"] = "Supabase"
    except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError, OSError):
        save_local_draft(data_relatorio, draft)
        st.session_state["storage_mode"] = "local"
    return draft


def clear_item_fields(prefix):
    keys = [key for key in st.session_state if key.startswith(f"{prefix}_")]
    for key in keys:
        del st.session_state[key]


def set_choice(key, options, value):
    value = text_value(value).strip()
    st.session_state[key] = value if value in options else options[0]


def set_status(prefix, idx, value):
    value = text_value(value).strip()
    if value in STATUS:
        st.session_state[f"{prefix}_status_{idx}"] = value
        st.session_state[f"{prefix}_status_livre_{idx}"] = ""
    else:
        st.session_state[f"{prefix}_status_{idx}"] = ""
        st.session_state[f"{prefix}_status_livre_{idx}"] = value


def apply_draft(draft):
    identity = draft.get("identity", {})
    st.session_state["identity_data"] = text_value(identity.get("data", ""))
    st.session_state["identity_colaborador"] = text_value(identity.get("colaborador", ""))
    st.session_state["identity_setor"] = text_value(identity.get("setor", ""))
    st.session_state["identity_funcao"] = text_value(identity.get("funcao", ""))
    st.session_state["identity_horario"] = text_value(identity.get("horario", ""))
    st.session_state["identity_responsavel"] = text_value(identity.get("responsavel", ""))

    clear_item_fields("planning")
    clear_item_fields("extra")
    clear_item_fields("done")

    counts = draft.get("counts", {})
    planning_rows = draft.get("planning", []) or []
    extra_rows = draft.get("extra", []) or []
    done_rows = draft.get("done", []) or []
    st.session_state["planning_count"] = max(3, int(counts.get("planning_count", len(planning_rows) or 3)), len(planning_rows))
    st.session_state["extra_count"] = max(2, int(counts.get("extra_count", len(extra_rows) or 2)), len(extra_rows))
    st.session_state["done_count"] = max(2, int(counts.get("done_count", len(done_rows) or 2)), len(done_rows))

    for idx, row in enumerate(planning_rows):
        st.session_state[f"planning_excluir_{idx}"] = False
        st.session_state[f"planning_processo_{idx}"] = text_value(row.get("processo", ""))
        st.session_state[f"planning_descricao_{idx}"] = text_value(row.get("descricao", ""))
        set_choice(f"planning_prioridade_{idx}", PRIORIDADES, row.get("prioridade", ""))
        set_status("planning", idx, row.get("status", ""))

    for idx, row in enumerate(extra_rows):
        st.session_state[f"extra_excluir_{idx}"] = False
        st.session_state[f"extra_processo_{idx}"] = text_value(row.get("processo", ""))
        st.session_state[f"extra_descricao_{idx}"] = text_value(row.get("descricao", ""))
        st.session_state[f"extra_prazo_{idx}"] = text_value(row.get("prazo", ""))
        set_choice(f"extra_prioridade_{idx}", PRIORIDADES, row.get("prioridade", ""))
        set_status("extra", idx, row.get("status", ""))

    for idx, row in enumerate(done_rows):
        st.session_state[f"done_excluir_{idx}"] = False
        st.session_state[f"done_origem_{idx}"] = ""
        st.session_state[f"done_livre_{idx}"] = text_value(row.get("processo", ""))
        st.session_state[f"done_atividade_{idx}"] = text_value(row.get("atividade", ""))
        st.session_state[f"done_tempo_{idx}"] = text_value(row.get("tempo", ""))
        set_status("done", idx, row.get("status", ""))
        st.session_state[f"done_obs_{idx}"] = text_value(row.get("observacoes", ""))

    indicators = draft.get("indicators", {})
    set_choice("ind_produtividade", PRODUTIVIDADE, indicators.get("produtividade", "Alto"))
    set_choice("ind_cumprimento", CUMPRIMENTO, indicators.get("cumprimento", "Parcialmente"))
    set_choice("ind_urgente", SIM_NAO, indicators.get("urgente", "Nao"))
    st.session_state["ind_urgente_comentario"] = text_value(indicators.get("urgente_comentario", ""))
    set_choice("ind_dependencia", SIM_NAO, indicators.get("dependencia", "Nao"))
    st.session_state["ind_dependencia_comentario"] = text_value(indicators.get("dependencia_comentario", ""))
    set_choice("ind_retrabalho", SIM_NAO, indicators.get("retrabalho", "Nao"))
    st.session_state["ind_retrabalho_comentario"] = text_value(indicators.get("retrabalho_comentario", ""))
    set_choice("ind_sobrecarga", SIM_NAO, indicators.get("sobrecarga", "Nao"))
    st.session_state["ind_sobrecarga_comentario"] = text_value(indicators.get("sobrecarga_comentario", ""))
    set_choice("ind_acumulo", SIM_NAO, indicators.get("acumulo", "Nao"))
    st.session_state["ind_acumulo_comentario"] = text_value(indicators.get("acumulo_comentario", ""))

    st.session_state["observacoes"] = text_value(draft.get("observacoes", ""))
    st.session_state["validacao"] = text_value(draft.get("validacao", ""))
    st.session_state["last_saved_at"] = text_value(draft.get("saved_at", ""))


def load_draft_for_current_date():
    typed_date = st.session_state.get("identity_data", "")
    data_relatorio = report_date_key(typed_date)
    draft = load_draft(data_relatorio)
    if text_value(typed_date).strip() and not text_value(draft.get("identity", {}).get("data", "")).strip():
        draft.setdefault("identity", {})["data"] = typed_date
    return data_relatorio, draft


def init_state():
    if not st.session_state.get("draft_initialized"):
        data_relatorio, draft = load_draft_for_current_date()
        apply_draft(draft)
        st.session_state["loaded_report_date"] = data_relatorio
        st.session_state["draft_initialized"] = True
    else:
        data_relatorio = report_date_key(st.session_state.get("identity_data", ""))
        if data_relatorio != st.session_state.get("loaded_report_date"):
            _, draft = load_draft_for_current_date()
            apply_draft(draft)
            st.session_state["loaded_report_date"] = data_relatorio
            st.session_state["_feedback"] = "Rascunho desta data carregado."
    pending = st.session_state.pop("_pending_draft", None)
    if pending is not None:
        apply_draft(pending)
        st.session_state["loaded_report_date"] = report_date_key(st.session_state.get("identity_data", ""))
    feedback = st.session_state.pop("_feedback", "")
    if feedback:
        st.success(feedback)


def status_value(prefix, index):
    livre = st.session_state.get(f"{prefix}_status_livre_{index}", "").strip()
    rapido = st.session_state.get(f"{prefix}_status_{index}", "").strip()
    return livre or rapido


def ensure_status(prefix, idx, default=""):
    if f"{prefix}_status_{idx}" not in st.session_state and f"{prefix}_status_livre_{idx}" not in st.session_state:
        set_status(prefix, idx, default)


def ensure_choice(key, options, default=""):
    if key not in st.session_state:
        set_choice(key, options, default)


def ensure_planning_row(idx):
    st.session_state.setdefault(f"planning_excluir_{idx}", False)
    st.session_state.setdefault(f"planning_processo_{idx}", "")
    st.session_state.setdefault(f"planning_descricao_{idx}", "")
    ensure_choice(f"planning_prioridade_{idx}", PRIORIDADES, "")
    ensure_status("planning", idx, "")


def ensure_extra_row(idx):
    st.session_state.setdefault(f"extra_excluir_{idx}", False)
    st.session_state.setdefault(f"extra_processo_{idx}", "")
    st.session_state.setdefault(f"extra_descricao_{idx}", "")
    st.session_state.setdefault(f"extra_prazo_{idx}", "")
    ensure_choice(f"extra_prioridade_{idx}", PRIORIDADES, "")
    ensure_status("extra", idx, "")


def ensure_done_row(idx):
    st.session_state.setdefault(f"done_excluir_{idx}", False)
    st.session_state.setdefault(f"done_origem_{idx}", "")
    st.session_state.setdefault(f"done_livre_{idx}", "")
    st.session_state.setdefault(f"done_atividade_{idx}", "")
    st.session_state.setdefault(f"done_tempo_{idx}", "")
    ensure_status("done", idx, "")
    st.session_state.setdefault(f"done_obs_{idx}", "")


def row_title(prefix, index, label, *keys):
    values = [st.session_state.get(f"{prefix}_processo_{index}", "")]
    values.extend(st.session_state.get(key, "") for key in keys)
    title = ""
    for value in values:
        title = " ".join(text_value(value).split())
        if title:
            break
    if not title:
        title = "sem assunto"
    if len(title) > 64:
        title = title[:61].rstrip() + "..."
    return f"{label} {index + 1}: {title}"


def render_removed_items(prefix, label, count):
    removed = []
    for idx in range(count):
        if st.session_state.get(f"{prefix}_excluir_{idx}", False):
            removed.append((idx, row_title(prefix, idx, label, f"{prefix}_livre_{idx}", f"{prefix}_origem_{idx}")))
    if not removed:
        return
    with st.expander("Itens removidos nesta vez", expanded=False):
        for idx, title in removed:
            if st.button(f"Restaurar {title}", key=f"{prefix}_restaurar_{idx}"):
                st.session_state[f"{prefix}_excluir_{idx}"] = False
                st.rerun()


def render_status(prefix, idx, on_change=None):
    st.selectbox("Status rapido", STATUS, key=f"{prefix}_status_{idx}", on_change=on_change)
    st.text_input("Status livre", key=f"{prefix}_status_livre_{idx}", on_change=on_change)


def planning_rows_from_state():
    rows = []
    for idx in range(st.session_state.get("planning_count", 0)):
        ensure_planning_row(idx)
        if st.session_state.get(f"planning_excluir_{idx}", False):
            continue
        rows.append(
            {
                "processo": st.session_state.get(f"planning_processo_{idx}", "").strip(),
                "descricao": st.session_state.get(f"planning_descricao_{idx}", "").strip(),
                "prioridade": st.session_state.get(f"planning_prioridade_{idx}", ""),
                "status": status_value("planning", idx),
            }
        )
    return clean(rows)


def extra_rows_from_state():
    rows = []
    for idx in range(st.session_state.get("extra_count", 0)):
        ensure_extra_row(idx)
        if st.session_state.get(f"extra_excluir_{idx}", False):
            continue
        rows.append(
            {
                "processo": st.session_state.get(f"extra_processo_{idx}", "").strip(),
                "descricao": st.session_state.get(f"extra_descricao_{idx}", "").strip(),
                "prazo": st.session_state.get(f"extra_prazo_{idx}", "").strip(),
                "prioridade": st.session_state.get(f"extra_prioridade_{idx}", ""),
                "status": status_value("extra", idx),
            }
        )
    return clean(rows)


def done_rows_from_state():
    rows = []
    for idx in range(st.session_state.get("done_count", 0)):
        ensure_done_row(idx)
        if st.session_state.get(f"done_excluir_{idx}", False):
            continue
        processo = st.session_state.get(f"done_livre_{idx}", "").strip() or st.session_state.get(f"done_origem_{idx}", "").strip()
        rows.append(
            {
                "processo": processo,
                "atividade": st.session_state.get(f"done_atividade_{idx}", "").strip(),
                "tempo": st.session_state.get(f"done_tempo_{idx}", "").strip(),
                "status": status_value("done", idx),
                "observacoes": st.session_state.get(f"done_obs_{idx}", "").strip(),
            }
        )
    return clean(rows)


def write_done_rows(rows):
    st.session_state.done_count = max(2, len(rows))
    clear_item_fields("done")

    for idx, row in enumerate(rows):
        st.session_state[f"done_excluir_{idx}"] = False
        st.session_state[f"done_origem_{idx}"] = ""
        st.session_state[f"done_livre_{idx}"] = row.get("processo", "")
        st.session_state[f"done_atividade_{idx}"] = row.get("atividade", "")
        st.session_state[f"done_tempo_{idx}"] = row.get("tempo", "")
        set_status("done", idx, row.get("status", "Em andamento"))
        st.session_state[f"done_obs_{idx}"] = row.get("observacoes", "")


def remember_done_rows():
    rows = done_rows_from_state()
    if rows:
        st.session_state["_done_backup"] = rows


def protect_done_rows():
    remember_done_rows()
    st.session_state["_restore_done_after_change"] = True


def restore_done_rows_if_needed():
    if not st.session_state.pop("_restore_done_after_change", False):
        return
    if done_rows_from_state():
        return
    backup = st.session_state.get("_done_backup", [])
    if backup:
        write_done_rows(backup)


def current_draft():
    planning = planning_rows_from_state()
    extra = extra_rows_from_state()
    done = done_rows_from_state()
    if not done and st.session_state.get("_restore_done_after_change", False):
        done = st.session_state.get("_done_backup", [])
    return {
        "identity": {
            "data": st.session_state.get("identity_data", ""),
            "colaborador": st.session_state.get("identity_colaborador", ""),
            "setor": st.session_state.get("identity_setor", ""),
            "funcao": st.session_state.get("identity_funcao", ""),
            "horario": st.session_state.get("identity_horario", ""),
            "responsavel": st.session_state.get("identity_responsavel", ""),
        },
        "planning": planning,
        "extra": extra,
        "done": done,
        "indicators": {
            "produtividade": st.session_state.get("ind_produtividade", "Alto"),
            "cumprimento": st.session_state.get("ind_cumprimento", "Parcialmente"),
            "urgente": st.session_state.get("ind_urgente", "Nao"),
            "urgente_comentario": st.session_state.get("ind_urgente_comentario", ""),
            "dependencia": st.session_state.get("ind_dependencia", "Nao"),
            "dependencia_comentario": st.session_state.get("ind_dependencia_comentario", ""),
            "retrabalho": st.session_state.get("ind_retrabalho", "Nao"),
            "retrabalho_comentario": st.session_state.get("ind_retrabalho_comentario", ""),
            "sobrecarga": st.session_state.get("ind_sobrecarga", "Nao"),
            "sobrecarga_comentario": st.session_state.get("ind_sobrecarga_comentario", ""),
            "acumulo": st.session_state.get("ind_acumulo", "Nao"),
            "acumulo_comentario": st.session_state.get("ind_acumulo_comentario", ""),
        },
        "observacoes": st.session_state.get("observacoes", ""),
        "validacao": st.session_state.get("validacao", ""),
        "counts": {
            "planning_count": max(3, len(planning)),
            "extra_count": max(2, len(extra)),
            "done_count": max(2, len(done)),
        },
        "saved_at": st.session_state.get("last_saved_at", ""),
    }


def save_and_reload(draft, message):
    saved = save_draft(draft)
    st.session_state["_pending_draft"] = saved
    st.session_state["_feedback"] = message
    st.session_state["loaded_report_date"] = report_date_key(saved.get("identity", {}).get("data", ""))
    st.rerun()


def add_line_and_reload(count_key, message):
    if count_key != "done_count":
        protect_done_rows()
    draft = current_draft()
    current_count = int(st.session_state.get(count_key, 0))
    draft["counts"][count_key] = max(int(draft["counts"].get(count_key, 0)), current_count) + 1
    save_and_reload(draft, message)


def auto_save_current_draft():
    if not st.session_state.get("draft_initialized"):
        return
    draft = save_draft(current_draft())
    st.session_state["last_saved_at"] = draft["saved_at"]
    st.session_state["loaded_report_date"] = report_date_key(draft.get("identity", {}).get("data", ""))


def render_draft_actions():
    st.subheader("Rascunho do relatorio")
    last_saved = st.session_state.get("last_saved_at", "")
    if last_saved:
        st.caption(f"Ultimo rascunho salvo em {last_saved}.")
    else:
        st.caption("Este relatorio ainda nao foi salvo como rascunho.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar rascunho", use_container_width=True):
            save_and_reload(current_draft(), "Rascunho salvo. Na proxima vez, o app abre deste ponto.")
    with c2:
        confirmar_limpeza = st.checkbox("Confirmo limpar somente as atividades diarias desta data.")
        if st.button("Limpar atividades diarias", use_container_width=True, disabled=not confirmar_limpeza):
            draft = current_draft()
            draft["done"] = []
            draft["counts"]["done_count"] = 2
            st.session_state["_done_backup"] = []
            save_and_reload(draft, "Atividades diarias limpas. Planejamento e demandas foram mantidos.")

    with st.expander("Zerar relatorio"):
        confirmar = st.checkbox("Confirmo que quero deixar o relatorio todo em branco.")
        if st.button("Zerar tudo", disabled=not confirmar):
            st.session_state["_done_backup"] = []
            save_and_reload(blank_draft(), "Relatorio zerado.")


def render_planning():
    st.subheader("Planejamento semanal")
    rows = []
    for idx in range(st.session_state.planning_count):
        ensure_planning_row(idx)
        if st.session_state.get(f"planning_excluir_{idx}", False):
            continue
        with st.expander(row_title("planning", idx, "Planejamento"), expanded=False):
            excluir = st.checkbox("X Remover este planejamento deste relatorio", key=f"planning_excluir_{idx}")
            c1, c2 = st.columns([1, 1])
            with c1:
                processo = st.text_input("Processo/assunto", key=f"planning_processo_{idx}", on_change=protect_done_rows)
                prioridade = st.selectbox("Prioridade", PRIORIDADES, key=f"planning_prioridade_{idx}", on_change=protect_done_rows)
            with c2:
                descricao = st.text_area("Descricao resumida", key=f"planning_descricao_{idx}", height=80, on_change=protect_done_rows)
                render_status("planning", idx, on_change=protect_done_rows)
        if not excluir:
            rows.append({"processo": processo.strip(), "descricao": descricao.strip(), "prioridade": prioridade, "status": status_value("planning", idx)})
    if st.button("Adicionar planejamento"):
        add_line_and_reload("planning_count", "Planejamento salvo e nova linha aberta.")
    render_removed_items("planning", "Planejamento", st.session_state.planning_count)
    return clean(rows)


def render_extra():
    st.subheader("Demandas extraordinarias")
    rows = []
    for idx in range(st.session_state.extra_count):
        ensure_extra_row(idx)
        if st.session_state.get(f"extra_excluir_{idx}", False):
            continue
        with st.expander(row_title("extra", idx, "Demanda extraordinaria"), expanded=False):
            excluir = st.checkbox("X Remover esta demanda deste relatorio", key=f"extra_excluir_{idx}")
            c1, c2 = st.columns([1, 1])
            with c1:
                processo = st.text_input("Processo/assunto", key=f"extra_processo_{idx}", on_change=protect_done_rows)
                prazo = st.text_input("Prazo solicitado", key=f"extra_prazo_{idx}", on_change=protect_done_rows)
                prioridade = st.selectbox("Prioridade", PRIORIDADES, key=f"extra_prioridade_{idx}", on_change=protect_done_rows)
            with c2:
                descricao = st.text_area("Descricao resumida", key=f"extra_descricao_{idx}", height=80, on_change=protect_done_rows)
                render_status("extra", idx, on_change=protect_done_rows)
        if not excluir:
            rows.append(
                {
                    "processo": processo.strip(),
                    "descricao": descricao.strip(),
                    "prazo": prazo.strip(),
                    "prioridade": prioridade,
                    "status": status_value("extra", idx),
                }
            )
    if st.button("Adicionar demanda extraordinaria"):
        add_line_and_reload("extra_count", "Demandas salvas e nova linha aberta.")
    render_removed_items("extra", "Demanda extraordinaria", st.session_state.extra_count)
    return clean(rows)


def demand_options(planning_rows, extra_rows):
    options = []
    for row in planning_rows + extra_rows:
        processo = row.get("processo", "").strip()
        if processo and processo not in options:
            options.append(processo)
    return options


def apply_done_prefill(new_rows, current_rows=None):
    existing_rows = done_rows_from_state()
    if not existing_rows and current_rows:
        existing_rows = list(current_rows)
    existing_pairs = {
        (
            row.get("processo", "").strip().lower(),
            row.get("atividade", "").strip().lower(),
        )
        for row in existing_rows
        if row.get("processo", "").strip() or row.get("atividade", "").strip()
    }
    merged_rows = list(existing_rows)

    for row in new_rows:
        processo = row.get("processo", "").strip()
        atividade = row.get("atividade", "").strip()
        pair = (processo.lower(), atividade.lower())
        if (not processo and not atividade) or pair in existing_pairs:
            continue
        merged_rows.append(
            {
                "processo": processo,
                "atividade": atividade,
                "tempo": row.get("tempo", ""),
                "status": row.get("status", "Em andamento"),
                "observacoes": row.get("observacoes", ""),
            }
        )
        existing_pairs.add(pair)

    write_done_rows(merged_rows)
    remember_done_rows()


def render_done(planning_rows, extra_rows):
    st.subheader("Atividades executadas")
    restore_done_rows_if_needed()
    options = [""] + demand_options(planning_rows, extra_rows)

    rows = []
    for idx in range(st.session_state.done_count):
        ensure_done_row(idx)
        if st.session_state.get(f"done_excluir_{idx}", False):
            continue
        current_origin = st.session_state.get(f"done_origem_{idx}", "")
        row_options = options if not current_origin or current_origin in options else options + [current_origin]
        with st.expander(row_title("done", idx, "Atividade executada", f"done_livre_{idx}", f"done_origem_{idx}"), expanded=False):
            excluir = st.checkbox("X Remover esta atividade deste relatorio", key=f"done_excluir_{idx}")
            c1, c2 = st.columns([1, 1])
            with c1:
                origem = st.selectbox("Processo ja listado", row_options, key=f"done_origem_{idx}")
                livre = st.text_input("Processo livre", key=f"done_livre_{idx}")
                tempo = st.text_input("Tempo aproximado", key=f"done_tempo_{idx}")
            with c2:
                atividade = st.text_area("Atividade realizada", key=f"done_atividade_{idx}", height=80)
                render_status("done", idx)
                obs = st.text_area("Observacoes", key=f"done_obs_{idx}", height=80)
        if not excluir:
            rows.append(
                {
                    "processo": livre.strip() or origem.strip(),
                    "atividade": atividade.strip(),
                    "tempo": tempo.strip(),
                    "status": status_value("done", idx),
                    "observacoes": obs.strip(),
                }
            )
    if st.button("Puxar planejamento e demandas para executadas", use_container_width=True):
        prefill_rows = []
        for row in planning_rows + extra_rows:
            if row.get("processo") or row.get("descricao"):
                prefill_rows.append({"processo": row.get("processo", ""), "atividade": row.get("descricao", ""), "status": "Em andamento"})
        apply_done_prefill(prefill_rows, rows)
        save_and_reload(current_draft(), "Demandas acrescentadas sem apagar as atividades existentes.")
    if st.button("Adicionar atividade executada"):
        add_line_and_reload("done_count", "Atividades salvas e nova linha aberta.")
    render_removed_items("done", "Atividade executada", st.session_state.done_count)
    return clean(rows)


inject_design()
render_header()
render_profile_links()
render_iphone_mode_hint()
init_state()
render_draft_actions()

st.subheader("Identificacao")
c1, c2, c3 = st.columns(3)
with c1:
    data = st.text_input("Data ou periodo", key="identity_data")
    setor = st.text_input("Setor/Nucleo", key="identity_setor")
with c2:
    colaborador = st.text_input("Colaborador(a)", key="identity_colaborador")
    funcao = st.text_input("Funcao", key="identity_funcao")
with c3:
    horario = st.text_input("Horario de trabalho", key="identity_horario")
    responsavel = st.text_input("Responsavel pela validacao", key="identity_responsavel")

planning_rows = render_planning()
extra_rows = render_extra()
done_rows = render_done(planning_rows, extra_rows)

st.subheader("Indicadores qualitativos")
i1, i2, i3 = st.columns(3)
with i1:
    produtividade = st.selectbox("Nivel de produtividade percebido", PRODUTIVIDADE, key="ind_produtividade")
    urgente = st.selectbox("Houve demanda urgente nao planejada?", SIM_NAO, key="ind_urgente")
    urgente_comentario = st.text_input("Comentario sobre demanda urgente", key="ind_urgente_comentario")
with i2:
    cumprimento = st.selectbox("Cumprimento das atividades planejadas", CUMPRIMENTO, key="ind_cumprimento")
    dependencia = st.selectbox("Houve dependencia de outro setor?", SIM_NAO, key="ind_dependencia")
    dependencia_comentario = st.text_input("Qual dependencia?", key="ind_dependencia_comentario")
with i3:
    retrabalho = st.selectbox("Houve retrabalho?", SIM_NAO, key="ind_retrabalho")
    retrabalho_comentario = st.text_input("Motivo do retrabalho", key="ind_retrabalho_comentario")
    sobrecarga = st.selectbox("Houve sobrecarga de demandas?", SIM_NAO, key="ind_sobrecarga")
    sobrecarga_comentario = st.text_input("Comentario sobre sobrecarga", key="ind_sobrecarga_comentario")

acumulo = st.selectbox("Houve acumulo de demandas?", SIM_NAO, key="ind_acumulo")
acumulo_comentario = st.text_input("Comentario sobre acumulo", key="ind_acumulo_comentario")

st.subheader("Observacoes e validacao")
observacoes = st.text_area("Observacoes do(a) colaborador(a)", height=120, key="observacoes")
validacao = st.text_area("Analise/validacao da chefia imediata", height=120, key="validacao")

c1, c2 = st.columns(2)
with c1:
    if st.button("Salvar rascunho agora", use_container_width=True):
        save_and_reload(current_draft(), "Rascunho salvo. Na proxima vez, o app abre deste ponto.")
with c2:
    gerar = st.button("Gerar relatorio Word", type="primary", use_container_width=True)

auto_save_current_draft()

if gerar:
    draft = save_draft(current_draft())
    payload = {
        "identity": draft["identity"],
        "planning": draft["planning"],
        "extra": draft["extra"],
        "done": draft["done"],
        "indicators": draft["indicators"],
        "observacoes": draft["observacoes"],
        "validacao": draft["validacao"],
    }
    target = generate_report(payload)
    data_bytes = Path(target).read_bytes()
    st.session_state["last_saved_at"] = draft["saved_at"]
    st.success("Relatorio gerado e rascunho salvo.")
    st.download_button(
        "Baixar relatorio Word",
        data=data_bytes,
        file_name=Path(target).name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
    )
