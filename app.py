from flask import Flask, request, jsonify  # Import Flask and utility functions for handling requests and responses
from models import db, QA  # Import database instance and the QA model
from config import Config  # Import the configuration class
from services import get_answer_from_openai  # Import the OpenAI service function
import openai  # Import the OpenAI library for interacting with their API
import logging  # Import logging to track errors
from flask_migrate import Migrate  # Import Flask-Migrate

# Initialize the Flask application
app = Flask(__name__)  # Create a Flask app instance
app.config.from_object(Config)  # Load the app configuration from a config file

# Initialize database
db.init_app(app)  # Initialize the database with the Flask app
migrate = Migrate(app, db)  # Add Migrate functionality

# Use app context to create tables
with app.app_context():  # Create an app context to interact with the database
    db.create_all()  # Create the tables in the database (if they don’t exist)

# Setup logging to capture errors
logging.basicConfig(level=logging.INFO)  # Setup logging for information and error tracking

# Define the `/ask` endpoint that accepts POST requests
@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()  # Get the JSON data from the request body
    question = data.get('question')  # Extract the "question" field from the JSON

    if not question:  # If no question is provided
        return jsonify({'error': 'Question is required!'}), 400  # Return a 400 error (bad request)

    try:
        # Get answer from OpenAI
        answer = get_answer_from_openai(question)  # Call the service to get the answer from OpenAI

        # Store the question and answer in the database
        new_qa = QA(question=question, answer=answer)  # Create a new QA entry with the question and answer
        db.session.add(new_qa)  # Add the new QA entry to the session
        db.session.commit()  # Commit the transaction to save the entry to the database

        # Return the question and answer as a JSON response
        return jsonify({'question': question, 'answer': answer})

    except openai.error.RateLimitError as e:  # Handle quota exceeded errors from OpenAI
        logging.error(f"Quota exceeded: {e}")  # Log the error
        return jsonify({'error': 'You have exceeded your OpenAI quota. Please check your plan and billing details.'}), 429  # Return a 429 error

    except Exception as e:  # Handle any other unexpected errors
        logging.error(f"Error occurred: {e}", exc_info=True)  # Log the full stack trace for debugging
        return jsonify({'error': str(e)}), 500  # Return a 500 error (internal server error)

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)  # Run the app in debug mode
