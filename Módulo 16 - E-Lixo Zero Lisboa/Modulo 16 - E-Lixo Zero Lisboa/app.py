from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_mail import Mail, Message  # Biblioteca para enviar emails
import pymysql

app = Flask(__name__)
# Chave secreta necessária para manter o utilizador ligado (sessão)
app.secret_key = "projeto_gpsi_2026"

# --- CONFIGURAÇÃO DE EMAIL ---
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "cheirosodobanho@gmail.com"  # Teu email real
app.config["MAIL_PASSWORD"] = "mfpy hhua lscj rfis"  # Senha de app gerada no Google
app.config["MAIL_DEFAULT_SENDER"] = "o_teu_email@gmail.com"

mail = Mail(app)


# Função para ligar ao MySQL
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="elixo_zero",
        cursorclass=pymysql.cursors.DictCursor,
    )


@app.route("/")
def mapa():
    # Carrega a página principal do mapa
    return render_template("mapa.html")


@app.route("/api/pontos")
def api_pontos():
    db = get_db_connection() # Conexão com a base de dados
    try:
        with db.cursor() as cursor:
            # Selecionamos os campos necessários para o mapa e para o filtro
            cursor.execute(
                "SELECT descricao, morada, latitude, longitude, localidade, codigo_pos FROM pontos_recolha"
            )
            pontos = cursor.fetchall()

            for p in pontos:
                # Transformar coordenadas em números reais (float) para o Leaflet
                p["latitude"] = float(p["latitude"])
                p["longitude"] = float(p["longitude"])


                # .strip() remove espaços extra, .title() põe apenas a primeira letra em maiúscula
                p["localidade"] = p["localidade"].strip().title()

                # Criar uma "Zona" baseada nos primeiros 4 dígitos do Código Postal
                # Isso permite filtrar por zonas de Lisboa (ex: 1000, 1100, 1500)
                if p["codigo_pos"]:
                    p["zona_postal"] = p["codigo_pos"][:4]
                else:
                    p["zona_postal"] = "Outra"

        return jsonify(pontos)
    finally:
        db.close()
        
# Rota para a página de informação sobre Resíduos Eletrónicos
@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


# ROTA DE REGISTO (Criação de conta)
@app.route("/registo", methods=["GET", "POST"])
def registo():
    if request.method == "POST":
        # Usar .get() evita o erro 400 se o campo falhar
        email = request.form.get("email")
        user = request.form.get("username")
        pw = request.form.get("password")

        # Verificação de segurança: se algum estiver vazio, não continua
        if not email or not user or not pw:
            return "Erro: Todos os campos são obrigatórios!"

        db = get_db_connection()
        try:
            with db.cursor() as cursor:
                # Verificamos se o utilizador já existe
                cursor.execute(
                    "SELECT id FROM utilizadores WHERE username = %s", (user,)
                )
                if cursor.fetchone():
                    return "Este nome de utilizador já existe!"

                # Inserção na base de dados
                sql = "INSERT INTO utilizadores (username, password, email, status) VALUES (%s, %s, %s, 0)"
                cursor.execute(sql, (user, pw, email))
                db.commit()

            # --- ENVIO DE EMAIL ---
            link_confirmacao = url_for("confirmar_email", utilizador=user, _external=True) # Cria o link de confirmação com o nome de utilizador que foi colocado. O external é para fazer um link completo, sem isto o email do utilizador não saberia em que servidor o site está.
            msg = Message("Ative a sua conta - E-Lixo Lisboa", recipients=[email])
            msg.body = (
                f"Olá {user}! Clique aqui para ativar a sua conta: {link_confirmacao}"
            )

            # Tenta enviar o email, se falhar, avisa mas não bloqueia tudo
            try:
                mail.send(msg)
            except Exception as e_mail:
                print(f"Erro de email: {e_mail}")
                return "Utilizador criado, mas houve um erro ao enviar o email."

            return redirect(url_for("aguardar_confirmacao"))

        finally:
            db.close()

    return render_template("registo.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        db = get_db_connection()
        with db.cursor() as cursor:
            # IMPORTANTE: Agora verificamos também se o status é 1 (Ativo)
            cursor.execute(
                "SELECT * FROM utilizadores WHERE username=%s AND password=%s",
                (user, pw),
            )
            utilizador = cursor.fetchone()
        db.close()

        if utilizador:
            # Se o utilizador existe mas o status é 0, mandamos para a página de espera
            if utilizador["status"] == 0:
                return redirect(url_for("aguardar_confirmacao"))

            # Se estiver tudo bem (status 1), cria a sessão
            session["logged_in"] = True
            session["username"] = utilizador["username"]
            return redirect(url_for("mapa"))
        else:
            return "Login Inválido!"

    return render_template("login.html")


# Página de aviso "Verifique o seu Email"
@app.route("/aguardar-confirmacao")
def aguardar_confirmacao():
    return render_template("aguardar_confirmacao.html")


# Rota que o utilizador clica no email
@app.route("/confirmar/<utilizador>")
def confirmar_email(utilizador):
    db = get_db_connection()
    with db.cursor() as cursor:
        # Atualiza o status para 1
        cursor.execute(
            "UPDATE utilizadores SET status = 1 WHERE username = %s", (utilizador,)
        )
        db.commit()
    db.close()
    # Enviamos para uma página de sucesso
    return render_template("sucesso_confirmacao.html")


@app.route("/logout")
def logout():
    session.clear()  # Limpa os dados da sessão (desloga)
    return redirect(url_for("mapa"))


@app.route("/jogo")
def jogo():
    return render_template("jogo.html")


if __name__ == "__main__":
    app.run(debug=True)
