import smtplib

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from pynubank import Nubank
from .db_func import *
from .. import views
from pathlib import Path
from datetime import datetime

class IntegracaoNubank():
    def __init__ (self, cpf = None, senha = None, certificado = None, valor = None, index_preferencia = None):
        self.cpf = cpf
        self.senha = senha
        basedir = Path(__file__).parent.parent
        self.certificado = os.path.join(basedir, views.app.UPLOAD_FOLDER_CERTIFICADO, certificado)
        self.valor = valor
        if index_preferencia == None:
            index_preferencia = 0
        self.index_preferencia = int(index_preferencia)

    def testaConexao(self):
        nu = Nubank()
        try:
            nu.authenticate_with_cert(self.cpf, self.senha, self.certificado)
            return True
        except:
            return False

    def getChavesPix(self):  
        nu = Nubank()
        nu.authenticate_with_cert(self.cpf, self.senha, self.certificado)

        chaves = nu.get_available_pix_keys()

        lista_chaves = []
        count = 0

        if len(chaves['keys']) != 0:
            for chaves_pix_dict in chaves['keys']:
                dados = chaves_pix_dict['kind'], chaves_pix_dict['formattedValue'].replace('\xa0', ' '), count
                lista_chaves.append(dados)
                count = count+1
        return lista_chaves

    def geraPgtoPix(self):
        try:
            nu = Nubank()
            nu.authenticate_with_cert(self.cpf, self.senha, self.certificado)
            data = nu.get_available_pix_keys()
            money_request = nu.create_pix_payment_qrcode(data['account_id'], self.valor, data['keys'][self.index_preferencia])

            qr = money_request['qr_code']
            img = qr.make_image()

            now = datetime.now(tz=tz)
            dt_string = now.strftime("%d%m%Y %H%M%S")
            
            basedir = Path(__file__).parent.parent
            imgname = str(self.cpf) + str(dt_string) +'.png'
            full_path = os.path.join(basedir, views.app.config['UPLOAD_FOLDER_QRCODE'], imgname)
            img.save(full_path)
            
            urlpay = money_request['payment_url']

            return True, imgname, urlpay, payment_code
        except:
            return False, None, None, None

    def geraPgtoBoleto(self):
        if float(self.valor) < 10:
            return False, None

        try:
            nu = Nubank()
            nu.authenticate_with_cert(self.cpf, self.senha, self.certificado)
            boleto = nu.create_boleto(self.valor)
            return True, boleto
        except:
            return False, None

class IntegracaoEmail():
    def __init__ (self, provedor = None, email = None, senha = None, destinatario = None, assunto = None, conteudo = None, imagem = None):
        self.provedor = provedor
        self.email = email
        self.senha = senha
        self.destinatario = destinatario
        self.assunto = assunto
        self.conteudo = conteudo
        self.imagem = imagem

    def testaConexao(self):        
        msg = MIMEText('Teste validado com sucesso!')
        msg['Subject'] = 'Teste de integração'
        msg['From'] = self.email
        msg['To'] = self.email
         
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(self.email, self.senha)
            server.sendmail(self.email, [self.email], msg.as_string())
            server.close()
            
            return True
        except:
            return False

    def enviarEmail(self):    
        if self.imagem == None:
            msg = MIMEText(self.conteudo)
            
        else:
            with open(self.imagem, 'rb') as f:
                img_data = f.read()
            
            msg = MIMEMultipart()
            text = MIMEText(self.conteudo)
            msg.attach(text)
            image = MIMEImage(img_data, name=os.path.basename(self.imagem))
            msg.attach(image)

        msg['Subject'] = self.assunto
        msg['From'] = self.email
        msg['To'] = self.destinatario

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(self.email, self.senha)
            server.sendmail(self.email, [self.destinatario], msg.as_string())
            server.close()           
            return True
        except:
            return False


