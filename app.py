import streamlit as st
import json
import os

JSON_FILE = "dados.json"

def carregar_dados():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if "questionarios" not in dados:
                dados["questionarios"] = []
            return dados
    return {"perguntas": [], "teses": [], "questionarios": []}

def salvar_dados(dados):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def gerar_id(dados, tipo):
    if dados[tipo]:
        return max(item["id"] for item in dados[tipo]) + 1
    return 1

def buscar_pergunta_por_id(dados, pergunta_id):
    for pergunta in dados["perguntas"]:
        if pergunta["id"] == pergunta_id:
            return pergunta
    return None

def get_texto_pergunta(dados, pergunta_id):
    pergunta = buscar_pergunta_por_id(dados, pergunta_id)
    return pergunta["pergunta"] if pergunta else "Pergunta não encontrada"

def encontrar_teses_relacionadas(dados, respostas):
    teses_encontradas = []
    for tese in dados["teses"]:
        if any(respostas.get(p_id) == "Sim" for p_id in tese["perguntas"]):
            teses_encontradas.append(tese)
    return teses_encontradas

dados = carregar_dados()

st.sidebar.title("Menu")
pagina = st.sidebar.radio("Escolha uma página", [
    "Criar Perguntas", "Criar Teses", "Responder Questionário", 
    "Listar Perguntas", "Listar Teses", "Listar Questionários"
])

if pagina == "Criar Perguntas":
    st.title("Criar Pergunta")
    pergunta = st.text_area("Digite a pergunta")
    pergunta_condicional = st.selectbox("Esta pergunta depende de outra pergunta?", ["Não", "Sim"])
    pergunta_pai = None
    if pergunta_condicional == "Sim":
        pergunta_pai = st.selectbox("Selecione a pergunta da qual depende", [p["pergunta"] for p in dados["perguntas"]])
    if st.button("Salvar Pergunta"):
        if pergunta:
            nova_pergunta = {"id": gerar_id(dados, "perguntas"), "pergunta": pergunta, "pergunta_pai": pergunta_pai}
            dados["perguntas"].append(nova_pergunta)
            salvar_dados(dados)
            st.success("Pergunta salva com sucesso!")
        else:
            st.error("A pergunta não pode estar vazia.")

elif pagina == "Criar Teses":
    st.title("Criar Teses")
    tese = st.text_area("Digite a tese")
    perguntas_disponiveis = {p["pergunta"]: p["id"] for p in dados["perguntas"]}
    perguntas_selecionadas = st.multiselect("Selecione perguntas relacionadas", list(perguntas_disponiveis.keys()))
    
    if st.button("Salvar Tese"):
        if tese and perguntas_selecionadas:
            perguntas_ids = [perguntas_disponiveis[p] for p in perguntas_selecionadas]
            nova_tese = {"id": gerar_id(dados, "teses"), "tese": tese, "perguntas": perguntas_ids}
            dados["teses"].append(nova_tese)
            salvar_dados(dados)
            st.success("Tese salva com sucesso!")

elif pagina == "Responder Questionário":
    st.title("Responder Questionário")
    
    nome_empresa = st.text_input("Nome da Empresa")
    
    respostas = {}
    perguntas_respondidas = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Criar dicionário de perguntas pai
        perguntas_pai = {p["pergunta_pai"]: [] for p in dados["perguntas"] if p.get("pergunta_pai")}
        for pergunta in dados["perguntas"]:
            if pergunta.get("pergunta_pai"):
                perguntas_pai[pergunta["pergunta_pai"]].append(pergunta)
        
        # Mostrar perguntas
        for pergunta in dados["perguntas"]:
            if not pergunta.get("pergunta_pai"):  # Perguntas principais
                resposta = st.radio(
                    pergunta["pergunta"],
                    ["Não", "Não sei", "Sim"],
                    key=f"p_{pergunta['id']}"
                )
                respostas[pergunta["id"]] = resposta
                perguntas_respondidas.append({
                    "pergunta_id": pergunta["id"],
                    "resposta": resposta
                })
                
                # Se respondeu Sim, mostrar perguntas dependentes
                if resposta == "Sim" or resposta == "Não sei":
                    for perg_dependente in dados["perguntas"]:
                        if perg_dependente.get("pergunta_pai") == pergunta["pergunta"]:
                            resp_dep = st.radio(
                                "↳ " + perg_dependente["pergunta"],
                                ["Não", "Não sei", "Sim"],
                                key=f"p_{perg_dependente['id']}"
                            )
                            respostas[perg_dependente["id"]] = resp_dep
                            perguntas_respondidas.append({
                                "pergunta_id": perg_dependente["id"],
                                "resposta": resp_dep
                            })
    
    with col2:
        st.markdown("### Teses Relacionadas")
        teses_relacionadas = encontrar_teses_relacionadas(dados, respostas)
        if teses_relacionadas:
            for tese in teses_relacionadas:
                st.info(f"📌 {tese['tese']}")
        else:
            st.write("Nenhuma tese relacionada encontrada.")

    if st.button("Finalizar") and nome_empresa:
        novo_questionario = {
            "id": gerar_id(dados, "questionarios"),
            "empresa": nome_empresa,
            "respostas": perguntas_respondidas,
            "teses_relacionadas": [t["id"] for t in teses_relacionadas]
        }
        
        dados["questionarios"].append(novo_questionario)
        salvar_dados(dados)
        st.success("Questionário salvo com sucesso!")

