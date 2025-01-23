from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
import joblib
import numpy as np
import pickle
import random
from fpdf import FPDF
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

### Color Matching Game
# Load the trained model
model = joblib.load('models/color_mood_regressor.pkl')

# Function to convert hex color to RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

@app.route('/')
def index():
    session.clear()  # Clear session data at the start
    return render_template('index.html')

@app.route('/color')
def color():
    return render_template('color.html')

@app.route('/predict-mood', methods=['POST'])
def predict_mood():
    data = request.get_json()
    selected_colors = data.get('colors', [])

    if not selected_colors:
        return jsonify({"error": "No colors selected"}), 400

    total_intensity = 0
    for color in selected_colors:
        rgb = hex_to_rgb(color)
        intensity = model.predict([rgb])[0]
        total_intensity += intensity

    avg_intensity = total_intensity / len(selected_colors)

    if avg_intensity > 0.7:
        predicted_mood = "Happy"
    elif avg_intensity > 0.4:
        predicted_mood = "Neutral"
    else:
        predicted_mood = "Sad"

    session['color_game_result'] = {
        "predicted_mood": predicted_mood,
        "mood_intensity": avg_intensity
    }
    session['color_game_completed'] = True  # Mark color game as completed
    return jsonify({"predicted_mood": predicted_mood, "mood_intensity": avg_intensity})

### Art Game
@app.route('/art_image_feedback', methods=['GET', 'POST'])
def art_image_feedback():
    if request.method == 'POST':
        feedback = [int(request.form.get(f"image{i}")) for i in range(1, 7)]
        depression_status = predict_depression(feedback)
        
        session['art_game_result'] = {
            "feedback": feedback,
            "depression_status": depression_status
        }
        session['art_game_completed'] = True
        
        # Return result to same template
        return render_template('art_therapy.html', 
                            depression_status=depression_status,
                            show_result=True)

    return render_template('art_therapy.html', show_result=False)

def predict_depression(feedback):
    avg_feedback = np.mean(feedback)
    if avg_feedback <= 1:
        return "Severe depressive symptoms"
    elif avg_feedback <= 2:
        return "Moderate depressive symptoms"
    elif avg_feedback <= 3:
        return "Mild depressive symptoms"
    elif avg_feedback <= 4:
        return "Neutral state"
    else:
        return "Good mental health"

### Quiz Game
quiz_model = pickle.load(open('models/quiz.pkl', 'rb'))

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/quiz_predict', methods=['POST'])
def quiz_predict():
    data = request.get_json()
    if not data or 'answers' not in data:
        return jsonify({'error': 'Invalid input'}), 400
        
    answers = data['answers']
    if len(answers) != 9:
        return jsonify({'error': 'Expected 9 answers'}), 400

    try:
        prediction = quiz_model.predict([answers])[0]
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    session['quiz_game_result'] = {"depression_level": prediction}
    session['quiz_game_completed'] = True
    return jsonify({
        'depression_level': prediction,
        'redirect': url_for('emoji_game')
    })




### Emoji Game
with open('models/emoji_mood_model.pkl', 'rb') as model_file:
    emoji_model = pickle.load(model_file)

with open('models/label_encoder.pkl', 'rb') as le_file:
    label_encoder = pickle.load(le_file)

emoji_to_num = {
    '😊': 1, '😃': 2, '😄': 3, '😎': 4, '😇': 5,
    '😢': 6, '😞': 7, '😔': 8, '😱': 9, '😂': 10
}
possible_emojis = ['😊', '😃', '😄', '😎', '😇', '😢', '😞', '😔', '😱', '😂']
selected_emojis = []

@app.route('/emoji_game')
def emoji_game():
    global selected_emojis
    selected_emojis = []  # Reset when starting new game
    emojis_for_round = random.sample(possible_emojis, 4)
    return render_template('emoji.html', emojis=emojis_for_round, round=1)

# Update the select_emoji route to track rounds
@app.route('/select_emoji', methods=['POST'])
def select_emoji():
    global selected_emojis

    selected_emoji = request.form['emoji']
    selected_emojis.append(selected_emoji)
    
    current_round = len(selected_emojis) + 1
    

    if len(selected_emojis) == 5:
        return redirect(url_for('analyze'))
    else:
        emojis_for_round = random.sample(possible_emojis, 4)
        return render_template('emoji.html', emojis=emojis_for_round, round=current_round)

### Update the analyze route in app.py
@app.route('/analyze')
def analyze():
    global selected_emojis
    emoji_nums = [emoji_to_num[emoji] for emoji in selected_emojis]
    prediction = emoji_model.predict([emoji_nums])[0]
    mood = label_encoder.inverse_transform([prediction])[0]

    session['emoji_game_result'] = {
        "selected_emojis": selected_emojis,
        "predicted_mood": mood
    }
    session['emoji_game_completed'] = True

    selected_emojis = []
    
    # Check if all games completed
    if all(session.get(f'{game}_game_completed') for game in ['color', 'art', 'quiz', 'emoji']):
        return redirect(url_for('generate_report'))
    else:
        return redirect(url_for('index'))


