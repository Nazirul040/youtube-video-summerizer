from flask import Flask, render_template, request, jsonify, redirect, url_for
import time
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

app = Flask(__name__)

#youtube summerizer code
ytapi = YouTubeTranscriptApi()
def get_summary_from_url(url):
    try:
        video_id = url.split('watch?v=')[-1]
        transcript = ytapi.fetch(video_id)
    except Exception as e:
        transcript = YouTubeTranscriptApi.fetch(video_id)

    prompt = ""
    for snipet in transcript:
        prompt += snipet.text

    load_dotenv()

    try:
        client = genai.Client() 
        print("Gemini client initialized successfully.")
    except Exception as e:
        print("Error initializing the client.")
        print("Please ensure the GEMINI_API_KEY is correctly set in your .env file.")
        print(f"Details: {e}")
        return "Configuration Error: API Key not found."

    try:
        print("Sending Request...")
        response = client.models.generate_content(
            model = "gemini-2.5-flash",
            contents=f"summarize the text for me -- {prompt}"
        )
        return response.text

    except APIError as e:
        return "An API error occurred"
        
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


#flask app routes
@app.route('/', methods=['GET', 'POST'])
def home():
    # If the HTML form action is "/" (default in some versions), handle the POST here
    if request.method == 'POST':
        return summarize()
    return render_template('index.html')

@app.route('/summarize', methods=['GET', 'POST'])
def summarize():
    # If someone tries to access /summarize directly via URL (GET), redirect to home to avoid 405 error
    if request.method == 'GET':
        return redirect(url_for('home'))

    # The frontend form sends data as form-data, not JSON, because of the standard <form> submission.
    # However, if using the previous JS logic, it sends JSON. 
    # The provided HTML uses <form action="/" method="POST"> which sends form-data.
    # BUT the provided python code uses `request.get_json()`.
    # To support the provided HTML (which does a standard POST), we must check form data.
    
    if request.is_json:
        data = request.get_json()
        video_url = data.get('url')
    else:
        video_url = request.form.get('url')

    if not video_url:
        # If standard form submit, we render template with error
        if not request.is_json:
            return render_template('index.html', error='Please provide a valid URL', url_value='')
        return jsonify({'error': 'Please provide a valid URL'}), 400

    try:
        summary_text = get_summary_from_url(video_url)
        
        # If standard form submit, render template with summary
        if not request.is_json:
             return render_template('index.html', summary=summary_text, url_value=video_url)
             
        return jsonify({'summary': summary_text})
    except Exception as e:
        if not request.is_json:
            return render_template('index.html', error=str(e), url_value=video_url)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)