"""Interactive local MVP. UI actions call tested domain services, not inline SQL updates."""
import hashlib
import json
from io import BytesIO

import pandas as pd
import streamlit as st

from src.alert_workflow import (
    AlertWorkflowError, alert_history, assign, list_alerts, transition
)
from src.config import MODEL_PATH
from src.database import initialize, query
from src.ingestion import ingest_batch
from src.model import verified_metrics
from src.reports import audit_events, detail, trend
from src.security import (
    authenticate, create_user, current_user, list_users, logout, require_role
)
from src.validation import DataValidationError
from src import agro_ui

st.set_page_config(page_title="SOMPO Agro | Centro de inteligência", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")
initialize()
st.markdown("""<style>
.block-container {padding-top: 1.4rem; max-width: 1480px;}
h1 {font-size: 2.15rem!important; letter-spacing: -.025em;}
h2 {font-size: 1.38rem!important; padding-top: .6rem!important;}
[data-testid="stMetric"] {padding: .95rem 1rem; background: #f4f8f7; border: 1px solid #d8e6e1; border-radius: 12px;}
[data-testid="stMetricLabel"] {font-weight: 650;}
[data-testid="stSidebar"] {border-right: 1px solid #d9e7e1;}
small {line-height: 1.4;}
</style>""", unsafe_allow_html=True)
st.caption("SOMPO Agro Risk Intelligence | FIAP, Tecnologia em Inteligência Artificial | Pedro Gomes12, RM 571446 | MVP acadêmico")

if "user" not in st.session_state:
    st.title("Bem-vindo ao SOMPO Agro")
    st.write("Entre para explorar dados medidos, entender cada resultado, investigar padrões incomuns e consultar a origem de cada análise.")
    st.info("A base do trator é telemetria agrícola. A base hidráulica é um experimento físico em bancada. Nenhuma das duas constitui registros de sinistros ou apólices da SOMPO.")
    left, right = st.columns([1,1])
    with left:
        with st.form("login"):
            username = st.text_input("Usuário", help="Conta local criada na inicialização do projeto.")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar no painel", use_container_width=True)
            if submitted:
                u = authenticate(username, password)
                if u:
                    st.session_state.user = u
                    st.rerun()
                else:
                    st.error("Credenciais inválidas ou acesso temporariamente bloqueado.")
    with right:
        st.markdown("**O que você encontrará no painel**")
        st.write("• Origem e qualidade dos arquivos científicos.\n\n• Exploração guiada dos sinais do trator.\n\n• Resultados explicados do diagnóstico hidráulico.\n\n• Casos, responsáveis e histórico de decisões.")
        st.caption("Se a senha local foi exposta, substitua-a antes de compartilhar ou publicar a aplicação.")
    st.stop()

user = current_user(st.session_state.user["username"])
if not user:
    st.session_state.pop("user", None)
    st.warning("Conta não disponível. Faça login novamente.")
    st.stop()
st.session_state.user = user

pages = ["Comece aqui", "Fontes e qualidade", "Trator agrícola real", "Diagnóstico hidráulico real",
         "Investigações agrícolas", "Guia: o que significa?", "Visão geral (demonstração)",
         "Importar CSV (demonstração)", "Alertas (demonstração)", "Tendências (demonstração)",
         "Rastreabilidade (demonstração)", "Auditoria", "Sobre o modelo sintético", "Usuários"]
if user["role"] == "analyst":
    pages = [p for p in pages if p not in ("Importar CSV (demonstração)", "Usuários")]
elif user["role"] == "operator":
    pages = [p for p in pages if p not in ("Auditoria", "Usuários")]

with st.sidebar:
    st.markdown("## 🌱 SOMPO Agro")
    st.caption("Pedro Gomes12 | RM 571446")
    st.caption("Medir → analisar → explicar → investigar")
    st.write(f'Conta: **{user["username"]}** | perfil: `{user["role"]}`')
    page = st.radio("Selecione uma área", pages, key="main_navigation")
    st.divider()
    counts=query("SELECT (SELECT COUNT(*) FROM agro_imports) tractor_files, (SELECT COUNT(*) FROM hydraulic_cycles) hydraulic_cycles, (SELECT COUNT(*) FROM agro_investigations WHERE state='open') open_cases")[0]
    st.caption(f"Arquivos de campo: {counts['tractor_files']} | Ciclos UCI: {counts['hydraulic_cycles']}")
    st.caption(f"Investigações abertas: {counts['open_cases']}")
    if st.button("Sair da conta", use_container_width=True):
        logout(user)
        st.session_state.pop("user", None)
        st.rerun()

is_demo = page in {"Visão geral (demonstração)","Importar CSV (demonstração)",
   "Alertas (demonstração)","Tendências (demonstração)",
   "Rastreabilidade (demonstração)","Sobre o modelo sintético"}
if is_demo:
    st.warning("ÁREA DIDÁTICA SINTÉTICA. Estes registros e scores foram criados para testar o fluxo do software; NÃO são dados medidos de tratores nem sinistros da SOMPO. As páginas científicas estão separadas no menu.")

if page == "Comece aqui":
    agro_ui.home(st)

elif page == "Fontes e qualidade":
    agro_ui.overview(st)

elif page == "Trator agrícola real":
    agro_ui.tractor(st)

elif page == "Diagnóstico hidráulico real":
    agro_ui.hydraulic(st)

elif page == "Investigações agrícolas":
    agro_ui.investigations(st,user)

elif page == "Guia: o que significa?":
    agro_ui.glossary(st)

elif page == "Importar CSV (demonstração)":
    require_role(user, ("admin", "operator"))
    st.subheader("Importar dados para demonstração")
    st.caption("Esta função alimenta apenas o fluxo legado de demonstração; os dois conjuntos científicos reais já estão em módulos separados.")
    st.info("Selecione a origem verdadeira do arquivo. A opção simulada deve ser usada só no CSV de exemplo.")
    demo_ready = query("SELECT COUNT(*) AS n FROM model_registry")[0]["n"] > 0
    if not demo_ready:
        st.warning("Demonstração sintética não instalada neste banco científico. A importação "
                   "didática está desativada; os dados reais e os modelos hidráulico/agrícola "
                   "permanecem disponíveis nas páginas anteriores.")
        st.stop()
    source = st.selectbox("Origem", [
        "UNDECLARED-IMPORT", "DEMO-SIM-V1",
    ], format_func=lambda x: {"UNDECLARED-IMPORT": "Origem não verificada",
                              "DEMO-SIM-V1": "Demonstração sintética do projeto"}[x])
    f = st.file_uploader("Arquivo no esquema do dicionário de dados", type=["csv"])
    if f:
        try:
            payload = f.getvalue()
            if len(payload) > 25*1024*1024:
                raise ValueError("Arquivo excede o limite de 25 MB.")
            df = pd.read_csv(BytesIO(payload))
            if len(df) > 100000:
                raise ValueError("O CSV excede o limite de 100.000 linhas.")
            st.dataframe(df.head(10), use_container_width=True, hide_index=True)
            if st.button("Validar e processar"):
                result = ingest_batch(
                    df.to_dict(orient="records"), actor=user["username"],
                    source_code=source,
                    linkage_method="simulated" if source == "DEMO-SIM-V1" else "unknown",
                    file_name=f.name,
                    content_sha256=hashlib.sha256(payload).hexdigest())
                st.success(f"Criados: {result['created']} | Duplicados: {result['duplicate']} "
                           f"| Rejeitados: {result['rejected']}")
                st.dataframe(pd.DataFrame(result["results"]), use_container_width=True)
        except (DataValidationError, ValueError, UnicodeDecodeError,
                pd.errors.ParserError, OSError) as exc:
            st.error(f"Falha na importação: {exc}")

elif page == "Visão geral (demonstração)":
    df = detail()
    if df.empty:
        st.info("Sem dados. Execute python -m scripts.demo_pipeline ou importe um CSV.")
        st.stop()
    region = st.multiselect("Regiões", sorted(df.region.unique()),
                            default=sorted(df.region.unique()))
    operation = st.multiselect("Tipos de operação", sorted(df.operation.unique()),
                               default=sorted(df.operation.unique()))
    df = df[df.region.isin(region) & df.operation.isin(operation)]
    if df.empty:
        st.warning("Nenhum registro corresponde aos filtros.")
        st.stop()
    active = list_alerts(limit=2000)
    active_count = sum(a["status"] != "resolved" and a["region"] in region
                       and a["operation"] in operation for a in active)
    a, b, c, d = st.columns(4)
    a.metric("Equipamentos", df.equipment_id.nunique())
    b.metric("Leituras", len(df))
    c.metric("Score médio", f"{df.score.mean():.1f}/100")
    d.metric("Alertas não resolvidos", active_count)
    st.subheader("Média de score por equipamento")
    st.bar_chart(df.groupby("equipment_id").score.mean())
    st.subheader("Leituras e riscos")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Exportar CSV", df.to_csv(index=False).encode("utf-8-sig"),
                       "relatorio_sompo.csv", "text/csv")

