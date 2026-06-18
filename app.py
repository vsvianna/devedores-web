from flask import Flask,render_template,redirect,request, send_file,session
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from werkzeug.security import generate_password_hash,check_password_hash

app=Flask(__name__)
import secrets
print(secrets.token_hex(32))
app.secret_key="8f739ca31886ade82396209d0d34b05f2498e8e5e703343414d195eb2c381d90"

@app.route("/")
def home():
    if "usuario_id" not in session:
        return redirect("/login")
    import sqlite3

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    usuario_id=session["usuario_id"]
    cursor.execute("""
        SELECT COUNT(*)
        FROM clientes
        WHERE usuario_id=?       
        """,(usuario_id,))
    total_clientes = cursor.fetchone()[0]

    cursor.execute("""
    SELECT SUM(valor)
    FROM compras
    WHERE status='ABERTA'
    AND cliente_id IN(
        SELECT id
        FROM clientes
        WHERE usuario_id=?
    )
    """,(usuario_id,))

    compras_abertas=cursor.fetchone()[0]
    if compras_abertas is None:
        compras_abertas=0

    cursor.execute("""
    SELECT COUNT(*)
    FROM compras
    WHERE status='PAGA'
    AND cliente_id IN(
        SELECT id
        FROM clientes
        WHERE usuario_id=?
    )
    """,(usuario_id,))

    pagas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT SUM(valor)
        FROM compras
        WHERE status='ABERTA'
        AND cliente_id IN(
            SELECT id
            FROM clientes
            WHERE usuario_id=?
    )
    """,(usuario_id,))
    total_receber = cursor.fetchone()[0]

    if total_receber is None:
        total_receber = 0

    from datetime import datetime
    mes_atual=datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT SUM(valor)
        FROM compras
        WHERE data_compra LIKE ?
        AND cliente_id IN(
            SELECT id
            FROM clientes
            WHERE usuario_id=?
        )
    """,(f"{mes_atual}%",usuario_id))

    vendas_mes=cursor.fetchone()[0]
    if vendas_mes is None:
        vendas_mes=0

    from datetime import datetime
    cursor.execute("""
        SELECT                  
            substr(data_compra,1,7) as mes,    
            SUM(valor)
        FROM compras          
        WHERE cliente_id IN(
            SELECT id
            FROM clientes
            WHERE usuario_id=?
        )
        GROUP BY substr(data_compra,1,7)
        ORDER BY mes
    """,(usuario_id,))
    resultado=cursor.fetchall()

    meses = []
    valores = []

    for linha in resultado:
        data_mes = datetime.strptime(linha[0], "%Y-%m")
        meses.append(
        data_mes.strftime("%b/%y")
        )
        valores.append(float(linha[1]))
    meses = meses[-6:]
    valores = valores[-6:]

    cursor.execute("""
        SELECT COUNT(*)
        FROM compras
        WHERE status='PAGA'
        AND cliente_id IN(
            SELECT id
            FROM clientes
            WHERE usuario_id=?
    )
    """,(usuario_id,))

    pagas=cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            clientes.nome,
            SUM(compras.valor) as total_divida              
        FROM clientes
        JOIN compras
            ON clientes.id=compras.cliente_id
        WHERE clientes.usuario_id=?
        AND compras.status='ABERTA'
        GROUP BY clientes.id, clientes.nome
        ORDER BY total_divida DESC
        LIMIT 5 
    """,(usuario_id,))
    top_devedores=cursor.fetchall()

    conn.close()

    print("compras_abertas =", compras_abertas)
    print("total_receber =", total_receber)
    print("pagas =", pagas)

    return render_template(
        "home.html",
        total_clientes=total_clientes,
        compras_abertas=compras_abertas,
        total_receber=total_receber,
        vendas_mes=vendas_mes,
        meses=meses,
        valores=valores,
        pagas=pagas,
        top_devedores=top_devedores
    )

@app.route("/novo_cliente",methods=["GET","POST"])
def novo_cliente():
    if request.method=="POST":
        nome=request.form["nome"]
        telefone=request.form["telefone"]
        
        import sqlite3
        conn=sqlite3.connect("banco.db")
        cursor=conn.cursor()
        usuario_id = session["usuario_id"]

        cursor.execute("""
            INSERT INTO clientes
            (nome, telefone, usuario_id)
            VALUES (?, ?, ?)
            """, (nome, telefone, usuario_id))
        conn.commit()
        conn.close()
        return redirect ("/clientes")
    return render_template ("novo_cliente.html")

@app.route("/clientes")
def clientes():
    busca=request.args.get("busca","")
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    usuario_id=session["usuario_id"]
    cursor.execute("""
        SELECT*
        FROM clientes
        WHERE usuario_id=?
        AND nome LIKE ?
        """,(usuario_id,f"%{busca}%"))
    clientes=cursor.fetchall()
    clientes_com_total=[]
    for cliente in clientes:
        id_cliente=cliente[0]
        cursor.execute("""
            SELECT SUM(valor)
            FROM compras
            WHERE cliente_id = ?
            AND status ='ABERTA'
        """,(id_cliente,))
        resultado=cursor.fetchone()
        total=resultado[0]
        if total is None:
            total=0
        clientes_com_total.append(
            (cliente[0],cliente[1],cliente[2],total)
        )
    conn.commit()
    conn.close()
    return render_template(
        "clientes.html",
        clientes=clientes_com_total
    )

@app.route("/nova_compra", methods=["GET", "POST"])
def nova_compra():

    usuario_id = session["usuario_id"]

    import sqlite3

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    if "usuario_id" not in session:
        return redirect("/login")

    cursor.execute("""
        SELECT id, nome
        FROM clientes
        WHERE usuario_id = ?
    """, (usuario_id,))
    clientes = cursor.fetchall()

    if request.method == "POST":

        cliente_id = request.form["cliente_id"]
        data_compra = request.form["data_compra"]
        valor = request.form["valor"]

        cursor.execute("""
            SELECT id
            FROM clientes
            WHERE id = ?
            AND usuario_id = ?
        """, (cliente_id, usuario_id))

        cliente = cursor.fetchone()

        if cliente is None:
            conn.close()
            return "Cliente inválido."

        cursor.execute("""
            INSERT INTO compras
            (cliente_id, data_compra, valor, status)
            VALUES (?, ?, ?, ?)
        """, (
            cliente_id,
            data_compra,
            valor,
            "ABERTA"
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    conn.close()

    return render_template(
        "nova_compra.html",
        clientes=clientes
    )

@app.route("/excluir_cliente/<int:id>")
def excluir_cliente(id):
    usuario_id=session["usuario_id"]
    if "usuario_id" not in session:
        return redirect("/login")
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    cursor.execute("""
        DELETE FROM clientes 
        WHERE id = ?
        AND usuario_id=?
    """,(id,usuario_id))
    conn.commit()
    conn.close()
    return redirect("/clientes")

@app.route("/cliente/<int:id>")
def detalhes_cliente(id):
    if "usuario_id" not in session:
        return redirect("/login")
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    usuario_id=session["usuario_id"]
    cursor.execute("""
        SELECT*
        FROM clientes
        WHERE id = ?
        AND usuario_id=?
    """,(id,usuario_id))
    
    cliente=cursor.fetchone()
    if cliente is None:
        conn.close()
        return "Cliente não encontrado."

    cursor.execute("""
        SELECT*
        FROM compras
        WHERE cliente_id = ?
    """,(id,))
    
    compras=cursor.fetchall()
    conn.close()
    return render_template(
        "detalhes_cliente.html",
        cliente=cliente,
        compras=compras
    )

@app.route("/pagar/<int:compra_id>")
def pagar(compra_id):

    import sqlite3

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    usuario_id = session["usuario_id"]

    cursor.execute("""
        SELECT compras.id
        FROM compras
        JOIN clientes
        ON compras.cliente_id = clientes.id
        WHERE compras.id = ?
        AND clientes.usuario_id = ?
    """,(compra_id, usuario_id))

    compra = cursor.fetchone()

    if compra is None:
        conn.close()
        return "Compra não encontrada."

    cursor.execute("""
        UPDATE compras
        SET status = ?, data_pagamento = ?
        WHERE id = ?
    """, (
        "PAGA",
        date.today().isoformat(),
        compra_id
    ))

    conn.commit()
    conn.close()

    return redirect("/clientes")

@app.route("/editar_cliente/<int:id>", methods=["GET","POST"])
def editar_cliente(id):
    if "usuario_id" not in session:
        return redirect ("/login")
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    usuario_id=session["usuario_id"]
    if request.method == "POST":
        nome=request.form["nome"]
        telefone=request.form["telefone"]

        cursor.execute("""
            UPDATE clientes
            SET nome = ?, telefone= ?
            WHERE id= ?
            AND usuario_id=?
        """,(nome,telefone,id,usuario_id))
        conn.commit()
        conn.close()
        return redirect("/clientes")
    cursor.execute("""
        SELECT*
        FROM clientes
        WHERE id = ?
        AND usuario_id=?
    """,(id,usuario_id))

    cliente=cursor.fetchone()
    conn.close()

    if cliente is None:
        return "Cliente não encontrado."
    return render_template(
        "editar_cliente.html",
        cliente=cliente
    )

@app.route("/relatorios")
def relatorios():
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    cursor.execute("""
        SELECT id, nome
        FROM clientes
        ORDER BY nome
    """)

    clientes = cursor.fetchall()

    conn.close()

    return render_template(
        "relatorios.html",
        clientes=clientes
    )

@app.route("/relatorio_mensal")
def relatorio_mensal():
    import sqlite3
    mes=request.args.get("mes")
    ano=request.args.get("ano")

    filtro = f"{ano}-{int(mes):02d}%"
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    cursor.execute("""
        SELECT data_compra, valor, status
        FROM compras
        WHERE data_compra LIKE?               
    """,(filtro,))
    compras=cursor.fetchall()
    conn.close()
    return render_template(
        "resultado_relatorio.html",
        titulo=f"Relatorio {mes}/{ano}",
        compras=compras
    )

@app.route("/relatorio_anual")
def relatorio_anual():
    ano=request.args.get("ano")
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    cursor.execute("""
        SELECT data_compra,valor,status
        FROM compras
        WHERE data_compra LIKE?
    """, (f"{ano}%",))
    compras=cursor.fetchall()

    conn.close()

    return render_template(
        "resultado_relatorio.html",
        titulo=f"Relatorio de {ano}",
        compras=compras
    )

@app.route("/relatorio_cliente")
def relatorio_cliente():
    cliente_id=request.args.get("cliente_id")
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()

    cursor.execute("""
        SELECT data_compra,valor,status
        FROM compras
        WHERE cliente_id=?
    """,(cliente_id,))

    compras=cursor.fetchall()
    conn.close()

    return render_template(
        "resultado_relatorio.html",
        titulo="Relatorio do Cliente",
        compras=compras
    )

@app.route("/relatorio_mensal_pdf")
def relatorio_mensal_pdf():
    import sqlite3
    import io
    mes=request.args.get("mes")
    ano=request.args.get("ano")

    filtro=f"{ano}-{int(mes):02d}%"

    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    cursor.execute("""
        SELECT data_compra, valor, status
        FROM compras
        WHERE data_compra LIKE ?
    """, (filtro,))

    compras = cursor.fetchall()
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elementos = [
        Paragraph(f"Relatório Mensal - {mes}/{ano}", styles["Title"])
    ]

    tabela = [["Data", "Valor", "Status"]]

    total = 0

    for compra in compras:
        tabela.append([
            str(compra[0]),
            f"R$ {compra[1]:.2f}",
            str(compra[2])
        ])
        total += float(compra[1])

    tabela.append(["", "TOTAL", f"R$ {total:.2f}"])

    tabela_pdf = Table(tabela)

    tabela_pdf.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ]))

    elementos.append(tabela_pdf)

    doc.build(elementos)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"relatorio_{mes}_{ano}.pdf",
        mimetype="application/pdf"
    )

import sqlite3
def criar_tabela_usuario():
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
            )     
        """)
    conn.commit()
    conn.close()
