from os import environ
from E_Commerce import app

if __name__ == '__main__':
    app.config['SERVER_NAME'] = 'teste.local:5000'
    
    app.run(host='0.0.0.0', port='5000', debug=True)
