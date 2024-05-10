
import session_info
import streamlit as st
import psycopg2
import time
import uuid
from datetime import datetime
import matplotlib.pyplot as plt
import locale

# Conectar ao banco de dados PostgreSQL
conn = psycopg2.connect(
    host="192.168.100.7",
    database="seulixo",
    user="postgres",
    password="postgres"
)

def create_user_table():
    try:
        with conn:
            with conn.cursor() as cur:
                # Criar a tabela de usuários dentro do esquema "public"
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        função VARCHAR(20) NOT NULL,
                        empresa VARCHAR(100) DEFAULT NULL,
                        acesso BOOLEAN DEFAULT FALSE
                    );
                """)
        # Commit a transação após a criação da tabela
        conn.commit()
    except psycopg2.Error as e:
        st.error(f"Erro ao criar tabela de usuários: {e}")
    finally:
        if conn:
            conn.close()


#cria a tabela caso tenha novo cadastro e ela não exista
def create_empresa(nome_empresa):
    try:
        with conn.cursor() as cur:
            # Verificar se a tabela da empresa já existe
            cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (nome_empresa,))
            exists = cur.fetchone()[0]
            if not exists:
                # Criar a tabela da empresa
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS "Dados de coleta".{nome_empresa} (
                        id SERIAL PRIMARY KEY,
                        data DATE NOT NULL,
                        mes INTEGER NOT NULL,
                        ano INTEGER NOT NULL,
                        volume DECIMAL(10, 2) NOT NULL,
                        nome_coletor VARCHAR(100) NOT NULL
                    );
                """)
                conn.commit()
            else:
                st.warning(f"A tabela para a empresa '{nome_empresa}' já existe.")
    except psycopg2.Error as e:
        st.error(f"Não foi possível criar a tabela para a empresa '{nome_empresa}': {e}")

#adiciona novo usuário na tabela users, podendo sem empresa ou coletor
def add_user(username, email, password, função, empresa=None):
    try:
        if not email:
            raise ValueError("Por favor, insira um endereço de e-mail.")
        if len(username) < 5:
            raise ValueError("O nome de usuário deve ter no mínimo 5 caracteres.")
        if len(password) < 5:
            raise ValueError("A senha deve ter no mínimo 5 caracteres.")
        if função not in ["Coletor", "Empresa", "Administrador"]:
            raise ValueError("Função inválida. Escolha entre 'Coletor', 'Empresa' ou 'Administrador'.")

        with conn.cursor() as cur:
            # Verifica se o nome de usuário ou e-mail já existem na base de dados
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s;", (username, email))
            existing_user = cur.fetchone()
            if existing_user:
                raise ValueError("Usuário ou e-mail já cadastrados. Por favor, altere ou utilize os já existentes.")
            
            # Convertendo a empresa para minúsculo se não for None
            empresa_lower = empresa.lower() if empresa else None
            
            cur.execute("INSERT INTO users (username, email, password, função, empresa) VALUES (%s, %s, %s, %s, %s);",
                        (username, email, password, função.capitalize(), empresa_lower))
            
            # Verifica se já existe uma tabela com o nome da empresa em "Dados de coleta"
            if função.lower() == "empresa":
                cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (empresa_lower,))
                table_exists = cur.fetchone()[0]
                if not table_exists:
                    # Se a tabela não existe, cria ela
                    create_empresa(empresa_lower)
        conn.commit()
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error("Erro ao cadastrar usuário. Por favor, tente novamente mais tarde.")

#para saber se o usuário ta online ou não
def on_session_state_changed():
    if st.session_state.is_session_state_changed:
        if st.session_state.is_session_state_changed:
            # Atualiza o status de login do usuário para False quando a sessão é encerrada
            update_user_login_status(st.session_state.username, False)

# Define a função on_session_state_changed como callback
st.session_state.on_session_state_changed = on_session_state_changed

# Função para atualizar o status de login do usuário
def update_user_login_status(username, is_logged_in):
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET acesso = %s WHERE username = %s;", (is_logged_in, username))
        conn.commit()
    except Exception as e:
        st.error("Erro ao atualizar o status de login do usuário.")

# Função para verificar se o usuário existe no banco de dados usando nome de usuário ou e-mail
def check_user(username_or_email, password):
    with conn.cursor() as cur:
        # Verificar se o nome de usuário ou o e-mail corresponde a um registro no banco de dados
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s;", (username_or_email, username_or_email))
        return cur.fetchone() is not None

