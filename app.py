from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # 用于会话管理
db = SQLAlchemy(app)
CORS(app)

# Player 模型，保存玩家信息
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

# Score 模型，保存玩家得分记录
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    game_date = db.Column(db.DateTime, default=datetime.utcnow)

# 初始化数据库
with app.app_context():
    db.create_all()

# 首页，展示登录界面
@app.route('/')
def home():
    return render_template('index.html')

# 玩家注册（POST）
@app.route('/players', methods=['POST'])
def add_player():
    data = request.get_json()
    username = data['username']
    existing_player = Player.query.filter_by(username=username).first()
    if existing_player:
        return jsonify({'message': 'Username already exists'}), 400
    new_player = Player(username=username)
    db.session.add(new_player)
    db.session.commit()
    return jsonify({'message': 'Player created', 'player_id': new_player.id}), 201

# 获取玩家（GET）
@app.route('/players', methods=['GET'])
def get_players():
    username = request.args.get('username')
    player = Player.query.filter_by(username=username).first()
    if player:
        return jsonify([{'id': player.id, 'username': player.username}])
    else:
        return jsonify([]), 404

# 玩家登录并获取得分记录（GET）
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    player = Player.query.filter_by(username=username).first()
    if player:
        # 如果登录成功，保存玩家到 session
        session['username'] = username
        return jsonify({'message': f'Welcome {username}!'}), 200
    else:
        return jsonify({'message': 'Player not found'}), 404

# 玩家登出（POST）
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# 添加玩家得分（POST）
@app.route('/players/<int:player_id>/scores', methods=['POST'])
def add_score(player_id):
    data = request.get_json()
    score = data['score']
    new_score = Score(player_id=player_id, score=score)
    db.session.add(new_score)
    db.session.commit()
    return jsonify({'message': 'Score added'}), 201

# 获取玩家得分记录（GET）
@app.route('/players/<int:player_id>/scores', methods=['GET'])
def get_scores(player_id):
    scores = Score.query.filter_by(player_id=player_id).all()
    return jsonify([{'score': score.score, 'game_date': score.game_date.isoformat()} for score in scores])

# 获取指定玩家信息（GET）
@app.route('/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = Player.query.get_or_404(player_id)
    return jsonify({'id': player.id, 'username': player.username})

# 获取当前登录玩家的得分记录
@app.route('/current_scores', methods=['GET'])
def current_scores():
    username = session.get('username')
    if username:
        player = Player.query.filter_by(username=username).first()
        scores = Score.query.filter_by(player_id=player.id).all()
        return jsonify({
            'username': username,
            'scores': [{'score': score.score, 'game_date': score.game_date.isoformat()} for score in scores]
        })
    else:
        return jsonify({'message': 'Not logged in'}), 401

# 设置默认游戏得分
@app.route('/set_default_score', methods=['POST'])
def set_default_score():
    username = session.get('username')
    if username:
        player = Player.query.filter_by(username=username).first()
        if not player:
            return jsonify({'message': 'Player not found'}), 404
        
        # 设置初始得分为 0
        existing_score = Score.query.filter_by(player_id=player.id).first()
        if not existing_score:
            new_score = Score(player_id=player.id, score=0)
            db.session.add(new_score)
            db.session.commit()

        return jsonify({'message': 'Score initialized to 0'}), 200
    else:
        return jsonify({'message': 'Not logged in'}), 401

# 启动应用
if __name__ == '__main__':
    app.run(debug=True)
