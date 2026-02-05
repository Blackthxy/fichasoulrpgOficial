# ================= IMPORTAÇÕES =================
import streamlit as st
import re
import random
import requests
import json

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def salvar_ficha(nome):
    dados = {
        "hp": st.session_state.hp,
        "pe": st.session_state.pe,
        "fadiga": st.session_state.fadiga,
        "atributos": st.session_state.atributos,
        "inventario": st.session_state.inventario,
        "manobras": st.session_state.manobras,
        "armas": st.session_state.armas
    }

    payload = {"nome": nome, "dados": dados}

    requests.post(
        f"{SUPABASE_URL}/rest/v1/fichas?on_conflict=nome",
        headers=HEADERS,
        data=json.dumps(payload)
    )

def carregar_ficha(nome):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/fichas?nome=eq.{nome}",
        headers=HEADERS
    )

    if r.status_code == 200 and r.json():
        dados = r.json()[0]["dados"]
        for k, v in dados.items():
            st.session_state[k] = v


# ================= CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(page_title="Ficha Digital RPG", layout="wide")

# ================= LISTAS FIXAS DO SISTEMA =================
ATRIBUTOS = ["FOR", "AGI", "PRE", "VIT", "INT"]

PERICIAS = [
    "Acrobacia[AGI]", "Adestramento[PRE]", "Artes[PRE]", "Atletismo[FOR]", "Ciências[INT]", "Crime[AGI]",
    "Diplomacia[PRE]", "Enganação[PRE]", "Espiritismo[PRE]", "Fortitude[VIT]", "Furtividade[AGI]",
    "Iniciativa[AGI]", "Intimidação[PRE]", "Intuição[PRE]", "Investigação[INT]", "Luta[FOR]",
    "Medicina[INT]", "Percepção[PRE]", "Pilotagem[AGI]", "Pontaria[INT]", "Reflexos[AGI]",
    "Religião[PRE]", "Sobrevivência[INT]", "Tática[INT]", "Tecnologia[INT]", "Vontade[VIT]"
]

CONHECIMENTOS = [
    "Artes Marciais", "Armas de Fogo", "Mecânica", "Investigação", "Psicologia", "Pilotagem",
    "Armas Brancas", "Diplomacia", "Ciências", "Furtividade", "Segurança Pessoal",
    "Criminologia", "História"
]

def extrair_atributo(nome_pericia):
    match = re.search(r"\[(.*?)\]", nome_pericia)
    return match.group(1) if match else None

