# ================= IMPORTAÇÕES =================
import streamlit as st
import re
import random
import requests
import json
import copy

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ================= FUNÇÕES SUPABASE =================
def salvar_ficha(nome):
    for p in PERICIAS:
        if f"a_{p}" in st.session_state:
            st.session_state.pericias[p] = {
                "atributo": st.session_state[f"a_{p}"],
                "treino": st.session_state[f"t_{p}"],
                "outros": st.session_state[f"o_{p}"]
            }

    dados = {
        "hp": st.session_state.hp,
        "pe": st.session_state.pe,
        "fadiga": st.session_state.fadiga,
        "atributos": st.session_state.atributos,
        "inventario": st.session_state.inventario,
        "manobras": st.session_state.manobras,
        "armas": st.session_state.armas,
        "nivel": st.session_state.nivel,
        "K": st.session_state.K,
        "conhecimento": st.session_state.conhecimento
    }

    payload = {"nome": nome, "dados": dados, "pericias": st.session_state.pericias}

    headers = HEADERS.copy()
    headers["Prefer"] = "resolution=merge-duplicates"

    requests.post(f"{SUPABASE_URL}/rest/v1/fichas?on_conflict=nome",
                  headers=headers, data=json.dumps(payload))


def carregar_ficha(nome):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fichas?nome=eq.{nome}", headers=HEADERS)
    if r.status_code == 200 and r.json():
        linha = r.json()[0]

        for k, v in linha["dados"].items():
            st.session_state[k] = v

        if "pericias" in linha and linha["pericias"]:
            st.session_state.pericias = linha["pericias"]

            # 🔥 injeta valores nos widgets
            for p, dados in linha["pericias"].items():
                st.session_state[f"a_{p}"] = dados["atributo"]
                st.session_state[f"t_{p}"] = dados["treino"]
                st.session_state[f"o_{p}"] = dados["outros"]


# ================= CONFIG =================
st.set_page_config(page_title="Ficha Digital RPG", layout="wide")

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

def atualizar_pericia(p):
    st.session_state.pericias[p] = {
        "atributo": st.session_state[f"a_{p}"],
        "treino": st.session_state[f"t_{p}"],
        "outros": st.session_state[f"o_{p}"]
    }

