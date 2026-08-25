# =========================
# IMPORTAÇÕES
# =========================

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

import requests
import webbrowser
import threading
import os
import urllib.parse

# =========================
# CRIAR APP FLASK
# =========================

app = Flask(__name__)


# =========================
# SECRET KEY
# =========================

# usada para sessões/login

#app.secret_key = "klodge_secret_key"


# =========================
# LOGIN ADMIN
# =========================


ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
app.secret_key = os.getenv("SECRET_KEY")


# =========================
# API KEY GEMINI
# =========================

API_KEY = os.getenv(
    "API_KEY"
)


#Wassup
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")


# =========================
# ROTA PRINCIPAL
# =========================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================
# HEALTH CHECK
# =========================

@app.route("/health")
def health():
    return {"status": "ok"}, 200



# =========================
# LOGIN
# =========================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        password = request.form.get(
            "password"
        )

        if password == ADMIN_PASSWORD:

            # salva sessão admin
            session["admin"] = True

            return redirect(
                url_for("admin")
            )

        else:

            return render_template(
                "login.html",
                error="Senha incorreta"
            )

    return render_template(
        "login.html"
    )


# =========================
# CHAT
# =========================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    # =========================
    # MEMÓRIA DO USUÁRIO
    # =========================

    if "chat_history" not in session:

        session["chat_history"] = []


    # =========================
    # PEGAR MENSAGEM
    # =========================

    data = request.get_json()

    user_message = data["message"]


    # =========================
    # HISTÓRICO
    # =========================

    history = session["chat_history"]

    history.append(
        f"Cliente: {user_message}"
    )

    history_text = "\n".join(
        history
    )


    # =========================
    # LER TXT DO LODGE
    # =========================

    with open(
        "lodge_info.txt",
        "r",
        encoding="utf-8"
    ) as file:

        lodge_info = file.read()


    # =========================
    # PROMPT
    # =========================

    prompt = f"""
Você é o assistente virtual oficial do Kalala Lodge.

O seu trabalho é ajudar hóspedes e potenciais clientes de forma profissional, simpática e clara.

REGRAS IMPORTANTES:

1. Utilize APENAS as informações fornecidas abaixo.
2. Nunca invente informações.
3. Se uma informação não estiver disponível, responda:
   "Peço desculpa, mas essa informação não está disponível. Entre em contacto com a receção para mais detalhes."
4. Nunca diga que é uma IA, modelo de linguagem ou que foi criado pela Google.
5. Responda de forma natural, como um rececionista experiente.
6. Seja educado e profissional.
7. Responda normalmente entre 2 e 5 frases.
8. Quando fizer sentido, incentive o cliente a fazer uma reserva ou contactar a receção.
9. Se o cliente cumprimentar apenas ("Olá", "Bom dia"), responda de forma simpática e pergunte como pode ajudar.
10. Se o cliente agradecer, responda cordialmente.

INFORMAÇÕES DO LODGE:

{lodge_info}

HISTÓRICO DA CONVERSA:

{history_text}

PERGUNTA DO CLIENTE:

{user_message}
"""


    # =========================
    # URL GEMINI
    # =========================

    url = (
        "https://generativelanguage.googleapis.com"
        f"/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    )


    # =========================
    # HEADERS
    # =========================

    headers = {

        "Content-Type":
        "application/json"

    }


    # =========================
    # BODY
    # =========================

    body = {

        "contents": [

            {

                "parts": [

                    {
                        "text": prompt
                    }

                ]

            }

        ]

    }


    # =========================
    # ENVIAR PARA GEMINI
    # =========================

    print(
        "Enviando para Gemini..."
    )

    try:

        response = requests.post(

            url,

            headers=headers,

            json=body,

            timeout=30

        )
        
        response.raise_for_status()

    except requests.exceptions.Timeout:

        return jsonify({

            "reply": "O assistente demorou muito para responder. Tente novamente."

        })

    except requests.exceptions.ConnectionError:

        return jsonify({

            "reply": "Sem ligação ao servidor da IA. Verifique a internet e tente novamente."

        })

    except requests.exceptions.RequestException:

        return jsonify({

            "reply": "Ocorreu um erro ao comunicar com a IA. Tente novamente mais tarde."

        })


    # =========================
    # RESPOSTA GEMINI
    # =========================

    try:

        result = response.json()

        print(result)

    except Exception:

        return jsonify({

            "reply": "Não foi possível interpretar a resposta da IA."

        })


    # =========================
    # VERIFICAR ERRO
    # =========================

    if "candidates" in result:

        reply = result[
            "candidates"
        ][0][
            "content"
        ][
            "parts"
        ][0][
            "text"
        ]

    else:

        reply = (
            "Erro ao falar com Gemini"
        )


    # =========================
    # GUARDAR IA
    # =========================

    history.append(
        f"IA: {reply}"
    )

    session["chat_history"] = history


    # =========================
    # ENVIAR PARA HTML
    # =========================

    return jsonify({

        "reply": reply

    })


# =========================
# ADMIN PANEL
# =========================

@app.route("/admin")
def admin():

    # verifica login
    if "admin" not in session:

        return redirect(
            url_for("login")
        )

    with open(
        "lodge_info.txt",
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()

    return render_template(

        "admin.html",

        content=content

    )


# =========================
# SALVAR ALTERAÇÕES
# =========================

@app.route(
    "/save",
    methods=["POST"]
)
def save():

    # verifica login
    if "admin" not in session:

        return redirect(
            url_for("login")
        )

    new_content = request.form["content"]

    with open(
        "lodge_info.txt",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            new_content
        )

    return "Salvo com sucesso!"


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.pop(
        "admin",
        None
    )

    return redirect(
        url_for("login")
    )


# =========================
# ABRIR NAVEGADOR
# =========================

def open_browser():

    webbrowser.open(
        "http://127.0.0.1:5000"
    )


#ROTA WHATSAPP
@app.route("/whatsapp")
def whatsapp():

    texto = urllib.parse.quote(
        "Olá! Gostaria de obter mais informações sobre o lodge."
    )

    return redirect(
        f"https://wa.me/{WHATSAPP_NUMBER}?text={texto}"
    )
    
   
      
#ANTI ERROS 
    
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD não foi definida.")

if not app.secret_key:
    raise ValueError("SECRET_KEY não foi definida.")

if not API_KEY:
    raise ValueError("API_KEY não foi definida.")

if not WHATSAPP_NUMBER:
    raise ValueError("WHATSAPP_NUMBER não foi definido.")



# =========================
# INICIAR SERVIDOR
# =========================

if __name__ == "__main__":

    threading.Timer(

        1,

        open_browser

    ).start()

    app.run(
    host="0.0.0.0",
    port=int(os.getenv("PORT", 5000))
)
    
