from flask import Flask, jsonify
import pandas as pd
import os

app = Flask(__name__)

@app.route('/tickets', methods=['GET'])
def get_tickets():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'processed', 'cleaned_tickets.xlsx')
    df = pd.read_excel(file_path)
    return jsonify(df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