elif page == "Alertas (demonstração)":
    st.subheader("Central de alertas demonstrativos")
    st.info("Estados e decisões aqui demonstram a lógica do software sobre dados sintéticos. Não correspondem a eventos operacionais da SOMPO.")
    st.caption("O alerta e a previsão originais são imutáveis; o andamento é registrado separadamente.")
    selected_status = st.selectbox(
        "Situação", ["Todos", "Abertos", "Em análise", "Resolvidos"])
    statuses = {"Todos": None, "Abertos": "open",
                "Em análise": "acknowledged", "Resolvidos": "resolved"}
    alerts = list_alerts(status=statuses[selected_status])
    counts = query("SELECT status,COUNT(*) quantity FROM alert_state GROUP BY status")
    count_by = {x["status"]: x["quantity"] for x in counts}
    c1, c2, c3 = st.columns(3)
    c1.metric("Abertos", count_by.get("open", 0))
    c2.metric("Em análise", count_by.get("acknowledged", 0))
    c3.metric("Resolvidos", count_by.get("resolved", 0))
    if not alerts:
        st.info("Não existem alertas para o filtro selecionado.")
    else:
        st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
        ids = {f"#{a['alert_id']} | {a['equipment_id']} | {a['level']} | "
               f"{a['status']}": a for a in alerts}
        chosen = st.selectbox("Abrir um alerta", list(ids))
        selected = ids[chosen]
        st.markdown(f"**Recomendação:** {selected['recommendation']}")
        st.caption(f"Versão de estado: {selected['version']} | "
                   f"Responsável: {selected['assignee'] or 'não atribuído'}")
        st.markdown("**Histórico imutável**")
        st.dataframe(pd.DataFrame(alert_history(selected["alert_id"])),
                     use_container_width=True, hide_index=True)
        if user["role"] in ("admin", "operator"):
            status_actions = {"open": ("acknowledge", "Reconhecer"),
                              "acknowledged": ("resolve", "Resolver"),
                              "resolved": ("reopen", "Reabrir")}
            action, caption = status_actions[selected["status"]]
            with st.form("workflow"):
                comment = st.text_area("Justificativa da decisão", max_chars=500)
                if st.form_submit_button(caption):
                    try:
                        transition(selected["alert_id"], action, user, comment,
                                   expected_version=selected["version"])
                        st.success("Decisão registrada na auditoria.")
                        st.rerun()
                    except (AlertWorkflowError, PermissionError) as exc:
                        st.error(str(exc))
            if selected["status"] != "resolved":
                people = [u["username"] for u in query(
                    "SELECT username FROM users WHERE role IN ('admin','operator') ORDER BY username")]
                options = ["(sem responsável)"] + people
                with st.form("assignment"):
                    target = st.selectbox("Atribuir responsável", options,
                        index=options.index(selected["assignee"])
                        if selected["assignee"] in options else 0)
                    reason = st.text_input("Observação da atribuição", max_chars=500)
                    if st.form_submit_button("Salvar responsável"):
                        try:
                            assign(selected["alert_id"],
                                   None if target == "(sem responsável)" else target,
                                   user, reason, expected_version=selected["version"])
                            st.success("Atribuição registrada.")
                            st.rerun()
                        except (AlertWorkflowError, PermissionError) as exc:
                            st.error(str(exc))
        else:
            st.info("Perfil analista: consulta somente leitura.")

