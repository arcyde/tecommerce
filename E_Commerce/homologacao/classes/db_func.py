import sqlite3
import os.path
import datetime as dt
import itertools
import operator

from sqlite3 import Error
from datetime import date
from .. import views
from flask import flash
from cryptography.fernet import Fernet
from .integracoes import *

class db:
    def __init__(self):
        self.db_name = '..\ecommercedb.db'
        
    def conectar_db(self):  
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, self.db_name)

        try:
            conn = sqlite3.connect(db_path)
        except Error as e:
            print(e)       
        return conn

    def execute_bd_com_param(self, query, dados):
        
        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.execute(query, dados)
            resultado = cursor.fetchall()
            conn.commit()
            
        except Error as e: 
            print(e)
            conn.rollback()
        finally:
            conn.close()
            return resultado

    def execute_bd_returnId(self, query, dados):
        
        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.execute(query, dados)
            conn.commit()
            
        except Error as e: 
            print(e)
            conn.rollback()
        finally:
            conn.close()
            return cursor.lastrowid

    def execute_bd(self, query, tipo):

        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.execute(query)
            if tipo == 'A':
                resultado = cursor.fetchall()
            elif tipo == 'O':
                resultado = cursor.fetchone()
            else:
                resultado = 0
            conn.commit()
            
        except Error as e: 
            print(e)
            conn.rollback()
        finally:
            conn.close()
            return resultado

class Carrinho():
    def __init__ (self, id_cliente, id_produto=None, tipo=None, obs=None, qtd=None):
        self.id_cliente = id_cliente
        self.id_produto = id_produto
        self.tipo = tipo
        self.obs = obs
        self.qtd = qtd

    def assimilaUser(self, cookie):
        self.cookie = cookie
        conn = db()
        try:
            conn.execute_bd_com_param('update tb_carrinho set id_cliente = ? where guest_number = ?', (self.id_cliente, self.cookie))
            return True
        except:
            return False

    def getCarrinho(self):
        conn = db()

        num_cookie = views.getCookie()

        if self.tipo == 'autenticado':
            produtos = conn.execute_bd_com_param('SELECT a.id_produto, a.produto, printf("%.2f", a.preco), b.diretorio, c.qtd, printf("%.2f", a.preco * c.qtd), c.obs FROM tb_produtos a inner join tb_produtos_imagens b on a.id_produto = b.id_produto inner join tb_carrinho c on a.id_produto = c.id_produto WHERE c.id_cliente = ? or guest_number = ?', (self.id_cliente, num_cookie))
            
        elif self.tipo == 'visitante':
            produtos = conn.execute_bd_com_param('SELECT a.id_produto, a.produto, printf("%.2f", a.preco), b.diretorio, c.qtd, printf("%.2f", a.preco * c.qtd), c.obs FROM tb_produtos a inner join tb_produtos_imagens b on a.id_produto = b.id_produto inner join tb_carrinho c on a.id_produto = c.id_produto WHERE c.guest_number = ?', (self.id_cliente, ))
            
        newProd = []

        param = Parametros(id_param = 3)
        param = param.getParametros()[0]

        if param[2] == 'SIM':
            agrupaQTD = True
        else:
            agrupaQTD = False

        if len(produtos) != 0:
            for items in produtos:
                id = items[0]

                qtdAtualProd = conn.execute_bd_com_param('select case when qtd is null then 0 else qtd end, case when qtd_max is null then qtd when qtd_max = 0 then qtd else qtd_max end from tb_produtos where id_produto = ?', (id,))
                for dadosQTD in qtdAtualProd:
                    qtdAtualProd = dadosQTD[0]
                    qtdMaxProd = dadosQTD[1]

                produto = items[1]
                diretorio = items[3]

                qtd = items[4]
                
                if int(qtdAtualProd) < qtd:
                    qtd = int(qtdAtualProd)
                else:
                    qtd = items[4]

                if qtd >= qtdMaxProd:
                    qtd = int(qtdMaxProd)

                obs = items[6]
                if agrupaQTD:
                    if self.tipo == 'autenticado':
                        qtdTotalCart = conn.execute_bd_com_param('SELECT sum(qtd) FROM tb_carrinho WHERE (id_cliente = ? or guest_number = ?) and id_produto = ?', (self.id_cliente, num_cookie, id))[0][0]
                    else:
                        qtdTotalCart = conn.execute_bd_com_param('SELECT sum(qtd) FROM tb_carrinho WHERE guest_number = ? and id_produto = ?', (self.id_cliente, id))[0][0]
                    
                    precoInd = views.getValorProduto(id, qtdTotalCart)
                    precoTot = float(views.getValorProduto(id, qtdTotalCart)) * qtd

                else:
                    precoInd = views.getValorProduto(id, qtd)
                    precoTot = float(views.getValorProduto(id, qtd)) * qtd
                new = [id, produto, precoInd, diretorio, qtd, "%.2f" % precoTot, obs]
                newProd.append(new)
            
            itensCarrinho = newProd
        else:
            itensCarrinho = []

        def accumulate(l):
            it = itertools.groupby(l, operator.itemgetter(0))
            for key, subiter in it:
                yield key, sum(item[4] for item in subiter) 

        if len(produtos) != 0:
            qtdTotalProdutosCart = list(accumulate(itensCarrinho))

            for produto in qtdTotalProdutosCart:
                id = produto[0]
                total = int(produto[1])
                
                qtd_atual = conn.execute_bd_com_param('select case when qtd is null then 0 else qtd end, case when qtd_max is null then qtd when qtd_max = 0 then qtd else qtd_max end  from tb_produtos where id_produto = ?', (id,))[0][0]
                
                if total > qtd_atual:
                    qtd_prod_cart = 0
                    for dados in itensCarrinho:
                        if dados[0] == id:
                            qtd_prod_cart = qtd_prod_cart + 1

                    for dados in itensCarrinho:
                        if dados[0] == id:
                            dados[4] = qtdAtualProd // qtd_prod_cart
        
        #if len(produtos) != 0:
        #    total = 0
        #    
        #    for dados in itensCarrinho:
        #        total = dados[4] + total    
        #        
        #    if total > qtdAtualProd:
        #        for dados in itensCarrinho:
        #            dados[4] = qtdAtualProd // len(itensCarrinho)
        
        return itensCarrinho

    def atualizaCarrinho(self):
        if self.tipo == 'autenticado':
            conn = db()
            conn.execute_bd_com_param('update tb_carrinho set qtd=? where id_produto=? and obs=? and id_cliente=?', (self.qtd, self.id_produto, self.obs, self.id_cliente))
            return True
        elif self.tipo == 'visitante':
            conn = db()
            conn.execute_bd_com_param('update tb_carrinho set qtd=? where id_produto=? and obs=? and guest_number=?', (self.qtd, self.id_produto, self.obs, self.id_cliente))
            return True
        return False

    def insereCarrinho(self):
        conn = db()
        try:
            if self.tipo == 'autenticado':
                verificaProd = conn.execute_bd_com_param("select * from tb_carrinho where id_cliente = ? and id_produto = ? and obs = ?", (self.id_cliente, self.id_produto, self.obs))
                if len(verificaProd) > 0:
                    for dados in verificaProd:
                        quantExist = dados[3]
                    self.qtd = self.qtd + int(quantExist)
                    queryCarrinho = "update tb_carrinho set qtd = ? where id_cliente = ? and id_produto = ? and obs = ?"
                else:        
                    queryCarrinho = "INSERT INTO tb_carrinho (qtd, id_cliente, id_produto, obs) VALUES (?, ?, ?, ?)"
                    
                dadosCarrinho = (self.qtd, self.id_cliente, self.id_produto, self.obs)  
                conn.execute_bd_com_param(queryCarrinho, dadosCarrinho)
                return True
            elif self.tipo == 'visitante':
                
                verificaProd = conn.execute_bd_com_param("select * from tb_carrinho where guest_number = ? and id_produto = ? and obs = ?", (self.id_cliente, self.id_produto, self.obs))
                if len(verificaProd) > 0:
                    for dados in verificaProd:
                        quantExist = dados[3]
                    self.qtd = self.qtd + int(quantExist)
                    queryCarrinho = "update tb_carrinho set qtd = ? where guest_number = ? and id_produto = ? and obs = ?"
                else:        
                    queryCarrinho = "INSERT INTO tb_carrinho (qtd, guest_number, id_produto, obs) VALUES (?, ?, ?, ?)"
                    
                dadosCarrinho = (self.qtd, self.id_cliente, self.id_produto, self.obs)  
                conn.execute_bd_com_param(queryCarrinho, dadosCarrinho)
                return True
            else:
                return False
        except Error as e:
            print(e)
            return False

    def removeCarrinho(self):
        conn = db()
        if self.id_produto != None:
            if self.tipo == 'autenticado':
                num_cookie = views.getCookie()
                query = conn.execute_bd_com_param("delete from tb_carrinho where (id_cliente = ? or guest_number = ?) and id_produto = ? and obs = ?", (self.id_cliente, num_cookie, self.id_produto, self.obs))
                return True
            elif self.tipo == 'visitante':
                query = conn.execute_bd_com_param("delete from tb_carrinho where guest_number = ? and id_produto = ? and obs = ?", (self.id_cliente, self.id_produto, self.obs))
                return True
            return False
        else:
            num_cookie = views.getCookie()
            query = conn.execute_bd_com_param("delete from tb_carrinho where (id_cliente = ? or guest_number = ?)", (self.id_cliente, num_cookie))
            return True


