from app import app, db, User
import json

app.app_context().push()
client = app.test_client()

with client.session_transaction() as sess:
    sess['user_email'] = User.query.first().email

r = client.get('/api/notifications')
data = json.loads(r.data)
print('Notification API Response:', data)
if data['items']:
    print('First notification message:', data['items'][0]['message'])
else:
    print('No notifications found')
