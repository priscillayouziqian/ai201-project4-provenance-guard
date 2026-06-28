from flask import Flask, request, jsonify
from dotenv import load_dotenv
from signals.groq_signal import get_groq_score
from storage.audit_log import write_log, read_log, create_entry
import uuid
import os

load_dotenv()

app = Flask(__name__)

def get_label(score: float) -> str:
    if score > 0.75:
        return ("Our system believes this content was created by AI. "
                "Confidence: High. If you are the creator and believe this "
                "is incorrect, you may submit an appeal.")
    elif score >= 0.40:
        return ("Our system was unable to confidently determine whether this "
                "content was written by a human or AI. If you are the creator, "
                "you may submit an appeal to provide more context.")
    else:
        return ("Our system believes this content was created by a human. "
                "Confidence: High. If you believe this assessment is incorrect, "
                "you may submit an appeal.")

def get_attribution(score: float) -> str:
    if score > 0.75:
        return "likely_ai"
    elif score >= 0.40:
        return "uncertain"
    else:
        return "likely_human"

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()

    # Validation
    if not data or "text" not in data or "creator_id" not in data:
        return jsonify({"error": "Missing required fields: text, creator_id"}), 400

    text = data["text"]
    creator_id = data["creator_id"]

    if len(text.strip()) < 50:
        return jsonify({"error": "Text too short. Minimum 50 characters required."}), 400

    # Generate unique ID
    content_id = str(uuid.uuid4())

    # Signal 1: Groq LLM
    groq_score = get_groq_score(text)

    # Placeholder confidence (will update in M4)
    confidence = groq_score

    # Generate attribution and label
    attribution = get_attribution(confidence)
    label = get_label(confidence)

    # Write to audit log
    entry = create_entry(content_id, creator_id, attribution, 
                         confidence, groq_score)
    write_log(entry)

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": round(confidence, 2),
        "label": label
    }), 200


@app.route("/log", methods=["GET"])
def get_log():
    content_id = request.args.get("content_id")
    logs = read_log()
    if content_id:
        logs = [e for e in logs if e["content_id"] == content_id]
    return jsonify({"entries": logs}), 200


if __name__ == "__main__":
    app.run(debug=True)