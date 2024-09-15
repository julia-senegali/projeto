from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import pyodbc
from datetime import datetime, date
import bcrypt

host = 'projetolocacao.mssql.somee.com'
database = 'projetolocacao'
username = 'juliaa_senegalii_SQLLogin_1'
password = 'julia123'

app = Flask(__name__)
app.secret_key = '123456'

connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host};DATABASE={database};UID={username};PWD={password}'

@app.route('/')
def index():
    return render_template("inicial.html")

# fazer o login usando o session
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']  
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM adm WHERE email = ? AND senha = ?", (email, senha))
                user = cursor.fetchone() 

                if user:
                    # guarda a informação da sessão
                    session['loggedin'] = True
                    session['id'] = user[0]  
                    session['email'] = user[1] 
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('menu'))
                else:
                    flash('Email ou senha incorretos!', 'danger')
    return render_template('login.html')

@app.route('/menu')
def menu():
    if 'loggedin' in session:
        return render_template('menu.html', email=session['email'])
    else:
        flash('Por favor, faça login para acessar esta página.', 'warning')
        return redirect(url_for('login'))


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Você foi desconectado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/cadastro_adm')
def cadastro_adm():
    return render_template('cadastro.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha'] 

        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO adm (email, senha)  -- Certifique-se de usar a coluna correta (provavelmente "senha" em vez de "username")
                    VALUES (?, ?)
                ''', (email, senha))
                connection.commit()

        return redirect('/login')
    return render_template('cadastro.html')

#mostra os carros
@app.route('/lista', methods=["GET", "POST"])
def lista():
    carros = []
    total_disponiveis = 0
    total_indisponiveis = 0
    id_carro = None
    data = None

    if request.method == 'POST':
        id_carro = request.form.get('id_carro')
        data = request.form.get('data')

        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id, marca, modelo, categoria FROM carros')
                for row in cursor.fetchall():
                    carro = {
                        'id': row.id,
                        'marca': row.marca,
                        'modelo': row.modelo,
                        'categoria': row.categoria,
                        'disponivel': None 
                    }

                    cursor.execute("SELECT dbo.verificar_disponibilidade(?, ?)", (carro['id'], data))
                    disponivel = cursor.fetchone()[0] 
                    if disponivel is not None:
                        carro['disponivel'] = disponivel
                        if disponivel:
                            total_disponiveis += 1
                        else:
                            total_indisponiveis += 1

                    carros.append(carro)

    else:  # GET
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id, marca, modelo, categoria FROM carros')
                for row in cursor.fetchall():
                    carro = {
                        'id': row.id,
                        'marca': row.marca,
                        'modelo': row.modelo,
                        'categoria': row.categoria,
                        'disponivel': None
                    }
                    carros.append(carro)

        total_disponiveis = 0
        total_indisponiveis = 0

    return render_template('lista.html', carros=carros, id_carro=id_carro, data=data,
                           total_disponiveis=total_disponiveis,
                           total_indisponiveis=total_indisponiveis)
                           
@app.route('/locacoes', methods=["GET", "POST"])
def locacoes():
    locacoes = []
    error = None
    if request.method == 'POST':
        id_carro = request.form.get('id_carro')
        data_retirada = request.form.get('data_retirada')
        data_entrega = request.form.get('data_entrega')
        locador = request.form.get('locador')
        email_locador = request.form.get('email_locador')
        try:
            with pyodbc.connect(connection_string) as connection:
                with connection.cursor() as cursor:
                    # Verifica se há alguma locação ativa para o carro
                    cursor.execute('''
                        SELECT data_retirada, data_entrega
                        FROM locacao
                        WHERE id_carro = ? AND devolvido = 0
                    ''', (id_carro,))
                    locacoes_ativas = cursor.fetchall()
                    data_retirada_input = datetime.strptime(data_retirada, '%Y-%m-%d').date()
                    data_entrega_input = datetime.strptime(data_entrega, '%Y-%m-%d').date()
                    overlap_found = False
                    for locacao in locacoes_ativas:
                        data_retirada_locacao = locacao[0]  # Já é um objeto date
                        data_entrega_locacao = locacao[1]  # Já é um objeto date
                        if not (data_entrega_input <= data_retirada_locacao or data_retirada_input >= data_entrega_locacao):
                            overlap_found = True
                            break
                    if overlap_found:
                        error = f"O carro {id_carro} já está locado durante o período solicitado ({data_retirada} a {data_entrega})."
                    else:
                        cursor.execute('''
                            EXEC adicionar_locacao ?, ?, ?, ?, ?
                        ''', (id_carro, data_retirada, data_entrega, locador, email_locador))
                        connection.commit()
        except pyodbc.Error as e:
            print(f"Erro ao adicionar locação: {e}")
            error = "Erro ao adicionar locação."
    try:
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT id_locacao, id_carro, data_retirada, data_entrega, locador, email_locador
                    FROM locacao
                ''')
                rows = cursor.fetchall()
                for row in rows:
                    locacao = {
                        'id_locacao': row.id_locacao,
                        'id_carro': row.id_carro,
                        'data_retirada': row.data_retirada.strftime('%Y-%m-%d'),
                        'data_entrega': row.data_entrega.strftime('%Y-%m-%d'),
                        'locador': row.locador,
                        'email_locador': row.email_locador
                    }
                    locacoes.append(locacao)
    except pyodbc.Error as e:
        print(f"Erro ao consultar locações: {e}")
    return render_template('locacoes.html', locacoes=locacoes, error=error)


