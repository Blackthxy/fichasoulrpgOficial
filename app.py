# ================= IMPORTAÇÕES =================
import streamlit as st
import json
import math
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
if "hp" not in st.session_state: st.session_state.hp = 0
if "pe" not in st.session_state: st.session_state.pe = 0
if "fadiga" not in st.session_state: st.session_state.fadiga = 5
if "atributos" not in st.session_state:
    st.session_state.atributos = {a: 0 for a in ATRIBUTOS}
if "inventario" not in st.session_state: st.session_state.inventario = []
if "manobras" not in st.session_state: st.session_state.manobras = []
if "armas" not in st.session_state: st.session_state.armas = []

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

def montar_dados_ficha(nome, nivel, K, conhecimento, pericias_valores):
    return {
        "nome": nome,
        "nivel": nivel,
        "K": K,
        "atributos": st.session_state.atributos,
        "pericias": pericias_valores,
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
        st.session_state.atributos[a] = cols[i].number_input(a, min_value=0, value=st.session_state.atributos[a], key=f"atr_{a}")

    atributos = st.session_state.atributos
    hp_max, pe_max = calcular_status(atributos, nivel, K)

    st.session_state.hp = min(st.session_state.hp, hp_max)
    st.session_state.pe = min(st.session_state.pe, pe_max)

    st.subheader("Vida")
    c1, c2, c3 = st.columns([1,3,1])
    c1.button("➖", key="hp_menos", on_click=alterar, args=(-1,"hp",hp_max))
    c2.progress(0 if hp_max == 0 else st.session_state.hp / hp_max, text=f"HP {st.session_state.hp}/{hp_max}")
    c3.button("➕", key="hp_mais", on_click=alterar, args=(1,"hp",hp_max))

    st.subheader("Energia")
    c1, c2, c3 = st.columns([1,3,1])
    c1.button("➖", key="pe_menos", on_click=alterar, args=(-1,"pe",pe_max))
    c2.progress(0 if pe_max == 0 else st.session_state.pe / pe_max, text=f"PE {st.session_state.pe}/{pe_max}")
    c3.button("➕", key="pe_mais", on_click=alterar, args=(1,"pe",pe_max))

    st.subheader("Fadiga")
    c1, c2, c3 = st.columns([1,3,1])
    c1.button("➖", key="fadiga_menos", on_click=alterar, args=(-1,"fadiga",5))
    c2.progress(st.session_state.fadiga / 5, text=f"Fadiga {st.session_state.fadiga}/5")
    c3.button("➕", key="fadiga_mais", on_click=alterar, args=(1,"fadiga",5))

# ================= ABA PERÍCIAS =================
with aba_ficha:
    st.subheader("Perícias")
    pericias_valores = {}

    h1, h2, h3, h4, h5 = st.columns([2,1,1,1,1])
    h1.markdown("**PERÍCIA**")
    h2.markdown("**ATRIB**")
    h3.markdown("**TREINO**")
    h4.markdown("**OUTROS**")
    h5.markdown("**BÔNUS**")
    st.divider()

    for pericia in PERICIAS:
        nome_limpo = pericia.split("[")[0]
        atributo_padrao = extrair_atributo(pericia)

        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        c1.markdown(nome_limpo)

        atributo_escolhido = c2.selectbox("Atributo", ATRIBUTOS, index=ATRIBUTOS.index(atributo_padrao), key=f"atrib_{pericia}", label_visibility="collapsed")
        treino = c3.selectbox("Treino", [0,3,5], key=f"treino_{pericia}", label_visibility="collapsed")
        outros = c4.selectbox("Outros", list(range(0,11)), key=f"outros_{pericia}", label_visibility="collapsed")

        bonus_total = atributos.get(atributo_escolhido, 0) + treino + outros

        # Bônus final em caixa estilo dropdown (travada)
        c5.selectbox(
            "Bônus",
            [bonus_total],
            key=f"bonus_{pericia}",
            label_visibility="collapsed",
            disabled=True
        )

        pericias_valores[pericia] = {
            "atributo": atributo_escolhido,
            "treino": treino,
            "outros": outros
        }

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
            st.error("Expressão inválida! Use formato tipo 2#2d6+3")

# ================= ABA INVENTÁRIO =================

with aba_inventario:
    st.subheader("🎒 Inventário")

    with st.expander("➕ Adicionar Item"):
        with st.form("novo_item", clear_on_submit=True):
            nome_item = st.text_input("Nome do Item")
            qtd = st.number_input("Quantidade", 1, 99, 1)
            desc = st.text_area("Descrição / efeito")
            if st.form_submit_button("Adicionar") and nome_item:
                st.session_state.inventario.append({"nome": nome_item,"qtd": qtd,"desc": desc})
                st.success("Item adicionado!")

    for i, item in enumerate(st.session_state.inventario):
        with st.expander(f"{item['nome']} (x{item['qtd']})"):
            st.write(item["desc"])
            if st.button("Remover", key=f"rem_item_{i}"):
                st.session_state.inventario.pop(i)
                st.rerun()

    st.divider()
    st.subheader("🗡️ Armas")

    with st.expander("➕ Adicionar Arma"):
        with st.form("nova_arma", clear_on_submit=True):
            nome_arma = st.text_input("Nome da Arma")
            desc = st.text_area("Descrição")
            if st.form_submit_button("Adicionar Arma") and nome_arma:
                st.session_state.armas.append({"nome": nome_arma, "desc": desc})
                st.success("Arma adicionada!")

    for i, arma in enumerate(st.session_state.armas):
        col1, col2 = st.columns([4,1])
        col1.write(f"🗡️ {arma['nome']}")
        if col2.button("Remover", key=f"rem_arma_{i}"):
            st.session_state.armas.pop(i)
            st.rerun()

# ================= ABA MANOBRAS =================
with aba_manobras:
    st.subheader("⚔️ Manobras")

    with st.expander("➕ Nova Manobra"):
        with st.form("nova_manobra", clear_on_submit=True):
            nome_m = st.text_input("Nome da Manobra")
            custo_m = st.number_input("Custo de PE", 0, 100, 0)
            desc_m = st.text_area("Descrição / efeito")
            if st.form_submit_button("Criar Manobra") and nome_m:
                st.session_state.manobras.append({"nome": nome_m,"custo": custo_m,"desc": desc_m})
                st.success("Manobra criada!")

    for i, m in enumerate(st.session_state.manobras):
        with st.expander(f"{m['nome']} (Custo {m['custo']} PE)"):
            st.write(m["desc"])
            col1, col2 = st.columns(2)

            if col1.button("Usar", key=f"usar_m_{i}"):
                if st.session_state.pe >= m["custo"]:
                    st.session_state.pe -= m["custo"]
                    st.success(f"{m['nome']} usada!")
                else:
                    st.error("PE insuficiente!")

            if col2.button("Remover", key=f"del_m_{i}"):
                st.session_state.manobras.pop(i)
                st.rerun()

# ================= ABA COMBATE =================
with aba_combate:
    st.subheader("⚔️ Combate")

    qtd = st.number_input("Quantidade de Dados", 1, 10, 1)
    lados = st.selectbox("Tipo de Dado", [4,6,8,10,12,20])
    bonus_dano = st.number_input("Bônus de Dano", 0, 50, 0)

    if st.button("💥 Rolar Dano", key="roll_dano"):
        rolagens = [random.randint(1,lados) for _ in range(qtd)]
        total = sum(rolagens) + bonus_dano
        st.success(f"Dano: {rolagens} + {bonus_dano} = {total}")

# ================= ABA SISTEMA =================
with aba_sistema:
    st.subheader("💾 Salvar Ficha")

    dados_ficha = montar_dados_ficha(nome, nivel, K, conhecimento, pericias_valores)

    json_str = json.dumps(dados_ficha, indent=4, ensure_ascii=False)

st.download_button(
    "💾 Baixar Ficha",
    data=json_str.encode("utf-8"),   # força virar bytes fixos
    file_name="ficha_rpg.json",
    mime="application/json"
)


st.divider()
    
st.subheader("📂 Carregar Ficha")

arquivo = st.file_uploader("Envie sua ficha salva", type="json", key="upload_ficha")

if arquivo is not None and "ficha_carregada" not in st.session_state:
    try:
        dados = json.loads(arquivo.getvalue().decode("utf-8"))

        st.session_state.hp = dados.get("hp", 0)
        st.session_state.pe = dados.get("pe", 0)
        st.session_state.fadiga = dados.get("fadiga", 5)
        st.session_state.atributos = dados.get("atributos", st.session_state.atributos)
        st.session_state.inventario = dados.get("inventario", [])
        st.session_state.manobras = dados.get("manobras", [])

        st.session_state.ficha_carregada = True  # trava para não reler o arquivo
        st.success("Ficha carregada com sucesso!")

    except Exception as e:
        st.error(f"Erro ao carregar ficha: {e}")

# Botão para permitir carregar outra depois
if "ficha_carregada" in st.session_state:
    if st.button("🔄 Carregar outra ficha"):
        del st.session_state.ficha_carregada
        st.rerun()