elif page == "Tendências (demonstração)":
    st.subheader("Tendência diária do score demonstrativo")
    st.caption("Score artificial de teste do fluxo de software. Não indica risco de sinistro real nem permite comparação com índice agrícola.")
    labels = {"Equipamento": "equipment_id", "Região": "region", "Operação": "operation"}
    group = labels[st.selectbox("Agrupar por", list(labels))]
    df = trend(group)
    if df.empty:
        st.info("Sem dados ainda.")
    else:
        selected = st.multiselect("Itens", sorted(df[group].unique()),
                                  default=sorted(df[group].unique()))
        subset = df[df[group].isin(selected)]
        if not subset.empty:
            st.line_chart(subset.pivot(index="day", columns=group, values="mean_score"))
        st.dataframe(subset, use_container_width=True, hide_index=True)

elif page == "Rastreabilidade (demonstração)":
    st.subheader("Rastreabilidade do fluxo sintético")
    st.caption("O objetivo é mostrar que a leitura, o modelo e o alerta de demonstração podem ser ligados no SQLite. Para dados medidos, consulte as páginas científicas e as investigações.")
    rows = query("""SELECT p.id prediction_id,r.id reading_id,r.equipment_id,r.timestamp,
       p.score,p.level,pp.model_version,pp.pipeline_version,pp.feature_sha256,
       ds.source_code,ds.origin_class,rp.linkage_method,b.id batch_id,
       a.id alert_id,als.status alert_status
       FROM predictions p JOIN readings r ON r.id=p.reading_id
       JOIN prediction_provenance pp ON pp.prediction_id=p.id
       JOIN reading_provenance rp ON rp.reading_id=r.id
       JOIN data_sources ds ON ds.id=rp.source_id
       LEFT JOIN ingestion_batches b ON b.id=rp.batch_id
       LEFT JOIN alerts a ON a.prediction_id=p.id
       LEFT JOIN alert_state als ON als.alert_id=a.id
       ORDER BY p.id DESC LIMIT 500""")
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma previsão disponível.")

