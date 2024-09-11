from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import pyodbc
from datetime import datetime

host = 'projetolocacao.mssql.somee.com'
database = 'projetolocacao'
username = 'juliaa_senegalii_SQLLogin_1'
password = 'julia123'

app = Flask(__name__)

connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host};DATABASE={database};UID={username};PWD={password}'

@app.route('/')
def index():
    try:
        connection = pyodbc.connect(connection_string)
        connection.close()
        return 'Conexão com o banco de dados estabelecida com sucesso!'
    except Exception as e:
        error_message = f'Erro ao conectar ao banco de dados: {str(e)}'
        return error_message, 500
    
@app.route('/login')
def teste():

    return render_template("login.html")   

#mostra os carros
@app.route('/lista', methods=["GET"])
def get_carros():
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        cursor.execute('SELECT id, marca, modelo, categoria, disponivel FROM carros')

        carros = []
        for row in cursor.fetchall():
            carro = {
                'id': row.id,
                'marca': row.marca,
                'modelo': row.modelo,
                'categoria': row.categoria,
                'disponivel': row.disponivel
            }
            carros.append(carro)

        cursor.close()
        connection.close()
        return render_template('lista.html', carros=carros)


@app.route('/add_novocarro')
def add_novocarro():
    return render_template('add_novocarro.html')


@app.route('/adicionar_carro', methods=['POST'])
def adicionar_carro():
    marca = request.form['marca']
    modelo = request.form['modelo']
    categoria = request.form['categoria']    
    disponivel = 'Sim'  # Definindo como padrão

    with pyodbc.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO carros (marca, modelo, categoria, disponivel)
                VALUES (?, ?, ?, ?)
            ''', (marca, modelo, categoria, disponivel))
            connection.commit()

    return redirect('/lista_carros_disponiveis')

#mostras as locaçoes
@app.route('/lista_locacao', methods=["GET"])
def get_locacao():
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        #é o codigo que "roda" no banco pra selecionar os dados
        cursor.execute('SELECT id_locacao, id_carro, data_retirada, data_entrega, locador, email_locador FROM locacao')

        locacao = []
        for row in cursor.fetchall():
            locar = {
                'id_locacao': row.id_locacao, #cada 'row.' é uma coluna do banco 
                'id_carro': row.id_carro,
                'data_retirada': row.data_retirada,
                'data_entrega': row.data_entrega,
                'locador': row.locador,
                'email_locador': row.email_locador
            }
            locacao.append(locar)
            print(f"Locações: {locacao}")
        cursor.close()
        connection.close()
        return render_template('locacao.html', locacao=locacao)

@app.route('/adicionar_locacao', methods=["GET"])
def mostrar_formulario():
    return render_template('adicionar_locacao.html')

#adiciona locacao
@app.route('/adicionar_locacao', methods=["POST"])
def adicionar_locacao():
    id_carro = request.form['id_carro']
    data_retirada = request.form['data_retirada']
    data_entrega = request.form['data_entrega']
    locador = request.form['locador']
    email_locador = request.form['email_locador']


    with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:

                cursor.execute('SELECT COUNT(*) FROM carros WHERE id = ?', (id_carro,))
                if cursor.fetchone()[0] == 0:
                    return redirect(url_for('mostrar_formulario', error='ID do carro não existe. Por favor, insira um ID válido.'))
                
                
                if data_entrega <= data_retirada:
                    raise ValueError('A data de entrega deve ser posterior à data de retirada.')

                try:
                    data_retirada = datetime.strptime(data_retirada, '%Y-%m-%d')
                    data_entrega = datetime.strptime(data_entrega, '%Y-%m-%d')
                except ValueError:
                    return redirect(url_for('mostrar_formulario', error='Formato de data inválido.'))

                cursor.execute('''
                    INSERT INTO locacao (id_carro, data_retirada, data_entrega, locador, email_locador)
                    VALUES (?, ?, ?, ?, ?)
                ''', (id_carro, data_retirada, data_entrega, locador, email_locador))
                
                connection.commit()

    return redirect(url_for('get_locacao'))


@app.route('/tornar_indisponivel', methods=["POST"])
def tornar_indisponivel():
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()

        id_carro = request.form['id_carro']
        cursor.execute("EXEC carro_indisponivel ?", (id_carro,)) #pega o id do carro e faz a procedure
        connection.commit()
        cursor.close()
        connection.close()
        return redirect('/lista')

@app.route('/tornar_disponivel', methods=["POST"])
def tornar_disponivel():
    # Obter o ID do carro do formulário
    id_carro = request.form['id_carro']
    
    # Conectar ao banco de dados
    with pyodbc.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            # Executar a stored procedure para tornar o carro disponível
            cursor.execute("EXEC carro_disponivel ?", (id_carro,))
            
            # Confirmar a transação
            connection.commit()

    # Redirecionar para a lista de carros
    return redirect('/lista')


@app.route('/lista_carros_disponiveis')
def lista_carros_disponiveis():
    carros = []

    # Conectar ao banco de dados
    with pyodbc.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            # Executar a stored procedure para obter carros disponíveis
            cursor.execute("EXEC carros_disponiveis")
            carros = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) AS total_disponiveis FROM carros WHERE disponivel = 'Sim';")
            total_disponiveis = cursor.fetchone().total_disponiveis

    return render_template('carros_disponiveis.html', carros=carros, total_disponiveis=total_disponiveis)

@app.route('/lista_carros_indisponiveis')
def lista_carros_indisponiveis():
    carros = []

    # Conectar ao banco de dados
    with pyodbc.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            # Executar a stored procedure para obter carros disponíveis
            cursor.execute("EXEC carros_indisponiveis")
            carros = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) AS total_indisponiveis FROM carros WHERE disponivel = 'Nao'")
            total_indisponiveis = cursor.fetchone().total_indisponiveis

    return render_template('carros_indisponiveis.html', carros=carros, total_indisponiveis=total_indisponiveis)

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


@app.route('/carros_atrasados', methods=['GET', 'POST'])
def carros_atrasados():
    resultados = None
    if request.method == 'POST':
        data_atual = request.form.get('data_atual')
        
        if data_atual:
            try:
                with pyodbc.connect(connection_string) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("{CALL carros_atrasados(?)}", (data_atual,))
                        resultados = cursor.fetchall()
            except pyodbc.Error as e:
                print(f"Erro ao consultar dados: {e}")
                resultados = []

    return render_template('carros_atrasados.html', resultados=resultados)


if __name__ == '__main__':
    app.run(debug=True)