class Categorias():
    def __init__ (self, nome_categ = None, exibe_web = None, id_categ = None):
        self.nome_categ = nome_categ
        self.exibe_web = exibe_web
        self.id_categ = id_categ

    def getCategoria(self, id_categ = None):
        self.id_categ = id_categ
        conn = db()
        if id_categ == None:
            resultado = conn.execute_bd('select id_categoria, nome_categoria, case when exibe_web = "T" then "SIM" ELSE "NÃO" END from tb_categorias', 'A')
            return resultado
        else:
            resultado = conn.execute_bd_com_param('select id_categoria, nome_categoria, case when exibe_web = "T" then "SIM" ELSE "NÃO" END from tb_categorias where id_categoria = ?', (self.id_categ,))
            return resultado

    def getCategoriaProduto(self, idProduto):
        self.idProduto = idProduto
        conn = db()
        resultado = conn.execute_bd_com_param('select a.* from tb_categorias a inner join tb_produtos b on a.id_categoria = b.id_categoria where b.id_produto = ?', (idProduto,))
        return resultado

    def insereCategoria(self):
        conn = db()
        try:
            conn.execute_bd_com_param('insert into tb_categorias (nome_categoria, exibe_web) values (?, ?)', (self.nome_categ, self.exibe_web))
            return True
        except:
            return False

    def alteraCategoria(self, id_categ):
        self.id_categ = id_categ
        conn = db()
        try:
            conn.execute_bd_com_param('update tb_categorias set nome_categoria = ?, exibe_web = ? where id_categoria = ?', (self.nome_categ, self.exibe_web, self.id_categ))
            return True
        except:
            return False

    def removeCategoria(self, id_categ):
        self.id_categ = id_categ
        conn = db()
        qtd = conn.execute_bd_com_param("select count(1) from tb_produtos where id_categoria = ?", (self.id_categ,))[0][0]
        if int(qtd) == 0:
            try:
                conn.execute_bd_com_param('delete from tb_categorias where id_Categoria = ?', (self.id_categ,))
                return True
            except:
                return False
        else:
            return False

    def exibeProdutosCategoria(self):
        conn= db()
        dadosProd = conn.execute_bd_com_param('''SELECT b.id_produto, b.produto, printf("%.2f", b.preco), c.diretorio, a.nome_Categoria FROM tb_categorias a inner JOIN tb_produtos b ON a.id_categoria = b.id_categoria inner JOIN tb_produtos_imagens c ON c.id_produto = b.id_produto WHERE a.id_categoria = ?''', self.id_categ)
        return dadosProd

