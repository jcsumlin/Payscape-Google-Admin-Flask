import configparser

import googleapiclient
from flask import Flask, render_template, request

from main import gmail_admin

config = configparser.ConfigParser()
config.read('auth.ini')

app = Flask(__name__)

Sandbox = ['sandbox', 'test', '0', 'not live']
if config.get('auth', 'environment').lower() in Sandbox:
    sandbox = True
else:
    sandbox = False

@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html', sandbox=sandbox)

@app.route('/output', methods = ['POST'])
def output():
    try:
        try:
            auth = request.form['auth']
        except:
            auth = None
        print(auth)
        g = gmail_admin()
        SF_Results = g.check_for_new_user(g.login_to_salesforce())
        if SF_Results is not False:
            output = g.create_email(SF_Results, auth)
        else:
            output = ("No user matching the criteria was found!")
            print(output)
        return render_template('index.html', sandbox=sandbox, output=output, reset=True)
    except googleapiclient.errors.HttpError as err:
        print(err)
        return render_template('index.html', sandbox=sandbox, output=err, reset=True)
    except Exception as e:
        print(e)
        return render_template('index.html', sandbox=sandbox, output=e, reset=True)

@app.route('/auth')
def auth():
    g = gmail_admin()
    g.open_auth()
    return render_template('index.html', sandbox=sandbox)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
