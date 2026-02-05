# ================= IMPORTAÇÕES =================
import streamlit as st
import json
import re
import random

# ================= CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(page_title="Ficha Digital RPG", layout="wide")

# ================= LISTAS FIXAS DO SISTEMA =================
ATRIBUTOS = ["FOR", "AGI", "PRE", "VIT", "INT"]

PERICIAS = [
    "Acrobacia[AGI]", "Adestramento[PRE]", "Artes[PRE]", "Atletismo[FOR]", "Ciências[INT]", "Crime[AGI]",
    "Diplomacia[PRE]", "Enganação[PRE]", "Espiritismo[PRE]", "Fortitude[VIT]",
    "Furtividade[AGI]", "Iniciativa[AGI]", "Intimidação[PRE]", "Intuição[PRE]",
    "Investigação[INT]", "Luta[FOR]", "Medicina[INT]", "Percepção[PRE]",
    "Pilotagem[AGI]", "Pontaria[INT]", "Reflexos[AGI]", "Religião[PRE]",
    "Sobrevivência[INT]", "Tática[INT]", "Tecnologia[INT]", "Vontade[VIT]"
]

CONHECIMENTOS = [
    "Artes Marciais", "Armas de Fogo", "Mecânica", "Investigação",
    "Psicologia", "Pilotagem", "Armas Brancas", "Diplomacia",
    "Ciências", "Furtividade", "Segurança Pessoal",
    "Criminologia", "História"
]

def extrair_atributo(nome_pericia):
    match = re.search(r"\[(.*?)\]", nome_pericia)
    return match.group(1) if match else None

# ================= ESTADOS =================
def init_state():
    defaults = {
        "hp": 0,
        "pe": 0,
        "fadiga": 5,
        "atributos": {a: 0 for a in ATRIBUTOS},
        "inventario": [],
        "manobras": [],
        "armas": [],
        "pericias_salvas": {}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ================= FUNÇÕES =================
def calcular_status(atributos, nivel, K):
    hp_max = 10 * atributos["VIT"] + (atributos["VIT"] + nivel) * K
    pe_max = 5 * atributos["INT"] + (atributos["INT"] + nivel) * K
    return hp_max, pe_max

def alterar(valor, chave, maximo=None):
    st.session_state[chave] += valor
    if maximo is not None:
        st.session_state[chave] = max(0, min(maximo, st.session_state[chave]))
    else:
        st.session_state[chave] = max(0, st.session_state[chave])

def calcular_bonus_pericia(atributo, treino, outros):
    return atributo + treino + outros

def rolar_expressao(expr, bonus=0):
    expr = expr.replace(" ", "").lower()
    vezes = 1

    if "#" in expr:
        partes = expr.split("#")
        vezes = int(partes[0])
        expr = partes[1]

    match = re.match(r"(\d+)d(\d+)([+-]\d+)?", expr)
    if not match:
        return None

    qtd = int(match.group(1))
    lados = int(match.group(2))
    bonus_extra = int(match.group(3)) if match.group(3) else 0

    resultados = []
    detalhes = []

    for _ in range(vezes):
        rolagens = [random.randint(1, lados) for _ in range(qtd)]
        total = sum(rolagens) + bonus_extra + bonus
        resultados.append(total)
        detalhes.append(f"{rolagens}+{bonus_extra}+{bonus}")

    return resultados, detalhes

def montar_dados_ficha(nome, nivel, K, conhecimento):
    return {
        "nome": nome,
        "nivel": nivel,
        "K": K,
        "atributos": st.session_state.atributos,
        "pericias": st.session_state.pericias_salvas,
        "conhecimento": conhecimento,
        "hp": st.session_state.hp,
        "pe": st.session_state.pe,
        "fadiga": st.session_state.fadiga,
        "inventario": st.session_state.inventario,
        "manobras": st.session_state.manobras,
        "armas": st.session_state.armas
    }

# ================= ABAS =================
aba_status, aba_ficha, aba_inventario, aba_manobras, aba_combate, aba_sistema = st.tabs(
    ["Status", "Perícias", "Inventário", "Manobras", "Combate", "Sistema"]
)

# ================= ABA STATUS =================
with aba_status:
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome", "Personagem")
        nivel = st.number_input("Nível", min_value=1, value=1)
        K = st.number_input("K", min_value=1, value=1)
    with col2:
        conhecimento = st.selectbox("Conhecimento", CONHECIMENTOS)

    st.divider()
    cols = st.columns(len(ATRIBUTOS))
    for i, a in enumerate(ATRIBUTOS):
        st.session_state.atributos[a] = cols[i].number_input(a, min_value=0, value=st.session_state.atributos[a])

    atributos = st.session_state.atributos
    hp_max, pe_max = calcular_status(atributos, nivel, K)
    st.session_state.hp = min(st.session_state.hp, hp_max)
    st.session_state.pe = min(st.session_state.pe, pe_max)

    st.subheader("Vida")
    c1, c2, c3 = st.columns([1,3,1])
    c1.button("➖", on_click=alterar, args=(-1,"hp",hp_max))
    c2.progress(0 if hp_max == 0 else st.session_state.hp / hp_max, text=f"HP {st.session_state.hp}/{hp_max}")
    c3.button("➕", on_click=alterar, args=(1,"hp",hp_max))

    st.subheader("Energia")
    c1, c2, c3 = st.columns([1,3,1])
    c1.button("➖", on_click=alterar, args=(-1,"pe",pe_max))
    c2.progress(0 if pe_max == 0 else st.session_state.pe / pe_max, text=f"PE {st.session_state.pe}/{pe_max}")
    c3.button("➕", on_click=alterar, args=(1,"pe",pe_max))

# ================= ABA PERÍCIAS =================
with aba_ficha:
    st.subheader("Perícias")

    for pericia in PERICIAS:
        nome_limpo = pericia.split("[")[0]
        atributo_padrao = extrair_atributo(pericia)

        c1, c2, c3, c4 = st.columns([2,1,1,1])
        c1.markdown(nome_limpo)

        atributo_escolhido = c2.selectbox("Atributo", ATRIBUTOS,
            index=ATRIBUTOS.index(atributo_padrao),
            key=f"atrib_{pericia}")

        treino = c3.selectbox("Treino", [0,3,5], key=f"treino_{pericia}")
        outros = c4.selectbox("Outros", list(range(0,11)), key=f"outros_{pericia}")

        st.session_state.pericias_salvas[pericia] = {
            "atributo": atributo_escolhido,
            "treino": treino,
            "outros": outros
        }

# ================= ABA SISTEMA =================
with aba_sistema:
    st.subheader("💾 Salvar Ficha")
    dados_ficha = montar_dados_ficha(nome, nivel, K, conhecimento)
    json_str = json.dumps(dados_ficha, indent=4, ensure_ascii=False)

    st.download_button("Baixar Ficha", data=json_str, file_name="ficha_rpg.json")

    st.divider()
    st.subheader("📂 Carregar Ficha")

    uploaded_file = st.file_uploader("Selecione a ficha", type="json")

    if uploaded_file:
        try:
            dados = json.loads(uploaded_file.read().decode("utf-8"))

            for chave in ["hp","pe","fadiga","atributos","inventario","manobras","armas","pericias"]:
                if chave in dados:
                    st.session_state[chave if chave != "pericias" else "pericias_salvas"] = dados[chave]

            st.success("Ficha carregada! Atualizando...")
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