@app.route('/add_novocarro')
def add_novocarro():
    return render_template('add_novocarro.html')

# faz um post para inserir novos carros
@app.route('/adicionar_carro', methods=['POST'])
def adicionar_carro():
    marca = request.form['marca']
    modelo = request.form['modelo']
    categoria = request.form['categoria']    
    disponivel = 'Sim'  # sempre vai ser inserido
    with pyodbc.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO carros (marca, modelo, categoria, disponivel)
                VALUES (?, ?, ?, ?)
            ''', (marca, modelo, categoria, disponivel))
            connection.commit()
    return redirect('/lista')

@app.route('/marcar_devolucao/<int:id_locacao>', methods=['POST'])
def marcar_devolucao(id_locacao):
    try:
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE locacao SET devolvido = 1 WHERE id_locacao = ?", (id_locacao,))
                cursor.execute("DELETE FROM locacao WHERE id_locacao = ?", (id_locacao,))
                connection.commit()
    except pyodbc.Error as e:
        print(f"Erro ao marcar devolução e remover locação: {e}")
    return redirect(url_for('locacoes'))
                       
@app.route('/carros_atrasados', methods=["GET"])
def carros_atrasados():
    carros_atrasados = []
    error = None
    try:
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                # pega a data atual de hoje
                hoje = datetime.now().date()
                # Consulta para obter os carros que estão atrasados
                cursor.execute('''
                    SELECT l.id_locacao, l.id_carro, l.data_retirada, l.data_entrega, l.locador, l.email_locador,
                           c.modelo, c.marca
                    FROM locacao l
                    JOIN carros c ON l.id_carro = c.id
                    WHERE l.devolvido = 0 AND l.data_entrega < ?
                ''', (hoje,))

                rows = cursor.fetchall()
                for row in rows:
                    carro_atrasado = {
                        'id_locacao': row[0],
                        'id_carro': row[1],
                        'data_retirada': row[2].strftime('%Y-%m-%d'),
                        'data_entrega': row[3].strftime('%Y-%m-%d'),
                        'locador': row[4],
                        'email_locador': row[5],
                        'modelo': row[6],
                        'marca': row[7]
                    }
                    carros_atrasados.append(carro_atrasado)
    except pyodbc.Error as e:
        error = f"Erro ao consultar carros atrasados: {e}"
        print(error)
        import traceback
        traceback.print_exc()

    data_atual = datetime.now().strftime('%Y-%m-%d')
    return render_template('carros_atrasados.html', resultados=carros_atrasados, error=error, data_atual=data_atual)



@app.route('/devolucoes', methods=['GET', 'POST'])
def devolucoes():
    resultados = None
    if request.method == 'POST':
        data_entrega = request.form.get('data_entrega')
        if data_entrega:
            try:
                with pyodbc.connect(connection_string) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("{CALL devolucao_dia(?)}", (data_entrega,))
                        resultados = cursor.fetchall()
            except pyodbc.Error as e:
                print(f"Erro ao consultar dados: {e}")
                resultados = []
    return render_template('devolucoes.html', resultados=resultados)



if __name__ == '__main__':
    app.run(debug=True)