elif page == "MetroPT-3":
    st.subheader("MetroPT-3 — extensão experimental opcional")
    counts = query("""SELECT (SELECT COUNT(*) FROM metropt_measurements) measurements,
      (SELECT COUNT(*) FROM metropt_anomaly_scores) scores,
      (SELECT COUNT(*) FROM metropt_alerts) alerts""")[0]
    a,b,c = st.columns(3)
    a.metric("Medições", counts["measurements"])
    b.metric("Scores", counts["scores"])
    c.metric("Alertas", counts["alerts"])
    rows = query("SELECT * FROM v_metropt_lineage ORDER BY inference_id DESC LIMIT 200")
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.warning("Dataset oficial não incluído/importado no banco demonstrativo.")

elif page == "Scania APS":
    st.subheader("Scania APS — extensão experimental opcional")
    counts = query("""SELECT (SELECT COUNT(*) FROM scania_samples WHERE split='train') train_rows,
      (SELECT COUNT(*) FROM scania_samples WHERE split='test') test_rows,
      (SELECT COUNT(*) FROM scania_predictions) predictions""")[0]
    a,b,c = st.columns(3)
    a.metric("Treino", counts["train_rows"])
    b.metric("Teste", counts["test_rows"])
    c.metric("Predições", counts["predictions"])
    models = query(
        "SELECT version,threshold,test_metrics_json,created_at FROM scania_models ORDER BY created_at DESC")
    if models:
        st.dataframe(pd.DataFrame(models), use_container_width=True, hide_index=True)
    else:
        st.warning("Dados oficiais ainda não importados nem avaliados nesta demonstração.")

elif page == "Auditoria":
    require_role(user, ("admin", "analyst"))
    st.subheader("Auditoria do uso do sistema")
    st.caption("Histórico de ações registradas pelos usuários. O conteúdo é operacional; credenciais e senhas não são exibidas.")
    st.dataframe(audit_events(limit=500), use_container_width=True, hide_index=True)

elif page == "Usuários":
    require_role(user, ("admin",))
    st.subheader("Gestão de contas locais")
    st.caption("Administrador cria contas e define acesso: operador pode registrar investigações; analista consulta; administrador gerencia contas.")
    st.dataframe(pd.DataFrame(list_users(user)), use_container_width=True, hide_index=True)
    with st.form("new_user"):
        new_name = st.text_input("Nome do novo usuário")
        new_role = st.selectbox("Perfil", ["operator", "analyst", "admin"])
        new_password = st.text_input("Senha (mín. 12 caracteres)", type="password")
        if st.form_submit_button("Criar usuário"):
            try:
                create_user(new_name, new_password, new_role, user)
                st.success("Usuário criado e ação registrada.")
                st.rerun()
            except (ValueError, PermissionError, __import__("sqlite3").IntegrityError) as exc:
                st.error(str(exc))

elif page == "Sobre o modelo sintético":
    st.subheader("Modelo preditivo experimental")
    try:
        st.json(verified_metrics())
        st.caption(f"Artefato: {MODEL_PATH.name}; métricas ligadas ao mesmo SHA-256.")
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        st.error(f"Modelo/métricas indisponíveis ou inconsistentes: {exc}")
    st.warning("Métricas de dados sintéticos não demonstram predição de sinistros reais.")
