import random
import hashlib
import webbrowser
import json
import locale
import pytz
import os
import string

from flask import jsonify
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime
from flask import *
from . import homologacao
from .classes.db_func import *
from .classes.integracoes import *
from werkzeug.utils import secure_filename
from flask import render_template as real_render_template
from cryptography.fernet import Fernet

#homologacao.secret_key = 'random string'

UPLOAD_FOLDER = 'static/uploads'
UPLOAD_FOLDER_CERTIFICADO = 'static/certificados/'
UPLOAD_FOLDER_QRCODE = 'static/qrcode/'

ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
ALLOWED_EXTENSIONS_ICO = set(['ico'])
ALLOWED_EXTENSIONS_CERT = set(['p12'])

tz = pytz.timezone('Brazil/East')

def render_template(*args, **kwargs):
    logomarca = Parametros(id_param = 1).getParametros()[0][2]
    qtdNotifs = Notificacoes().getQtdNotificacoes()[0][0]
    nomeLoja = Parametros(id_param = 2).getParametros()[0][2]
    ativa_referencia = Parametros(id_param = '10').getParametros()[0][2]
    
    facebook = Parametros(id_param = 4).getParametrosSocial()[0][2]
    twitter = Parametros(id_param = 5).getParametrosSocial()[0][2]
    instagram = Parametros(id_param = 6).getParametrosSocial()[0][2]
    linkedin = Parametros(id_param = 7).getParametrosSocial()[0][2]
    whatsapp = Parametros(id_param = 11).getParametrosSocial()[0][2]

    status_consent = getConsentimentoCookie()

    return real_render_template(*args, **kwargs, status_consent = status_consent, ativa_referencia = ativa_referencia, whatsapp = whatsapp, logomarca = logomarca, qtdNotifs = qtdNotifs, nomeLoja = nomeLoja, facebook = facebook, twitter = twitter, instagram = instagram, linkedin = linkedin)

#---------------------------------------------------------------------------------------#

def getConsentimentoCookie():
    conn = db()
    try:
        resultado = conn.execute_bd_com_param('select * from tb_consentimento where num_cookie = ?', (int(getCookie()),))
        if len(resultado) == 0:
            return False
        else:
            if resultado[0][1] == 'T':
                return True
            else:
                return False
    except:
        return False

#---------------------------------------------------------------------------------------#

def getDetalhesLogin():
    if 'email' not in session:
        autenticado = False
        nome = 'Visitante'
        tipoUser = 'U'
        
        conn = db()
        num_cookie = request.cookies.get('cartCookie')
        queryCart = "SELECT count(id_produto) FROM tb_carrinho WHERE guest_number = ?"
        dadosCart = (num_cookie,)
        data_cart = conn.execute_bd_com_param(queryCart, dadosCart)

        qtdCarrinho = data_cart[0]
    else:
        conn= db()
        autenticado = True

        queryUser= "SELECT id_cliente, nome, tipo_ACESSO FROM tb_cliente WHERE email = ?"
        dadosUser = (session['email'],)
        data_cli = conn.execute_bd_com_param(queryUser, dadosUser)
        for dados in data_cli:
            id_cliente = dados[0]
            nome = dados[1]
            tipoUser = dados[2]

        queryCart = "SELECT count(id_produto) FROM tb_carrinho WHERE id_cliente = ?"
        dadosCart = (id_cliente,)
        data_cart = conn.execute_bd_com_param(queryCart, dadosCart)
        qtdCarrinho = data_cart[0]
 
    return (autenticado, nome, tipoUser, qtdCarrinho)

#---------------------------------------------------------------------------------------#

def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(6):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans

#---------------------------------------------------------------------------------------#

def getDadosCategorias():
    conn = db()
    cat = conn.execute_bd('''SELECT a.id_categoria,
       a.nome_categoria
  FROM tb_categorias a
  inner join tb_produtos b on a.id_categoria = b.id_categoria
 WHERE a.EXIBE_wEB = "T" 
 group by a.id_categoria,
       a.nome_categoria''', "A")
    return cat

#---------------------------------------------------------------------------------------#

def geraCodigo():
    length = 64
    chars = string.ascii_letters + string.digits + '-'
    random.seed = (os.urandom(1024))   
    codigo = ''.join(random.choice(chars) for i in range(length))
    return codigo

#---------------------------------------------------------------------------------------#

def checaCodigo(codigo):
    conn = db()
    validacao = conn.execute_bd_com_param('select * from tb_redef_senha where codigo =?', (codigo,))
    if len(validacao) != 0:
        valido = validacao[0][2]
        print(valido)
        if valido=='T':
            return True
        else:
            return False
    else:
        return False
#---------------------------------------------------------------------------------------#

def getIdCliente(email):
    conn = db()
    query = conn.execute_bd_com_param("SELECT id_cliente FROM tb_cliente WHERE email = ?", (email, ))
    for dados in query:
        id_cliente = dados[0]
    return id_cliente

#---------------------------------------------------------------------------------------#

def getNomeCliente(id):
    conn = db()
    nome = conn.execute_bd_com_param("SELECT nome FROM tb_cliente WHERE id_cliente = ?", (id, ))[0][0]
    return nome

#---------------------------------------------------------------------------------------#

def getIdClientePorVenda(id):
    conn = db()
    id = conn.execute_bd_com_param("SELECT id_cliente FROM tb_vendas WHERE id_venda = ?", (id, ))[0][0]
    return id

#---------------------------------------------------------------------------------------#

def getMailCliente(id):
    conn = db()
    email = conn.execute_bd_com_param("SELECT email FROM tb_cliente WHERE id_cliente = ?", (id, ))[0][0]
    return email

#---------------------------------------------------------------------------------------#

def dadosValidos(email, password):
    conn = db()
    data = conn.execute_bd('SELECT email, senha FROM tb_cliente', 'A')
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False

#---------------------------------------------------------------------------------------#

def getCookie():
    num_cookie = request.cookies.get('cartCookie')
    if num_cookie == None:
        random_cookie = str(round(random.uniform(0, 10000000)))
        resp = make_response(redirect('/home'))
        resp.set_cookie('cartCookie', random_cookie)
        return resp
    return num_cookie

