from __future__ import annotations

from pathlib import Path

import streamlit as st

from app import generate_report, read_defaults


st.set_page_config(page_title="Relatorio JMCM", layout="wide")
st.title("Relatorio JMCM")

defaults = read_defaults()

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


def init_state():
    st.session_state.setdefault("use_previous_items", True)
    st.session_state.setdefault("planning_count", max(5, len(defaults.get("planning", []))))
    st.session_state.setdefault("extra_count", 3)
    st.session_state.setdefault("done_count", 3)


def text_value(name, default=""):
    return "" if default is None else str(default)


def select_index(options, value):
    value = text_value("", value).strip()
    return options.index(value) if value in options else 0


def status_value(prefix, index):
    livre = st.session_state.get(f"{prefix}_status_livre_{index}", "").strip()
    rapido = st.session_state.get(f"{prefix}_status_{index}", "").strip()
    return livre or rapido


def row_title(prefix, index, label, default="", *extra_keys):
    values = [st.session_state.get(f"{prefix}_processo_{index}", default)]
    values.extend(st.session_state.get(key, "") for key in extra_keys)
    title = ""
    for value in values:
        title = " ".join(text_value("", value).split())
        if title:
            break
    if not title:
        title = "sem assunto"
    if len(title) > 64:
        title = title[:61].rstrip() + "..."
    excluded = st.session_state.get(f"{prefix}_excluir_{index}", False)
    suffix = " - removido desta vez" if excluded else ""
    return f"{label} {index + 1}: {title}{suffix}"


def clean(rows):
    cleaned = []
    for row in rows:
        if any(str(value).strip() for value in row.values()):
            cleaned.append(row)
    return cleaned


def demand_options(planning_rows, extra_rows):
    options = []
    for row in planning_rows + extra_rows:
        processo = row.get("processo", "").strip()
        if processo and processo not in options:
            options.append(processo)
    return options


def apply_done_prefill(rows):
    st.session_state.done_count = max(3, len(rows))
    for idx, row in enumerate(rows):
        st.session_state[f"done_excluir_{idx}"] = False
        st.session_state[f"done_origem_{idx}"] = row.get("processo", "")
        st.session_state[f"done_livre_{idx}"] = ""
        st.session_state[f"done_atividade_{idx}"] = row.get("atividade", "")
        st.session_state[f"done_tempo_{idx}"] = ""
        st.session_state[f"done_status_{idx}"] = "Em andamento"
        st.session_state[f"done_status_livre_{idx}"] = ""
        st.session_state[f"done_obs_{idx}"] = ""


def render_status(prefix, idx, default=""):
    st.selectbox(
        "Status rapido",
        STATUS,
        index=select_index(STATUS, default),
        key=f"{prefix}_status_{idx}",
    )
    st.text_input("Status livre", key=f"{prefix}_status_livre_{idx}")


def clear_item_fields(prefix):
    keys = [key for key in st.session_state if key.startswith(f"{prefix}_")]
    for key in keys:
        del st.session_state[key]


def start_with_previous_items():
    clear_item_fields("planning")
    clear_item_fields("extra")
    clear_item_fields("done")
    st.session_state.use_previous_items = True
    st.session_state.planning_count = max(5, len(defaults.get("planning", [])))
    st.session_state.extra_count = 3
    st.session_state.done_count = 3
    st.rerun()


def start_blank_report():
    clear_item_fields("planning")
    clear_item_fields("extra")
    clear_item_fields("done")
    st.session_state.use_previous_items = False
    st.session_state.planning_count = 3
    st.session_state.extra_count = 2
    st.session_state.done_count = 2
    st.rerun()


def render_start_options():
    st.subheader("Inicio do relatorio")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Manter itens anteriores", use_container_width=True):
            start_with_previous_items()
    with c2:
        if st.button("Iniciar em branco", use_container_width=True):
            start_blank_report()


def render_planning():
    st.subheader("Planejamento semanal")
    source = defaults.get("planning", []) if st.session_state.use_previous_items else []
    rows = []
    for idx in range(st.session_state.planning_count):
        base = source[idx] if idx < len(source) else {}
        with st.expander(
            row_title("planning", idx, "Planejamento", base.get("processo", "")),
            expanded=idx < 3,
        ):
            excluir = st.checkbox("X Remover este planejamento deste relatorio", key=f"planning_excluir_{idx}")
            c1, c2 = st.columns([1, 1])
            with c1:
                processo = st.text_input(
                    "Processo/assunto",
                    value=text_value("processo", base.get("processo", "")),
                    key=f"planning_processo_{idx}",
                )
                prioridade = st.selectbox(
                    "Prioridade",
                    PRIORIDADES,
                    index=select_index(PRIORIDADES, base.get("prioridade", "")),
                    key=f"planning_prioridade_{idx}",
                )
            with c2:
                descricao = st.text_area(
                    "Descricao resumida",
                    value=text_value("descricao", base.get("descricao", "")),
                    key=f"planning_descricao_{idx}",
                    height=80,
                )
                render_status("planning", idx, base.get("status", ""))
        if not excluir:
            rows.append(
                {
                    "processo": processo.strip(),
                    "descricao": descricao.strip(),
                    "prioridade": prioridade,
                    "status": status_value("planning", idx),
                }
            )
    if st.button("Adicionar planejamento"):
        st.session_state.planning_count += 1
        st.rerun()
    return clean(rows)


