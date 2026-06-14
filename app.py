from flask import Flask,render_template,redirect,request, send_file
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app=Flask(__name__)
@app.route("/")
def home():
    import sqlite3

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM compras
        WHERE status = 'ABERTA'
    """)
    compras_abertas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT SUM(valor)
        FROM compras
        WHERE status = 'ABERTA'
    """)
    total_receber = cursor.fetchone()[0]

    if total_receber is None:
        total_receber = 0

    from datetime import datetime
    mes_atual=datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT SUM(valor)
        FROM compras
        WHERE data_compra LIKE ?
    """,(f"{mes_atual}%",))

    vendas_mes=cursor.fetchone()[0]
    if vendas_mes is None:
        vendas_mes=0
    conn.close()

    return render_template(
        "home.html",
        total_clientes=total_clientes,
        compras_abertas=compras_abertas,
        total_receber=total_receber,
        vendas_mes=vendas_mes
    )

@app.route("/novo_cliente",methods=["GET","POST"])
def novo_cliente():
    if request.method=="POST":
        nome=request.form["nome"]
        telefone=request.form["telefone"]
        
        import sqlite3
        conn=sqlite3.connect("banco.db")
        cursor=conn.cursor()
        cursor.execute(
           """
           INSERT INTO clientes
           (nome,telefone)
           VALUES(?, ?)
           """,
           (nome,telefone)
        )
        conn.commit()
        conn.close()
        return redirect ("/")
    return render_template ("novo_cliente.html")

@app.route("/clientes")
def clientes():
    busca=request.args.get("busca","")
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    cursor.execute("""
        SELECT*
        FROM clientes
        WHERE nome LIKE ?
    """,(f"%{busca}",))
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
    conn.close()
    return render_template(
        "clientes.html",
        clientes=clientes_com_total
    )

@app.route("/nova_compra", methods=["GET", "POST"])
def nova_compra():

    import sqlite3

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    # Buscar clientes para preencher o <select>
    cursor.execute("SELECT id, nome FROM clientes")
    clientes = cursor.fetchall()

    if request.method == "POST":

        cliente_id = request.form["cliente_id"]
        data_compra = request.form["data_compra"]
        valor = request.form["valor"]

        cursor.execute("""
            INSERT INTO compras
            (cliente_id, data_compra, valor, status)
            VALUES (?, ?, ?, ?)
        """, (cliente_id, data_compra, valor, "ABERTA"))

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
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    cursor.execute(
        "DELETE FROM clientes WHERE id = ?",
        (id,)
    )
    conn.commit()
    conn.close()
    return redirect("/clientes")

@app.route("/cliente/<int:id>")
def detalhes_cliente(id):
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    cursor.execute(
        "SELECT*FROM clientes WHERE id = ?",
        (id,)
    )
    cliente=cursor.fetchone()
    cursor.execute(
        "SELECT*FROM compras WHERE cliente_id = ?",
        (id,)
    )

    compras=cursor.fetchall()
    conn.close
    return render_template(
        "detalhes_cliente.html",
        cliente=cliente,
        compras=compras
    )

@app.route("/pagar/<int:compra_id>")
def pagar(compra_id):
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()

    cursor.execute("""
        UPDATE compras
        SET status =?, data_pagamento=?
        WHERE id=?
    """,(
        "PAGA",
        date.today().isoformat(),
        compra_id
    ))
    conn.commit()
    conn.close()

    return redirect("/clientes")

@app.route("/editar_cliente/<int:id>", methods=["GET","POST"])
def editar_cliente(id):
    import sqlite3
    conn=sqlite3.connect("banco.db")
    cursor=conn.cursor()
    if request.method == "POST":
        nome=request.form["nome"]
        telefone=request.form["telefone"]

        cursor.execute("""
            UPDATE clientes
            SET nome = ?, telefone= ?,
            WHERE id= ?
        """,(nome,telefone,id))
        conn.commit()
        conn.close()
        return redirect("/clientes")
    cursor.execute(
        "SELECT*FROM clientes WHERE id = ?",
        (id,)
    )
    cliente=cursor.fetchone()
    conn.close()
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

if (__name__) == "__main__":
    app.run(debug=True)