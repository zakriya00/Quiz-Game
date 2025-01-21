from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np

app = Flask(__name__)

# Load the trained model
model = joblib.load('color_mood_regressor.pkl')

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




if __name__ == '__main__':
    app.run(debug=True)