# Adiciona o estilo CSS para a div da imagem de fundo
st.markdown(
    """
    <style>
    .container {
        text-align: center;
    }
    .background1-image1 {
        background-image: url('https://i.im.ge/2024/05/06/ZRUJ9S.WhatsApp-Image-2024-05-05-at-5-41-21-PM-Photoroom-png-Photoroom.md.png');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        height: 23vh; /* Ajustar conforme necessário */
        width: 40%; /* Ajustar conforme necessário */
        display: inline-block;
    }
    </style>
    """
    , unsafe_allow_html=True
)

# Adiciona a div da imagem de fundo dentro de um contêiner centralizado
st.markdown("<div class='container'><div class='background1-image1'></div></div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Início", "Cadastro", "Relatório de Coleta"])

def home():
    with tab1:
        st.markdown("<h1 style='color: #38b6ff;'>Quem Somos</h1>", unsafe_allow_html=True)
        # Adiciona o texto com o estilo de centralização
        st.markdown("""
        <div style='color: #000000; width: 100%;'>
        <p>Somos especialistas em gestão de resíduos e rejeitos não perigosos em condomínios residenciais, escritórios, bares, restaurantes, supermercados, escolas, universidades e eventos.</p>

        <p>Cuidamos de todo o processo, desde a educação ambiental dos usuários até a destinação adequada dos materiais, enviados para recicladores parceiros. O resultado é economia e bem estar nos espaços onde atuamos, além da possibilidade de premiação pública e/ou privada para as boas práticas adotadas por nossos clientes.</p>

        <p>O trabalho é executado por profissionais capacitados que recolhem os resíduos em veículos não poluentes ou de baixa emissão. Além da coleta seletiva, também implementamos processos para a compostagem da massa verde, resíduos orgânicos e gestão eficiente dos recursos energéticos e hídricos.</p>
        </div>
        """, unsafe_allow_html=True) 
        st.markdown("<p style='font-size:20px'><span style='color: #000000;'>Nos convide para uma visita, a </span><span style='font-weight:bold; color: #38b6ff;'>SEU </span><span style='font-weight:bold; color: #000000;'>LIXO</span><span style='color: #000000;'> vai até você.</span></p>", unsafe_allow_html=True)

      # Criando uma tabela com duas colunas e bordas invisíveis
        # Define o estilo CSS para a animação de texto
        # Define o estilo CSS para a animação de texto e o fundo roxo claro
        st.markdown("""
            <style>
                @keyframes color-change {
                    0% { color: #38b6ff; }
                    50% { color: white; }
                    100% { color: #38b6ff; }
                }

                .animated-text {
                    animation: color-change 3s infinite;
                    background-color: #96298F; /* roxo claro */
                    padding: 20px;
                    border-radius: 10px;
                }
            </style>
        """, unsafe_allow_html=True)

        # Adiciona a primeira imagem à primeira coluna e centraliza
        st.write('<table style="border: none; width: 100%;"><tr><td style="text-align: center; width: 50%;"><a href="https://im.ge/i/WhatsApp-Image-2023-02-20-at-19-54-59.ZWiFf8"><img src="https://i.im.ge/2024/05/06/ZWiFf8.WhatsApp-Image-2023-02-20-at-19-54-59.md.jpeg" alt="WhatsApp Image 2023 02 20 at 19 54 59" border="0" style="max-width: 100%; max-height: 100%;"></a></td><td style="width: 50%;"><p class="animated-text">Estamos felizes em cuidar do bem estar das pessoas.<br>Reciclar preserva o planeta.<br>Consulte-nos.</p></td></tr></table>', 
                unsafe_allow_html=True)
                # Define o estilo CSS para a animação de texto e o fundo roxo claro
        st.write(" ")
        st.write('<table style="border: none;"><tr><td><img src="https://i.im.ge/2024/05/06/ZWUtBc.WhatsApp-Image-2023-04-22-at-09-52-44.md.jpeg" alt="WhatsApp Image 2023 04 22 at 09 52 44" width="330" height="430"></td><td><img src="https://i.im.ge/2024/05/06/ZWUgXS.d8693ed2-6672-40a7-a873-42d42ed04e1f.md.jpeg" alt="d8693ed2 6672 40a7 a873 42d42ed04e1f" width="330" height="430"></td></tr></table>', 
                unsafe_allow_html=True)
        st.write(" ")
        st.write('<table style="border: none;"><tr><td><img src="https://i.im.ge/2024/05/06/ZWhZ5r.1691099049993.md.jpeg" alt="1691099049993" width="330" height="430"></td><td><img src="https://i.im.ge/2024/05/06/ZWhzEc.1689353357634.md.jpeg" alt="1689353357634" width="330" height="430"></td></tr></table>', 
                unsafe_allow_html=True)
        st.write(" ")
        st.markdown("""
            <style>
                @keyframes color-change {
                    0% { color: #38b6ff; }
                    50% { color: white; }
                    100% { color: #38b6ff; }
                }

                .animated-text {
                    animation: color-change 3s infinite;
                    background-color: #96298F; /* roxo claro */
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center; /* Centraliza o texto */
                }

                .big-text {
                    font-size: 24px; /* Tamanho maior de fonte */
                    text-transform: uppercase; /* Transforma o texto em maiúsculo */
                }
            </style>
        """, unsafe_allow_html=True)

        # Adiciona a nova imagem e a frase à tabela
        st.write('<table style="border: none; width: 100%;"><tr><td style="text-align: center; width: 50%;"><a href="https://im.ge/i/bicicletaseulixo.ZW5nfP"><img src="https://i.im.ge/2024/05/06/ZW5nfP.bicicletaseulixo.md.jpeg" alt="bicicletaseulixo" border="0" style="max-width: 100%; max-height: 100%;"></a></td><td style="width: 50%;"><div class="animated-text big-text">Veículos não poluentes</div><br><div class="animated-text">Utilizamos somente veículos não poluentes para transportar os resíduos, como os bike-triciclos de gaiola para condomínios pequenos, os Tuk Tuk elétricos para distâncias maiores e vias urbanas e o Eco-Truck elétrico com baú para coletas urbanas de maior distância.</div></td></tr></table>', 
                unsafe_allow_html=True)
        
        st.markdown("<h1 style='color: #38b6ff; text-align: center;'>Clientes SEU LIXO</h1>", unsafe_allow_html=True)
        st.write('<table style="border: none;"><tr><td><img src="https://i.im.ge/2024/05/06/ZWjLBW.DVILE.md.png" alt="DVILE" width="150" height="150"></td><td><img src="https://i.im.ge/2024/05/06/ZWj91L.NUGUER.md.jpeg" alt="NUGUER" width="150" height="150"></td><td><img src="https://i.im.ge/2024/05/06/ZWjmZx.EUDORA.jpeg" alt="EUDORA" width="150" height="150"></td><td><img src="https://i.im.ge/2024/05/06/ZWjNhJ.RECICLA-CLUB.png" alt="RECICLA CLUB" width="150" height="150"></td></tr></table>', 
         unsafe_allow_html=True)
        st.write(" ")
        st.write('<table style="border: none;"><tr><td><img src="https://i.im.ge/2024/05/06/ZWm1ey.pasta.md.jpeg" alt="pasta" width="210" height="210"></td><td><img src="https://i.im.ge/2024/05/06/ZWmSDS.divino.md.jpeg" alt="divino" width="210" height="210"></td><td><img src="https://i.im.ge/2024/05/06/ZWmqv6.terra.md.jpeg" alt="terra" width="210" height="210"></td></tr><tr><td><img src="https://i.im.ge/2024/05/06/ZWm6Nq.oli-pizza.md.jpeg" alt="oli pizza" width="210" height="210"></td><td><img src="https://i.im.ge/2024/05/06/ZWmfMJ.OLI-POp.jpeg" alt="OLI POp" width="210" height="210"></td><td><img src="https://i.im.ge/2024/05/06/ZWmkIy.banana.jpeg" alt="banana" width="210" height="210"></td></tr></table>', 
         unsafe_allow_html=True)
        st.write(" ")
        st.write('<table style="border: none; margin: auto;"><tr><td style="text-align: center;"><img src="https://i.im.ge/2024/05/06/ZWwQQh.rota.md.jpeg" alt="rota" width="400"></td></tr></table>', 
         unsafe_allow_html=True)
        st.write(" ")
        st.markdown("<h1 style='color: #38b6ff; text-align: center;'>Condomínios</h1>", unsafe_allow_html=True)
        st.write('<table style="border: none;"><tr><td><img src="https://i.im.ge/2024/05/06/ZWwxWX.jardin.md.jpeg" alt="jardin" width="325" height="325"></td><td><img src="https://i.im.ge/2024/05/06/ZWwbUh.tambore.md.jpeg" alt="tambore" width="325" height="325"></td></tr><tr><td><img src="https://i.im.ge/2024/05/06/ZWwg4Y.gavea.md.jpeg" alt="gavea" width="325" height="325"></td><td><img src="https://i.im.ge/2024/05/06/ZWwWt4.park.jpeg" alt="park" width="325" height="325"></td></tr></table>', 
                unsafe_allow_html=True)
        st.write(" ")
        st.markdown("<h1 style='color: #38b6ff; text-align: center;'>Eventos</h1>", unsafe_allow_html=True)
        st.write('<table style="border: none;"><tr><td><img src="https://i.im.ge/2024/05/06/ZW6OaS.corriga.jpeg" alt="corriga" width="325" height="325"></td><td><img src="https://i.im.ge/2024/05/06/ZW62H6.mov.md.jpeg" alt="mov" width="325" height="325"></td></tr></table>', 
         unsafe_allow_html=True)
        st.write(" ")
        st.markdown("<h1 style='color: #38b6ff; text-align: center;'>Escritório</h1>", unsafe_allow_html=True)
        st.write('<table style="border: none;"><tr><td><img src="https://i.im.ge/2024/05/06/ZW691C.EEE.md.jpeg" alt="EEE" width="325" height="325"></td><td><img src="https://i.im.ge/2024/05/06/ZW66XP.ARIEL.md.jpeg" alt="ARIEL" width="325" height="325"></td></tr></table>', 
         unsafe_allow_html=True)
        st.write(" ")
        st.markdown("<h1 style='color: #38b6ff; text-align: center;'>Produtos</h1>", unsafe_allow_html=True)
        st.write('<table style="border: none;"><tr><td><img src="https://i.im.ge/2024/05/06/ZW6tGm.caneta.md.jpeg" alt="caneta" width="325" height="325"></td><td><img src="https://i.im.ge/2024/05/06/ZW6gXG.conteiner.md.jpeg" alt="conteiner" width="325" height="325"></td></tr></table>', 
         unsafe_allow_html=True)

        


    # Página de cadastro
