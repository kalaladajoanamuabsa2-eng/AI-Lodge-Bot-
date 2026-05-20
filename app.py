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


# =========================
# CRIAR APP FLASK
# =========================

app = Flask(__name__)


# =========================
# SECRET KEY
# =========================

# usada para sessões/login

app.secret_key = "klodge_secret_key"


# =========================
# LOGIN ADMIN
# =========================

ADMIN_PASSWORD = "admin1234"


# =========================
# API KEY GEMINI
# =========================

API_KEY = os.getenv(
    "API_KEY"
) or "AIzaSyA1W60_S923o5XE6NSDDYmwxudSFNY9nOY"

# =========================
# ROTA PRINCIPAL
# =========================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


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
Voce é o assistente oficial do Lemon Beach Lodge.

Use SOMENTE as informações abaixo.

Nao invente respostas.

Se nao souber algo,
diga que a informação nao está disponível.

Informações do lodge:
{lodge_info}

Histórico:
{history_text}

Pergunta:
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

    response = requests.post(

        url,

        headers=headers,

        json=body

    )


    # =========================
    # RESPOSTA GEMINI
    # =========================

    result = response.json()

    print(result)


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

        port=5000

    )