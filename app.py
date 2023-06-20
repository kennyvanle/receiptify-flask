from flask import Flask, request, url_for, session, redirect, render_template

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import time 
from time import gmtime, strftime

from credentials import CLIENT_ID, CLIENT_SECRET, SECRET_KEY
import os

TOKEN_INFO = 'token_info'

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = 'OREO_Cookie'

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=url_for("callback", _external=True), 
        scope="user-top-read user-library-read"
    )

def get_token(): 
    token_info = session.get(TOKEN_INFO, None)
    if not token_info: 
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60 
    if (is_expired): 
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info 

@app.route('/')
def index():
    name = 'username'
    return render_template('index.html', title='Welcome', username=name)

@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = create_spotify_oauth()
    session.clear() 
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info    
    return redirect(url_for("fetch_top_songs", _external=True))

def get_token():
    return session.get(TOKEN_INFO, None)

@app.route('/top-songs')
def fetch_top_songs():
    try:
        token_info = get_token()
    except Exception:
        print("User is not logged in, attempting to redirect")
        return redirect("/")
    sp = spotipy.Spotify(
        auth=token_info['access_token'],
    )

    current_user_name = sp.current_user()['display_name']
    short_term = sp.current_user_top_tracks(
        limit=10,
        offset=0,
        time_range="short_term",
    )
    medium_term = sp.current_user_top_tracks(
        limit=10,
        offset=0,
        time_range="medium_term",
    )
    long_term = sp.current_user_top_tracks(
        limit=10,
        offset=0,
        time_range="long_term",
    )

    if os.path.exists(".cache"): 
        os.remove(".cache")

    return render_template('receipt.html', user_display_name=current_user_name, short_term=short_term, medium_term=medium_term, long_term=long_term, currentTime=gmtime())


@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    return strftime("%a, %d %b %Y", date)

@app.template_filter('mmss')
def _jinja2_filter_miliseconds(time, fmt=None):
    time = int(time / 1000)
    minutes, seconds = divmod(time, 60)
    if seconds < 10: 
        return f"{str(minutes)}:0{str(seconds)}"
    return f"{str(minutes)}:{str(seconds)}" 