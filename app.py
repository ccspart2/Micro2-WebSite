from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('main.html')


@app.route("/<direction>")

def move(direction):

    # Choose the direction of the request
    print(direction)
    print(direction.split('*',1))
    return "success!"
    '''
    if direction == 'left':
        return 'izquierda'
    elif direction == 'right':
        return 'derecha'
    elif direction == 'up':
        return 'arriba'
    elif direction == 'down':
        return 'abajo'
	'''
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