#---------------------------------------------------------------------------------------#

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def allowed_file_ico(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS_ICO

def allowed_file_cert(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS_CERT

#---------------------------------------------------------------------------------------#

def getValorProduto(idProduto, qtdSite):
    qtdSite = int(qtdSite)

    prod = Produtos()
    prod = prod.getProduto(idProduto)
    valor = prod[0][4]
    
    tab = Tabelas()
    tab = tab.getTabelaProd(idProduto)

    idTab = None
    if len(tab) != 0:
        idTab = tab[0][0]

    if idTab != None:
        tab = Tabelas()
        faixasPreco = tab.getFaixas(idTab)
        for faixa in faixasPreco:
            if faixa[2] == None or faixa[2] == '':
                qtdMax = 99999999
            else:
                qtdMax = int(faixa[2])

            qtdMin = int(faixa[1])
            vlr = faixa[3]

            if qtdSite >= qtdMin and qtdSite <= qtdMax:
                valor = vlr
                break
    return "%.2f" % float(valor)

#---------------------------------------------------------------------------------------#

def getTaxasValor(valor, taxa):
    calcTx = valor * (float(taxa)/100)
    return "%.2f" % calcTx

def getAcrescimoValor(valor, calcTx, acrescimo):
    calcAc = (valor + calcTx) * (float(acrescimo)/100)
    return "%.2f" % calcAc

def getDadosCheckout(id_cliente, formaPgto):
    cart = Carrinho(id_cliente, tipo='autenticado')
    produtos = cart.getCarrinho() 
    
    tx = FormasPgto(formaPgto)
    taxas = tx.getTaxas()[0][0]
    if taxas != '':
        taxas = float(taxas)
    else: 
        taxas = 0
    
    acrescimo = tx.getAcrescimos()
    if acrescimo != '':
        acrescimo = float(acrescimo)
    else: 
        acrescimo = 0
    
    precoTotal = []
    for x in produtos:
        precoTotal.append(float(x[5]))
    subtotal = sum(precoTotal)
    
    calcTx = getTaxasValor(subtotal, taxas)
    calcAc = getAcrescimoValor(subtotal, float(calcTx), acrescimo)
    
    total = (float(subtotal) + float(calcTx)) + float(calcAc)
    
    return produtos, taxas, acrescimo, subtotal, calcTx, calcAc, total

def getDadosPedido(id_pedido, formaPgto):
    pedidos = Vendas(id_venda = id_pedido)
    produtos = pedidos.getDetVendas() 
    
    tx = FormasPgto(formaPgto)
    taxas = tx.getTaxas()[0][0]
    if taxas != '':
        taxas = float(taxas)
    else: 
        taxas = 0
    
    acrescimo = tx.getAcrescimos()
    if acrescimo != '':
        acrescimo = float(acrescimo)
    else: 
        acrescimo = 0

    precoTotal = []
    for x in produtos:
        precoTotal.append(float(x[5]))
    subtotal = sum(precoTotal)
    
    calcTx = getTaxasValor(subtotal, taxas)
    calcAc = getAcrescimoValor(subtotal, float(calcTx), acrescimo)
    
    total = (float(subtotal) + float(calcTx)) + float(calcAc)
    return produtos, taxas, acrescimo, subtotal, calcTx, calcAc, total 

#---------------------------------------------------------------------------------------#

def checaEmail(email):
    conn = db()
    resultado = conn.execute_bd_com_param('select * from tb_cliente where email = ?', (email,))
    if len(resultado) == 0:
        return False
    else:
        return True

#---------------------------------------------------------------------------------------#

def buscaItens(itemBusca):
    conn = db()
    dadosItens = conn.execute_bd_com_param('SELECT a.id_produto, produto, descricao, preco, b.diretorio, qtd, EXIBE_VALOR_WEB FROM tb_produtos a left join tb_produtos_imagens b on a.id_produto = b.id_produto and b.principal = "T" where exibe_web = "T" and produto like ?', ('%'+ itemBusca +'%',))
    return dadosItens

#---------------------------------------------------------------------------------------#

@homologacao.errorhandler(404) 
def not_found(e): 
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    dadosCategorias = getDadosCategorias()
    return render_template("404.html", autenticado=autenticado, nome=nome, tipoUser=tipoUser, dadosCategorias=dadosCategorias) 

#---------------------------------------------------------------------------------------#

@homologacao.route('/')
def redir():
    try:
        if 'url' not in session:
            session['url'] = '.home'
        int(getCookie())
        return redirect(url_for(session['url']))
    except:
        random_cookie = str(round(random.uniform(0, 1000000)))
        resp = make_response(redirect('/home'))
        resp.set_cookie('cartCookie', random_cookie)
        return resp

@homologacao.route('/home', methods = ['POST', 'GET'])
def home():
    session['url'] = '.home'
    num_cookie = getCookie()
    try:
        int(num_cookie)
    except:
        return redirect(url_for('.redir'))

    conn= db()

    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    query = '''
               SELECT a.id_produto, produto, descricao, printf("%.2f", preco), b.diretorio, qtd, EXIBE_VALOR_WEB
               FROM tb_produtos a 
               left join tb_produtos_imagens b on a.id_produto = b.id_produto and b.principal = "T"
               inner join tb_categorias c on a.id_categoria = c.id_categoria
               where A.exibe_web = "T" 
            '''

    params = Parametros(id_param = '8')
    exibe_indisponivel = params.getParametros()[0][2]

    params = Parametros(id_param = '9')
    exibe_categ_oculta = params.getParametros()[0][2]

    if exibe_indisponivel == 'NÃO':
        query = query + ' and a.qtd_max > 0 '

    if exibe_categ_oculta == 'NÃO':
        query = query + ' and c.exibe_web = "T"'

    dadosItens = conn.execute_bd(query, 'A')      
    
    dadosCategorias = getDadosCategorias() 

    dadosItens = parse(dadosItens)

    return render_template('ecommerce/home.html', dadosItens=dadosItens, autenticado=autenticado, nome=nome, tipoUser=tipoUser, qtdCarrinho=qtdCarrinho, dadosCategorias=dadosCategorias)

#---------------------------------------------------------------------------------------#

@homologacao.route('/cookieAceito', methods = ['POST'])
def consentCookie():
    if request.method == 'POST':
        conn=db()
        conn.execute_bd_com_param('insert into tb_consentimento (num_cookie, cookie_aceito) values (?, ?)', (int(getCookie()), 'T'))
    return 'success'

#---------------------------------------------------------------------------------------#

@homologacao.route('/pesquisar', methods = ['POST', 'GET'])
def pesquisaQuery():
    session['url'] = '.home'
    num_cookie = getCookie()
    try:
        int(num_cookie)
    except:
        return redirect(url_for('.redir'))

    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    prodBusca = request.args.get("q")
    dadosItens = buscaItens(prodBusca)
    dadosItens = parse(dadosItens)

    dadosCategorias = getDadosCategorias()

    return render_template('ecommerce/resultadoBusca.html', dadosItens=dadosItens, autenticado=autenticado, nome=nome, tipoUser=tipoUser, qtdCarrinho=qtdCarrinho, dadosCategorias=dadosCategorias)

#---------------------------------------------------------------------------------------#

@homologacao.route("/exibirCategoria")
def displayCategory():
    session['url'] = '.home'
    num_cookie = getCookie()
    try:
        int(num_cookie)
    except:
        return redirect(url_for('.redir'))

    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    idCategoria = request.args.get("idCategoria")

    statusWEB = Categorias()
    statusWEB = statusWEB.getCategoria(idCategoria)

    if statusWEB[0][2] == 'NÃO':
        flash('Categoria inválida!', 'warning')
        return redirect(url_for('.home'))

    prodCateg = Categorias(id_categ = idCategoria)
    data = prodCateg.exibeProdutosCategoria()

    if len(data) != 0:
        nomeCategoria = data[0][4]
        dadosItens = parse(data)
    else:
        flash('Categoria inválida!', 'warning')
        return redirect(url_for('.home'))
    
    dadosCategorias = getDadosCategorias()
    return render_template('ecommerce/exibeCategoria.html',  dadosItens=dadosItens, autenticado=autenticado, nome=nome, tipoUser=tipoUser, qtdCarrinho=qtdCarrinho, nomeCategoria=nomeCategoria, dadosCategorias=dadosCategorias)
    
#---------------------------------------------------------------------------------------#

@homologacao.route("/login", methods = ['POST', 'GET'])
def login():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    num_cookie = getCookie()
    try:
        int(num_cookie)
    except:
        return redirect(url_for('.home'))

    if 'email' in session:
        flash('Você já está autenticado!', 'info')
        if tipoUser == 'A':
            return redirect(url_for('.admin'))
        else:
            return redirect(url_for('.home'))

    if session['url'] != '.checkout':
        if session['url'] != '.home':
            if session['url'] != '.carrinho':
                session['url'] = '.home'

    if request.method == 'POST':
        autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
        if request.form['btnLogin'] == 'doLogin':
            email = request.form['email']
            password = request.form['password']
            if dadosValidos(email, password):
                num_cookie = getCookie()
                id_cliente = getIdCliente(email)
                altUsr = Carrinho(id_cliente)
                altUsr.assimilaUser(num_cookie)
            
                session['email'] = email
                flash('Autenticado com sucesso!', 'success')    
            
                if 'url' in session:
                    if tipoUser == 'A':
                        return redirect(url_for('.admin'))
                    return redirect(url_for(session['url']))
                if tipoUser == 'A':
                    return redirect(url_for('.admin'))
                else:
                    return redirect(url_for('.home'))
            else:
                flash('Usuário ou senha inválidos!', 'danger')
        else:
            email = request.form['emailF']
            if len(email) == 0:
                flash('E-mail não preenchido!', 'warning')

            if checaEmail(email):
                dados_email = Integracoes()
                email_login, senha_login = dados_email.getDadosAcessoEmail()

                link_site = 'http://homologacao.teste.homo/rs/'
                codigo_user = geraCodigo()

                conteudo = """Redefinição de senha\n
Foi solicitado através de nosso site uma troca de senha. Clique no link abaixo para iniciar os procedimentos de redefinição:\n
%s

OBS: Caso não tenha solicitado esta redefinição, gentileza ignorar este e-mail.

Atenciosamente,
%s
                           """ % (link_site+codigo_user, Parametros(id_param = 2).getParametros()[0][2])
                
                integracao = IntegracaoEmail(email = email_login, senha = senha_login, destinatario = email, assunto = 'Redefinição de senha', conteudo = conteudo)
                
                if integracao.enviarEmail():
                    flash('E-mail enviado com os procedimentos de redefinição de acesso!', 'info')
                    conn = db()
                    conn.execute_bd_com_param('insert into tb_redef_senha (email, codigo, valido, data_hora) values (?, ?, ?, ?)', (email, codigo_user, 'T', datetime.now(tz=tz)))
                    return redirect(url_for('.home'))
                else:
                    flash('Erro ao enviar o e-mail de redefinição de acesso!', 'warning')
            else:
                flash('E-mail não encontrado no sistema!', 'warning')
    nomeLoja = Parametros(id_param = 2).getParametros()[0][2]
    return render_template('ecommerce/login.html')

#---------------------------------------------------------------------------------------#

@homologacao.route("/rs/<codigo>", methods = ['GET', 'POST'])
def redefSenha(codigo):

    if not checaCodigo(codigo):
        return render_template("404.html"), 404

    if request.method == 'POST':
        senha = request.form['newPWD']
        repSenha = request.form['repNewPWD']

        if len(senha) < 6:
            flash("Campo senha deve conter no mínimo 6 caracteres!", 'warning')
            return redirect(url_for("registrar"))

        if senha != repSenha:
            flash("As senhas não coincidem!", 'warning')
            return redirect(url_for("redefSenha", codigo=codigo))

        senha = hashlib.md5(senha.encode()).hexdigest()
        conn = db()
        try:
            email = conn.execute_bd_com_param('select email from tb_redef_Senha where codigo =?', (codigo,))[0][0]
            conn.execute_bd_com_param('update tb_cliente set senha = ? where email = ?', (senha, email))
            conn.execute_bd_com_param('update tb_redef_senha set valido = ? where codigo = ?', ('F', codigo))
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('.login'))
        except:
            flash('Erro ao alterar a senha!', 'warning')
            return redirect(url_for('.login'))

    return render_template('ecommerce/redefsenha.html')

#---------------------------------------------------------------------------------------#

@homologacao.route("/logout")
def logout():
    session['url'] = '.home'
    session.pop('email', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('.home'))

#---------------------------------------------------------------------------------------#

@homologacao.route("/registrar", methods = ['GET', 'POST'])
def registrar():
    if session['url'] != '.checkout':
        session['url'] = '.registrar'
    
    if 'email' not in session:

        if request.method == 'POST':
            num_cookie = getCookie()
            try:
                int(num_cookie)
            except:
                return redirect(url_for('.redir'))
        
            senha = request.form['password']
            email = request.form['email']
            nome = request.form['nome']

            if len(senha) < 6:
                flash("Campo senha deve conter no mínimo 6 caracteres!", 'warning')
                return redirect(url_for("registrar"))

            senha = hashlib.md5(senha.encode()).hexdigest()
        
            conn = db()
            dt_cad = datetime.now(tz=tz)

            query = 'INSERT INTO tb_cliente (senha, email, nome, tipo_acesso,DT_CAD) VALUES (?, ?, ?, ?, ?)'
            dados = (senha, email, nome, 'U', dt_cad)
         
            try:
                data = conn.execute_bd_returnId(query, dados)
                
                if data == None:
                    flash('Erro ao registrar, o e-mail informado já está sendo utilizado!', 'warning')
                    return redirect(url_for("registrar"))

                cart = Carrinho(num_cookie, tipo='visitante')
                cart = cart.getCarrinho()
                if len(cart) != 0:
                    altUsr = Carrinho(data)
                    altUsr.assimilaUser(num_cookie)
                flash("Registrado com sucesso, gentileza autenticar-se!", 'success')
                return redirect(url_for("login"))
            except:
                flash('Erro ao registrar!', 'danger')
                return redirect(url_for("registrar"))
    else:
        return redirect(url_for("login"))
    nomeLoja = Parametros(id_param = 2).getParametros()[0][2]
    return render_template("ecommerce/registrar.html")

#---------------------------------------------------------------------------------------#

@homologacao.route("/perfil", methods = ['GET', 'POST'])
def perfil():
    session['url'] = '.perfil'
    if 'email' not in session:
        flash('Você deve estar autenticado para realizar esta ação!', 'warning')
        return redirect(url_for('.home'))
    
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    email = session['email']
    id_cliente = getIdCliente(email)
    
    if request.method == 'POST':
        if request.form['btnSave'] == 'savePerf':
            nome = request.form['nome']
            sobrenome = request.form['sobrenome']
            cpf = request.form['cpf']
            endereco = request.form['endereco']
            bairro = request.form['bairro']
            cep = request.form['cep']
            cidade = request.form['cidade']
            estado = request.form['estado']
            telefone = request.form['telefone']
            celular = request.form['celular']
            
            try:
                conn = db()
                queryUp = "update tb_cliente set nome = ?, sobrenome = ?, cpf = ?, endereco = ?, bairro = ?, cep = ?, cidade = ?, estado = ?, telefone = ?, celular = ? where id_cliente = ?" 
                dadosUp = (nome, sobrenome, cpf, endereco, bairro, cep, cidade, estado, telefone, celular, id_cliente) 
                conn.execute_bd_com_param(queryUp, dadosUp)
                flash('Dados atualizados com sucesso!', 'success')
                return redirect(url_for('.perfil'))
            except:
                flash('Falha ao atualizar os dados!', 'danger')
                return redirect(url_for('.perfil'))

        elif request.form['btnSave'] == 'savePWD':
            pwdAtual = request.form['PWDA']
            pwdAtual = hashlib.md5(pwdAtual.encode()).hexdigest()
            pwdNova = request.form['PWDN']

            if len(pwdNova) < 6:
                flash('Senha deve conter mais de 6 caracteres!', 'warning')
                return redirect(url_for('.perfil'))

            pwdNova = hashlib.md5(pwdNova.encode()).hexdigest()
            pwdConfirm = request.form['PWDC']
            pwdConfirm = hashlib.md5(pwdConfirm.encode()).hexdigest()

            if pwdNova == pwdConfirm:

                conn = db()
                queryPWD = "SELECT id_cliente, senha FROM tb_cliente WHERE email = ?"
                dadosPWD = (session['email'],)
                
                dadosUser = conn.execute_bd_com_param(queryPWD, dadosPWD)
                for dados in dadosUser:
                    id_cliente = dados[0]
                    senha = dados[1]
                
                if (senha == pwdAtual):
                    try:
                        queryChange = "UPDATE tb_cliente SET senha = ? WHERE id_cliente = ?"
                        dadosChange = (pwdNova, id_cliente)
                        conn.execute_bd_com_param(queryChange, dadosChange)
                        flash('Senha alterada com sucesso!', 'success')
                    except:
                        flash('Erro ao alterar a senha!', 'danger')
                    return redirect(url_for('.perfil'))
                else:
                    flash('Senha incorreta!', 'warning')
                
                return redirect(url_for('.perfil'))

            else:
                flash('Senhas não coincidem!', 'warning')
                return redirect(url_for('.perfil'))
        else:
            user_PicPay = request.form['usr_pp']

            try:
                conn = db()
                queryUp = "update tb_cliente set user_picpay = ? WHERE id_cliente = ?" 
                dadosUp = (user_PicPay, id_cliente) 
                conn.execute_bd_com_param(queryUp, dadosUp)
                flash('Dados atualizados com sucesso!', 'success')
                return redirect(url_for('.perfil'))
            except:
                flash('Falha ao atualizar os dados!', 'danger')
                return redirect(url_for('.perfil'))
    else:
        conn = db()
        queryUser = "SELECT * FROM VW_PERFUSER WHERE email = ?"
        dataUser = (session['email'],)
        dadosPerfil = conn.execute_bd_com_param(queryUser, dataUser)
        dadosCategorias = getDadosCategorias()

    return render_template("ecommerce/perfil.html", dadosPerfil=dadosPerfil, autenticado=autenticado, nome=nome, tipoUser=tipoUser, qtdCarrinho=qtdCarrinho, dadosCategorias=dadosCategorias)

#---------------------------------------------------------------------------------------#

@homologacao.route("/meusPedidos", methods=['GET', 'POST'])
def historicoPedidos():
    session['url'] = '.historicoPedidos'

    num_cookie = getCookie()
    if num_cookie == None:
        return redirect(url_for('.redir'))

    if 'email' not in session:
        flash('Você deve estar autenticado para realizar esta ação!', 'warning')
        return redirect(url_for('.home'))

    email = session['email']
    id_cliente = getIdCliente(email)
    
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if request.method == 'POST':
        id_venda = request.form['idVenda']
        referencia = request.form['OBS']
        dt_hr = datetime.now(tz=tz)
        exibe_web = 'F'

        refs = Referencias(id_cliente = id_cliente, data_hora = dt_hr, comentario = referencia, exibe_web = exibe_web, id_venda = id_venda)
        notifs = Notificacoes(titulo = 'Referência', subtitulo = 'Nova referência recebida', conteudo = 'Você recebeu uma referência, gentileza verificar a rotina para aprovação.', data_hora = datetime.now(tz=tz), tipo_notif = 'edit', visualizado = 'F', categ_notif = 'success', id_venda = None)
        notifs.insereNotificacoes()
        
        if refs.insereReferencias():
            flash('Referências enviadas para aprovação!', 'success')
        else:
            flash('Erro ao enviar referências!', 'warning')
        return redirect(url_for('.historicoPedidos'))

    dadosCategorias = getDadosCategorias()
    venda = Vendas(id_cliente = int(id_cliente))
    pedidos = venda.getVendasCliente()

    return render_template("ecommerce/pedidosCliente.html", autenticado = autenticado, nome = nome, tipoUser=tipoUser, qtdCarrinho = qtdCarrinho, dadosCategorias=dadosCategorias, data = pedidos)
   
@homologacao.route("/meusPedidos/cancelar/<idPedido>", methods = ['GET', 'POST'])
def cancelaPedidosCliente(idPedido):
    email = session['email']
    id_cliente = getIdCliente(email)

    if 'email' not in session:
        flash('Você deve estar autenticado para realizar esta ação!', 'warning')
        return redirect(url_for('.home'))

    vendas = Vendas(id_venda = idPedido, id_cliente = id_cliente)
    venda = vendas.getVendasCliente()

    if len(venda) == 0:
        flash('Número de pedido inválido!', 'warning')
        return redirect(url_for('.historicoPedidos'))

    status = vendas.getStatusVenda()[0][0]

    if int(status) == 3:
        alt = Vendas(id_venda = idPedido, statusVenda = 1)
        
        if alt.alteraStatus():
            flash('Pedido cancelado com sucesso!', 'info')
            cart = Carrinho(id_cliente)
            cart.removeCarrinho()

            conteudo = """Cancelamento de pedido\n
Caro cliente, você acabou de cancelar o pedido de nº %s.
Este e-mail serve como comprovante da ação realizada.

Atenciosamente,
%s
                       """ % (idPedido, Parametros(id_param = 2).getParametros()[0][2])
            dados_email = Integracoes()
            email_login, senha_login = dados_email.getDadosAcessoEmail()
            integracao = IntegracaoEmail(email = email_login, senha = senha_login, destinatario = email, assunto = 'Cancelamento de Pedido', conteudo = conteudo)
            if not integracao.enviarEmail():
                flash('Erro no envio de notificação via e-mail!', 'danger')
        
            if not alt.insereHist(idPedido, 1, datetime.now(tz=tz), 'Pedido cancelado pelo cliente!', None, None):
                flash('Erro ao inserir histórico!', 'danger')
        else:
            flash('Erro ao alterar situação do pedido!', 'danger')
        return redirect(url_for('.historicoPedidos'))
    else:
        flash('Não foi possível cancelar o pedido. O status deve constar como pagamento pendente!', 'warning')
        return redirect(url_for('.historicoPedidos'))

@homologacao.route("/meusPedidos/visualizar/<idPedido>", methods = ['GET', 'POST'])
def historicoPedidosDetalhes(idPedido):

    session['url'] = '.historicoPedidos'

    num_cookie = getCookie()
    if num_cookie == None:
        return redirect(url_for('.redir'))

    if 'email' not in session:
        flash('Você deve estar autenticado para realizar esta ação!', 'warning')
        return redirect(url_for('.home'))

    email = session['email']
    id_cliente = getIdCliente(email)

    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    dadosCategorias = getDadosCategorias()

    vendas = Vendas(id_venda = idPedido, id_cliente = id_cliente)
    venda = vendas.getVendasCliente()
    dados_hist = vendas.getHist()

    histPix = []
    histBol = []
    for dados in dados_hist:
        if dados[5] != None:
            if len(str(dados[5])) != 0:
                histPix.append(vendas.getDadosPix(dados[5]))
        if dados[6] != None:
            if len(str(dados[6])) != 0:
                histBol.append(vendas.getDadosBol(dados[6]))

    if len(venda) == 0:
        flash('Número de pedido inválido!', 'warning')
        return redirect(url_for('.historicoPedidos'))

    dados_prod = vendas.getDetVendasCliente()
   
    forma_pagamento = venda[0][4]
    subt = venda[0][7]
    calcTx = getTaxasValor(float(subt), float(venda[0][5]))
    calcAc = getAcrescimoValor(float(subt), float(calcTx), float(venda[0][6]))

    if venda[0][13] != None:
        banco = venda[0][13] + ' - ' + venda[0][14]
    else:
        banco=  ''
   
    dadosPgto = [forma_pagamento, calcTx, calcAc, banco]

    return render_template("ecommerce/pedidosClienteDet.html", histPix = histPix, histBol = histBol, dados_hist = dados_hist, dados_venda = venda, dados_pgto = dadosPgto, dados_prod = dados_prod, autenticado = autenticado, nome = nome, tipoUser=tipoUser, qtdCarrinho = qtdCarrinho, dadosCategorias=dadosCategorias)

#---------------------------------------------------------------------------------------#
@homologacao.route("/descricaoProduto", methods = ['GET', 'POST'])
def descProduto():
    session['url'] = '.home'

    num_cookie = getCookie()
    if num_cookie == None:
        return redirect(url_for('.redir'))

    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    id_produto = request.args.get('idProduto')

    if request.method == 'POST':
        qtd = int(request.form['rangeInput'])

        prod = Produtos()
        qtdMax = prod.getQtdMax(id_produto)

        if int(qtdMax) == 0:
            flash('Produto indiponível!', 'warning')
            return redirect(url_for('.descProduto', idProduto=id_produto))

        if qtd <= 0:
            flash('Quantidade deve ser maior que 0!', 'warning')
            return redirect(url_for('.descProduto', idProduto=id_produto))

        if int(qtd) > int(qtdMax):
            flash('Quantidade inserida maior que a permitida, quantidade ajustada!', 'warning')
            qtd = qtdMax

        obs = request.form['OBS']
        if 'email' not in session:
            num_cookie = getCookie()
            
            if num_cookie == None:
                return redirect(url_for('.redir'))

            try:
                cart = Carrinho(num_cookie, id_produto, 'visitante', obs, qtd)
                cart.insereCarrinho()
                                
                flash('Produto adicionado ao carrinho', 'info')
            except:
                flash('Erro ao adicionar o produto ao carrinho!', 'danger')
            return redirect(url_for('.home'))
        else:
            conn = db()
        
            queryId = "SELECT id_cliente FROM tb_cliente WHERE email = ?"
            dadosId = (session['email'], )
            resultId = conn.execute_bd_com_param(queryId, dadosId)
        
            for dados in resultId:
                id_cliente = dados[0]

            cart = Carrinho(id_cliente, id_produto, 'autenticado', obs, qtd,)
            if cart.insereCarrinho():
                flash('Produto adicionado ao carrinho', 'info')
            else:
                flash('Erro ao adicionar o produto ao carrinho!', 'danger')
            
            return redirect(url_for('.home'))
    else:
        conn = db()
        
        dadosProd = conn.execute_bd_com_param("SELECT a.id_produto, a.produto, a.preco, a.descricao, b.diretorio, case when a.qtd_max <> '' and a.qtd_max > 0 then a.qtd_max else a.qtd end, A.STEPS FROM tb_produtos a inner join tb_produtos_imagens b on a.id_produto = b.id_produto WHERE a.id_produto = ?", id_produto)
        
        dadosCategorias = getDadosCategorias()
             
        prod = Produtos()
        qtdMax = prod.getQtdMax(id_produto)

        return render_template("ecommerce/descProd.html", dadosProd=dadosProd, autenticado = autenticado, nome = nome, tipoUser=tipoUser, qtdCarrinho = qtdCarrinho, dadosCategorias=dadosCategorias, qtdMax = qtdMax)

#---------------------------------------------------------------------------------------#

@homologacao.route("/carrinho", methods = ['GET', 'POST'])
def carrinho():
    session['url'] = '.carrinho'
    num_cookie = getCookie()
    try:
        int(num_cookie)
    except:
        return redirect(url_for('.redir'))

    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    dadosCategorias = getDadosCategorias()

    if request.method == "POST":
        if request.form['btnFunc'] == 'attCart':
            newQTD = request.form['newQTD']

            if newQTD == 0 or newQTD == None or newQTD.strip() == '':
                flash('A quantidade informada não pode ser 0 ou nulo!', 'warning')
                return redirect(url_for('.carrinho'))

            if not newQTD.isdigit():
                flash('A quantidade deve ser um valor numérico!', 'warning')
                return redirect(url_for('.carrinho'))

            prod = request.form['idProdAtt']
            
            obs = request.form['OBSAtt']

            produtos = Produtos() 
            steps = produtos.getSteps(prod)

            if (int(newQTD) % int(steps)) != 0:
                flash('Quantidade ajustada: produto só pode ser vendido em múltiplos de ' + str(steps) + '!', 'warning')
                mult = round(int(newQTD) / int(steps))
                while (int(newQTD) % int(steps)) != 0:
                    newQTD = mult * int(steps)
                    mult = mult + 1

            if newQTD == '0' or newQTD == 0:
                newQTD = steps

            if autenticado:
                email = session['email']
                id_cliente = getIdCliente(email)
                
                cart = Carrinho(id_cliente = id_cliente, id_produto = prod, tipo = 'autenticado', obs = obs, qtd = newQTD)
                if cart.atualizaCarrinho():
                    flash('Quantidade atualizada com sucesso!', 'info')
                else:
                    flash('Erro ao atualizar quantidade!', 'danger')
            else:
                num_cookie = getCookie()

                cart = Carrinho(num_cookie, prod, 'visitante', obs, newQTD)
                if cart.atualizaCarrinho():
                    flash('Quantidade atualizada com sucesso!', 'info')
                else:
                    flash('Erro ao atualizar quantidade!', 'danger')

        return redirect(url_for('.carrinho'))
    else:
        if autenticado:
            conn=db()

            email = session['email']
            id_cliente = getIdCliente(email)
            
            cart = Carrinho(id_cliente, tipo='autenticado')
            produtos = cart.getCarrinho()

            precoTotal = []
            for x in produtos:
                precoTotal.append(float(x[5]))
            precoTotal = "%.2f" % sum(precoTotal)

        else:
            conn = db()

            num_cookie = getCookie()

            cart = Carrinho(id_cliente=num_cookie, tipo='visitante')
            produtos = cart.getCarrinho()

            precoTotal = []
            for x in produtos:
                precoTotal.append(float(x[5]))
            precoTotal = "%.2f" % sum(precoTotal)

    return render_template("ecommerce/carrinho.html", produtos = produtos, precoTotal=precoTotal, autenticado=autenticado, nome=nome, tipoUser=tipoUser, qtdCarrinho=qtdCarrinho, dadosCategorias=dadosCategorias)

@homologacao.route("/getValorCarrinho", methods=['POST'])
def attVlrCart():
    if request.method == "POST":
          result=request.get_json()
          result = result[0]
          result = result.get('data')
          
          idProd = result[0]
          qtd = result[1]

          valor = getValorProduto(idProd, qtd)

    return jsonify(valor)

@homologacao.route("/removerCarrinho")
def removerDoCarrinho():
    id_produto = int(request.args.get('idProduto'))
    obs = request.args.get('OBS')

    if 'email' not in session:
        num_cookie = getCookie()
        try:
            int(num_cookie)
        except:
            return redirect(url_for('.redir'))


        cart = Carrinho(num_cookie, id_produto, 'visitante', obs)
        if cart.removeCarrinho():
            flash('Produto removido do carrinho!', 'info')
        else:
            flash('Erro ao remover produto do carrinho!', 'danger')

    else:
        email = session['email']
        id_cliente = getIdCliente(email)

        cart = Carrinho(id_cliente, id_produto, 'autenticado', obs)

        if cart.removeCarrinho():
            flash('Produto removido do carrinho!', 'info')
        else:
            flash('Erro ao remover produto do carrinho!', 'danger')
    return redirect(url_for('.carrinho'))

#---------------------------------------------------------------------------------------#

@homologacao.route('/checkout/', defaults={'idPedido': None}, methods = ['GET', 'POST'])
@homologacao.route("/checkout/<idPedido>", methods=['GET','POST'])
def checkout(idPedido):
    session['url'] = '.checkout'
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if 'email' not in session:
        session['url'] = '.checkout'
        return redirect(url_for('.login'))
    else:
        email = session['email']
        id_cliente = getIdCliente(email)

    if idPedido == None:
        verCart = Carrinho(id_cliente = id_cliente, tipo = 'autenticado')
        verCart = verCart.getCarrinho()
        if len(verCart) == 0:
            flash('Você não possui itens no carrinho!', 'warning')
            return redirect(url_for('.home'))
        session['idPedido'] = None
    else:
        detPedido = Vendas(id_venda=idPedido)
        detPedido = detPedido.getDetVendas()
        if len(detPedido) == 0:
            flash('Este pedido não possui itens!', 'warning')
            return redirect(url_for('.home'))
    
        vendas = Vendas(id_venda = idPedido, id_cliente = id_cliente)
        venda = vendas.getVendasCliente()            
        if len(venda) == 0:
            flash('Número de pedido inválido!', 'warning')
            return redirect(url_for('.home'))
        session['idPedido'] = idPedido
            
    if request.method == 'POST':
        if request.form['btnConfirm'] == 'avancaDet':
            session['formaPgto'] = request.form['selectFormaPgto']
            
            if int(session['formaPgto']) == 3 or int(session['formaPgto']) == 4:
                return redirect(url_for('.checkoutGetBanco'))
            else:
                return redirect(url_for('.checkoutDetalhes'))  
    else:                
        formas = FormasPgto(visivel='T', situacao='A')
        lstFormaPgto = formas.getFormasPgto()
        dadosCategorias = getDadosCategorias()
        return render_template("checkout/checkout_formaPgto.html", lstFormaPgto=lstFormaPgto, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dadosCategorias = dadosCategorias)

@homologacao.route('/checkout/listaBancos/', methods = ['GET', 'POST'])
def checkoutGetBanco():
    session['url'] = '.checkout'
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if 'email' not in session:
        session['url'] = '.checkout'
        return redirect(url_for('.login'))
    else:
        email = session['email']
        id_cliente = getIdCliente(email)
        
    if 'formaPgto' not in session:
        return redirect(url_for('.checkout'))
        
    if request.method == 'POST':
        if request.form['btnConfirm'] == 'avancaDet2':
            session['tipoBanco'] = request.form['optBanco']
            return redirect(url_for('.checkoutDetalhes'))
        else:
            return redirect(url_for('.checkout'))
    else:  
        lstBancos = FormasPgto(session['formaPgto'])
        lstBancos = lstBancos.getBancosForma()

        dadosCategorias = getDadosCategorias()

    return render_template("checkout/checkout_slctBanco.html", lstBancos=lstBancos, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dadosCategorias = dadosCategorias)
       
@homologacao.route('/checkout/completaDados/<complemento>', methods = ['GET', 'POST'])
def checkoutCompletaDados(complemento):
    session['url'] = '.checkout'
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if 'email' not in session:
        session['url'] = '.checkout'
        return redirect(url_for('.login'))
    else:
        email = session['email']
        id_cliente = getIdCliente(email)
        
    if 'formaPgto' not in session:
        return redirect(url_for('.checkout'))

    perf = Perfil(id_cliente = id_cliente, id_formaPgto = session['formaPgto'])
    retorno_validacao_perfil, completa_dados = perf.validaPerfilCheckout()

    if complemento != completa_dados:
        flash('Os dados enviados na requisição são inválidos!', 'warning')
        return redirect(url_for('.checkout'))

    if request.method == 'POST':
        if request.form['btnConfirm'] == 'avancaDet':
            conn =db()

            if complemento == 'picpay':
                user_picpay = request.form['usr_picpay']
                conn.execute_bd_com_param('update tb_cliente set user_picpay = ? where id_cliente = ?', (user_picpay, id_cliente))

            elif complemento == 'nomeCompleto':
                nome_cli = request.form['nome_cli']
                sobrenome_cli = request.form['sobrenome_cli']
                conn.execute_bd_com_param('update tb_cliente set nome = ?, sobrenome = ? where id_cliente = ?', (nome_cli, sobrenome_cli, id_cliente))

            return redirect(url_for('.checkoutDetalhes'))
        else:
            return redirect(url_for('.checkout'))
    else:
        dadosCategorias = getDadosCategorias()

        return render_template("checkout/checkout_completeDados.html", tipo_form = complemento, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dadosCategorias = dadosCategorias)
    
@homologacao.route('/checkout/detalhes/', methods = ['GET', 'POST'])
def checkoutDetalhes():
    session['url'] = '.checkout'
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if 'email' not in session:
        session['url'] = '.checkout'
        return redirect(url_for('.login'))
    else:
        email = session['email']
        id_cliente = getIdCliente(email)
        
    if 'formaPgto' not in session:
        return redirect(url_for('.checkout'))

    perf = Perfil(id_cliente = id_cliente, id_formaPgto = session['formaPgto'])
    retorno_validacao_perfil, completa_dados = perf.validaPerfilCheckout()
    
    if not retorno_validacao_perfil:
        return redirect(url_for('.checkoutCompletaDados', complemento = completa_dados))
        
    if request.method == 'POST':
        if request.form['btnConfirm'] == 'avancaObs':
            return redirect(url_for('.checkoutObs'))
        else:
            return redirect(url_for('.checkout'))
    else:  
        if session['idPedido'] == None:
            produtos, taxas, acrescimo, subtotal, calcTx, calcAc, total = getDadosCheckout(id_cliente, session['formaPgto'])
        else:
            produtos, taxas, acrescimo, subtotal, calcTx, calcAc, total = getDadosPedido(session['idPedido'], session['formaPgto'])
        
        dadosCategorias = getDadosCategorias()

        if session['formaPgto'] == 5 and float(total) < 10:
            flash('A forma de pagamento selecionada é válida apenas para pedidos acima de R$ 10,00!', 'info')
            return redirect(url_for('.checkout', idPedido = session['idPedido']))
    
    return render_template("checkout/checkout_detProd.html", lstProdCart=produtos, autenticado=autenticado, nome=nome, tipoUser=tipoUser, taxas=taxas, calcTx=calcTx, acrescimo=acrescimo, calcAc=calcAc, subtotal=subtotal, total=total, dadosCategorias = dadosCategorias)
 
@homologacao.route('/checkout/inserirObservacoes/', methods = ['GET', 'POST'])
def checkoutObs():
    session['url'] = '.checkout'
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if 'email' not in session:
        session['url'] = '.checkout'
        return redirect(url_for('.login'))
    else:
        email = session['email']
        id_cliente = getIdCliente(email)
        
    if 'formaPgto' not in session:
        return redirect(url_for('.checkout'))
        
    if request.method == 'POST': 
        if request.form['btnConfirm'] == 'finComp':
            session['obsPgto'] = request.form['OBS']
            return redirect(url_for('.checkoutFinalCompra'))
        else:
            return redirect(url_for('.checkoutDetalhes'))
    else:
        dadosCategorias = getDadosCategorias()
    return render_template("checkout/checkout_obs.html", autenticado=autenticado, nome=nome, tipoUser=tipoUser, dadosCategorias = dadosCategorias)
    
@homologacao.route('/checkout/finalizaPedido/')
def checkoutFinalCompra():
    session['url'] = '.checkout'
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if 'email' not in session:
        session['url'] = '.checkout'
        return redirect(url_for('.login'))
    else:
        email = session['email']
        id_cliente = getIdCliente(email)
        
    if 'formaPgto' not in session:
        return redirect(url_for('.checkout'))
        
    if 'tipoBanco' not in session:
        session['tipoBanco'] = None
        
    if session['idPedido'] == None:
        produtos, taxas, acrescimo, subtotal, calcTx, calcAc, total = getDadosCheckout(id_cliente, session['formaPgto'])
    else:
        produtos, taxas, acrescimo, subtotal, calcTx, calcAc, total = getDadosPedido(session['idPedido'], session['formaPgto'])
    
    if request.method == 'GET': 
        
        if session['idPedido'] == None:
            check = Checkout(id_cliente, session['formaPgto'], taxas, acrescimo, subtotal, round(total,2), produtos, session['obsPgto'], 3, datetime.now(tz=tz), session['tipoBanco'])
            resultado_insert_venda, resultado_id_venda = check.insereVenda()
        else:
            pedido = Vendas(id_venda = session['idPedido'])
            if pedido.alteraVenda(session['formaPgto'], taxas, acrescimo, subtotal, round(total,2), session['obsPgto'], datetime.now(tz=tz), session['tipoBanco']):
                resultado_insert_venda = True
                resultado_id_venda = session['idPedido']
                        
        if resultado_insert_venda:
            if int(session['formaPgto']) == 1:
                form = FormasPgto(int(session['formaPgto']))
                nomeForma = form.getFormasPgtoDet()[0][1]
                user = form.getFormasPgtoDet()[0][2]
                idPix = None
                idBol = None
                flash('Pedido cadastrado, gentileza realizar o pagamento no botão abaixo!', 'info') 
                
                tipo_forma_pgto = 'PicPay'
                retorno_checkout = render_template("checkout/checkout_pgto.html", valorPgto = "%.2f" % total, formaPgto=session['formaPgto'], nomeForma=nomeForma, user=user, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
            
            elif int(session['formaPgto']) == 2:
                form = FormasPgto(int(session['formaPgto']))
                nomeForma = form.getFormasPgtoDet()[1]
                flash('Pedido cadastrado, gentileza realizar o PIX com os dados abaixo!', 'info')
                dados_pix = form.getFormasPgtoDet()
                path_imagem = ''
                urlPgto = ''
                payment_code = ''
                retorno_integ = False
                idPix = None
                idBol = None
                      
                integ = Integracoes(id_integracao = 1)
                if integ.getStatusIntegracao() == 'T':
                    dados_integracao = integ.getDadosIntegracaoNubank()
                    retorno_integ, path_imagem, urlPgto, payment_code = True, '4968753683725112021 233325.png', 'https://nubank.com.br/pagar/1d56tk/Wc0FecJD9E', '00020126360014BR.GOV.BCB.PIX0114+551195471670952040000530398654045.255802BR5925Gabriele Dornelas Gomes d6009SAO PAULO61080540900062070503***6304E486'
                    alt = Vendas(id_venda = resultado_id_venda)
                    #if dados_integracao[4] == 'SIM':
                    #    cpf, senha, cert_dir = integ.getDadosAcessoNubank()
                    #    nubank = IntegracaoNubank(cpf = cpf, senha = senha, certificado = cert_dir, valor = total, index_preferencia = dados_pix[6])
                    #    retorno_integ, path_imagem, urlPgto, payment_code = nubank.geraPgtoPix()
                    retorno_inserePix, idPix = alt.insereDadosPix(cod_cc = payment_code, url_banco = urlPgto, dir_qrcode = path_imagem)
                    if retorno_inserePix:
                        idPix = idPix
                    else:
                        flash('Erro ao obter retorno da integração PIX!', 'danger')
                        idPix = None
                    idBol = None

                tipo_forma_pgto = 'PIX'

                data_hoje = datetime.now(tz=tz).strftime("%d/%m/%Y, %H:%M:%S")
                retorno_checkout = render_template("checkout/checkout_pgto.html", data_hoje = data_hoje, payment_code = payment_code, retorno_integ = retorno_integ, qrcode = path_imagem, urlPgto = urlPgto, valorPgto = "%.2f" % total, formaPgto=session['formaPgto'], nomeForma=nomeForma, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dados_pix=dados_pix)
                        
            
            elif int(session['formaPgto']) == 3:
                form = FormasPgto(int(session['formaPgto']))
                nomeForma = form.getFormasPgtoDet()[0][1]
                flash('Pedido cadastrado, gentileza realizar o depósito bancário com os dados abaixo!', 'info')
                dados_lstBanco = form.getBancosForma(session['tipoBanco'])
                idPix = None
                idBol = None
                
                tipo_forma_pgto = 'Depósito Bancário'
                retorno_checkout = render_template("checkout/checkout_pgto.html", valorPgto = "%.2f" % total, formaPgto=session['formaPgto'], nomeForma=nomeForma, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dados_lstBanco=dados_lstBanco)
            
            elif int(session['formaPgto']) == 4:
                form = FormasPgto(int(session['formaPgto']))
                nomeForma = form.getFormasPgtoDet()[0][1]
                flash('Pedido cadastrado, gentileza realizar a transferência bancária com os dados abaixo!', 'info')
                dados_lstBanco = form.getBancosForma(session['tipoBanco'])
                idPix = None
                idBol = None

                tipo_forma_pgto =  'Transferência Bancária'
                retorno_checkout = render_template("checkout/checkout_pgto.html", valorPgto = "%.2f" % total, formaPgto=session['formaPgto'], nomeForma=nomeForma, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dados_lstBanco=dados_lstBanco)
              
            elif int(session['formaPgto']) == 5:
                form = FormasPgto(int(session['formaPgto']))
                nomeForma = form.getFormasPgtoDet()[0][1]
                flash('Pedido cadastrado, gentileza realizar o pagamento do boleto com os dados abaixo!', 'info')
                dados_lstBanco = form.getBancosForma(session['tipoBanco'])
                idPix = None

                integ = Integracoes(id_integracao = 1)
                if integ.getStatusIntegracao() == 'T':
                    alt = Vendas(id_venda = resultado_id_venda)
                    dados_integracao = integ.getDadosIntegracaoNubank()
                    if dados_integracao[4] == 'SIM':
                        cpf, senha, cert_dir = integ.getDadosAcessoNubank()
                        nubank = IntegracaoNubank(cpf = cpf, senha = senha, certificado = cert_dir, valor = total)
                        retorno_bol, num_bol = nubank.geraPgtoBoleto()
                        if retorno_bol:
                            retorno_insereBol, id_boleto = alt.insereDadosBoleto(num_bol = num_bol, valor_bol = total, dt_geracao = datetime.now(tz=tz), dt_pgto = None)         
                            if retorno_insereBol:
                                idBol = id_boleto
                            else:
                                flash('Erro ao gerar informações do boleto!', 'warning')
                        else:
                            flash('Erro ao obter dados de integração!', 'warning')
                            idBol = None

                tipo_forma_pgto =  'Boleto Bancário'
                retorno_checkout = render_template("checkout/checkout_pgto.html", data_hoje = datetime.now(tz=tz).strftime("%d/%m/%Y, %H:%M:%S"), num_bol = num_bol, valorPgto = "%.2f" % total, formaPgto=session['formaPgto'], nomeForma=nomeForma, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dados_lstBanco=dados_lstBanco)

            if session['idPedido'] == None:
                notifs = Notificacoes(titulo = 'Novo pedido', subtitulo = 'Pedido aguardando pagamento - ' + str(tipo_forma_pgto), conteudo = 'Novo pedido cadastrado (cód.: ' + str(resultado_id_venda) + ') - Cliente: '+ str(getNomeCliente(id_cliente)) + ' Total: R$' + str("%.2f" % total) + ' Observações: ' + session['obsPgto'], data_hora = datetime.now(tz=tz), tipo_notif = 'money', visualizado = 'F', categ_notif = 'success', id_venda = resultado_id_venda)                     
            else:
                notifs = Notificacoes(titulo = 'Pedido ' + str(session['idPedido']), subtitulo = 'Pedido aguardando pagamento - ' + str(tipo_forma_pgto), conteudo = 'Pedido renovado (cód.: ' + str(session['idPedido']) + ') - Cliente: '+ str(getNomeCliente(id_cliente)) + ' Total: R$' + str("%.2f" % total) + ' Observações: ' + session['obsPgto'], data_hora = datetime.now(tz=tz), tipo_notif = 'money', visualizado = 'F', categ_notif = 'success', id_venda = session['idPedido'])
            
            pedido = Vendas()
            if session['idPedido'] == None or session['idPedido'] == '':
                id_pedidoVenda = resultado_id_venda            
            else:
                id_pedidoVenda = session['idPedido']

            if session['idPedido'] == None:
                try:
                    pedido.insereHist(id_pedidoVenda, 3, datetime.now(tz=tz), 'Pedido cadastrado!', idPix, idBol)
                except:
                    flash('Erro ao inserir dados no histórico do pedido!', 'danger')
            else:
                try:
                    pedido.insereHist(id_pedidoVenda, 3, datetime.now(tz=tz), 'Pedido atualizado', idPix, idBol)
                except:
                    flash('Erro ao inserir dados no histórico do pedido!', 'danger')

            try:
                notifs.insereNotificacoes()
            except:
                flash('Erro ao criar notificação do pedido!', 'danger')

            conteudo = """Cadastro de novo pedido\n
Caro cliente, você acabou de cadastrar um pedido em nossa loja. O processamento ocorrerá assim que o pagamento for confirmado.
Este e-mail serve como comprovante da ação realizada.

Acompanhe seu pedido através do link: %s

Detalhes:

Nº do pedido: %s
Data do pedido: %s
Forma de Pagamento: %s
E-mail: %s
Status: %s
Valor: R$%s

Atenciosamente,
%s
                       """ % ('http://homologacao.teste.homo/meusPedidos/visualizar/'+str(session['idPedido']),session['idPedido'], datetime.now(tz=tz).strftime("%d/%m/%Y, %H:%M:%S"), tipo_forma_pgto, email, 'Pedido aguardando pagamento', total, Parametros(id_param = 2).getParametros()[0][2])
            dados_email = Integracoes()
            email_login, senha_login = dados_email.getDadosAcessoEmail()
            integracao = IntegracaoEmail(email = email_login, senha = senha_login, destinatario = email, assunto = 'Cadastro de Pedido', conteudo = conteudo)
            if not integracao.enviarEmail():
                flash('Erro no envio de notificação via e-mail!', 'danger')

            session.pop('idPedido', None)
            session.pop('formaPgto', None)
            session.pop('tipoBanco', None)
            session.pop('obsPgto', None)

            return retorno_checkout
            
        else:
            flash('Erro ao avançar na compra!', 'danger')
            return redirect(url_for('.checkout'))

#---------------------------------------------------------------------------------------#

@homologacao.route("/politicas/cookies")
def politicasCookies():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    dadosCategorias = getDadosCategorias()
    return render_template('politicas/cookies.html', nome=nome, tipoUser=tipoUser, dadosCategorias = dadosCategorias)

@homologacao.route("/politicas/privacidade")
def politicasPrivacidade():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    dadosCategorias = getDadosCategorias()
    return render_template('politicas/privacidade.html', nome=nome, tipoUser=tipoUser, dadosCategorias = dadosCategorias)

#---------------------------------------------------------------------------------------#

@homologacao.route("/referencias/")
def referencias():
    ativa_referencia = Parametros(id_param = '10').getParametros()[0][2]
    if ativa_referencia == 'NÃO':
        return render_template("404.html"), 404

    session['url'] = '.referencias'
    num_cookie = getCookie()
    try:
        int(num_cookie)
    except:
        return redirect(url_for('.redir'))

    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    dadosCategorias = getDadosCategorias()

    refs = Referencias()
    refs = refs.getReferenciasWeb()

    return render_template("ecommerce/referencias.html", referencias = refs, qtdCarrinho=qtdCarrinho, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dadosCategorias = dadosCategorias)

#---------------------------------------------------------------------------------------#

                          #---------------------------------------------------------------------------------------#
                          #                                                                                       #
                          #------------------------------------PAINEL ADMIN---------------------------------------#
                          #                                                                                       #
                          #---------------------------------------------------------------------------------------#

#---------------------------------------------------------------------------------------#
                          
@homologacao.route("/painelAdmin")
def admin():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        locale.setlocale(locale.LC_ALL, 'pt-BR')

        data = Vendas()
        vendasDia = "%.2f" % data.getVendasDia()[0]
        vendasMes = "%.2f" % data.getVendasMes()[0]
        receberMes = "%.2f" % data.getReceberMes()[0]

        hoje = date.today()

        qtdMes = []
        nomeMes = []
        valorRecebidoMes = []
        valorReceberMes = []

        for i in range(0,6):
           mesCons = (hoje - relativedelta(months=i)).strftime('%m/%Y')
           nomeMesCons = (hoje - relativedelta(months=i)).strftime('%B')
           qtd = data.getQtdVendas(mesCons)[0]
           valoresMes = "%.2f" % data.getVendasMes(mesCons)[0]
           valoresARecMes = "%.2f" % data.getReceberMes(mesCons)[0]

           valorRecebidoMes.append(valoresMes)
           qtdMes.append(qtd)
           nomeMes.append(nomeMesCons)
           valorReceberMes.append(valoresARecMes)

        qtdMes = json.dumps(qtdMes[::-1])
        nomeMes = json.dumps(nomeMes[::-1])
        valorRecebidoMes = json.dumps(valorRecebidoMes[::-1])
        valorReceberMes = json.dumps(valorReceberMes[::-1])
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]

        return render_template("dashboard/visGeral.html", autenticado=autenticado, nome=nome, tipoUser=tipoUser, vendasDia = vendasDia, vendasMes = vendasMes, receberMes = receberMes, nomeMes=nomeMes, qtdMes=qtdMes, valorRecebidoMes=valorRecebidoMes, valorReceberMes=valorReceberMes)
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/cadastro/clientes")
def exibeCliente():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        cli = Clientes()
        clientes = cli.getClientes()
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        
        return render_template("cadastro/clientes/cad_cliCons.html", data = clientes, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/clientes/visualizar/<idCliente>")
def visCliente(idCliente):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    if tipoUser == 'A':
        cli = Clientes(idCliente)
        clientes = cli.getClientes()
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]

        return render_template("cadastro/clientes/cad_cliVis.html",  dados_cli=clientes, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/cadastro/categorias")
def exibeCategoria():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        categ = Categorias()
        categorias = categ.getCategoria()

        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        
        return render_template("cadastro/categorias/cad_categCons.html", data=categorias, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/categorias/inserir", methods = ['GET', 'POST'])
def addCategoria():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            categoria = request.form['categ']
            exibe_web = request.form['exibeWEB']

            if exibe_web == 'True':
                exibe_web = 'T'
            else:
                exibe_web = 'F'

            categ = Categorias(categoria, exibe_web)
            if categ.insereCategoria():
                flash('Categoria adicionada com sucesso!', 'success')
                return redirect(url_for('.addCategoria'))
            else:
                flash('Erro ao inserir categoria!', 'danger')
        
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        return render_template("cadastro/categorias/cad_categAdd.html", autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/categorias/visualizar/<idCategoria>")
def visCategoria(idCategoria):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    if tipoUser == 'A':
        categ = Categorias()
        dados_categ = categ.getCategoria(idCategoria)
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]

        return render_template("cadastro/categorias/cad_categVis.html", dados_categ=dados_categ, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/categorias/editar/<idCategoria>", methods = ['GET', 'POST'])
def upCategoria(idCategoria):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            categ = request.form['categ']
            exibe_web = request.form['exibeWEB']

            if exibe_web == 'True':
                exibe_web = 'T'
            else:
                exibe_web = 'F'

            attCateg = Categorias(categ, exibe_web)

            attCateg.alteraCategoria(idCategoria)
            flash('Dados alterados com sucesso!', 'info')
            return redirect(url_for('.upCategoria', idCategoria=idCategoria))
        else:
            categ = Categorias()
            dados_categ = categ.getCategoria(idCategoria)
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        return render_template("cadastro/categorias/cad_categEdit.html", dados_categ=dados_categ, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/categorias/remover/<idCateg>")
def remCategoria(idCateg):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        cat = Categorias()
        if cat.removeCategoria(idCateg):
            flash('Categoria removida com sucesso!', 'success')
        else:
            flash('Erro ao remover: existe(m) produto(s) cadastrado com esta categoria!', 'danger')
        return redirect(url_for('.exibeCategoria'))
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/cadastro/produtos")
def exibeProduto():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        prod = Produtos()
        produtos = prod.getProduto()
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]

        return render_template("cadastro/produtos/cad_prodCons.html", data=produtos, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/produtos/inserir", methods = ['GET', 'POST'])
def addProduto():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            produto = request.form['prod']
            descricao = request.form['desc']
            quantidade = request.form['qtd']
            valor = request.form['vlr']
            categoria = request.form['categ']
            incremento = request.form['incremento']
            exibeWeb = request.form['exibeWEB']
            exibeVlr = request.form['exibeValorWEB']
            qtdMax = request.form['qtdMax']

            image = request.files['image']

            if image.filename == '':
                imagename = 'box.png'
            else:
                if image and allowed_file(image.filename):
                    basedir = os.path.abspath(os.path.dirname(__file__))
                    filename = secure_filename(image.filename)
                    full_file = os.path.join(basedir, UPLOAD_FOLDER, filename)
                    image.save(full_file)
                    imagename = filename
                else:
                    flash('Imagem em formato inválido!', 'warning')
                    return redirect(url_for('.addProduto'))

            if incremento == '':
                incremento = None

            if exibeWeb == 'SIM':
                exibeWeb = 'T'
            elif exibeWeb == 'NAO':
                exibeWeb = 'F'
            else:
                flash('Valor inválido para o campo Exibe na WEB', 'warning')
                return redirect(url_for('.addProduto'))

            if exibeVlr == 'SIM':
                exibeVlr = 'T'
            elif exibeVlr == 'NAO':
                exibeVlr = 'F'
            else:
                flash('Valor inválido para o campo Exibe Valor na WEB', 'warning')
                return redirect(url_for('.addProduto'))

            if qtdMax == '':
                qtdMax = 0

            prod = Produtos(produto)
            if prod.insereProduto(descricao, quantidade, valor, categoria, incremento, exibeWeb, exibeVlr, qtdMax):
                conn = db()
                id_produto = conn.execute_bd('select max(id_produto) from tb_produtos', 'O')

                conn.execute_bd_com_param('insert into tb_produtos_imagens (id_produto, diretorio, principal) values (?, ?, ?)', (id_produto[0], imagename, 'T'))
                flash('Produto adicionado com sucesso!', 'success')
                return redirect(url_for('.addProduto'))
            else:
                flash('Erro ao inserir produto!', 'danger')
        
        categ = Categorias()
        categorias = categ.getCategoria()

        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        
        return render_template("cadastro/produtos/cad_prodAdd.html", dados_categ = categorias, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/produtos/visualizar/<idProduto>")
def visProduto(idProduto):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    if tipoUser == 'A':
        prod = Produtos()
        dados_prod = prod.getProduto(idProduto)

        categ = Categorias()
        categProd = categ.getCategoriaProduto(idProduto)

        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        return render_template("cadastro/produtos/cad_prodVis.html", dados_prod=dados_prod, categProd=categProd, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/produtos/editar/<idProduto>", methods = ['GET', 'POST'])
def upProduto(idProduto):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            produto = request.form['prod']
            descricao = request.form['desc']
            quantidade = request.form['qtd']
            valor = request.form['vlr']
            categoria = request.form['categ']
            incremento = request.form['incremento']
            exibeWeb = request.form['exibeWEB']
            exibeVlr = request.form['exibeValorWEB']
            qtdMax = request.form['qtdMax']
            image = request.files['image']

            if image.filename == '':
                conn = db()
                imagename = conn.execute_bd_com_param("SELECT diretorio FROM tb_produtos_imagens where id_produto = ? and principal = 'T'", (idProduto,))[0][0]
            else:
                if image and allowed_file(image.filename):
                    basedir = os.path.abspath(os.path.dirname(__file__))
                    filename = secure_filename(image.filename)
                    full_file = os.path.join(basedir, homologacao.config['UPLOAD_FOLDER'], filename)
                    image.save(full_file)
                    imagename = filename
                else:
                    flash('Imagem em formato inválido!', 'warning')
                    return redirect(url_for('.addProduto'))

            if incremento == '':
                incremento = None

            if exibeWeb == 'SIM':
                exibeWeb = 'T'
            elif exibeWeb == 'NAO':
                exibeWeb = 'F'
            else:
                flash('Valor inválido para o campo Exibe na WEB', 'warning')
                return redirect(url_for('.addProduto'))

            if exibeVlr == 'SIM':
                exibeVlr = 'T'
            elif exibeVlr == 'NAO':
                exibeVlr = 'F'
            else:
                flash('Valor inválido para o campo Exibe Valor na WEB', 'warning')
                return redirect(url_for('.addProduto'))

            if qtdMax == '':
                qtdMax = 0

            if int(qtdMax) > int(quantidade):
                qtdMax = quantidade

            prod = Produtos()
            if prod.alteraProduto(idProduto, produto, descricao, quantidade, valor, categoria, incremento, exibeWeb, exibeVlr, qtdMax):
                conn = db()
                conn.execute_bd_com_param("update tb_produtos_imagens set diretorio = ? where id_produto = ? and principal = 'T'", (imagename, idProduto))
                flash('Produto atualizado com sucesso!', 'success')
            else:
                flash('Erro ao atualizar produto!', 'danger')

            return redirect(url_for('.exibeProduto', idProduto=idProduto))
        else:
            prod = Produtos()
            dados_prod = prod.getProduto(idProduto)

            categ = Categorias()
            categorias = categ.getCategoria()

            categProd = categ.getCategoriaProduto(idProduto)
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        return render_template("cadastro/produtos/cad_prodEdit.html", dados_prod=dados_prod, dados_categ = categorias, categProd = categProd, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/produtos/remover/<idProd>")
def remProduto(idProd):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        prod = Produtos()
        if prod.removeProduto(idProd):
            flash('Produto removido com sucesso!', 'success')
        else:
            flash('Erro ao remover: este produto já foi registrado nas vendas!', 'danger')
        return redirect(url_for('.exibeProduto'))
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/cadastro/tabelaPrecos")
def exibeTabPreco():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        tab = Tabelas()
        tabelas = tab.getTabelaPrecos()
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        return render_template("cadastro/tabelaPrecos/cad_tabprecoCons.html", data=tabelas, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/tabelaPrecos/inserir", methods = ['GET', 'POST'])
def addTabPreco():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            idProduto = request.form['idProd']
            situacao = request.form['situacao']
            form = request.form
            faixaPreco = []
            for key, value in form.items():
                if key.startswith("cell"):
                    faixaPreco.append(value)

            faixas = [faixaPreco[i:i + 3] for i in range(0, len(faixaPreco), 3)]
            
            tab = Tabelas()
            resultadoInsert, idInsert = tab.insereTabela(idProduto, situacao)
            if idInsert != None:

                if tab.insereFaixas(idInsert, faixas):
                    flash('Faixas de preço da tabela cadastradas com sucesso!', 'success')
                else:
                    flash('Erro ao cadastrar faixas de preço na tabela!', 'erro')
                    return redirect(url_for('.exibeTabPreco'))

                flash('Tabela de preço inserida com sucesso!', 'success')
            else:

                flash('Erro ao inserir tabela de preço', 'danger')

            return redirect(url_for('.exibeTabPreco'))
        else:
            prod = Produtos()
            dados_prod = prod.getProduto()

            tab = Tabelas()
            tabelas = tab.getTabelaPrecos()
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
            return render_template("cadastro/tabelaPrecos/cad_tabprecoAdd.html", dados_prod=dados_prod, data=tabelas, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/tabelaPrecos/visualizar/<idTabPreco>")
def visTabPreco(idTabPreco):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        tab = Tabelas()
        dados_tabPreco = tab.getTabelaPrecos(idTabPreco)
        dados_faixa = tab.getFaixas(idTabPreco)

        prod = Produtos()
        dados_prod = prod.getProduto()
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        return render_template("cadastro/tabelaPrecos/cad_tabprecoVis.html", dados_faixa=dados_faixa, dados_prod=dados_prod, dados_tabPreco=dados_tabPreco, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/tabelaPrecos/editar/<idTabPreco>", methods = ['GET', 'POST'])
def upTabPreco(idTabPreco):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            situacao = request.form['situacao']
            attTab = Tabelas()

            attTab.alteraTabela(idTabPreco, situacao)
            attTab.removeFaixas(idTabPreco)

            form = request.form
            faixaPreco = []
            for key, value in form.items():
                if key.startswith("cell"):
                    faixaPreco.append(value)

            faixas = [faixaPreco[i:i + 3] for i in range(0, len(faixaPreco), 3)]

            if attTab.insereFaixas(idTabPreco, faixas):
                flash('Tabela alterada com sucesso!', 'success')
            else:
                flash('Erro ao alterar tabela', 'danger')
            return redirect(url_for('.exibeTabPreco'))
        else:
            tab = Tabelas()
            dados_tabPreco = tab.getTabelaPrecos(idTabPreco)
            dados_faixa = tab.getFaixas(idTabPreco)
           
            prod = Produtos()
            dados_prod = prod.getProduto()
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
            return render_template("cadastro/tabelaPrecos/cad_tabprecoEdit.html", dados_faixa=dados_faixa, dados_prod=dados_prod, dados_tabPreco=dados_tabPreco, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/cadastro/tabelaPrecos/remover/<idTabPreco>")
def remTabPreco(idTabPreco):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        tab = Tabelas()
        if tab.removeTabelaPrecos(idTabPreco):
            flash('Tabela de preços e faixas removidas com sucesso!', 'success')
        else:
            flash('Erro ao remover tabela de preços e faixas!', 'danger')
        return redirect(url_for('.exibeTabPreco'))
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/formasPgto")
def formasPagamento():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    if tipoUser == 'A':
        formas = FormasPgto()
        formas = formas.getFormasPgto()
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        return render_template("formasPgto/formasPgtoCons.html", dadosFormas = formas, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/formasPgto/editar/<idFormaPgto>", methods = ['GET', 'POST'])
def upFormasPgto(idFormaPgto):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    form = FormasPgto(idFormaPgto)
    form = form.getFormasPgto()
    if len(form) != 0:
        if form[0][3] == 'SIM':
            flash('Opção não disponível para forma de pagamento integrada!', 'warning')
            return redirect(url_for('.formasPagamento'))
    else:
        flash('Forma de pagamento inválida!', 'warning')
        return redirect(url_for('.formasPagamento'))

    if tipoUser == 'A':
        if request.method == 'POST':
            if int(idFormaPgto) == 1:
                exibeWeb = request.form['exibeCheck']
                acres = request.form['acres']
                user = request.form['usrPicPay']
                observacao = request.form['OBS']

                if exibeWeb == 'True':
                    exibeWeb = 'T'
                else:
                    exibeWeb = 'F'

                form = FormasPgto(idFormaPgto)

                if form.alteraFormaPgto(exibe_web = exibeWeb, acrescimo = acres, usuario = user, obs = observacao):
                    flash('Dados alterados com sucesso!', 'success')
                else:
                    flash('Erro ao alterar dados da forma de pagamento!', 'danger')
            elif int(idFormaPgto) == 2:
                exibeWeb = request.form['exibeCheck']
                celular = request.form['tel']
                cpf = request.form['cpf']
                email = request.form['email']

                if exibeWeb == 'True':
                    exibeWeb = 'T'
                else:
                    exibeWeb = 'F'

                form = FormasPgto(idFormaPgto)

                if form.alteraFormaPgto(exibe_web = exibeWeb, celular = celular, cpf = cpf, email = email):
                    flash('Dados alterados com sucesso!', 'success')
                else:
                    flash('Erro ao alterar dados da forma de pagamento!', 'danger')

            elif int(idFormaPgto) == 3 or int(idFormaPgto) == 4:
                exibeWeb = request.form['exibeCheck']
                attBanco = FormasPgto(idFormaPgto)

                if not attBanco.alteraFormaPgto(exibe_web = exibeWeb):
                    flash('Erro ao atualizar os dados!', 'danger')
                    return redirect(url_for('.upFormasPgto', idFormaPgto = idFormaPgto))

                attBanco.removeBancos()
                
                form = request.form
                lstBancos = []
                lstFav = []

                for key, value in form.items():
                    if key.startswith("cell"):
                        lstBancos.append(value)
                    if key.startswith("ocell"):
                        lstFav.append(value)

                faixas = [lstBancos[i:i + 6] for i in range(0, len(lstBancos), 6)]
                favs = [lstFav[i:i + 2] for i in range(0, len(lstFav), 2)]

                i = 0
                for faixa in faixas:
                    faixa.append(favs[i][0])
                    faixa.append(favs[i][1])
                    i = i + 1

                if attBanco.insereFaixas(faixas):
                    flash('Dados atualizados com sucesso!', 'success')
                else:
                    flash('Erro ao atualizar os dados!', 'danger')
                return redirect(url_for('.formasPagamento'))
            else:
                return redirect(url_for('.formasPagamento'))
        else:
            forma = FormasPgto(int(idFormaPgto))
            formas = forma.getFormasPgtoDet()

            lstBanco = Bancos()
            bancos = lstBanco.getBancos()
            operacoes = lstBanco.getOperacoes()

            dados_lstBanco = forma.getBancosForma()
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
            return render_template("formasPgto/formasPgtoEdit.html", dadosFormas = formas, autenticado=autenticado, nome=nome, tipoUser=tipoUser, dados_lstBanco=dados_lstBanco, lstBancos = bancos, lstOp = operacoes)
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/integracoes")
def integracoes():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    if tipoUser == 'A':
        integ = Integracoes()
        integracoes = integ.getIntegracoes()
        notificacoes = Notificacoes()
        qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
        return render_template("integracoes/integracoes.html", integracoes = integracoes, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/integracoes/<idIntegracao>", methods = ['GET', 'POST'])
def integracoesEdit(idIntegracao):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    if tipoUser == 'A':
        if int(idIntegracao) == 1:
            webPage = 'integracoes/integracoesNubank.html'

        if int(idIntegracao) == 2:
            webPage = 'integracoes/integracoesEmail.html'

        if request.method == 'POST':
            if int(idIntegracao) == 1:
                if request.form['btnSave'] == 'saveInteg':
                    cert_dir = request.files['certDir']
                    cpf = request.form['cpf']
                    senha = request.form['senha']

                    if len(cpf) == 0:
                        flash('Gentileza inserir o CPF (apenas números)!', 'warning')
                        return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))

                    if len(senha) == 0:
                        flash('Gentileza inserir a senha!', 'warning')
                        return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))
                    
                    if cert_dir.filename == '':
                        flash('Diretório do certificado não foi preenchido!', 'warning')
                        return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))
                    else:
                        if cert_dir and allowed_file_cert(cert_dir.filename):
                            basedir = os.path.abspath(os.path.dirname(__file__))
                            filename = secure_filename(cert_dir.filename)
                            full_file = os.path.join(basedir, UPLOAD_FOLDER_CERTIFICADO, filename)
                            cert_dir.save(full_file)
                        else:
                            flash('Certificado possui um formato inválido!', 'warning')
                            return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))
                    
                    integracao = IntegracaoNubank(cpf, senha, full_file)
                    if integracao.testaConexao():
                        key = Fernet.generate_key()
                        fernet = Fernet(key)
                        encCPF = fernet.encrypt(cpf.encode())
                        encPWD = fernet.encrypt(senha.encode())
                    
                        integracao = Integracoes(id_integracao = idIntegracao, dir_cert = filename, cpf = encCPF, senha = encPWD, key = key)
                        if integracao.alteraAcessoNubank():
                            flash('Dados de acesso alterados com sucesso!', 'success')              
                        else:
                            flash('Erro ao alterar dados!', 'warning')
                    else:
                        flash('Credenciais do Nubank inválidas!', 'warning')
                    return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))

                elif request.form['btnSave'] == 'saveParam':
                    ativa_integracao = request.form['ativaInteg']
                    pix = request.form['propagaPix']
                    banco = request.form['verBanc']
                    boleto = request.form['ativaBol']
                    chave_preferencial = request.form['prefKey']

                    integracao = Integracoes(id_integracao = idIntegracao, status_integracao = ativa_integracao, propagar_pix = pix, propagar_banco = banco, utiliza_boleto = boleto, chave_preferencial = chave_preferencial)
                    if integracao.alteraParamNubank():
                        flash('Parâmetros alterados com sucesso!', 'success')              
                    else:
                        flash('Erro ao alterar parâmetros!', 'warning')
                    return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))

            elif int(idIntegracao) == 2:
                provedorMail = request.form['provedor']
                emailUser = request.form['mail']
                senhaMail = request.form['pwd']

                if len(emailUser) == 0:
                    flash('Gentileza inserir o email!', 'warning')
                    return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))
                
                if len(senhaMail) == 0:
                    flash('Gentileza inserir a senha!', 'warning')
                    return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))
                
                integracao = IntegracaoEmail(email = emailUser, senha = senhaMail)
                if integracao.testaConexao():
                    key = Fernet.generate_key()
                    fernet = Fernet(key)
                    senhaMail = fernet.encrypt(senhaMail.encode())
                    
                    integracao = Integracoes(id_integracao = idIntegracao, key = key, email_integ = emailUser, senha_email = senhaMail, id_provedor = provedorMail)
                    
                    if integracao.alteraDadosEmail():
                        flash('Dados alterados com sucesso!', 'success')              
                    else:
                        flash('Erro ao alterar os dados!', 'warning')
                else:
                    flash('Erro ao validar a conexão. Gentileza verificar os dados inseridos!', 'warning')
                return redirect(url_for('.integracoesEdit', idIntegracao = idIntegracao))
        else:
            dados_integracao = Integracoes(idIntegracao)
            status_integ = dados_integracao.getStatusIntegracao()
            if int(idIntegracao) == 1: 
                dados_integ = dados_integracao.getDadosIntegracaoNubank()
                dados_email = []
            elif int(idIntegracao) ==2:
                dados_integ = dados_integracao.getDadosIntegracaoEmail()
                dados_email = dados_integracao.getListaEmail()
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
            return render_template(webPage, dados_email = dados_email, dados_integ = dados_integ, status_integ = status_integ, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route('/painelAdmin/financeiro/vendas', defaults={'idCliente': None} , methods = ['GET', 'POST'])
@homologacao.route("/painelAdmin/financeiro/vendas/<idCliente>", methods = ['GET', 'POST'])
def exibeVendas(idCliente):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            idVenda = request.form['idVenda']
            newStatus = request.form['statusVenda']

            alt = Vendas(id_venda = idVenda, statusVenda = newStatus)
            status_atual = alt.getStatusVenda()[0][0]
            if int(status_atual) != int(newStatus):
                if alt.alteraStatus():
                    flash('Situação da venda alterada com sucesso!', 'success')
                
                    if int(newStatus) == 0:
                        cart = Carrinho(getIdClientePorVenda(idVenda))
                        cart.removeCarrinho()
                
                    if not alt.insereHist(idVenda, newStatus, datetime.now(tz=tz), 'Situação do pedido alterada: ' + alt.getNomeStatus(status_venda = status_atual) + ' -> ' + alt.getNomeStatus(), None, None):
                        flash('Erro ao inserir histórico!')

                    conteudo = """Atualização do status do pedido\n
Caro cliente, o status do pedido %s foi alterado.
Este e-mail serve como comprovante da ação realizada.

Acompanhe seu pedido através do link: %s

Detalhes:

Nº do pedido: %s
Data da alteração: %s
Status atual: %s
Status anterior: %s

Atenciosamente,
%s
                       """ % (idVenda, 'http://homologacao.teste.homo/meusPedidos/visualizar/'+str(idVenda),idVenda, datetime.now(tz=tz).strftime("%d/%m/%Y, %H:%M:%S"), alt.getNomeStatus(), alt.getNomeStatus(status_venda = status_atual), Parametros(id_param = 2).getParametros()[0][2])
                    dados_email = Integracoes()
                    email_login, senha_login = dados_email.getDadosAcessoEmail()
                    email = getMailCliente(getIdClientePorVenda(idVenda))
                    integracao = IntegracaoEmail(email = email_login, senha = senha_login, destinatario = email, assunto = 'Atualização de status do pedido', conteudo = conteudo)
                    if not integracao.enviarEmail():
                        flash('Erro no envio de notificação via e-mail!', 'danger')
                else:
                    flash('Erro ao alterar situação da venda!', 'danger')
            else:
                flash('Situação da venda mantida!', 'info')
            return redirect(url_for('.exibeVendas'))
        else:
            if idCliente == None:
                venda = Vendas()
                venda = venda.getVendas()
            else:
                venda = Vendas(id_cliente=idCliente)
                venda = venda.getVendas()
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]
            return render_template("financeiro/vendas/fin_vendaCons.html", data=venda, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/financeiro/vendas/visualizar/<idVenda>", methods = ['GET', 'POST'])
def visVenda(idVenda):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            newStatus = request.form['statusVenda']

            alt = Vendas(id_venda = idVenda, statusVenda = newStatus)
            status_atual = alt.getStatusVenda()[0][0]
            if int(status_atual) != int(newStatus):
                if alt.alteraStatus():
                    flash('Situação da venda alterada com sucesso!', 'success')
                
                    if int(newStatus) == 0:
                        cart = Carrinho(getIdClientePorVenda(idVenda))
                        cart.removeCarrinho()
                
                    if not alt.insereHist(idVenda, newStatus, datetime.now(tz=tz), 'Situação do pedido alterada: ' + alt.getNomeStatus(status_venda = status_atual) + ' -> ' + alt.getNomeStatus(), None, None):
                        flash('Erro ao inserir histórico!')

                    conteudo = """Atualização do status do pedido\n
Caro cliente, o status do pedido %s foi alterado.
Este e-mail serve como comprovante da ação realizada.

Acompanhe seu pedido através do link: %s

Detalhes:

Nº do pedido: %s
Data da alteração: %s
Status atual: %s
Status anterior: %s

Atenciosamente,
%s
                       """ % (idVenda, 'http://homologacao.teste.homo/meusPedidos/visualizar/'+str(idVenda),idVenda, datetime.now(tz=tz).strftime("%d/%m/%Y, %H:%M:%S"), alt.getNomeStatus(), alt.getNomeStatus(status_venda = status_atual), Parametros(id_param = 2).getParametros()[0][2])
                    dados_email = Integracoes()
                    email_login, senha_login = dados_email.getDadosAcessoEmail()
                    email = getMailCliente(getIdClientePorVenda(idVenda))
                    integracao = IntegracaoEmail(email = email_login, senha = senha_login, destinatario = email, assunto = 'Atualização de status do pedido', conteudo = conteudo)
                    if not integracao.enviarEmail():
                        flash('Erro no envio de notificação via e-mail!', 'danger')

                else:
                    flash('Erro ao alterar situação da venda!', 'danger')
            else:
                flash('Situação da venda mantida!', 'info')

            return redirect(url_for('.visVenda', idVenda = idVenda))

        else:
            vendas = Vendas(idVenda)
            venda = vendas.getVendas()
            dados_prod = vendas.getDetVendas()
            dados_hist = vendas.getHist()

            histPix = []
            histBol = []
            for dados in dados_hist:
                if dados[5] != None:
                    if len(str(dados[5])) != 0:
                        histPix.append(vendas.getDadosPix(dados[5]))
                if dados[6] != None:
                    if len(str(dados[6])) != 0:
                        histBol.append(vendas.getDadosBol(dados[6]))

            forma_pagamento = venda[0][4]
            subt = venda[0][7]
            calcTx = getTaxasValor(float(subt), float(venda[0][5]))
            calcAc = getAcrescimoValor(float(subt), float(calcTx), float(venda[0][6]))
            
            if venda[0][13] != None:
                banco = venda[0][13] + ' - ' + venda[0][14]
            else:
                banco=  ''
            
            dadosPgto = [forma_pagamento, calcTx, calcAc, banco]
            
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]

            print(histPix)

            return render_template("financeiro/vendas/fin_vendaVis.html", histPix = histPix, histBol = histBol, dados_hist = dados_hist,  dados_venda=venda, dados_prod=dados_prod, dados_pgto = dadosPgto, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/financeiro/pedidos", methods = ['GET', 'POST'])
def exibePedidos():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        if request.method == 'POST':
            idVenda = request.form['idVenda']
            if request.form['btnConfirm'] == 'confEntr':
                alt = Vendas(id_venda = idVenda, statusVenda = 0)
                status_atual = alt.getStatusVenda()[0][0]
                if int(status_atual) != 0:
                    if alt.alteraStatus():
                        cart = Carrinho(getIdClientePorVenda(idVenda))
                        cart.removeCarrinho()
                    
                        flash('Venda cadastrada!', 'success')
                    
                        if not alt.insereHist(idVenda, 0, datetime.now(tz=tz), 'Situação do pedido alterada: ' + alt.getNomeStatus(status_venda = status_atual) + ' -> ' + alt.getNomeStatus(), None, None):
                            flash('Erro ao inserir histórico!')

                        conteudo = """Atualização do status do pedido\n
Caro cliente, o status do pedido %s foi alterado.
Este e-mail serve como comprovante da ação realizada.

Acompanhe seu pedido através do link: %s

Detalhes:

Nº do pedido: %s
Data da alteração: %s
Status atual: %s
Status anterior: %s

Atenciosamente,
%s
                       """ % (idVenda, 'http://homologacao.teste.homo/meusPedidos/visualizar/'+str(idVenda),idVenda, datetime.now(tz=tz).strftime("%d/%m/%Y, %H:%M:%S"), alt.getNomeStatus(), alt.getNomeStatus(status_venda = status_atual), Parametros(id_param = 2).getParametros()[0][2])
                        dados_email = Integracoes()
                        email_login, senha_login = dados_email.getDadosAcessoEmail()
                        email = getMailCliente(getIdClientePorVenda(idVenda))
                        integracao = IntegracaoEmail(email = email_login, senha = senha_login, destinatario = email, assunto = 'Atualização de status do pedido', conteudo = conteudo)
                        if not integracao.enviarEmail():
                            flash('Erro no envio de notificação via e-mail!', 'danger')
                    else:
                        flash('Erro ao alterar situação do pedido!', 'danger')
                else:
                    flash('Situação da venda mantida!', 'info')
                return redirect(url_for('.exibePedidos'))

            elif request.form['btnConfirm'] == 'confPgto':
                alt = Vendas(id_venda = idVenda, statusVenda = 2)
                status_atual = alt.getStatusVenda()[0][0]
                if int(status_atual) != 2:
                    if alt.alteraStatus():
                        flash('Pagamento confirmado, aguardando entrega do produto!', 'info')
                    
                        if not alt.insereHist(idVenda, 2, datetime.now(tz=tz), 'Situação do pedido alterada: ' + alt.getNomeStatus(status_venda = status_atual) + ' -> ' + alt.getNomeStatus(), None, None):
                                flash('Erro ao inserir histórico!')

                        conteudo = """Atualização do status do pedido\n
Caro cliente, o status do pedido %s foi alterado.
Este e-mail serve como comprovante da ação realizada.

Acompanhe seu pedido através do link: %s

Detalhes:

Nº do pedido: %s
Data da alteração: %s
Status atual: %s
Status anterior: %s

Atenciosamente,
%s
                       """ % (idVenda, 'http://homologacao.teste.homo/meusPedidos/visualizar/'+str(idVenda),idVenda, datetime.now(tz=tz).strftime("%d/%m/%Y, %H:%M:%S"), alt.getNomeStatus(), alt.getNomeStatus(status_venda = status_atual), Parametros(id_param = 2).getParametros()[0][2])
                        
                        dados_email = Integracoes()
                        email_login, senha_login = dados_email.getDadosAcessoEmail()
                        email = getMailCliente(getIdClientePorVenda(idVenda))
                        integracao = IntegracaoEmail(email = email_login, senha = senha_login, destinatario = email, assunto = 'Atualização de status do pedido', conteudo = conteudo)
                        if not integracao.enviarEmail():
                            flash('Erro no envio de notificação via e-mail!', 'danger')

                    else:
                        flash('Erro ao alterar confirmação do pagamento!', 'danger')
                else:
                    flash('Situação da venda mantida!', 'info')
                return redirect(url_for('.exibePedidos'))

            else:
                alt = Vendas(id_venda = idVenda, statusVenda = 1)
                status_atual = alt.getStatusVenda()[0][0]
                if int(status_atual) != 1:
                    if alt.alteraStatus():
                        flash('Pedido cancelado com sucesso!', 'info')
                    
                        if not alt.insereHist(idVenda, 1, datetime.now(tz=tz), 'Situação do pedido alterada: ' + alt.getNomeStatus(status_venda = status_atual) + ' -> ' + alt.getNomeStatus(), None, None):
                                flash('Erro ao inserir histórico!')

                        conteudo = """Cancelamento de pedido\n
Caro cliente, o pedido de nº %s foi cancelado.
Este e-mail serve como comprovante da ação realizada.

Atenciosamente,
%s
                       """ % (idVenda, Parametros(id_param = 2).getParametros()[0][2])
                        dados_email = Integracoes()
                        email_login, senha_login = dados_email.getDadosAcessoEmail()
                        integracao = IntegracaoEmail(email = email_login, senha = senha_login, destinatario = email, assunto = 'Cancelamento de Pedido', conteudo = conteudo)
                        if not integracao.enviarEmail():
                            flash('Erro no envio de notificação via e-mail!', 'danger')
                        
                    else:
                        flash('Erro ao alterar situação do pedido!', 'danger')
                else:
                    flash('Situação da venda mantida!', 'info')

                return redirect(url_for('.exibePedidos'))
        else:
            venda = Vendas()
            waitEntrega = venda.getAguardaEntrega()
            waitPgto = venda.getAguardaPgto()
            notificacoes = Notificacoes()
            qtdNotifs = notificacoes.getQtdNotificacoes()[0][0]

        return render_template("financeiro/pedidos/fin_pedidosCons.html", dadosEntrega = waitEntrega, dadosPgto = waitPgto, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/notificacoes")
def exibeNotificacao():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        
        notificacoes = Notificacoes()
        notifs = notificacoes.getNotificacoes()

        return render_template("notificacoes/notificacoes.html", notificacoes = notifs, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/notificacoes/topNotif", methods=['POST'])
def exibeTopNotifs():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        conn = db()
        topNotifs = conn.execute_bd("SELECT * FROM VW_notificacoes where visualizado = 'F' order by id_notificacao desc LIMIT 5", 'A')

        return jsonify({'data': render_template('notificacoes/resposta_notif.html', conteudo = topNotifs)})
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/notificacoes/contaNotif", methods=['GET','POST'])
def contaNotifs():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        conn = db()
        total = conn.execute_bd("select count(1) from TB_NOTIFICACOES where visualizado = 'F'", 'A')[0][0]
        
        if int(total) == 0:
            resultado = "Você não possui novas notificações."
        elif int(total) == 1:
            resultado = "Você possui 1 nova notificação:"
        else:
            resultado = "Você possui " + str(total) + " novas notificações:"

        return jsonify({'data': [total, resultado]})
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/notificacoes/removerNotificacao", methods=['GET','POST'])
def removerNotificacao():
    id_notif = int(request.args.get('idNotificacao'))

    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    
    if tipoUser == 'A':
        notif = Notificacoes(id_notificacao=id_notif)

        if notif.removeNotificacoes():
            flash('Notificação removida!', 'info')
        else:
            flash('Erro ao remover notificação!', 'danger')

        if request.method == "POST":
            return redirect(url_for('.visVenda'))
        else:       
            return redirect(url_for('.exibeNotificacao'))
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/parametros/ecommerce")
def paramsEcommerce():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    
    if tipoUser == 'A':
        params = Parametros()
        params = params.getParametros()

        return render_template("parametros/ecommerce.html", params = params, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/parametros/visualizar/<idParametro>", methods=['GET', 'POST'])
def visParamsEcommerce(idParametro):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    
    if tipoUser == 'A':
        if request.method == 'POST':
            if int(idParametro) == 1:
                image = request.files['image']
                if image.filename == '':
                    flash('Um arquivo deve ser selecionado!', 'warning')
                    return redirect(url_for('.visParamsEcommerce', idParametro=idParametro))
                else:
                    if image and allowed_file_ico(image.filename):
                        basedir = os.path.abspath(os.path.dirname(__file__))
                        filename = secure_filename(image.filename)
                        full_file = os.path.join(basedir, homologacao.config['UPLOAD_FOLDER'], filename)
                        image.save(full_file)
                        imagename = filename
                    else:
                        flash('Imagem em formato inválido! Gentileza seleiconar um arquivo do tipo .ICO', 'warning')
                        return redirect(url_for('.visParamsEcommerce', idParametro=idParametro))

                    params = Parametros(id_param = idParametro, valor_param = imagename)
                if params.alteraParametro():                  
                    flash('Parâmetro alterado com sucesso!', 'info')
                else:   
                    flash('Erro ao alterar parâmetro!', 'danger')
            else:
                valor = request.form['valorParam']
                params = Parametros(id_param = idParametro, valor_param = valor)
                if params.alteraParametro():                  
                    flash('Parâmetro alterado com sucesso!', 'info')
                else:   
                    flash('Erro ao alterar parâmetro!', 'danger')
            return redirect(url_for('.visParamsEcommerce', idParametro=idParametro))
        else:
            params = Parametros(idParametro)
            categ = params.getCateg()[0][0]

            if int(categ) != 2:
                params = params.getParametros()
            else:
                params = params.getParametrosSocial()
            notificacoes = Notificacoes()
            
            return render_template("parametros/visParams.html", params = params, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/parametros/social")
def paramsSocial():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    
    if tipoUser == 'A':
        params = Parametros()
        params = params.getParametrosSocial()

        return render_template("parametros/socialMedia.html", params = params, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

#---------------------------------------------------------------------------------------#

@homologacao.route("/painelAdmin/ecommerce/referencias")
def exibeReferencias():
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()
    
    if tipoUser == 'A':
        refs = Referencias()
        refs = refs.getListaReferencias()

        return render_template("ecommerce/painelAdmin/ecom_referenciasCons.html", data = refs, autenticado=autenticado, nome=nome, tipoUser=tipoUser)
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/ecommerce/referencias/remover/<idReferencia>")
def remReferencia(idReferencia):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        refs = Referencias(idReferencia)
        if refs.removeReferencia():
            flash('Referência removida com sucesso!', 'success')
        else:
            flash('Erro ao remover referência!', 'danger')
        return redirect(url_for('.exibeReferencias'))
    else:
        return render_template("404.html"), 404

@homologacao.route("/painelAdmin/ecommerce/referencias/exibicao/<idReferencia>")
def altReferencia(idReferencia):
    autenticado, nome, tipoUser, qtdCarrinho = getDetalhesLogin()

    if tipoUser == 'A':
        refs = Referencias(idReferencia)
        if refs.alteraReferencia():
            flash('Referência atualizada com sucesso!', 'success')
        else:
            flash('Erro ao atualizar referência!', 'danger')
        return redirect(url_for('.exibeReferencias'))
    else:
        return render_template("404.html"), 404