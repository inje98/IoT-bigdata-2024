from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 데이터베이스 모델 정의
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    box_num = db.Column(db.String(50), nullable=False, unique=True)
    phone_num = db.Column(db.String(50), nullable=False)
    rand_num = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 데이터베이스 및 테이블 생성
def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def get_data():
    users = User.query.all()
    data = {
        'hour': [],
        'count': [],
        'data': []
    }
    
    df = pd.DataFrame([{
        'hour': user.created_at.hour,
        'count': 1,
        'box_num': user.box_num,
        'phone_num': user.phone_num
    } for user in users])

    df_grouped = df.groupby('hour').agg({
        'count': 'sum',
        'box_num': lambda x: list(x),
        'phone_num': lambda x: list(x)
    }).reset_index()

    # Fill in missing hours with zero counts
    all_hours = range(24)
    for hour in all_hours:
        if hour not in df_grouped['hour'].values:
            df_grouped = pd.concat([
                df_grouped,
                pd.DataFrame({'hour': [hour], 'count': [0], 'box_num': [[]], 'phone_num': [[]]})
            ], ignore_index=True)

    df_grouped = df_grouped.sort_values(by='hour').reset_index(drop=True)

    for index, row in df_grouped.iterrows():
        data['hour'].append(f'{row["hour"]:02d}:00')  # Formatting hours as HH:MM
        data['count'].append(row['count'])
        data['data'].append({
            'box_num': row['box_num'],
            'phone_num': row['phone_num']
        })

    return jsonify(data)

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    data = [{
        'id': user.id,
        'box_num': user.box_num,
        'phone_num': user.phone_num,
        'rand_num': user.rand_num,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for user in users]
    return jsonify(data)

@app.route('/user', methods=['POST'])
def add_user():
    data = request.json
    new_user = User(
        box_num=data['box_num'],
        phone_num=data['phone_num'],
        rand_num=data['rand_num']
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User added successfully!"}), 201

@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully!"})
    return jsonify({"message": "User not found!"}), 404

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=10110)