class Produtos():
    def __init__ (self, nome_prod = None):
        self.nome_prod = nome_prod

    def getProduto(self, id_prod = None):
        self.id_prod = id_prod
        conn = db()
        if id_prod == None:
            resultado = conn.execute_bd('select * from VW_PROD', 'A')
            return resultado
        else:
            resultado = conn.execute_bd_com_param('select * from VW_PROD where id_produto = ?', (self.id_prod,))
            return resultado

    def getNomeProduto(self, id_prod = None):
        self.id_prod = id_prod
        conn = db()
        resultado = conn.execute_bd_com_param('select produto from tb_PROD where id_produto = ?', (self.id_prod,))
        return resultado

    def insereProduto(self, descricao, qtd, preco, id_categoria, steps, exibe_web, exibe_valor_web, qtd_max):
        self.descricao = descricao
        self.qtd = qtd
        preco = str(preco)
        self.preco = float(preco.replace(',', '.'))
        self.id_categoria = id_categoria
        self.steps = steps
        self.exibe_web = exibe_web
        self.exibe_valor_web = exibe_valor_web
        self.qtd_max = qtd_max

        conn = db()
        try:
            conn.execute_bd_com_param('insert into tb_produtos (produto, descricao, qtd, preco, id_categoria, steps, exibe_web, exibe_valor_web, qtd_max) values (?, ?, ?, ?, ?, ?, ?, ?, ?)', (self.nome_prod, self.descricao, self.qtd, self.preco, self.id_categoria, self.steps, self.exibe_web, self.exibe_valor_web, self.qtd_max))
            return True
        except:
            return False

    def alteraProduto(self, id_prod, produto, descricao, qtd, preco, id_categoria, steps, exibe_web, exibe_valor_web, qtd_max):
        self.id_prod = id_prod
        self.nome_prod = produto
        self.descricao = descricao
        self.qtd = qtd
        preco = str(preco)
        self.preco = float(preco.replace(',', '.'))
        self.id_categoria = id_categoria
        self.steps = steps
        self.exibe_web = exibe_web
        self.exibe_valor_web = exibe_valor_web
        self.qtd_max = qtd_max

        conn = db()
        
        try:
            conn.execute_bd_com_param('update tb_produtos set produto = ?, descricao = ?, qtd = ?, preco = ?, id_categoria = ?, steps = ?, exibe_web = ?, EXIBE_VALOR_WEB = ?, qtd_max = ? where id_produto = ?', (self.nome_prod, self.descricao, self.qtd, self.preco, self.id_categoria, self.steps, self.exibe_web, self.exibe_valor_web, self.qtd_max, self.id_prod))
            return True
        except:
            return False

    def getSteps(self, id_prod):
        self.id_prod = id_prod
        conn=db()
        steps = conn.execute_bd_com_param("select case when steps is null then 1 when steps = 0 then 1 else steps end from tb_produtos where id_produto = ?", (self.id_prod,))[0][0]
        return steps

    def getQtdMax(self, id_prod):
        self.id_prod = id_prod
        conn=db()
        qtdMax = conn.execute_bd_com_param("select case when qtd_max is null then qtd when qtd_max = 0 then qtd else qtd_max end from tb_produtos where id_produto = ?", (self.id_prod,))[0][0]
        return qtdMax

    def alteraQTD(self, qtd, id_prod):
        self.id_prod = id_prod
        self.qtd = qtd
        conn = db()
        try:
            conn.execute_bd_com_param('update tb_produtos set qtd = ? where id_produto = ?', (int(self.qtd), int(self.id_prod)))
            return True
        except:
            return False

    def removeProduto(self, idProd):
        self.idProd = idProd
        conn = db()
        qtd = conn.execute_bd_com_param("select count(1) from tb_vendas_det where id_produto = ?", (self.idProd,))[0][0]
        if int(qtd) == 0:
            try:
                conn.execute_bd_com_param('delete from tb_produtos where id_produto = ?', (self.idProd,))
                return True
            except:
                return False
        else:
            return False


class Tabelas():
    def getTabelaPrecos(self, id_tabPreco=None):
        self.id_tabPreco = id_tabPreco
        conn = db()
        if self.id_tabPreco == None:
            tabelas = conn.execute_bd('select * from vw_tabprecos', 'A')
        else:
            tabelas = conn.execute_bd_com_param('select * from vw_tabprecos where id_tabpreco = ?', (self.id_tabPreco,))
        return tabelas

    def getTabelaProd(self, id_produto):
        self.id_produto = id_produto
        conn = db()
        tabelas = conn.execute_bd_com_param('select * from tb_tabprecos where id_produto = ?', (self.id_produto,))
        return tabelas

    def insereTabela(self, id_produto, cancelada):
        self.id_produto = id_produto
        self.cancelada = cancelada
        conn = db()
        try:
            insert = conn.execute_bd_returnId('insert into tb_tabprecos (id_produto, cancelada) values (?, ?)', (self.id_produto, self.cancelada))
            return True, insert
        except:
            return False, None

    def alteraTabela(self, id_tabPreco, cancelada):
        self.id_tabPreco = id_tabPreco
        self.cancelada = cancelada
        conn = db()
        try:
            conn.execute_bd_com_param('update tb_tabprecos set cancelada = ? where id_tabpreco = ?', (self.cancelada, self.id_tabPreco))
            return True
        except:
            return False

    def removeTabelaPrecos(self, id_tabPreco):
        self.id_tabPreco = id_tabPreco
        conn = db()
        try:
            conn.execute_bd_com_param('DELETE FROM TB_TABPRECOS WHERE ID_TABPRECO = ?', (self.id_tabPreco,))
            conn.execute_bd_com_param('DELETE FROM TB_TABPRECOS_vlr WHERE ID_TABPRECO = ?', (self.id_tabPreco,))
            return True
        except:
            return False

    def removeFaixas(self, id_tabPreco):
        self.id_tabPreco = id_tabPreco
        conn = db()
        try:
            conn.execute_bd_com_param('DELETE FROM TB_TABPRECOS_vlr WHERE ID_TABPRECO = ?', (self.id_tabPreco,))
            return True
        except:
            return False

    def insereFaixas(self, id_tabPreco, faixas):
        self.id_tabPreco = id_tabPreco
        self.faixas = faixas

        conn = db()
        try:
            for dados in self.faixas:
                teste = conn.execute_bd_com_param('insert into tb_tabprecos_vlr(id_tabpreco, de, ate, vlr) values (?, ?, ?, ?)', (self.id_tabPreco, dados[0], dados[1], dados[2].replace(',', '.')))
            return True
        except:
            return False
 
    def getFaixas(self, id_tabPreco):
        self.id_tabPreco = id_tabPreco
        conn = db()
        faixas = conn.execute_bd_com_param('select * from tb_tabprecos_vlr where id_tabpreco = ?', (self.id_tabPreco,))
        return faixas

