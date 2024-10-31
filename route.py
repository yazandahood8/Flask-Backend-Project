from flask import Blueprint, request, jsonify
from models import db, QA  # Import database instance and QA model
from services import get_answer_from_openai  # Import the OpenAI service function
import openai  # Import OpenAI library for interacting with their API
import logging  # Import logging to track errors

# Setup logging to capture errors
logging.basicConfig(level=logging.INFO)

# Define a Blueprint for routes
routes = Blueprint('routes', __name__)

# Define the `/ask` endpoint that accepts POST requests
@routes.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'Question is required!'}), 400

    try:
        # Get answer from OpenAI
        answer = get_answer_from_openai(question)

        # Store the question and answer in the database
        new_qa = QA(question=question, answer=answer)
        db.session.add(new_qa)
        db.session.commit()

        # Return the question and answer as a JSON response
        return jsonify({'question': question, 'answer': answer})

    except openai.error.RateLimitError as e:
        logging.error(f"Quota exceeded: {e}")
        return jsonify({'error': 'You have exceeded your OpenAI quota. Please check your plan and billing details.'}), 429

    except Exception as e:
        logging.error(f"Error occurred: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
