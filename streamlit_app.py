from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from app import generate_report, read_defaults


st.set_page_config(page_title="Relatorio JMCM", layout="wide")
st.title("Relatorio JMCM")

defaults = read_defaults()
SAVE_PATH = Path(__file__).with_name("relatorio_salvo.json")

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


def load_draft():
    if not SAVE_PATH.exists():
        return default_draft()
    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_draft()
    if not isinstance(data, dict):
        return default_draft()
    return data


def save_draft(draft):
    draft = dict(draft)
    draft["saved_at"] = saved_now()
    SAVE_PATH.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
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


def init_state():
    if not st.session_state.get("draft_initialized"):
        apply_draft(load_draft())
        st.session_state["draft_initialized"] = True
    pending = st.session_state.pop("_pending_draft", None)
    if pending is not None:
        apply_draft(pending)
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


def render_status(prefix, idx):
    st.selectbox("Status rapido", STATUS, key=f"{prefix}_status_{idx}")
    st.text_input("Status livre", key=f"{prefix}_status_livre_{idx}")


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


def current_draft():
    planning = planning_rows_from_state()
    extra = extra_rows_from_state()
    done = done_rows_from_state()
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
    st.rerun()


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
        if st.button("Limpar atividades diarias", use_container_width=True):
            draft = current_draft()
            draft["done"] = []
            draft["counts"]["done_count"] = 2
            save_and_reload(draft, "Atividades diarias limpas. Planejamento e demandas foram mantidos.")

    with st.expander("Zerar relatorio"):
        confirmar = st.checkbox("Confirmo que quero deixar o relatorio todo em branco.")
        if st.button("Zerar tudo", disabled=not confirmar):
            save_and_reload(blank_draft(), "Relatorio zerado.")


def render_planning():
    st.subheader("Planejamento semanal")
    rows = []
    for idx in range(st.session_state.planning_count):
        ensure_planning_row(idx)
        if st.session_state.get(f"planning_excluir_{idx}", False):
            continue
        with st.expander(row_title("planning", idx, "Planejamento"), expanded=idx < 3):
            excluir = st.checkbox("X Remover este planejamento deste relatorio", key=f"planning_excluir_{idx}")
            c1, c2 = st.columns([1, 1])
            with c1:
                processo = st.text_input("Processo/assunto", key=f"planning_processo_{idx}")
                prioridade = st.selectbox("Prioridade", PRIORIDADES, key=f"planning_prioridade_{idx}")
            with c2:
                descricao = st.text_area("Descricao resumida", key=f"planning_descricao_{idx}", height=80)
                render_status("planning", idx)
        if not excluir:
            rows.append({"processo": processo.strip(), "descricao": descricao.strip(), "prioridade": prioridade, "status": status_value("planning", idx)})
    if st.button("Adicionar planejamento"):
        save_draft(current_draft())
        st.session_state.planning_count += 1
        st.rerun()
    render_removed_items("planning", "Planejamento", st.session_state.planning_count)
    return clean(rows)


def render_extra():
    st.subheader("Demandas extraordinarias")
    rows = []
    for idx in range(st.session_state.extra_count):
        ensure_extra_row(idx)
        if st.session_state.get(f"extra_excluir_{idx}", False):
            continue
        with st.expander(row_title("extra", idx, "Demanda extraordinaria"), expanded=idx < 2):
            excluir = st.checkbox("X Remover esta demanda deste relatorio", key=f"extra_excluir_{idx}")
            c1, c2 = st.columns([1, 1])
            with c1:
                processo = st.text_input("Processo/assunto", key=f"extra_processo_{idx}")
                prazo = st.text_input("Prazo solicitado", key=f"extra_prazo_{idx}")
                prioridade = st.selectbox("Prioridade", PRIORIDADES, key=f"extra_prioridade_{idx}")
            with c2:
                descricao = st.text_area("Descricao resumida", key=f"extra_descricao_{idx}", height=80)
                render_status("extra", idx)
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
        save_draft(current_draft())
        st.session_state.extra_count += 1
        st.rerun()
    render_removed_items("extra", "Demanda extraordinaria", st.session_state.extra_count)
    return clean(rows)


def demand_options(planning_rows, extra_rows):
    options = []
    for row in planning_rows + extra_rows:
        processo = row.get("processo", "").strip()
        if processo and processo not in options:
            options.append(processo)
    return options


def apply_done_prefill(new_rows):
    existing_rows = done_rows_from_state()
    existing_processos = {
        row.get("processo", "").strip().lower()
        for row in existing_rows
        if row.get("processo", "").strip()
    }
    merged_rows = list(existing_rows)

    for row in new_rows:
        processo = row.get("processo", "").strip()
        if not processo or processo.lower() in existing_processos:
            continue
        merged_rows.append(
            {
                "processo": processo,
                "atividade": row.get("atividade", ""),
                "tempo": row.get("tempo", ""),
                "status": row.get("status", "Em andamento"),
                "observacoes": row.get("observacoes", ""),
            }
        )
        existing_processos.add(processo.lower())

    st.session_state.done_count = max(2, len(merged_rows))
    clear_item_fields("done")

    for idx, row in enumerate(merged_rows):
        st.session_state[f"done_excluir_{idx}"] = False
        st.session_state[f"done_origem_{idx}"] = ""
        st.session_state[f"done_livre_{idx}"] = row.get("processo", "")
        st.session_state[f"done_atividade_{idx}"] = row.get("atividade", "")
        st.session_state[f"done_tempo_{idx}"] = row.get("tempo", "")
        set_status("done", idx, row.get("status", "Em andamento"))
        st.session_state[f"done_obs_{idx}"] = row.get("observacoes", "")


def render_done(planning_rows, extra_rows):
    st.subheader("Atividades executadas")
    options = [""] + demand_options(planning_rows, extra_rows)

    if st.button("Puxar planejamento e demandas para executadas"):
        save_draft(current_draft())
        rows = []
        for row in planning_rows + extra_rows:
            if row.get("processo"):
                rows.append({"processo": row["processo"], "atividade": row.get("descricao", ""), "status": "Em andamento"})
        apply_done_prefill(rows)
        st.rerun()

    rows = []
    for idx in range(st.session_state.done_count):
        ensure_done_row(idx)
        if st.session_state.get(f"done_excluir_{idx}", False):
            continue
        current_origin = st.session_state.get(f"done_origem_{idx}", "")
        row_options = options if not current_origin or current_origin in options else options + [current_origin]
        with st.expander(row_title("done", idx, "Atividade executada", f"done_livre_{idx}", f"done_origem_{idx}"), expanded=idx < 3):
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
    if st.button("Adicionar atividade executada"):
        save_draft(current_draft())
        st.session_state.done_count += 1
        st.rerun()
    render_removed_items("done", "Atividade executada", st.session_state.done_count)
    return clean(rows)


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