def register():
    with tab2:
        st.markdown("<h1 style='color: #38b6ff;'>Cadastro de Usuário</h1>", unsafe_allow_html=True)
        username = st.text_input("Nome de Usuário").lower()
        email = st.text_input("Endereço de E-mail")
        password = st.text_input("Senha", type="password")
        função = st.selectbox("Função", ["Coletor", "Empresa"])
        empresa = None
        if função == "Empresa":
            empresa = st.text_input("Nome da Empresa").lower()

        if st.button("Cadastrar"):
            add_user(username, email, password, função, empresa)
            st.success("Usuário cadastrado com sucesso!")
# Chamar a função register para exibir o formulário de cadastro na aba 2
register()

#ve se a tabela já existe e se tiver vai add os dados e se não tiver vai criar tabela com base na função create_empresa
def check_table_existence(senha_empresa, username, dia, mes, ano, volume):
    try:
        # Abrir um cursor para executar consultas SQL
        with conn.cursor() as cur:
            # Consulta SQL para verificar se a senha existe na tabela users e obter o ID e a empresa
            cur.execute("SELECT id, empresa FROM public.users WHERE password = %s;", (senha_empresa,))
            empresa_info = cur.fetchone()
            if empresa_info:
                user_id, empresa = empresa_info
                
                # Verificar a existência da tabela
                cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (empresa,))
                table_exists = cur.fetchone()[0]
                if table_exists:
                    # Insere os dados na tabela existente
                    cur.execute(f"""
                        INSERT INTO "Dados de coleta".{empresa} (data, mes, ano, volume, nome_coletor)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (f'{ano}-{mes}-{dia}', mes, ano, volume, username))
                    conn.commit()
                    return f"Dados inseridos na tabela '{empresa}'."
                else:
                    return f"A tabela '{empresa}' não existe."
            else:
                return "Senha da empresa não encontrada."
    except psycopg2.Error as e:
        return f"Erro ao conectar ao banco de dados: {e}"

# Configura o idioma para português
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Função para conectar ao banco de dados PostgreSQL, buscar os valores das colunas para uma linha específica
# e criar um gráfico de pizza com base nesses valores
def buscar_valores_e_criar_grafico(senha):
    # Criar um cursor para executar consultas
    try:
        # Conectar ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            host="192.168.100.7",
            database="seulixo",
            user="postgres",
            password="postgres"
        )

        # Criar um cursor para executar consultas
        cur = conn.cursor()
        # Consulta para obter os valores das colunas específicas da tabela "users" para a linha com a senha fornecida
        cur.execute("""
            SELECT "papel e papelão", "vidro", "plastico", "embalagem longa vida", "outros metais", "aluminio"
            FROM users
            WHERE password = %s;
        """, (senha,))

        # Obter os resultados da consulta
        valores = cur.fetchone()

        # Fechar o cursor e a conexão com o banco de dados
        cur.close()
        conn.close()

        # Filtrar colunas que têm valores diferentes de zero ou None
        valores_validos = [valor for valor in valores if valor is not None and valor != 0]


        # Criar os rótulos para as colunas correspondentes aos valores válidos
        rotulos = ["Papel e papelão", "Vidro", "Plástico", "Embalagem longa vida", "Outros metais", "Alumínio"]
        rotulos_validos = [rotulo for rotulo, valor in zip(rotulos, valores) if valor is not None and valor != 0]

        # Certificar-se de que os rótulos e os valores têm o mesmo comprimento
        valores_validos = [valor for valor in valores if valor is not None and valor != 0]

        # Atualizar os rótulos e os valores
        rotulos = rotulos_validos
        valores = valores_validos

        # Criar o gráfico de pizza
        plt.figure(figsize=(8, 8))
        plt.pie(valores_validos, labels=rotulos, autopct='%1.1f%%')
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        # Exibir o gráfico
        st.pyplot(plt)

    except psycopg2.Error as e:
        st.e
#verifica os valores das proporções do banco de dados
def buscar_valores_proporcoes(senha):
    try:
        # Conectar ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            host="192.168.100.7",
            database="seulixo",
            user="postgres",
            password="postgres"
        )

        # Criar um cursor para executar consultas
        cur = conn.cursor()
        # Consulta para obter as proporções do usuário com a senha fornecida
        cur.execute("""
            SELECT "plastico", "vidro", "papel e papelão", "embalagem longa vida", "outros metais", "aluminio"
            FROM users
            WHERE password = %s;
        """, (senha,))
        proporcoes = cur.fetchone()
        cur.close()
        conn.close()  # Fechar a conexão após a conclusão das operações no banco de dados
        return proporcoes
    except psycopg2.Error as e:
        print("Erro ao buscar proporções do usuário:", e)
        return None
#aqui já cria as variáveis 
def solicitar_proporcoes(senha_empresa):
    proporcoes = buscar_valores_proporcoes(senha_empresa)  # Não é necessário passar conn aqui
    if proporcoes:
        proporcao_plastico = proporcoes[0]
        proporcao_vidro = proporcoes[1]
        proporcao_papel_papelao = proporcoes[2]
        proporcao_embalagem_longa_vida = proporcoes[3]
        proporcao_outros_metais = proporcoes[4]
        proporcao_aluminio = proporcoes[5]
        return proporcao_plastico, proporcao_vidro, proporcao_papel_papelao, proporcao_embalagem_longa_vida, proporcao_outros_metais, proporcao_aluminio
    else:
        print("Não foi possível obter as proporções do usuário.")
        return None

def calcular_economias(porcentagem_plastico, porcentagem_vidro, porcentagem_papel_papelao, porcentagem_embalagem_longa_vida, porcentagem_outros_metais, porcentagem_aluminio, volume_destinado_corretamente):
    total_kg = float(volume_destinado_corretamente)
    
    if porcentagem_plastico is not None:
        porcentagem_plastico = float(porcentagem_plastico)
    if porcentagem_vidro is not None:
        porcentagem_vidro = float(porcentagem_vidro)
    if porcentagem_papel_papelao is not None:
        porcentagem_papel_papelao = float(porcentagem_papel_papelao)
    if porcentagem_embalagem_longa_vida is not None:
        porcentagem_embalagem_longa_vida = float(porcentagem_embalagem_longa_vida)
    if porcentagem_outros_metais is not None:
        porcentagem_outros_metais = float(porcentagem_outros_metais)
    if porcentagem_aluminio is not None:
        porcentagem_aluminio = float(porcentagem_aluminio)

    # Calcular peso de cada tipo de resíduo
    peso_plastico = total_kg * porcentagem_plastico if porcentagem_plastico is not None else 0
    peso_vidro = total_kg * porcentagem_vidro if porcentagem_vidro is not None else 0
    peso_papel_papelao = total_kg * porcentagem_papel_papelao if porcentagem_papel_papelao is not None else 0
    peso_embalagem_longa_vida = total_kg * porcentagem_embalagem_longa_vida if porcentagem_embalagem_longa_vida is not None else 0
    peso_outros_metais = total_kg * porcentagem_outros_metais if porcentagem_outros_metais is not None else 0
    peso_aluminio = total_kg * porcentagem_aluminio if porcentagem_aluminio is not None else 0

    # Proporções fornecidas pelo Cataki
    proporcoes = {
        "papel_papelao": {"energia": 2.5, "agua": 48, "co2": 3.47, "volume_aterrro": 1.74, "arvores": 0.02, "petroleo": 0.4},
        "vidro": {"energia": 0.64, "agua": 0.5, "co2": 0.28, "volume_aterrro": 1.2, "arvores": 0, "petroleo": 0},
        "plastico": {"energia": 5.3, "agua": 0.45, "co2": 1.21, "volume_aterrro": 3.14, "arvores": 0, "petroleo": 1},
        "embalagem_longa_vida": {"energia": 5.55, "agua": 34.65, "co2": 2.96, "volume_aterrro": 2.34, "arvores": 0.014, "petroleo": 0.53},
        "outros_metais": {"energia": 6.56, "agua": 5.36, "co2": 1.93, "volume_aterrro": 1.98, "arvores": 0, "petroleo": 0},
        "aluminio": {"energia": 48.46, "agua": 18.69, "co2": 4.62, "volume_aterrro": 6.74, "arvores": 0, "petroleo": 0}
    }

    # Inicializar economias como zero
    economia_energia = 0
    economia_agua = 0
    economia_co2 = 0
    economia_volume_aterrro = 0
    economia_arvores = 0
    economia_petroleo = 0

    # Calcular economias com base nas proporções
    economia_energia += peso_papel_papelao * proporcoes["papel_papelao"]["energia"]
    economia_energia += peso_vidro * proporcoes["vidro"]["energia"]
    economia_energia += peso_plastico * proporcoes["plastico"]["energia"]
    economia_energia += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["energia"]
    economia_energia += peso_outros_metais * proporcoes["outros_metais"]["energia"]
    economia_energia += peso_aluminio * proporcoes["aluminio"]["energia"]

    economia_agua += peso_papel_papelao * proporcoes["papel_papelao"]["agua"]
    economia_agua += peso_vidro * proporcoes["vidro"]["agua"]
    economia_agua += peso_plastico * proporcoes["plastico"]["agua"]
    economia_agua += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["agua"]
    economia_agua += peso_outros_metais * proporcoes["outros_metais"]["agua"]
    economia_agua += peso_aluminio * proporcoes["aluminio"]["agua"]

    economia_co2 += peso_papel_papelao * proporcoes["papel_papelao"]["co2"]
    economia_co2 += peso_vidro * proporcoes["vidro"]["co2"]
    economia_co2 += peso_plastico * proporcoes["plastico"]["co2"]
    economia_co2 += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["co2"]
    economia_co2 += peso_outros_metais * proporcoes["outros_metais"]["co2"]
    economia_co2 += peso_aluminio * proporcoes["aluminio"]["co2"]

    economia_volume_aterrro += peso_papel_papelao * proporcoes["papel_papelao"]["volume_aterrro"]
    economia_volume_aterrro += peso_vidro * proporcoes["vidro"]["volume_aterrro"]
    economia_volume_aterrro += peso_plastico * proporcoes["plastico"]["volume_aterrro"]
    economia_volume_aterrro += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["volume_aterrro"]
    economia_volume_aterrro += peso_outros_metais * proporcoes["outros_metais"]["volume_aterrro"]
    economia_volume_aterrro += peso_aluminio * proporcoes["aluminio"]["volume_aterrro"]

    economia_arvores += peso_papel_papelao * proporcoes["papel_papelao"]["arvores"]
    economia_arvores += peso_vidro * proporcoes["vidro"]["arvores"]
    economia_arvores += peso_plastico * proporcoes["plastico"]["arvores"]
    economia_arvores += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["arvores"]
    economia_arvores += peso_outros_metais * proporcoes["outros_metais"]["arvores"]
    economia_arvores += peso_aluminio * proporcoes["aluminio"]["arvores"]

    economia_petroleo += peso_papel_papelao * proporcoes["papel_papelao"]["petroleo"]
    economia_petroleo += peso_vidro * proporcoes["vidro"]["petroleo"]
    economia_petroleo += peso_plastico * proporcoes["plastico"]["petroleo"]
    economia_petroleo += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["petroleo"]
    economia_petroleo += peso_outros_metais * proporcoes["outros_metais"]["petroleo"]
    economia_petroleo += peso_aluminio * proporcoes["aluminio"]["petroleo"]

    return {
        "Economia de Energia (kWh)": format(round(economia_energia/100, 2), '.2f'),
        "Economia de Água (litros)": format(round(economia_agua/100, 2), '.2f'),
        "Redução de CO2 (kg)": format(round(economia_co2/100, 2), '.2f'),
        "Redução de Volume no Aterro (litros)": format(round(economia_volume_aterrro/100, 2), '.2f'),
        "Economia de Árvores (%)": format(round(economia_arvores/100, 2), '.2f'),
        "Economia de Petróleo (litros)": format(round(economia_petroleo/100, 2), '.2f')
    }

# Função para gerar o relatório
def generate_report(senha_empresa, data_inicio, data_fim):
    # Conectar ao banco de dados PostgreSQL
    conn = psycopg2.connect(
        host="192.168.100.7",
        database="seulixo",
        user="postgres",
        password="postgres"
    )
    
    # Abrir um cursor para executar consultas SQL
    with conn.cursor() as cur:
        # Consulta SQL para obter informações da empresa com base na senha fornecida
        cur.execute("SELECT id, empresa FROM public.users WHERE password = %s;", (senha_empresa,))
        empresa_info = cur.fetchone()
        
        if empresa_info:
            user_id, empresa = empresa_info  # Definindo a variável empresa aqui
            
            # Consulta SQL para obter a porcentagem de rejeitos com base na senha fornecida
            cur.execute("""
                SELECT porcentagem_rejeitos
                FROM users
                WHERE password = %s;
            """, (senha_empresa,))
            porcentagem_rejeitos = cur.fetchone()

            if porcentagem_rejeitos is not None:
                porcentagem_rejeitos = float(porcentagem_rejeitos[0])  # Converter para float

                # Consulta SQL para obter os dados de coleta da empresa no período especificado
                cur.execute(f"""
                    SELECT data, volume
                    FROM "Dados de coleta".{empresa}
                    WHERE data >= %s AND data <= %s;
                """, (data_inicio, data_fim))
                coleta_data = cur.fetchall()

                if coleta_data:
                    # Cálculo do total de coletas e volume coletado
                    total_coletas = len(coleta_data)
                    total_volume_coletado = sum(float(row[1]) for row in coleta_data)  # Convertendo para float
                    perda_rejeito = total_volume_coletado * (porcentagem_rejeitos / 100)
                    volume_destinado_corretamente = total_volume_coletado - perda_rejeito

                    # Formatação da data do relatório
                    data_relatorio = time.strftime("%d de %B de %Y")
                    
                    # Formatação das datas de início e fim
                    data_inicio_formatada = data_inicio.strftime("%d/%m/%Y")
                    data_fim_formatada = data_fim.strftime("%d/%m/%Y")
                    
                    # Escrita do relatório
                    st.markdown("<h1 style='color: #38b6ff;'>Relatório de Coleta</h1>", unsafe_allow_html=True)
                    st.write("Plano de Gerenciamento de Resíduos Sólidos (PGRS)")
                    st.write(f"Uberlândia, {data_relatorio}")
                    st.write(f"No período entre {data_inicio_formatada} a {data_fim_formatada} foram feitas {total_coletas} coletas, totalizando cerca de {round(total_volume_coletado, 2)} kg coletados.")
                    st.write(f"Foi considerada uma perda de {porcentagem_rejeitos}% de rejeito ou materiais não recicláveis nos recipientes de coleta.")
                    st.write(f"Ao final do período conseguimos destinar corretamente {round(volume_destinado_corretamente, 2)} kg, reinserindo-os na economia circular, através da reciclagem e da compostagem.")
                    st.markdown("<h2 style='color: #38b6ff;'>Análise Gravimétrica</h2>", unsafe_allow_html=True)
                    st.write("Porcentagem de cada tipo de material em relação ao peso total")

                    # Chamar a função para buscar os valores das colunas e criar o gráfico
                    buscar_valores_e_criar_grafico(senha_empresa)

                    # Calcular economias com base nas proporções
                    proporcoes = solicitar_proporcoes(senha_empresa)
                    if proporcoes:
                        resultado = calcular_economias(*proporcoes, volume_destinado_corretamente)

                        # Exibir resultados das economias
                        st.markdown("<h2 style='color: #38b6ff;'>Ganhos Ambientais</h2>", unsafe_allow_html=True)
                        st.write("Dados dos ganhos ambientais na preservação do meio ambiente alcançados com a destinação correta dos resíduos recicláveis e orgânicos.")

                        # Dividindo os resultados em uma matriz 3x2
                        num_rows = 3
                        num_cols = 2
                        resultados = list(resultado.items())

                        # Dicionário de emojis correspondentes aos diferentes tipos de economias
                        emojis = {
                            "Economia de Energia (kWh)": "💡",
                            "Economia de Água (litros)": "💧",
                            "Redução de CO2 (kg)": "🌍",
                            "Redução de Volume no Aterro (litros)": "♻️",
                            "Economia de Árvores (%)": "🌳",
                            "Economia de Petróleo (litros)": "⛽"
                        }

                        for i in range(num_rows):
                            for j in range(num_cols):
                                index = i * num_cols + j
                                if index < len(resultados):
                                    chave, valor = resultados[index]
                                    # Adicionar emoji correspondente à economia
                                    emoji = emojis.get(chave, "")
                                    # Criar a moldura com o emoji e o valor
                                    st.markdown(f"<div style='border: 1px solid black; padding: 20px; text-align: center; color: #38b6ff;'>{emoji} {chave}: {valor}</div>", unsafe_allow_html=True)
                                else:
                                    # Criar uma moldura vazia
                                    st.markdown("<div style='border: 1px solid black; padding: 20px;'></div>", unsafe_allow_html=True)

                        # Colorindo os títulos em azul
                        st.markdown(
                            """
                            <style>
                            .title-text {
                                color: #38b6ff;
                            }
                            </style>
                            """, 
                            unsafe_allow_html=True
                        )

                        st.write("Fonte: Cálculos desenvolvidos pelo Cataki em parceria com o Instituto GEA.")
                        st.markdown("<h2 style='color: #38b6ff;'>Gabriela Brant</h2>", unsafe_allow_html=True)
                        st.write("Responsável Técnica Seu Lixo LTDA")
                        st.markdown("<h2 style='color: #38b6ff;'>Alexandre Corrêa</h2>", unsafe_allow_html=True)
                        st.write("Diretor Seu Lixo LTDA")

                else:
                    st.error("Não há dados de coleta para o período especificado.")
        else:
            st.error("Senha da empresa não encontrada.")

# Função para exibir o formulário de coleta
def collection_form():
    with tab3:
        st.markdown("<h1 style='color: #38b6ff;'>Relatório de Coleta</h1>", unsafe_allow_html=True)
        with st.form("registro_coleta_form"):
            st.write("Plano de Gerenciamento de Resíduos Sólidos (PGRS)")
            username = st.text_input("Nome do Coletor")
            dia = st.number_input("Dia", min_value=1, max_value=31)
            mes = st.number_input("Mês", min_value=1, max_value=12)
            ano = st.number_input("Ano", min_value=2024)
            volume = st.number_input("Volume Coletado", min_value=0.01)
            senha_empresa = st.text_input("Senha da Empresa", type="password")

            submit_button_cadastro = st.form_submit_button("Registrar Coleta")
            if submit_button_cadastro:
                result_message = check_table_existence(senha_empresa, username, dia, mes, ano, volume)
                st.write(result_message)

        with st.form("gerar_relatorio_form"):
            st.markdown("<h1 style='color: #38b6ff;'>Gerar Relatório</h1>", unsafe_allow_html=True)
            data_inicio = st.date_input("Data de Início")
            data_fim = st.date_input("Data Final")
            senha_relatorio = st.text_input("Senha da Empresa para Relatório", type="password")
            submit_button_relatorio = st.form_submit_button("Gerar Relatório")
            
            if submit_button_relatorio:
                generate_report(senha_relatorio, data_inicio, data_fim)

collection_form()

# Criar a tabela de usuários se ainda não existir
create_user_table()

# Executar o site
home()

#Todas as versões do python e bibliotecas
session_info.show()

create_user_table()

# Executar o site
home()
