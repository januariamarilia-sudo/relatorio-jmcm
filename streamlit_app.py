from __future__ import annotations

from pathlib import Path

import streamlit as st

from app import generate_report, read_defaults


st.set_page_config(
    page_title="Relatorio JMCM",
    page_icon="DOC",
    layout="wide",
)

st.title("Relatorio JMCM")

defaults = read_defaults()

PRIORIDADES = ["", "Alta", "Media", "Média", "media", "média", "Baixa", "Urgente", "urgente"]
STATUS_OPCOES = [
    "",
    "Nao iniciada",
    "Não iniciada",
    "Em andamento",
    "Paralisado",
    "Concluido",
    "Concluído",
    "Parcialmente concluido",
    "Parcialmente concluído",
    "Aguardando outro setor",
    "Aguardando assinatura",
    "Aguardando documentos",
    "Aguardando publicacao",
    "Aguardando publicação",
]


def default_rows(rows, columns):
    normalized = []
    for row in rows:
        normalized.append({column: row.get(column, "") for column in columns})
    return normalized or [{column: "" for column in columns}]


def with_status_helpers(rows, columns):
    prepared = []
    for row in rows:
        item = {column: row.get(column, "") for column in columns}
        status = item.pop("status", "")
        item["status_rapido"] = status if status in STATUS_OPCOES else ""
        item["status_livre"] = "" if status in STATUS_OPCOES else status
        prepared.append(item)
    return prepared or [{column: "" for column in columns if column != "status"} | {"status_rapido": "", "status_livre": ""}]


def clean_rows(rows):
    cleaned = []
    for row in rows:
        item = {key: "" if value is None else str(value).strip() for key, value in row.items()}
        if any(item.values()):
            cleaned.append(item)
    return cleaned


def final_status(row):
    livre = str(row.get("status_livre", "") or "").strip()
    rapido = str(row.get("status_rapido", "") or "").strip()
    return livre or rapido


def finalize_planning(rows):
    finalized = []
    for row in clean_rows(rows):
        finalized.append(
            {
                "processo": row.get("processo", ""),
                "descricao": row.get("descricao", ""),
                "prioridade": row.get("prioridade", ""),
                "status": final_status(row),
            }
        )
    return finalized


def finalize_extra(rows):
    finalized = []
    for row in clean_rows(rows):
        finalized.append(
            {
                "processo": row.get("processo", ""),
                "descricao": row.get("descricao", ""),
                "prazo": row.get("prazo", ""),
                "prioridade": row.get("prioridade", ""),
                "status": final_status(row),
            }
        )
    return finalized


def demand_options(planning_rows, extra_rows):
    options = []
    for row in clean_rows(planning_rows) + clean_rows(extra_rows):
        processo = str(row.get("processo", "") or "").strip()
        if processo and processo not in options:
            options.append(processo)
    return options


def finalize_done(rows):
    finalized = []
    for row in clean_rows(rows):
        processo_livre = row.get("processo_livre", "")
        processo_origem = row.get("processo_origem", "")
        finalized.append(
            {
                "processo": processo_livre or processo_origem,
                "atividade": row.get("atividade", ""),
                "tempo": row.get("tempo", ""),
                "status": final_status(row),
                "observacoes": row.get("observacoes", ""),
            }
        )
    return finalized


def rows_for_done_from_demands(planning_rows, extra_rows):
    rows = []
    for row in clean_rows(planning_rows):
        processo = str(row.get("processo", "") or "").strip()
        if processo:
            rows.append(
                {
                    "processo_origem": processo,
                    "processo_livre": "",
                    "atividade": row.get("descricao", ""),
                    "tempo": "",
                    "status_rapido": "Em andamento",
                    "status_livre": "",
                    "observacoes": "",
                }
            )
    for row in clean_rows(extra_rows):
        processo = str(row.get("processo", "") or "").strip()
        if processo:
            rows.append(
                {
                    "processo_origem": processo,
                    "processo_livre": "",
                    "atividade": row.get("descricao", ""),
                    "tempo": "",
                    "status_rapido": "Em andamento",
                    "status_livre": "",
                    "observacoes": "",
                }
            )
    return rows or [
        {
            "processo_origem": "",
            "processo_livre": "",
            "atividade": "",
            "tempo": "",
            "status_rapido": "",
            "status_livre": "",
            "observacoes": "",
        }
    ]