# ================= ESTADOS =================
defaults = {
    "hp": 0,
    "pe": 0,
    "fadiga": 5,
    "atributos": {a: 0 for a in ATRIBUTOS},
    "inventario": [],
    "manobras": [],
    "armas": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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

    resultados, detalhes = [], []
    for _ in range(vezes):
        rolagens = [random.randint(1, lados) for _ in range(qtd)]
        total = sum(rolagens) + bonus_extra + bonus
        resultados.append(total)
        detalhes.append(f"{rolagens}+{bonus_extra}+{bonus}")
    return resultados, detalhes

# ================= ABAS =================
aba_status, aba_ficha, aba_inventario, aba_manobras, aba_combate = st.tabs(
    ["Status", "Perícias", "Inventário", "Manobras", "Combate"]
)

# ================= ABA STATUS =================
with aba_status:
    col1, col2 = st.columns(2)

    with col1:
        nome = st.text_input("Nome", "Personagem")

        if "ficha_carregada" not in st.session_state or st.session_state.get("ultimo_nome") != nome:
            carregar_ficha(nome)
            st.session_state.ficha_carregada = True
            st.session_state.ultimo_nome = nome

        nivel = st.number_input("Nível", min_value=1, value=1)
        K = st.number_input("K", min_value=1, value=1)

    with col2:
        conhecimento = st.selectbox("Conhecimento", CONHECIMENTOS)

    st.divider()

    cols = st.columns(len(ATRIBUTOS))
    for i, a in enumerate(ATRIBUTOS):
        st.session_state.atributos[a] = cols[i].number_input(a, min_value=0, value=st.session_state.atributos[a], key=f"atr_{a}")

    atributos = st.session_state.atributos
    hp_max, pe_max = calcular_status(atributos, nivel, K)

    # 🔒 Garante que valores não ultrapassem o máximo
    st.session_state.hp = min(st.session_state.hp, hp_max)
    st.session_state.pe = min(st.session_state.pe, pe_max)
    st.session_state.fadiga = min(st.session_state.fadiga, 5)

    st.subheader("Vida")
    c1, c2, c3 = st.columns([1,3,1])
    c1.button("➖", key="hp_menos_btn", on_click=alterar, args=(-1,"hp",hp_max))
    hp_ratio = min(st.session_state.hp / hp_max, 1.0) if hp_max else 0
    c2.progress(hp_ratio, text=f"HP {st.session_state.hp}/{hp_max}")
    c3.button("➕", key="hp_mais_btn", on_click=alterar, args=(1,"hp",hp_max))

    st.subheader("Energia")
    c1, c2, c3 = st.columns([1,3,1])
    c1.button("➖", key="pe_menos_btn", on_click=alterar, args=(-1,"pe",pe_max))
    pe_ratio = min(st.session_state.pe / pe_max, 1.0) if pe_max else 0
    c2.progress(pe_ratio, text=f"PE {st.session_state.pe}/{pe_max}")
    c3.button("➕", key="pe_mais_btn", on_click=alterar, args=(1,"pe",pe_max))

    st.subheader("Fadiga")
    c1, c2, c3 = st.columns([1,3,1])
    c1.button("➖", key="fadiga_menos_btn", on_click=alterar, args=(-1,"fadiga",5))
    fadiga_ratio = min(st.session_state.fadiga / 5, 1.0)
    c2.progress(fadiga_ratio, text=f"Fadiga {st.session_state.fadiga}/5")
    c3.button("➕", key="fadiga_mais_btn", on_click=alterar, args=(1,"fadiga",5))

# ================= ABA PERÍCIAS =================
with aba_ficha:
    st.subheader("Perícias")
    pericias_valores = {}

    for pericia in PERICIAS:
        nome_limpo = pericia.split("[")[0]
        atributo_padrao = extrair_atributo(pericia)

        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        c1.markdown(nome_limpo)

        atributo_escolhido = c2.selectbox("Atributo", ATRIBUTOS, index=ATRIBUTOS.index(atributo_padrao), key=f"atrib_{pericia}", label_visibility="collapsed")
        treino = c3.selectbox("Treino", [0,3,5], key=f"treino_{pericia}", label_visibility="collapsed")
        outros = c4.selectbox("Outros", list(range(0,11)), key=f"outros_{pericia}", label_visibility="collapsed")

        bonus_total = atributos.get(atributo_escolhido, 0) + treino + outros
        c5.selectbox("Bônus", [bonus_total], key=f"bonus_{pericia}", label_visibility="collapsed", disabled=True)

        pericias_valores[pericia] = {"atributo": atributo_escolhido, "treino": treino, "outros": outros}

    st.divider()
    st.subheader("🎲 Rolagem de Perícia")

    col1, col2 = st.columns([2,1])
    pericia_roll = col1.selectbox("Escolha a perícia", list(pericias_valores.keys()))
    expressao = col1.text_input("Digite a rolagem (ex: 2#2d6+1)", "2d6")

    if col2.button("Rolar Agora"):
        dados_pericia = pericias_valores[pericia_roll]
        atributo_valor = atributos.get(dados_pericia["atributo"], 0)
        bonus_total = calcular_bonus_pericia(atributo_valor, dados_pericia["treino"], dados_pericia["outros"])
        resultado = rolar_expressao(expressao, bonus_total)

        if resultado:
            totais, detalhes = resultado
            for i, (t, d) in enumerate(zip(totais, detalhes), 1):
                st.success(f"Rolagem {i}: 🎲 {d} = **{t}**")
        else:
            st.error("Expressão inválida!")

# ================= ABA INVENTÁRIO =================
with aba_inventario:
    st.subheader("🎒 Inventário")

    with st.form("novo_item", clear_on_submit=True):
        nome_item = st.text_input("Nome do Item")
        qtd = st.number_input("Quantidade", 1, 99, 1)
        desc = st.text_area("Descrição")
        if st.form_submit_button("Adicionar") and nome_item:
            st.session_state.inventario.append({"nome": nome_item,"qtd": qtd,"desc": desc})
            st.rerun()

    for i, item in enumerate(st.session_state.inventario):
        st.write(f"**{item['nome']}** x{item['qtd']} — {item['desc']}")
        if st.button("Remover", key=f"rem_item_{i}"):
            st.session_state.inventario.pop(i)
            st.rerun()

# ================= ABA MANOBRAS =================
with aba_manobras:
    st.subheader("⚔️ Manobras")

    with st.form("nova_manobra", clear_on_submit=True):
        nome_m = st.text_input("Nome da Manobra")
        custo_m = st.number_input("Custo de PE", 0, 100, 0)
        desc_m = st.text_area("Descrição")
        if st.form_submit_button("Criar Manobra") and nome_m:
            st.session_state.manobras.append({"nome": nome_m,"custo": custo_m,"desc": desc_m})
            st.rerun()

    for i, m in enumerate(st.session_state.manobras):
        st.write(f"**{m['nome']}** (Custo {m['custo']} PE) — {m['desc']}")
        if st.button("Usar", key=f"usar_m_{i}") and st.session_state.pe >= m["custo"]:
            st.session_state.pe -= m["custo"]
            st.rerun()

# ================= ABA COMBATE =================
with aba_combate:
    st.subheader("⚔️ Combate")

    qtd = st.number_input("Quantidade de Dados", 1, 10, 1)
    lados = st.selectbox("Tipo de Dado", [4,6,8,10,12,20])
    bonus_dano = st.number_input("Bônus de Dano", 0, 50, 0)

    if st.button("💥 Rolar Dano"):
        rolagens = [random.randint(1,lados) for _ in range(qtd)]
        total = sum(rolagens) + bonus_dano
        st.success(f"Dano: {rolagens} + {bonus_dano} = {total}")

# ================= SALVAMENTO AUTOMÁTICO =================
if nome:
    salvar_ficha(nome)
