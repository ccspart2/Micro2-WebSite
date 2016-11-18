from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route("/<command>")
def getCommand(command):

    # Choose the command of the request
    print(command)
    
    
    return "success!"
    
    
    
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