elif pagina == "Listar Perguntas":
    st.title("Listar Perguntas")
    for pergunta in dados["perguntas"]:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**Pergunta {pergunta['id']}:** {pergunta['pergunta']}")
            if pergunta.get("pergunta_pai"):
                st.write(f"*Depende da pergunta:* {pergunta['pergunta_pai']}")
        
        with col2:
            if st.button(f"Editar", key=f"edit_{pergunta['id']}"):
                st.session_state.editing = pergunta['id']
        
        with col3:
            if st.button(f"Excluir", key=f"delete_{pergunta['id']}"):
                dados["perguntas"].remove(pergunta)
                salvar_dados(dados)
                st.success("Pergunta excluída com sucesso!")
                st.rerun()
        
        if st.session_state.get('editing') == pergunta['id']:
            with st.form(key=f"edit_form_{pergunta['id']}"):
                nova_pergunta = st.text_area("Edite a pergunta", value=pergunta["pergunta"])
                pergunta_condicional = st.selectbox(
                    "Esta pergunta depende de outra pergunta?",
                    ["Não", "Sim"],
                    index=0 if not pergunta.get("pergunta_pai") else 1
                )
                pergunta_pai = None
                if pergunta_condicional == "Sim":
                    pergunta_pai = st.selectbox(
                        "Selecione a pergunta da qual depende",
                        [p["pergunta"] for p in dados["perguntas"] if p["id"] != pergunta["id"]]
                    )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.form_submit_button("Salvar"):
                        pergunta["pergunta"] = nova_pergunta
                        pergunta["pergunta_pai"] = pergunta_pai if pergunta_condicional == "Sim" else None
                        salvar_dados(dados)
                        st.session_state.editing = None
                        st.success("Pergunta atualizada com sucesso!")
                        st.rerun()
                
                with col2:
                    if st.form_submit_button("Cancelar"):
                        st.session_state.editing = None
                        st.rerun()

elif pagina == "Listar Teses":
    st.title("Listar Teses")
    for tese in dados["teses"]:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**Tese {tese['id']}:** {tese['tese']}")
            st.write("**Perguntas relacionadas:**")
            for pergunta_id in tese["perguntas"]:
                texto_pergunta = get_texto_pergunta(dados, pergunta_id)
                st.write(f"- {texto_pergunta}")
        
        with col2:
            if st.button(f"Editar", key=f"edit_tese_{tese['id']}"):
                st.session_state.editing_tese = tese['id']
        
        with col3:
            if st.button(f"Excluir", key=f"delete_tese_{tese['id']}"):
                dados["teses"].remove(tese)
                salvar_dados(dados)
                st.success("Tese excluída com sucesso!")
                st.rerun()

        if st.session_state.get('editing_tese') == tese['id']:
            with st.form(key=f"edit_form_tese_{tese['id']}"):
                nova_tese = st.text_area("Edite a tese", value=tese["tese"])
                perguntas_disponiveis = {p["pergunta"]: p["id"] for p in dados["perguntas"]}
                perguntas_atuais = [get_texto_pergunta(dados, pid) for pid in tese["perguntas"]]
                perguntas_selecionadas = st.multiselect(
                    "Selecione perguntas relacionadas",
                    list(perguntas_disponiveis.keys()),
                    default=perguntas_atuais
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.form_submit_button("Salvar"):
                        tese["tese"] = nova_tese
                        tese["perguntas"] = [perguntas_disponiveis[p] for p in perguntas_selecionadas]
                        salvar_dados(dados)
                        st.session_state.editing_tese = None
                        st.success("Tese atualizada com sucesso!")
                        st.rerun()
                
                with col2:
                    if st.form_submit_button("Cancelar"):
                        st.session_state.editing_tese = None
                        st.rerun()
        st.write("---")

elif pagina == "Listar Questionários":
    st.title("Questionários Respondidos")
    
    for questionario in dados["questionarios"]:
        st.write("---")
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.subheader(f"Empresa: {questionario['empresa']}")
        
        with col2:
            if st.button(f"Excluir", key=f"delete_questionario_{questionario['id']}"):
                dados["questionarios"].remove(questionario)
                salvar_dados(dados)
                st.success("Questionário excluído com sucesso!")
                st.rerun()
        
        with st.expander("Ver respostas"):
            st.write("**Respostas:**")
            for resposta in questionario["respostas"]:
                pergunta = buscar_pergunta_por_id(dados, resposta["pergunta_id"])
                if pergunta:
                    st.write(f"- {pergunta['pergunta']}: {resposta['resposta']}")
            
            st.write("\n**Teses relacionadas:**")
            for tese_id in questionario["teses_relacionadas"]:
                for tese in dados["teses"]:
                    if tese["id"] == tese_id:
                        st.write(f"- {tese['tese']}")