from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from app import generate_report, read_defaults


st.set_page_config(
    page_title="Relatório JMCM",
    page_icon="📄",
    layout="wide",
)

st.title("Relatório JMCM")

defaults = read_defaults()


def normalize_rows(rows, columns):
    normalized = []
    for row in rows:
        normalized.append({column: row.get(column, "") for column in columns})
    return normalized or [{column: "" for column in columns}]


with st.form("relatorio"):
    st.subheader("Identificação")
    col1, col2, col3 = st.columns(3)
    with col1:
        data = st.text_input("Data ou período", value=defaults["identity"].get("data", ""))
        setor = st.text_input("Setor/Núcleo", value=defaults["identity"].get("setor", ""))
    with col2:
        colaborador = st.text_input("Colaborador(a)", value=defaults["identity"].get("colaborador", ""))
        funcao = st.text_input("Função", value=defaults["identity"].get("funcao", ""))
    with col3:
        horario = st.text_input("Horário de trabalho", value=defaults["identity"].get("horario", ""))
        responsavel = st.text_input("Responsável pela validação", value=defaults["identity"].get("responsavel", ""))

    st.subheader("Planejamento semanal")
    planning = st.data_editor(
        normalize_rows(defaults.get("planning", []), ["processo", "descricao", "prioridade", "status"]),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "processo": "Processo/assunto",
            "descricao": "Descrição resumida",
            "prioridade": st.column_config.SelectboxColumn("Prioridade", options=["Alta", "Média", "Baixa", "Urgente"]),
            "status": "Status",
        },
        key="planning",
    )

    st.subheader("Demandas extraordinárias")
    extra = st.data_editor(
        normalize_rows(defaults.get("extra", []), ["processo", "descricao", "prazo", "prioridade", "status"]),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "processo": "Processo/assunto",
            "descricao": "Descrição resumida",
            "prazo": "Prazo solicitado",
            "prioridade": st.column_config.SelectboxColumn("Prioridade", options=["Alta", "Média", "Baixa", "Urgente"]),
            "status": "Status",
        },
        key="extra",
    )

    st.subheader("Atividades executadas")
    done = st.data_editor(
        normalize_rows(defaults.get("done", []), ["processo", "atividade", "tempo", "status", "observacoes"]),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "processo": "Processo/demanda",
            "atividade": "Atividade realizada",
            "tempo": "Tempo aproximado",
            "status": "Status",
            "observacoes": "Observações",
        },
        key="done",
    )

    st.subheader("Indicadores qualitativos")
    c1, c2, c3 = st.columns(3)
    with c1:
        produtividade = st.selectbox("Nível de produtividade percebido", ["Alto", "Médio", "Baixo"], index=0)
        urgente = st.selectbox("Houve demanda urgente não planejada?", ["Sim", "Não"], index=0)
        urgente_comentario = st.text_input("Comentário sobre demanda urgente")
    with c2:
        cumprimento = st.selectbox("Cumprimento das atividades planejadas", ["Sim", "Parcialmente", "Não"], index=1)
        dependencia = st.selectbox("Houve dependência de outro setor?", ["Sim", "Não"], index=0)
        dependencia_comentario = st.text_input("Qual dependência?")
    with c3:
        retrabalho = st.selectbox("Houve retrabalho?", ["Sim", "Não"], index=0)
        retrabalho_comentario = st.text_input("Motivo do retrabalho")
        sobrecarga = st.selectbox("Houve sobrecarga de demandas?", ["Sim", "Não"], index=0)
        sobrecarga_comentario = st.text_input("Comentário sobre sobrecarga")

    acumulo = st.selectbox("Houve acúmulo de demandas?", ["Sim", "Não"], index=0)
    acumulo_comentario = st.text_input("Comentário sobre acúmulo")

    st.subheader("Observações e validação")
    observacoes = st.text_area("Observações do(a) colaborador(a)", value=defaults.get("observacoes", ""), height=120)
    validacao = st.text_area("Análise/validação da chefia imediata", value="", height=120)

    submitted = st.form_submit_button("Gerar relatório Word", type="primary")


def clean_rows(rows):
    cleaned = []
    for row in rows:
        item = {key: "" if value is None else str(value).strip() for key, value in row.items()}
        if any(item.values()):
            cleaned.append(item)
    return cleaned


if submitted:
    payload = {
        "identity": {
            "data": data,
            "colaborador": colaborador,
            "setor": setor,
            "funcao": funcao,
            "horario": horario,
            "responsavel": responsavel,
        },
        "planning": clean_rows(planning),
        "extra": clean_rows(extra),
        "done": clean_rows(done),
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
    st.success("Relatório gerado com sucesso.")
    st.download_button(
        "Baixar relatório Word",
        data=data_bytes,
        file_name=Path(target).name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
    )