criar_tabela_usuario()

@app.route("/cadastro", methods=["GET","POST"])
def cadastro():
    import sqlite3
    if request.method=="POST":
        nome=request.form["nome"]
        email=request.form["email"]
        senha=request.form["senha"]

        senha_hash=generate_password_hash(senha)
        conn=sqlite3.connect("banco.db")
        cursor=conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO usuarios (nome,email,senha)
                VALUES (?,?,?)
            """,(nome,email,senha_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Este e-mail ja esta cadastro",
        conn.close()
        return redirect("/login")
    return render_template("cadastro.html")

@app.route("/login",methods=["GET","POST"])
def login():
    import sqlite3
    if "usuario_id" in session:
        return redirect("/")
    if request.method=="POST":
        email=request.form["email"]
        senha=request.form["senha"]

        conn=sqlite3.connect("banco.db")
        cursor=conn.cursor()
        cursor.execute("""
            SELECT id, senha
            FROM usuarios
            WHERE email= ?
        """,(email,))
        usuario=cursor.fetchone()
        conn.close()

        if usuario is not None:
            id_usuario=usuario[0]
            senha_hash=usuario[1]

            if check_password_hash(senha_hash,senha):
                session["usuario_id"]=id_usuario
                return redirect("/")
        return "E-mail ou senha invalida."
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if (__name__) == "__main__":
    app.run(debug=True)