# ================= ESTADOS =================
defaults = {
    "hp": 0, "pe": 0, "fadiga": 5,
    "atributos": {a: 0 for a in ATRIBUTOS},
    "inventario": [], "manobras": [], "armas": [],
    "pericias": {}, "nivel": 1, "K": 1,
    "conhecimento": CONHECIMENTOS[0]
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= FUNÇÕES =================
def calcular_status(atributos, nivel, K):
    return (10 * atributos["VIT"] + (atributos["VIT"] + nivel) * K,
            5 * atributos["INT"] + (atributos["INT"] + nivel) * K)

def alterar(valor, chave, maximo=None):
    st.session_state[chave] += valor
    if maximo is not None:
        st.session_state[chave] = max(0, min(maximo, st.session_state[chave]))

# ================= ABAS =================
aba_status, aba_ficha, aba_inventario, aba_manobras, aba_combate = st.tabs(
    ["Status", "Perícias", "Inventário", "Manobras", "Combate"]
)

# ================= STATUS =================
with aba_status:
    c1, c2 = st.columns(2)

    with c1:
        nome = st.text_input("Nome")
        if nome and st.session_state.get("ultimo_nome") != nome:
            carregar_ficha(nome)
            st.session_state.ultimo_nome = nome

        st.session_state.nivel = st.number_input("Nível", 1, value=st.session_state.nivel)
        st.session_state.K = st.number_input("K", 1, value=st.session_state.K)

    with c2:
        st.session_state.conhecimento = st.selectbox(
            "Conhecimento", CONHECIMENTOS,
            index=CONHECIMENTOS.index(st.session_state.conhecimento)
        )

    cols = st.columns(len(ATRIBUTOS))
    for i, a in enumerate(ATRIBUTOS):
        st.session_state.atributos[a] = cols[i].number_input(a, 0, value=st.session_state.atributos[a])

    hp_max, pe_max = calcular_status(st.session_state.atributos, st.session_state.nivel, st.session_state.K)

    st.subheader("Vida")
    a,b,c = st.columns([1,3,1])
    a.button("➖", key="hp_menos", on_click=alterar, args=(-1,"hp",hp_max))
    b.progress(min(st.session_state.hp/hp_max if hp_max else 0,1.0), text=f"HP {st.session_state.hp}/{hp_max}")
    c.button("➕", key="hp_mais", on_click=alterar, args=(1,"hp",hp_max))

    st.subheader("Energia")
    a,b,c = st.columns([1,3,1])
    a.button("➖", key="pe_menos", on_click=alterar, args=(-1,"pe",pe_max))
    b.progress(min(st.session_state.pe/pe_max if pe_max else 0,1.0), text=f"PE {st.session_state.pe}/{pe_max}")
    c.button("➕", key="pe_mais", on_click=alterar, args=(1,"pe",pe_max))

    st.subheader("Fadiga")
    a,b,c = st.columns([1,3,1])
    a.button("➖", key="fadiga_menos", on_click=alterar, args=(-1,"fadiga",5))
    b.progress(st.session_state.fadiga/5, text=f"Fadiga {st.session_state.fadiga}/5")
    c.button("➕", key="fadiga_mais", on_click=alterar, args=(1,"fadiga",5))

# ================= PERÍCIAS =================
with aba_ficha:
    st.subheader("Perícias")

    for p in PERICIAS:
        if p not in st.session_state.pericias:
            st.session_state.pericias[p] = {
                "atributo": extrair_atributo(p),
                "treino": 0,
                "outros": 0
            }

        d = st.session_state.pericias[p]

        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        c1.write(p.split("[")[0])

        c2.selectbox("A", ATRIBUTOS, key=f"a_{p}", on_change=atualizar_pericia, args=(p,), label_visibility="collapsed")
        c3.selectbox("T", [0,3,5], key=f"t_{p}", on_change=atualizar_pericia, args=(p,), label_visibility="collapsed")
        c4.selectbox("O", list(range(11)), key=f"o_{p}", on_change=atualizar_pericia, args=(p,), label_visibility="collapsed")

        bonus = st.session_state.atributos[st.session_state[f"a_{p}"]] + st.session_state[f"t_{p}"] + st.session_state[f"o_{p}"]
        c5.selectbox("B", [bonus], key=f"b_{p}", disabled=True, label_visibility="collapsed")

# ================= AUTO SAVE =================
if nome:
    estado_dict = {
        "hp": st.session_state.hp,
        "pe": st.session_state.pe,
        "fadiga": st.session_state.fadiga,
        "atributos": copy.deepcopy(st.session_state.atributos),
        "inventario": copy.deepcopy(st.session_state.inventario),
        "manobras": copy.deepcopy(st.session_state.manobras),
        "armas": copy.deepcopy(st.session_state.armas),
        "pericias": copy.deepcopy(st.session_state.pericias),
        "nivel": st.session_state.nivel,
        "K": st.session_state.K,
        "conhecimento": st.session_state.conhecimento
    }

    estado = json.dumps(estado_dict, sort_keys=True)

    if st.session_state.get("ultimo_estado_salvo") != estado:
        salvar_ficha(nome)
        st.session_state.ultimo_estado_salvo = estado

# ================= INVENTÁRIO =================
with aba_inventario:
    st.subheader("🎒 Inventário")
    with st.form("item"):
        n = st.text_input("Nome")
        q = st.number_input("Qtd",1,99,1)
        d = st.text_area("Desc")
        if st.form_submit_button("Adicionar"):
            st.session_state.inventario.append({"nome":n,"qtd":q,"desc":d})
            st.rerun()
    for i,item in enumerate(st.session_state.inventario):
        st.write(f"**{item['nome']}** x{item['qtd']} — {item['desc']}")
        if st.button("Remover", key=f"ri{i}"):
            st.session_state.inventario.pop(i)
            st.rerun()

# ================= MANOBRAS =================
with aba_manobras:
    st.subheader("⚔️ Manobras")
    with st.form("manobra"):
        n = st.text_input("Nome")
        c = st.number_input("Custo",0,100,0)
        d = st.text_area("Desc")
        if st.form_submit_button("Criar"):
            st.session_state.manobras.append({"nome":n,"custo":c,"desc":d})
            st.rerun()
    for i,m in enumerate(st.session_state.manobras):
        st.write(f"**{m['nome']}** (Custo {m['custo']})")
        if st.button("Usar", key=f"um{i}") and st.session_state.pe>=m["custo"]:
            st.session_state.pe -= m["custo"]
            st.rerun()

# ================= COMBATE =================
with aba_combate:
    st.subheader("⚔️ Combate")
    q = st.number_input("Qtd Dados",1,10,1)
    l = st.selectbox("Dado",[4,6,8,10,12,20])
    b = st.number_input("Bônus",0,50,0)
    if st.button("Rolar Dano", key="rolar_dano"):
        r = [random.randint(1,l) for _ in range(q)]
        st.success(f"Dano: {r} + {b} = {sum(r)+b}")

