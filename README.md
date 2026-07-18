# relatorio-jmcm

Aplicativo Streamlit para gerar relatorios de produtividade em Word.

## Arquivos

- `streamlit_app.py`: tela do app online.
- `app.py`: motor que gera o `.docx`.
- `modelo_relatorio.docx`: modelo Word usado como base.
- `requirements.txt`: dependencias para o Streamlit instalar.
- `supabase_relatorios.sql`: tabela permanente dos rascunhos.

## Supabase

Crie a tabela executando o conteudo de `supabase_relatorios.sql` no SQL Editor do Supabase.

No Streamlit Community Cloud, abra as configuracoes do app e adicione os secrets:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-chave-anon-ou-service-role"
```

Quando esses secrets existem, o app salva cada data na tabela `relatorios`.
Sem esses secrets, ele usa arquivos locais apenas para desenvolvimento.

## Publicar no Streamlit Community Cloud

1. Envie os arquivos para o repositorio `relatorio-jmcm`.
2. Acesse `https://share.streamlit.io/`.
3. Selecione o repositorio `relatorio-jmcm`.
4. Em **Main file path**, use `streamlit_app.py`.
5. Clique em **Deploy**.