class UnicodePDF(FPDF):
    def header(self):
        # Custom header if needed
        pass

    def footer(self):
        # Custom footer if needed
        pass

    def add_unicode_text(self, text):
        # Replace or remove unsupported characters
        cleaned_text = self.clean_text(text)
        self.multi_cell(0, 8, txt=cleaned_text)

    def clean_text(self, text):
        # Replace emojis with text descriptions
        emoji_map = {
            '😊': '[Smiling Face]',
            '😃': '[Grinning Face]',
            '😄': '[Grinning Face with Smiling Eyes]',
            '😎': '[Smiling Face with Sunglasses]',
            '😇': '[Smiling Face with Halo]',
            '😢': '[Crying Face]',
            '😞': '[Disappointed Face]',
            '😔': '[Pensive Face]',
            '😱': '[Face Screaming in Fear]',
            '😂': '[Face with Tears of Joy]'
        }
        
        # Replace emojis using the mapping
        for emoji, desc in emoji_map.items():
            text = text.replace(emoji, desc)
        
        return text

### Generate Report (Updated)
@app.route('/generate_report')
def generate_report():
    if not all(session.get(f'{game}_game_completed', False) for game in ['color', 'art', 'quiz', 'emoji']):
        return redirect(url_for('index'))

    # Get game results
    color_result = session.get('color_game_result', {})
    art_result = session.get('art_game_result', {})
    quiz_result = session.get('quiz_game_result', {})
    emoji_result = session.get('emoji_game_result', {})

    # Create PDF with Unicode support
    report = UnicodePDF()
    report.add_page()
    report.set_font("Arial", size=12)

    # Header
    report.set_font('Arial', 'B', 16)
    report.cell(200, 10, txt="Comprehensive Mental Health Assessment Report", ln=True, align='C')
    report.ln(10)

    # Patient Demographics
    report.set_font('Arial', 'B', 12)
    report.cell(200, 10, txt="Patient Demographics", ln=True)
    report.set_font('Arial', '', 12)
    report.cell(200, 10, txt=f"Assessment Date: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    report.cell(200, 10, txt="Clinical Setting: Digital Screening", ln=True)
    report.ln(8)

    # Presenting Concerns
    report.set_font('Arial', 'B', 12)
    report.cell(200, 10, txt="Presenting Concerns", ln=True)
    report.set_font('Arial', '', 12)
    concerns = f"The patient has completed a series of gamified mental health assessments. The results indicate the following:\n\n"
    concerns += f"- Emotional State: {color_result.get('predicted_mood', 'N/A')}\n"
    concerns += f"- Mood Intensity: {color_result.get('mood_intensity', 0):.2f}/1.0\n"
    concerns += f"- Depression Status: {art_result.get('depression_status', 'N/A')}\n"
    concerns += f"- Depression Level (Quiz): {quiz_result.get('depression_level', 'N/A')}\n"
    concerns += f"- Predicted Mood (Emoji Game): {emoji_result.get('predicted_mood', 'N/A')}\n"
    report.add_unicode_text(concerns)
    report.ln(8)

    # Detailed Analysis
    report.set_font('Arial', 'B', 12)
    report.cell(200, 10, txt="Detailed Analysis", ln=True)
    report.set_font('Arial', '', 12)
    analysis = f"1. **Color Game Results**:\n"
    analysis += f"   - The patient's selected colors indicate a predominant mood of {color_result.get('predicted_mood', 'N/A')}.\n"
    analysis += f"   - The mood intensity score of {color_result.get('mood_intensity', 0):.2f}/1.0 suggests a {color_result.get('predicted_mood', 'N/A')} emotional state.\n\n"
    analysis += f"2. **Art Therapy Game Results**:\n"
    analysis += f"   - The patient's feedback on the art images suggests {art_result.get('depression_status', 'N/A')}.\n"
    analysis += f"   - This indicates a {art_result.get('depression_status', 'N/A').lower()} level of depressive symptoms.\n\n"
    analysis += f"3. **Quiz Game Results**:\n"
    analysis += f"   - The patient's responses to the quiz indicate a depression level of {quiz_result.get('depression_level', 'N/A')}.\n"
    analysis += f"   - This suggests a {quiz_result.get('depression_level', 'N/A').lower()} level of depressive symptoms.\n\n"
    analysis += f"4. **Emoji Game Results**:\n"
    analysis += f"   - The patient's selected emojis suggest a mood of {emoji_result.get('predicted_mood', 'N/A')}.\n"
    analysis += f"   - The selected emojis were: {', '.join(emoji_result.get('selected_emojis', []))}.\n\n"
    report.add_unicode_text(analysis)
    report.ln(8)

    # Clinical Recommendations
    report.set_font('Arial', 'B', 12)
    report.cell(200, 10, txt="Clinical Recommendations", ln=True)
    report.set_font('Arial', '', 12)
    recommendations = f"Based on the assessment results, the following recommendations are made:\n\n"
    recommendations += f"- **Follow-Up Consultation**: It is recommended that the patient schedule a follow-up consultation with a mental health professional for a more detailed evaluation.\n"
    recommendations += f"- **Therapeutic Interventions**: Depending on the severity of the symptoms, therapeutic interventions such as Cognitive Behavioral Therapy (CBT) or counseling may be beneficial.\n"
    recommendations += f"- **Lifestyle Modifications**: Encouraging the patient to engage in regular physical activity, maintain a balanced diet, and ensure adequate sleep can help improve overall mental well-being.\n"
    recommendations += f"- **Support Systems**: The patient should be encouraged to seek support from family, friends, or support groups to help manage their mental health.\n"
    report.add_unicode_text(recommendations)
    report.ln(8)

    # Save and return report
    report_path = os.path.join('reports', 'clinical_report.pdf')
    os.makedirs('reports', exist_ok=True)
    report.output(report_path)

    return send_file(report_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)