if "planning_data" not in st.session_state:
    st.session_state.planning_data = with_status_helpers(
        defaults.get("planning", []),
        ["processo", "descricao", "prioridade", "status"],
    )
if "extra_data" not in st.session_state:
    st.session_state.extra_data = with_status_helpers(
        defaults.get("extra", []),
        ["processo", "descricao", "prazo", "prioridade", "status"],
    )
if "done_data" not in st.session_state:
    st.session_state.done_data = [
        {
            "processo_origem": "",
            "processo_livre": "",
            "atividade": "",
            "tempo": "",
            "status_rapido": "",
            "status_livre": "",
            "observacoes": "",
        }
    ]


st.subheader("Identificacao")
col1, col2, col3 = st.columns(3)
with col1:
    data = st.text_input("Data ou periodo", value=defaults["identity"].get("data", ""))
    setor = st.text_input("Setor/Nucleo", value=defaults["identity"].get("setor", ""))
with col2:
    colaborador = st.text_input("Colaborador(a)", value=defaults["identity"].get("colaborador", ""))
    funcao = st.text_input("Funcao", value=defaults["identity"].get("funcao", ""))
with col3:
    horario = st.text_input("Horario de trabalho", value=defaults["identity"].get("horario", ""))
    responsavel = st.text_input("Responsavel pela validacao", value=defaults["identity"].get("responsavel", ""))

st.subheader("Planejamento semanal")
planning = st.data_editor(
    st.session_state.planning_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "processo": "Processo/assunto",
        "descricao": "Descricao resumida",
        "prioridade": st.column_config.SelectboxColumn("Prioridade", options=PRIORIDADES),
        "status_rapido": st.column_config.SelectboxColumn("Status rapido", options=STATUS_OPCOES),
        "status_livre": "Status livre",
    },
    key="planning_editor",
)
st.session_state.planning_data = planning

st.subheader("Demandas extraordinarias")
extra = st.data_editor(
    st.session_state.extra_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "processo": "Processo/assunto",
        "descricao": "Descricao resumida",
        "prazo": "Prazo solicitado",
        "prioridade": st.column_config.SelectboxColumn("Prioridade", options=PRIORIDADES),
        "status_rapido": st.column_config.SelectboxColumn("Status rapido", options=STATUS_OPCOES),
        "status_livre": "Status livre",
    },
    key="extra_editor",
)
st.session_state.extra_data = extra

options = demand_options(planning, extra)

st.subheader("Atividades executadas")
col_copy, col_hint = st.columns([1, 3])
with col_copy:
    if st.button("Puxar demandas para executadas", type="secondary"):
        st.session_state.done_data = rows_for_done_from_demands(planning, extra)
        st.rerun()
with col_hint:
    st.caption("Use 'Processo ja listado' para escolher uma demanda do planejamento/extraordinarias, ou preencha 'Processo livre' para digitar outro.")

done = st.data_editor(
    st.session_state.done_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "processo_origem": st.column_config.SelectboxColumn(
            "Processo ja listado",
            options=[""] + options,
        ),
        "processo_livre": "Processo livre",
        "atividade": "Atividade realizada",
        "tempo": "Tempo aproximado",
        "status_rapido": st.column_config.SelectboxColumn("Status rapido", options=STATUS_OPCOES),
        "status_livre": "Status livre",
        "observacoes": "Observacoes",
    },
    key="done_editor",
)
st.session_state.done_data = done

st.subheader("Indicadores qualitativos")
c1, c2, c3 = st.columns(3)
with c1:
    produtividade = st.selectbox("Nivel de produtividade percebido", ["Alto", "Medio", "Baixo"], index=0)
    urgente = st.selectbox("Houve demanda urgente nao planejada?", ["Sim", "Nao"], index=0)
    urgente_comentario = st.text_input("Comentario sobre demanda urgente")
with c2:
    cumprimento = st.selectbox("Cumprimento das atividades planejadas", ["Sim", "Parcialmente", "Nao"], index=1)
    dependencia = st.selectbox("Houve dependencia de outro setor?", ["Sim", "Nao"], index=0)
    dependencia_comentario = st.text_input("Qual dependencia?")
with c3:
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
        "planning": finalize_planning(planning),
        "extra": finalize_extra(extra),
        "done": finalize_done(done),
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
