"""
Basic unit tests for web application chat persistence.
"""
from web_app import app, load_chats, load_users, save_users
from werkzeug.security import generate_password_hash


def setup_users():
    save_users([])
    users = [{
        'user_id': 'tuser',
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@snow.edu',
        'password_hash': generate_password_hash('secret'),
        'created_at': '',
        'last_login': ''
    }]
    save_users(users)


def test_chat_lifecycle():
    setup_users()
    with app.test_client() as client:
        # login
        rv = client.post('/login', data={'email': 'test@snow.edu', 'password': 'secret'}, follow_redirects=True)
        assert rv.status_code == 200

        # create new chat
        rv = client.post('/new_chat', json={'domain': 'CompTIA A+ Hardware'})
        assert rv.status_code == 200
        chat_id = rv.json['chat_id']
        assert chat_id

        # ask a question
        rv = client.post('/chat', json={'question': 'What is CPU?'})
        assert rv.json.get('success')

        # check stored chats file contains entry
        chats = load_chats()
        assert any(c['chat_id'] == chat_id for c in chats)

        # logout/login, verify chat persists
        client.get('/logout')
        client.post('/login', data={'email': 'test@snow.edu', 'password': 'secret'}, follow_redirects=True)
        rv = client.get('/dashboard')
        assert b'CompTIA A+ Hardware' in rv.data
        rv = client.get(f'/load_chat/{chat_id}')
        assert b'CPU' in rv.data


if __name__ == '__main__':
    test_chat_lifecycle()
    print('chat persistence test passed')