class FormasPgto():
    def __init__ (self, id_formaPgto = None, visivel=None, situacao=None):
        self.id_formaPgto = id_formaPgto
        self.visivel = visivel
        self.situacao = situacao

    def getFormasPgto(self):
        conn = db()
        query = "SELECT A.ID_FORMA_PGTO, A.NOME_FORMA, case when A.SITUACAO = 'A' THEN 'ATIVA' ELSE 'CANCELADA' END,  case when A.INTEGRADA = 'T' THEN 'SIM' ELSE 'NÃO' END FROM TB_FORMA_PGTO A INNER JOIN TB_FORMA_PGTO_DET B WHERE 1=1 "
        if self.visivel == 'T':
            query = query + " AND A.EXIBE_WEB = 'T'"
        if self.situacao == 'A':
            query = query + " AND A.situacao = 'A'"
        if self.id_formaPgto == None:
            formasPgto = conn.execute_bd(query, "A")
        else:
            query = query + " AND A.ID_FORMA_PGTO = ?"
            query = query + " order by 1"
            formasPgto = conn.execute_bd_com_param( query, (self.id_formaPgto,))
        return formasPgto

    def getFormasPgtoDet(self):
        conn = db()
        if self.id_formaPgto == 1:
            formasPgto = conn.execute_bd_com_param("SELECT * FROM VW_FORMA_PGTO_DET WHERE ID_FORMA_PGTO = ?", (self.id_formaPgto,))
        elif self.id_formaPgto == 2:
            dados = self.getFormasPgto()[0]
            if dados[3] == 'SIM':
                formasPgto = conn.execute_bd_com_param("SELECT A.ID_FORMA_PGTO, b.nome_forma, B.EXIBE_WEB, case  when A.celular_PIX is null then '' else a.celular_pix end, case when A.CPF_PIX is null then '' else a.cpf_pix end, case when A.email_PIX is null then '' else a.email_pix end, index_preferencia FROM TB_FORMA_PGTO_INTEGRACAO A INNER JOIN  tb_forma_pgto b on a.id_forma_pgto = b.id_forma_pgto where a.id_forma_pgto = ?", (self.id_formaPgto,))[0]
            else:
                formasPgto = conn.execute_bd_com_param("SELECT A.ID_FORMA_PGTO, b.nome_forma, B.EXIBE_WEB, case  when A.celular_PIX is null then '' else a.celular_pix end, case when A.CPF_PIX is null then '' else a.cpf_pix end, case when A.email_PIX is null then '' else a.email_pix end, index_preferencia FROM TB_FORMA_PGTO_INTEGRACAO A INNER JOIN  tb_forma_pgto b on a.id_forma_pgto = b.id_forma_pgto where a.id_forma_pgto = ?", (self.id_formaPgto,))
        else:
            formasPgto = conn.execute_bd_com_param("select * FROM TB_FORMA_PGTO WHERE ID_FORMA_PGTO = ?", (self.id_formaPgto,))
        return formasPgto

    def getAcrescimos(self):
        conn = db()
        try:
            acrescimo = conn.execute_bd_com_param("SELECT case when tx_acrescimo is null then 0 else tx_acrescimo end FROM tb_FORMA_PGTO_DET WHERE ID_FORMA_PGTO = ?", (self.id_formaPgto,))[0][0]
        except:
            acrescimo = ''
        return acrescimo

    def getTaxas(self):
        conn = db()
        taxas = conn.execute_bd_com_param("SELECT case when taxas is null then 0 else taxas end FROM tb_FORMA_PGTO WHERE ID_FORMA_PGTO = ?", (self.id_formaPgto,))
        return taxas

    def alteraFormaPgto(self, exibe_web = None, acrescimo = None, usuario = None, obs = None, celular = None, cpf = None, email = None):
        self.exibe_web = exibe_web
        self.acrescimo = acrescimo
        self.usuario = usuario
        self.obs = obs
        self.celular = celular
        self.cpf = cpf
        self.email = email

        conn = db()
        if int(self.id_formaPgto) == 1:
            try:
                alteraPic = conn.execute_bd_com_param('update tb_forma_pgto_det set usuario = ?, tx_acrescimo = ?, exibe_web = ?, obs = ? where id_forma_pgto = 1', (self.usuario, self.acrescimo, self.exibe_web, self.obs))
                return True
            except:
                return False
        elif int(self.id_formaPgto) == 2:
            try:
                alteraPic = conn.execute_bd_com_param('update tb_forma_pgto_integracao set celular_pix = ?, cpf_pix = ?, email_pix = ? where id_forma_pgto = 2', (self.celular, self.cpf, self.email))
                alteraWeb = conn.execute_bd_com_param('update tb_forma_pgto set exibe_web = ? where id_forma_pgto = 2', (self.exibe_web,))
                return True
            except:
                return False
        elif int(self.id_formaPgto) == 3 or int(self.id_formaPgto) == 4:
            try:
                alteraWeb = conn.execute_bd_com_param('update tb_forma_pgto set exibe_web = ? where id_forma_pgto = ?', (self.exibe_web, self.id_formaPgto))
                return True
            except:
                return False
        return False

    def removeBancos(self):
        conn = db()
        try:
            remBanco = conn.execute_bd_com_param("delete from TB_FORMA_PGTO_BANCO where id_forma_pgto = ?", (self.id_formaPgto,))
            return True
        except:
            return False

    def insereFaixas(self, faixas):
        self.faixas = faixas

        conn = db()

        for dados in self.faixas:
            dados = conn.execute_bd_com_param('insert into tb_forma_pgto_banco (id_forma_pgto, cod_banco, cod_operacao, agencia, dig_agencia, conta, dig_conta, favorecido, cpf_cnpj) values (?, ?, ?, ?, ?, ?, ?, ?, ?)', (self.id_formaPgto, dados[0], dados[1], dados[2], dados[3], dados[4], dados[5], dados[6], dados[7]))
        return True
        
        return False

    def getBancosForma(self, id_banco = None):
        self.id_banco = id_banco
        conn = db()
        if id_banco == None:
            lstBancosForma = conn.execute_bd_com_param('select id_forma_pgto, a.cod_banco, cod_operacao, agencia, dig_agencia, conta, dig_conta, obs, nome_banco, favorecido, cpf_cnpj from tb_forma_pgto_banco a inner join tb_bancos b on a.cod_banco = b.id_banco where id_forma_pgto = ? order by 1', (self.id_formaPgto,)) 
        else:
            lstBancosForma = conn.execute_bd_com_param("select * from VW_DADOS_BANCO_FORMA where id_forma_pgto = ? and cod_banco = ?", (self.id_formaPgto, self.id_banco)) 
        return lstBancosForma

