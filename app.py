from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
import os
from symspellpy import SymSpell, Verbosity
import sys
import language_tool_python
import nltk
from nltk.corpus import wordnet
import re

# Download wordnet if not already downloaded
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Get dataset path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(BASE_DIR, "dict1.csv")

# Load the dictionary dataset
def load_dictionary():
    try:
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        df = pd.read_csv(dataset_path)
        # Ensure the columns exist
        if "word" not in df.columns:
            raise ValueError("CSV must contain a 'word' column.")
        df = df.dropna(subset=["word"])
        df["word"] = df["word"].astype(str).str.strip().str.lower()
        return set(df["word"].tolist())
    except Exception as e:
        print(f"Error loading dictionary: {e}")
        return set()

correct_words = load_dictionary()

# Initialize SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=4, prefix_length=7)

dictionary_path = os.path.join(BASE_DIR, "frequency.txt")
if not os.path.exists(dictionary_path):
    print(f"Dictionary not found: {dictionary_path}", file=sys.stderr)
    sys.exit(1)
if not sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1):
    print("Dictionary not found or failed to load.", file=sys.stderr)
    sys.exit(1)

tool = language_tool_python.LanguageTool('en-US')
common_words = ["machine", "learning", "not", "like", "do"]
for word in common_words:
    sym_spell.create_dictionary_entry(word, 100000)

def get_best_match(word):
    if word.lower() in correct_words:
        return word
    suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=4)
    return suggestions[0].term if suggestions else word

def correct_spelling(text):
    words = re.findall(r'\b\w+\b|[.,!?;]', text)
    corrected_words = [get_best_match(word) if word.isalpha() else word for word in words]
    # Fix spacing: add space before words, not before punctuation
    result = ""
    for i, word in enumerate(corrected_words):
        if i == 0:
            result += word
        elif word in ".,!?;":
            result += word
        else:
            result += " " + word
    return result

def check_grammar(text):
    matches = tool.check(text)
    corrected_text = language_tool_python.utils.correct(text, matches)
    return corrected_text

def check_meaning(word):
    return bool(wordnet.synsets(word))

def correct_text_pipeline(text):
    spell_checked = correct_spelling(text)
    grammar_checked = check_grammar(spell_checked)
    return grammar_checked

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask server is running!"})

@app.route("/correct", methods=["POST"])
def correct_text():
    try:
        data = request.json
        if not data or "text" not in data:
            return jsonify({"error": "No text provided"}), 400
        paragraph = data["text"].strip()
        if not paragraph:
            return jsonify({"error": "Text is empty"}), 400
        corrected_paragraph = correct_text_pipeline(paragraph)
        return jsonify({"corrected_text": corrected_paragraph})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while processing the request."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)