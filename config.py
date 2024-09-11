from flask import Flask, jsonify, render_template
import pyodbc

app = Flask(__name__)

# Configurações do banco de dados
host = 'projetolocacao.mssql.somee.com'
database = 'projetolocacao'
username = 'juliaa_senegalii_SQLLogin_1'
password = 'julia123'

string_conectar = f'DRIVER={{SQL Server}};SERVER={host};DATABASE={database};UID={username};PWD={password}'

# Função para conectar ao banco de dados
def conectar():
    try:
        conexao = pyodbc.connect(string_conectar)
        print("Conexão bem-sucedida ao banco de dados!")
        return conexao
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Rota para obter todos os carros
@app.route('/carros', methods=['GET'])
def obter_carros():
    return make_response(



        
    )





@app.route('/pagina_carros')
def pagina_carros():
    return render_template('/carros.html')

if __name__ == '__main__':
    app.run(debug=True)