class Checkout():
    def __init__ (self, id_cliente, formaPgto, taxas, acrescimo, subtotal, total, produtos, obs, status, data_hora, tipoBanco):
        self.id_cliente = id_cliente
        self.formaPgto = formaPgto
        taxas = str(taxas)
        self.taxas = float(taxas.replace(',', '.'))
        acrescimo = str(acrescimo)
        self.acrescimo = float(acrescimo.replace(',', '.'))
        subtotal = str(subtotal)
        self.subtotal = float(subtotal.replace(',', '.'))
        total = str(total)
        self.total = float(total.replace(',', '.'))
        self.produtos = produtos
        self.obs = obs
        self.status = status
        self.data_hora = data_hora
        self.tipoBanco = tipoBanco

    def insereVenda(self):
        conn = db()

        maxIdVenda = conn.execute_bd_com_param('select max(id_venda) from tb_vendas where id_cliente = ? and status_venda = 3', (self.id_cliente,))[0][0]
        
        if maxIdVenda == None:
            idVenda = conn.execute_bd_returnId('insert into tb_vendas (id_cliente, id_forma_pgto, taxas, acrescimo, subtotal, total, obs, status_venda, data_hora, cod_Banco) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (self.id_cliente, self.formaPgto, self.taxas, self.acrescimo, self.subtotal, self.total, self.obs, self.status, self.data_hora, self.tipoBanco))
            for itens in self.produtos:
                idProd = itens[0]
                vlrUnt = itens[2]
                qtd_det = itens[4]
                total_det = "%.2f" % (float(vlrUnt) * int(qtd_det))
                obs = itens[6]
            
                self.insereVendaDet(idVenda, idProd, vlrUnt, qtd_det, total_det, obs)
            
            return True, idVenda

        else:

            conn.execute_bd_com_param('''update tb_vendas set id_forma_pgto = ?, taxas = ?, acrescimo = ?, subtotal = ?, 
            total = ?, obs = ?, status_venda = ?, data_hora = ?, cod_banco = ? 
            where id_cliente = ? and id_Venda = ?''', (self.formaPgto, self.taxas, self.acrescimo, self.subtotal, self.total, self.obs, self.status, self.data_hora, self.tipoBanco, self.id_cliente, maxIdVenda))
            
            conn.execute_bd_com_param('delete from tb_vendas_det where id_venda = ?', (maxIdVenda,))

            for itens in self.produtos:
                idProd = itens[0]
                vlrUnt = itens[2]
                qtd_det = itens[4]
                total_det = "%.2f" % (float(vlrUnt) * int(qtd_det))
                obs = itens[6]
            
                self.insereVendaDet(maxIdVenda, idProd, vlrUnt, qtd_det, total_det, obs)

            venda = Vendas()
            venda.insereHist(maxIdVenda, 3, datetime.now(tz=tz), 'Pedido atualizado!', None, None)
            flash('Pedido atualizado com sucesso!', 'success')
            
            return True, maxIdVenda

    def insereVendaDet(self, id_venda, id_produto_det, valor_unt_det, quantidade_det, total_det, obs_det):
        self.id_venda = id_venda
        self.id_produto_det = id_produto_det
        valor_unt_det = str(valor_unt_det)
        self.valor_unt_det = float(valor_unt_det.replace(',', '.'))
        self.quantidade_det = quantidade_det
        total_det = str(total_det)
        self.total_det = float(total_det.replace(',', '.'))
        self.obs_det = obs_det

        conn = db()
        conn.execute_bd_com_param('insert into tb_vendas_det (id_Venda, id_produto, vlr_ind, qtd, total, obs) values (?, ?, ?, ?, ?, ?)', (self.id_venda, self.id_produto_det, self.valor_unt_det, self.quantidade_det, self.total_det, self.obs_det))

class Vendas():
    def __init__ (self, id_venda=None, id_cliente=None, statusVenda=None):
        self.id_venda = id_venda
        self.id_cliente = id_cliente
        self.statusVenda = statusVenda

    def getVendas(self):
        conn=db()
        if self.id_venda == None and self.id_cliente == None:
            query = "select * FROM VW_VENDAS order by 1 desc"
            dadosVenda = conn.execute_bd(query, 'A')
        elif self.id_venda != None and self.id_cliente == None:
            query = "select * FROM VW_VENDAS where id_venda=?"
            dadosVenda = conn.execute_bd_com_param(query, (self.id_venda,))
        else:
            query = "select * FROM VW_VENDAS where id_cliente=?"
            dadosVenda = conn.execute_bd_com_param(query, (self.id_cliente,))
        return dadosVenda

    def getVendasCliente(self):
        conn=db()
        if self.id_venda == None:
            query = "select * FROM VW_VENDAS where id_cliente = ? order by 1 desc"
            dadosVenda = conn.execute_bd_com_param(query, (self.id_cliente,))  
        else:
            query = "select * FROM VW_VENDAS where id_cliente = ? and id_venda = ? order by 1 desc"
            dadosVenda = conn.execute_bd_com_param(query, (self.id_cliente, self.id_venda))  
        return dadosVenda

    def getDetVendasCliente(self):
        conn=db()
        resultado=conn.execute_bd_com_param("select a.* from vw_vendas_det a inner join tb_vendas b on a.id_venda = b.id_venda where a.id_venda=? and id_cliente = ?", (self.id_venda, self.id_cliente))
        return resultado

    def getDetVendas(self):
        conn=db()
        resultado=conn.execute_bd_com_param("select * from vw_vendas_det where id_venda=?", (self.id_venda, ))
        return resultado

    def getHist(self):
        conn=db()
        resultado=conn.execute_bd_com_param("select * from vw_vendas_hist where id_venda=?", (self.id_venda, ))
        return resultado

    def getDadosPix(self, id_pix = None):
        self.id_pix = id_pix

        conn=db()
        if id_pix == None:
            resultado=conn.execute_bd_com_param("select * from tb_vendas_det_pix where id_venda= ?", (self.id_venda, ))
        else:
            resultado=conn.execute_bd_com_param("select * from tb_vendas_det_pix where id_pix = ?", (self.id_pix, ))[0]
        return resultado

    def getDadosBol(self, id_boleto = None):
        self.id_boleto = id_boleto

        conn=db()
        resultado=conn.execute_bd_com_param("select * from tb_vendas_det_bol where id_venda= ?", (self.id_venda, ))[0]
        return resultado

    def insereHist(self, id_venda, id_status, data_hora, obs, id_pix, id_bol):
        self.id_venda = id_venda
        self.id_status = id_status
        self.data_hora = data_hora
        self.obs = obs
        self.id_pix = id_pix
        self.id_bol = id_bol

        conn = db()
        try:
            conn.execute_bd_com_param('insert into tb_vendas_movimentacoes (id_venda, id_status, data_hora, obs, id_pix, id_bol) values (?, ?, ?, ?, ?, ?)', (self.id_venda, self.id_status, self.data_hora, self.obs, self.id_pix, self.id_bol))
            return True
        except:
            return False

    def alteraStatus(self):
        conn=db()
        try:
            statusAtual = str(self.getStatusVenda()[0][0])
            novoStatus = conn.execute_bd_com_param("update tb_vendas set status_venda = ? where id_Venda = ?", (self.statusVenda, self.id_venda))
            
            if (int(statusAtual) == 0) and int(self.statusVenda) != 0:
                if self.atualizaEstoque('D'):
                    return True
                else:
                    return False
            elif (int(statusAtual) != 0) and int(self.statusVenda) == 0:
                if self.atualizaEstoque('R'):
                    return True
                else:
                    return False
            else:
                return True
        except:   
            return False

    def atualizaEstoque(self, tipo):
        detalhesVenda = self.getDetVendas()

        for itensVenda in detalhesVenda:
            id_produto = detalhesVenda[0][1]
            qtd_venda = detalhesVenda[0][4]

            detalhesProd = Produtos()
            detalhesProduto = detalhesProd.getProduto(id_produto)
            qtd_produto = detalhesProduto[0][3]

            if tipo == 'R': #R remove do estoque / #D devolve ao estoque
                qtd_final = int(qtd_produto) - int(qtd_venda)
            else:
                qtd_final = int(qtd_produto) + int(qtd_venda)

            if qtd_final >= 0:
                if detalhesProd.alteraQTD(qtd_final, int(id_produto)):
                    return True
                else:
                    return False
            else:
                flash('Quantidade maior que a disponível em estoque!', 'warning')
                return False

    def getAguardaEntrega(self):
        conn=db()
        waitEntrega = conn.execute_bd("SELECT * from vw_vendas where id_status = 2", ('A'))
        return waitEntrega

    def getAguardaPgto(self):
        conn=db()
        waitEntrega = conn.execute_bd("SELECT * from vw_vendas where id_status = 3", ('A'))
        return waitEntrega

    def getNomeStatus(self, status_venda = None):
        conn=db()
        if status_venda == None:
            resultado = conn.execute_bd_com_param("SELECT status_venda from tb_status_venda where id_status = ?", (self.statusVenda,))[0][0]
        else:
            resultado = conn.execute_bd_com_param("SELECT status_venda from tb_status_venda where id_status = ?", (status_venda,))[0][0]
        return resultado

    def getVendasDia(self):
        conn=db()
        hoje = date.today()
        hoje = hoje.strftime("%d/%m/%Y")
        vendasDia = conn.execute_bd_com_param(""" select case when sum(total) is null then 0 else sum(total) end from(
SELECT distinct a.total 
  FROM tb_vendas a
       INNER JOIN
       tb_vendas_movimentacoes b ON a.id_Venda = b.id_venda
 WHERE strftime('%d/%m/%Y', b.data_hora) = ? AND 
       status_venda IN (0, 2) ) """, (hoje,))[0]
        return vendasDia

    def getVendasMes(self, mes=None):
        self.mes = mes
        conn=db()
        if mes == None:
            hoje = date.today()
            self.mes = hoje.strftime("%m/%Y")
            vendasMes = conn.execute_bd_com_param("SELECT case when sum(a.total) is null then 0 else sum(a.total) end from tb_vendas a inner join tb_vendas_movimentacoes b on a.id_venda = b.id_venda where strftime('%m/%Y', b.data_hora) = ? and status_venda in (0, 2)", (self.mes,))[0]
        else:
            vendasMes = conn.execute_bd_com_param("SELECT case when sum(a.total) is null then 0 else sum(a.total) end from tb_vendas a inner join tb_vendas_movimentacoes b on a.id_venda = b.id_venda where strftime('%m/%Y', b.data_hora) = ? and status_venda in (0, 2)", (self.mes,))[0]
        return vendasMes

    def getReceberMes(self, mes=None):
        self.mes = mes
        conn=db()
        if mes == None:
            hoje = date.today()
            self.mes = hoje.strftime("%m/%Y")
            receberMes = conn.execute_bd_com_param("SELECT case when sum(total) is null then 0 else sum(total) end from tb_vendas where strftime('%m/%Y', data_hora) = ? and status_venda = 3", (self.mes,))[0]
        else:
            receberMes = conn.execute_bd_com_param("SELECT case when sum(total) is null then 0 else sum(total) end from tb_vendas where strftime('%m/%Y', data_hora) = ? and status_venda = 3", (self.mes,))[0]
        return receberMes

    def getQtdVendas(self, mes=None):
        self.mes = mes
        conn=db()
        qtdMes = conn.execute_bd_com_param("SELECT count(1) from tb_vendas where strftime('%m/%Y', data_hora) = ? and status_venda in (0, 2)", (self.mes,))[0]
        return qtdMes

    def getStatusVenda(self):
        conn = db()
        statusVenda = conn.execute_bd_com_param('select status_venda from tb_vendas where id_venda = ?', (self.id_venda,))
        return statusVenda

    def alteraVenda(self, id_forma_pgto, taxas, acrescimo, subtotal, total, obs, data_hora, cod_banco):
        self.id_forma_pgto = id_forma_pgto
        self.taxas = taxas
        self.acrescimo = acrescimo
        self.subtotal = subtotal
        self.total = total
        self.obs = obs
        self.data_hora = data_hora
        self.cod_banco = cod_banco

        conn = db()
        try:
            forma_pgto = conn.execute_bd_com_param("update tb_vendas set id_forma_pgto = ?, taxas = ?, acrescimo = ?, subtotal = ?, total = ?, obs = ?, data_hora = ?, cod_banco = ? where id_venda = ?", (self.id_forma_pgto, self.taxas, self.acrescimo, self.subtotal, self.total, self.obs, self.data_hora, self.cod_banco, self.id_venda))
            return True
        except:
            return False

    def insereDadosPix(self, cod_cc = None, url_banco = None, dir_qrcode = None):
        self.cod_cc = cod_cc
        self.url_banco = url_banco
        self.dir_qrcode = dir_qrcode

        conn = db()
        try:
            dados_pix = conn.execute_bd_returnId("insert into tb_vendas_Det_pix (id_venda, cod_cc, url_banco, dir_qrcode) values (?, ?, ?, ?)", (self.id_venda, self.cod_cc, self.url_banco, self.dir_qrcode))
            return True, dados_pix
        except:
            return False, None

    def insereDadosBoleto(self, num_bol = None, valor_bol = None, dt_geracao = None, dt_pgto = None):
        self.num_bol = num_bol
        self.valor_bol = valor_bol
        self.dt_geracao = dt_geracao
        self.dt_pgto = dt_pgto

        conn = db()
        try:
            dados_bol = conn.execute_bd_returnId("insert into tb_vendas_Det_bol (id_venda, numero_boleto, valor_boleto, dt_geracao, dt_pagamento) values (?, ?, ?, ?, ?)", (self.id_venda, self.num_bol, self.valor_bol, self.dt_geracao, self.dt_pgto))
            return True, dados_bol
        except:
            return False, None

class Bancos():
    def getBancos(self):
        conn = db()
        bancos = conn.execute_bd("select id_banco, nome_banco from tb_bancos order by 1 asc", "A")
        return bancos

    def getOperacoes(self):
        conn = db()
        operacoes = conn.execute_bd("select id_operacao, nome_operacao from tb_bancos_OPERACOES order by 1 asc", "A")
        return operacoes

class Clientes():
    def __init__ (self, idCliente = None):
        self.idCliente = idCliente

    def getClientes(self):
        conn = db()
        if self.idCliente == None:
            clientes = conn.execute_bd("select * from vw_clientes order by 1 desc", "A")
        else:
            clientes = conn.execute_bd_com_param("select * from vw_clientes where id_cliente = ? order by 1 desc", (self.idCliente,))
        return clientes

class Notificacoes():
    def __init__ (self, id_notificacao = None, titulo = None, subtitulo = None, conteudo = None, data_hora = None, tipo_notif = None, visualizado = None, categ_notif = None, id_venda = None):
        self.id_notificacao = id_notificacao
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.conteudo = conteudo
        self.data_hora = data_hora
        self.tipo_notif = tipo_notif
        self.visualizado = visualizado
        self.categ_notif = categ_notif
        self.id_venda = id_venda

    def getNotificacoes(self):
        conn = db()
        notifs = conn.execute_bd("select * from VW_NOTIFICACOES where visualizado = 'F' order by 1 desc", 'A')
        return notifs

    def getQtdNotificacoes(self):
        conn = db()
        qtd = conn.execute_bd("select count(1) from TB_NOTIFICACOES where visualizado = 'F'", 'A')
        return qtd

    def removeNotificacoes(self):
        conn = db()
        try:
            conn.execute_bd_com_param("update TB_NOTIFICACOES set visualizado = 'T' where id_notificacao = ?", (self.id_notificacao,))
            return True
        except:
            return False
    
    def insereNotificacoes(self):
        conn = db()
        try:
            conn.execute_bd_com_param("insert into TB_NOTIFICACOES (titulo, subtitulo, conteudo, data_hora, tipo_notif, visualizado, categ_notif, id_venda) values (?, ?, ?, ?, ?, ?, ?, ?)", (self.titulo, self.subtitulo, self.conteudo, self.data_hora, self.tipo_notif, self.visualizado, self.categ_notif, self.id_venda))
            return True
        except:
            return False

class Parametros():
    def __init__ (self, id_param = None, nome_param = None, valor_param = None, id_categ = None):
        self.id_param = id_param
        self.nome_param = nome_param
        self.valor_param = valor_param
        self.id_categ = id_categ

    def getParametros(self):
        conn = db()
        if self.id_param == None:
            listaParams = conn.execute_bd('select * from vw_params where ID_CATEG_PARAM <> 2', 'A')
        else:
            listaParams = conn.execute_bd_com_param('select * from vw_params where ID_CATEG_PARAM <> 2 and id_param = ?', (self.id_param,))
        return listaParams

    def getCateg(self):
        conn = db()
        categ = conn.execute_bd_com_param('select ID_CATEG_PARAM from vw_params where id_param = ?', (self.id_param,))
        return categ

    def getParametrosSocial(self):
        conn = db()
        if self.id_param == None:
            listaParams = conn.execute_bd('select * from vw_params where ID_CATEG_PARAM = 2', 'A')
        else:
            listaParams = conn.execute_bd_com_param('select * from vw_params where ID_CATEG_PARAM = 2 and id_param = ?', (self.id_param,))
        return listaParams

    def alteraParametro(self):
        conn = db()
        try:
            conn.execute_bd_com_param("update TB_PARAMS set valor_param = ? where id_param = ?", (self.valor_param, self.id_param))
            return True
        except:
            return False

class Referencias():
    def __init__ (self, id_referencia = None, id_cliente = None, data_hora = None, comentario = None, exibe_web = None, id_venda = None):
        self.id_referencia = id_referencia
        self.id_cliente = id_cliente
        self.data_hora = data_hora
        self.comentario = comentario
        self.exibe_web = exibe_web
        self.id_venda = id_venda

    def getReferenciasWeb(self):
        conn = db()
        referencias = conn.execute_bd('select * from vw_Referencias where exibe_web = "SIM"', 'A')
        return referencias

    def getListaReferencias(self):
        conn = db()
        referencias = conn.execute_bd('select * from vw_Referencias', 'A')
        return referencias

    def insereReferencias(self):
        conn = db()
        try:
            conn.execute_bd_com_param("insert into TB_rEFERENCIAS (ID_CLIENTE, DATA_HORA, COMENTARIO, EXIBE_WEB, ID_VENDA) values (?, ?, ?, ?, ?)", (self.id_cliente, self.data_hora, self.comentario, self.exibe_web, self.id_venda))
            return True
        except:
            return False

    def removeReferencia(self):
        conn = db()
        try:
            conn.execute_bd_com_param("delete from tb_referencias where id_referencia = ?", (self.id_referencia,))
            return True
        except:
            return False

    def alteraReferencia(self):
        conn = db()
        try:
            status_exibicao = self.getStatusExibicao()
            if status_exibicao == 'T':
                optExibeWeb = 'F'
            else:
                optExibeWeb = 'T'

            conn.execute_bd_com_param("update tb_referencias set exibe_web = ? where id_referencia = ?", (optExibeWeb, self.id_referencia))
            return True
        except:
            return False

    def getStatusExibicao(self):
        conn = db()
        referencias = conn.execute_bd_com_param('select exibe_web from tb_Referencias where id_Referencia = ?', (self.id_referencia,))[0][0]
        return referencias

class Integracoes():
    def __init__ (self, id_integracao = None, nome_integracao = None, status_integracao = None, dir_cert = None, cpf = None, senha = None, propagar_pix = None, propagar_banco = None, utiliza_boleto = None, key = None, chave_preferencial = None, email_integ = None, senha_email = None, id_provedor = None):
        self.id_integracao = id_integracao
        self.nome_integracao = nome_integracao
        self.status_integracao = status_integracao
        self.dir_cert = dir_cert
        self.cpf = cpf
        self.senha = senha
        self.propagar_pix = propagar_pix
        self.propagar_banco = propagar_banco
        self.utiliza_boleto = utiliza_boleto
        self.key = key
        self.chave_preferencial = chave_preferencial
        self.email_integ = email_integ
        self.senha_email = senha_email
        self.id_provedor = id_provedor

    def getIntegracoes(self):
        conn = db()
        integracoes = conn.execute_bd('select * from VW_integracoes', 'A')
        return integracoes

    def getStatusIntegracao(self):
        conn = db()
        status = conn.execute_bd_com_param('select status_integracao from tb_integracoes where id_integracao = ?', (int(self.id_integracao),))
        if len(status) != 0:
            status = status[0][0]
        return status

    def getDadosIntegracaoNubank(self):
        conn = db()
        integracoes = conn.execute_bd('select * from VW_integracoes_nubank', 'A')[0]
        return integracoes

    def getDadosIntegracaoEmail(self):
        conn = db()
        integracoes = conn.execute_bd('select * from VW_integracoes_email', 'A')
        return integracoes

    def getListaEmail(self):
       conn = db()
       lista = conn.execute_bd('select * from tb_email_provedor', 'A')
       return lista

    def getDadosAcessoNubank(self):
        conn = db()
        dados_nubank = self.getDadosIntegracaoNubank()
        cert_dir = dados_nubank[1]
        cpf = dados_nubank[2]
        senha = dados_nubank[3]
        key = dados_nubank[7]

        fernet = Fernet(key)
        cpf = fernet.decrypt(cpf).decode()
        senha = decMessage = fernet.decrypt(senha).decode()

        return cpf, senha, cert_dir

    def getDadosAcessoEmail(self):
        conn = db()
        dados_email = self.getDadosIntegracaoEmail()
        email = dados_email[0][3]
        senha = dados_email[0][4]
        key = dados_email[0][5]

        fernet = Fernet(key)
        senha = decMessage = fernet.decrypt(senha).decode()

        return email, senha

    def alteraAcessoNubank(self):
        conn = db()
        try:
            conn.execute_bd_com_param('update tb_integracoes_nubank set dir_Cert = ?, cpf = ?, pwd = ?, key_crip = ? where id_integracao = ?', (self.dir_cert, self.cpf, self.senha, self.key, self.id_integracao))
            return True
        except:
            return False

    def alteraParamNubank(self):
        conn = db()
        dados_nubank = self.getDadosIntegracaoNubank()
        for dados in dados_nubank:
            cert_dir = dados[1]
            cpf = dados[2]
            senha = dados[3]
        
        try:
            if (cert_dir != None or cpf != None or senha != None):
                if (len(cert_dir) != 0 or len(cpf) != 0 or len(senha) != 0):
                    conn.execute_bd_com_param('update tb_integracoes set status_integracao = ? where id_integracao = ?', (self.status_integracao, self.id_integracao))    
                else:
                    flash('A integração não foi ativada pois os dados de acessos estão incorretos!', 'warning')
                    return False
            else:
                flash('A integração não foi ativada pois os dados de acessos estão incorretos!', 'warning')
                return False
            conn.execute_bd_com_param('update tb_integracoes_nubank set propagar_pix = ?, propagar_banco = ?, utiliza_boleto = ?, chave_preferencial = ? where id_integracao = ?', (self.propagar_pix, self.propagar_banco, self.utiliza_boleto, self.chave_preferencial, self.id_integracao))
            
            if self.utiliza_boleto == 'T':
                optBol = 'A'
                integrada = 'T'
            else:
                optBol = 'I'
                integrada = 'F'
            
            conn.execute_bd_com_param('update tb_forma_pgto set situacao = ?, integrada = ? where id_forma_pgto = 5', (optBol, integrada))

            if self.propagar_pix == 'T':
                situacaoPix = 'A'
                integrada = 'T'
            else:
                situacaoPix = 'A'
                integrada = 'F'
            
            conn.execute_bd_com_param('update tb_forma_pgto set situacao = ?, integrada = ? where id_forma_pgto = 2', (situacaoPix, integrada))
            
            if self.propagar_pix == 'T':
                cpf, senha, cert_dir = self.getDadosAcessoNubank()
                integra_nubank = IntegracaoNubank(cpf = cpf, senha = senha, certificado =cert_dir)
                dados_pix = integra_nubank.getChavesPix()
                index = ''
                if len(dados_pix) != 0:
                    for dados in dados_pix:
                        if dados[0] == 'EMAIL':
                            coluna = 'email_pix'
                        elif dados[0] == 'CPF':
                            coluna = 'cpf_pix'
                        elif dados[0] == 'PHONE':
                            coluna = 'celular_pix'
                    
                        valor = dados[1]
            
                        if self.chave_preferencial != None and self.chave_preferencial == dados[0]: 
                            index = dados[2]
                    
                        conn.execute_bd_com_param('update tb_forma_pgto_integracao set ' + coluna + ' = ?, index_preferencia = ? where id_forma_pgto = 2', (valor, index))
                    flash('Pix propagado com sucesso!', 'success')
            return True
        except:
            return False

    def alteraDadosEmail(self):
        conn = db()
        try:
            conn.execute_bd_com_param('update tb_integracoes_email set id_email = ?, email = ?, pwd = ?, cip_key = ? where id_integracao = ?', (self.id_provedor, self.email_integ, self.senha_email, self.key, self.id_integracao))
            return True
        except:
            return False


class Perfil():
    def __init__ (self, id_cliente = None, id_formaPgto = None):
        self.id_cliente = id_cliente
        self.id_formaPgto = id_formaPgto

    def validaPerfilCheckout(self):
        conn = db()
        dados_user = conn.execute_bd_com_param('select * from vw_perfuser where id_cliente = ?', (self.id_cliente,))[0]
        sobrenome = dados_user[2]
        user_picpay = dados_user[13]

        if int(self.id_formaPgto) == 1:
            if user_picpay == '':
                return False, 'picpay'
            return True, ''
        else:
            if sobrenome == '':
                return False, 'nomeCompleto'
            return True, ''

        