from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np

app = Flask(__name__)

# Load trained model
model = pickle.load(open('model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json['answers']
    
    # Ensure we have exactly 9 features
    if len(data) != 9:
        return jsonify({'error': 'Invalid input, expected 9 answers'}), 400
    
    prediction = model.predict([data])  # Predict depression level
    return jsonify({'depression_level': prediction[0]})

if __name__ == '__main__':
    app.run(debug=True)
