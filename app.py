from flask import Flask, request, jsonify, render_template, redirect, url_for
import joblib
import numpy as np
import pickle
import random

app = Flask(__name__)


### Color matching Game
# Load the trained model
model = joblib.load('models/color_mood_regressor.pkl')

# Function to convert hex color to RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict-mood', methods=['POST'])
def predict_mood():
    # Get the selected color(s) from the request
    data = request.get_json()
    selected_colors = data.get('colors', [])

    if not selected_colors:
        return jsonify({"error": "No colors selected"}), 400

    # Aggregate mood intensity for the selected colors
    total_intensity = 0

    for color in selected_colors:
        rgb = hex_to_rgb(color)
        intensity = model.predict([rgb])[0]
        total_intensity += intensity

    # Calculate the average intensity
    avg_intensity = total_intensity / len(selected_colors)

    # Determine mood based on the average intensity
    if avg_intensity > 0.7:
        predicted_mood = "Happy"
    elif avg_intensity > 0.4:
        predicted_mood = "Neutral"
    else:
        predicted_mood = "Sad"

    return jsonify({"predicted_mood": predicted_mood, "mood_intensity": avg_intensity})



### Art Game
@app.route('/art_image_feedback', methods=['GET', 'POST'])
def art_image_feedback():
    if request.method == 'POST':
        # Get the user's feedback on the images
        feedback = []
        for i in range(1, 6):
            feeling = request.form.get(f"image{i}")
            feedback.append(int(feeling))

        # Predict depression based on feedback
        depression_status = predict_depression(feedback)

        return render_template('result.html', depression_status=depression_status)

    return render_template('art_therapy.html')

def predict_depression(feedback):
    # Calculate the average feedback score
    avg_feedback = np.mean(feedback)

    # Generate depression suggestions based on the average feedback score
    if avg_feedback <= 1:
        return "It seems you may be experiencing severe depressive symptoms. Please consider seeking professional help immediately."
    elif avg_feedback <= 2:
        return "You may be experiencing symptoms of depression. It's important to reach out to a healthcare professional for guidance."
    elif avg_feedback <= 3:
        return "You may be feeling low. Consider talking to someone you trust or a mental health professional to help you through this."
    elif avg_feedback <= 4:
        return "You seem to be in a neutral state. If you feel like you're struggling, it's okay to seek support from friends, family, or a counselor."
    else:
        return "You are in good mental health. Keep up the positive mindset, and remember, it's always good to check in on your mental well-being."


### Quiz Game
# Load the Quiz model
quiz_model = pickle.load(open('models/quiz.pkl', 'rb'))

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/quiz_predict', methods=['POST'])
def quiz_predict():
    data = request.json['answers']
    
    # Ensure we have exactly 9 features
    if len(data) != 9:
        return jsonify({'error': 'Invalid input, expected 9 answers'}), 400
    
    prediction = quiz_model.predict([data])  # Predict depression level
    return jsonify({'depression_level': prediction[0]})


### Emoji Game
# Load the pre-trained model and label encoder
with open('models/emoji_mood_model.pkl', 'rb') as model_file:
    emoji_model = pickle.load(model_file)

with open('models/label_encoder.pkl', 'rb') as le_file:
    label_encoder = pickle.load(le_file)

# Define emoji to number mapping (same as in training)
emoji_to_num = {
    '😊': 1, '😃': 2, '😄': 3, '😎': 4, '😇': 5,
    '😢': 6, '😞': 7, '😔': 8, '😱': 9, '😂': 10
}

# List of possible emojis for each round
possible_emojis = ['😊', '😃', '😄', '😎', '😇', '😢', '😞', '😔', '😱', '😂']

# Store selected emojis globally (for simplicity)
selected_emojis = []

@app.route('/emoji_game')
def emoji_game():
    # Select 4 random emojis for the round
    emojis_for_round = random.sample(possible_emojis, 4)
    return render_template('emoji.html', emojis=emojis_for_round)

@app.route('/select_emoji', methods=['POST'])
def select_emoji():
    global selected_emojis

    # Get selected emoji from the form
    selected_emoji = request.form['emoji']
    selected_emojis.append(selected_emoji)
    
    # If 5 rounds are completed, analyze the result
    if len(selected_emojis) == 5:
        return redirect(url_for('analyze'))
    else:
        # If not yet 5 rounds, show the next round with different emojis
        emojis_for_round = random.sample(possible_emojis, 4)
        return render_template('emoji.html', emojis=emojis_for_round)

@app.route('/analyze')
def analyze():
    global selected_emojis
    
    # Convert selected emojis to numerical values
    emoji_nums = [emoji_to_num[emoji] for emoji in selected_emojis]
    
    # Predict mood using the model
    prediction = emoji_model.predict([emoji_nums])
    mood = prediction[0]
    
    # Decode the prediction (mood)
    mood_labels = label_encoder.inverse_transform([mood])
    predicted_mood = mood_labels[0]
    
    # Reset selected emojis for the next game
    selected_emojis = []
    
    return render_template('emoji_result.html', predicted_mood=predicted_mood)



if __name__ == '__main__':
    app.run(debug=True)