def render_extra():
    st.subheader("Demandas extraordinarias")
    rows = []
    for idx in range(st.session_state.extra_count):
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
        st.session_state.extra_count += 1
        st.rerun()
    return clean(rows)


def render_done(planning_rows, extra_rows):
    st.subheader("Atividades executadas")
    options = [""] + demand_options(planning_rows, extra_rows)

    if st.button("Puxar planejamento e demandas para executadas"):
        rows = []
        for row in planning_rows + extra_rows:
            if row.get("processo"):
                rows.append({"processo": row["processo"], "atividade": row.get("descricao", "")})
        apply_done_prefill(rows)
        st.rerun()

    rows = []
    for idx in range(st.session_state.done_count):
        with st.expander(
            row_title(
                "done",
                idx,
                "Atividade executada",
                "",
                f"done_livre_{idx}",
                f"done_origem_{idx}",
            ),
            expanded=idx < 3,
        ):
            excluir = st.checkbox("X Remover esta atividade deste relatorio", key=f"done_excluir_{idx}")
            c1, c2 = st.columns([1, 1])
            with c1:
                origem = st.selectbox(
                    "Processo ja listado",
                    options,
                    key=f"done_origem_{idx}",
                )
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
        st.session_state.done_count += 1
        st.rerun()
    return clean(rows)


init_state()

render_start_options()

st.subheader("Identificacao")
c1, c2, c3 = st.columns(3)
with c1:
    data = st.text_input("Data ou periodo", value=defaults["identity"].get("data", ""))
    setor = st.text_input("Setor/Nucleo", value=defaults["identity"].get("setor", ""))
with c2:
    colaborador = st.text_input("Colaborador(a)", value=defaults["identity"].get("colaborador", ""))
    funcao = st.text_input("Funcao", value=defaults["identity"].get("funcao", ""))
with c3:
    horario = st.text_input("Horario de trabalho", value=defaults["identity"].get("horario", ""))
    responsavel = st.text_input("Responsavel pela validacao", value=defaults["identity"].get("responsavel", ""))

planning_rows = render_planning()
extra_rows = render_extra()
done_rows = render_done(planning_rows, extra_rows)

st.subheader("Indicadores qualitativos")
i1, i2, i3 = st.columns(3)
with i1:
    produtividade = st.selectbox("Nivel de produtividade percebido", ["Alto", "Medio", "Baixo"], index=0)
    urgente = st.selectbox("Houve demanda urgente nao planejada?", ["Sim", "Nao"], index=0)
    urgente_comentario = st.text_input("Comentario sobre demanda urgente")
with i2:
    cumprimento = st.selectbox("Cumprimento das atividades planejadas", ["Sim", "Parcialmente", "Nao"], index=1)
    dependencia = st.selectbox("Houve dependencia de outro setor?", ["Sim", "Nao"], index=0)
    dependencia_comentario = st.text_input("Qual dependencia?")
with i3:
    retrabalho = st.selectbox("Houve retrabalho?", ["Sim", "Nao"], index=0)
    retrabalho_comentario = st.text_input("Motivo do retrabalho")
    sobrecarga = st.selectbox("Houve sobrecarga de demandas?", ["Sim", "Nao"], index=0)
    sobrecarga_comentario = st.text_input("Comentario sobre sobrecarga")

acumulo = st.selectbox("Houve acumulo de demandas?", ["Sim", "Nao"], index=0)
acumulo_comentario = st.text_input("Comentario sobre acumulo")

st.subheader("Observacoes e validacao")
observacoes = st.text_area("Observacoes do(a) colaborador(a)", value=defaults.get("observacoes", ""), height=120)
validacao = st.text_area("Analise/validacao da chefia imediata", value="", height=120)

if st.button("Gerar relatorio Word", type="primary"):
    payload = {
        "identity": {
            "data": data,
            "colaborador": colaborador,
            "setor": setor,
            "funcao": funcao,
            "horario": horario,
            "responsavel": responsavel,
        },
        "planning": planning_rows,
        "extra": extra_rows,
        "done": done_rows,
        "indicators": {
            "produtividade": produtividade,
            "cumprimento": cumprimento,
            "urgente": urgente,
            "urgente_comentario": urgente_comentario,
            "dependencia": dependencia,
            "dependencia_comentario": dependencia_comentario,
            "retrabalho": retrabalho,
            "retrabalho_comentario": retrabalho_comentario,
            "sobrecarga": sobrecarga,
            "sobrecarga_comentario": sobrecarga_comentario,
            "acumulo": acumulo,
            "acumulo_comentario": acumulo_comentario,
        },
        "observacoes": observacoes,
        "validacao": validacao,
    }
    target = generate_report(payload)
    data_bytes = Path(target).read_bytes()
    st.success("Relatorio gerado com sucesso.")
    st.download_button(
        "Baixar relatorio Word",
        data=data_bytes,
        file_name=Path(target).name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
    )
