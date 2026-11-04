"""Authenticated Reddit requests; no profile data or lookup history retained."""
import os
import threading
import time
import requests

class RedditAccessError(Exception):
    pass

class RedditClient:
    def __init__(self):
        self.lock = threading.Lock()
        self.token = None
        self.expires = 0
        self.next_request = 0

    def _token(self, headers):
        explicit = os.getenv('REDDIT_ACCESS_TOKEN', '').strip()
        if explicit:
            return explicit
        if self.token and time.monotonic() < self.expires:
            return self.token
        client_id = os.getenv('REDDIT_CLIENT_ID', '').strip()
        secret = os.getenv('REDDIT_CLIENT_SECRET', '').strip()
        if not client_id or not secret:
            raise RedditAccessError('Setup required: configure approved Reddit API credentials in .env.')
        response = requests.post('https://www.reddit.com/api/v1/access_token',
            auth=(client_id, secret), data={'grant_type':'client_credentials'},
            headers=headers, timeout=(5,15), allow_redirects=False)
        if response.status_code == 429:
            self.next_request = time.monotonic() + 60
            raise RedditAccessError('Token request rate-limited (429). Wait at least one minute.')
        if response.status_code != 200:
            raise RedditAccessError(f'OAuth setup rejected (HTTP {response.status_code}). Check credentials and approved API access.')
        try:
            payload = response.json()
            token = payload['access_token']
            lifetime = float(payload['expires_in'])
            if not isinstance(token,str) or not token or lifetime <= 0:
                raise ValueError()
        except (KeyError,ValueError,TypeError):
            raise RedditAccessError('Invalid OAuth response. Check Reddit API setup.') from None
        self.token = token
        self.expires = time.monotonic() + max(0,lifetime-60)
        return token

    def about(self, username):
        with self.lock:
            agent = os.getenv('REDDIT_USER_AGENT','').strip()
            if not agent or 'YOUR_REDDIT_USERNAME' in agent:
                raise RedditAccessError('Setup required: set REDDIT_USER_AGENT with your Reddit username in .env.')
            wait = self.next_request-time.monotonic()
            if wait > 2:
                raise RedditAccessError(f'Reddit rate limit: retry in {int(wait)+1} seconds.')
            if wait > 0:
                time.sleep(wait)
            headers = {'User-Agent':agent}
            try:
                headers['Authorization'] = 'Bearer ' + self._token(headers)
                response = requests.get(f'https://oauth.reddit.com/user/{username}/about',
                    headers=headers, timeout=(5,15), allow_redirects=False)
                self.next_request = time.monotonic()+1.1
                if response.status_code == 401:
                    self.token=None
                    raise RedditAccessError('OAuth rejected (401). Check credentials; replace an expired manual token.')
                if response.status_code == 403:
                    raise RedditAccessError('Reddit denied API access (403). Check API approval. This does not prove an account ban.')
                if response.status_code == 404:
                    raise RedditAccessError('Profile unavailable (404). Deleted, suspended or nonexistent cannot be distinguished here.')
                if response.status_code == 429:
                    try:
                        delay=max(60,min(3600,float(response.headers.get('Retry-After',60))))
                    except (ValueError,TypeError):
                        delay=60
                    self.next_request=time.monotonic()+delay
                    raise RedditAccessError(f'Reddit rate limit (429). Retry in {int(delay)} seconds.')
                if response.status_code != 200:
                    raise RedditAccessError(f'Reddit HTTP {response.status_code}. Try later.')
                try:
                    if float(response.headers.get('X-Ratelimit-Remaining','1')) <= 0:
                        self.next_request=time.monotonic()+max(1,float(response.headers.get('X-Ratelimit-Reset','60')))
                except (TypeError,ValueError):
                    pass
                payload=response.json()
                data=payload.get('data') if isinstance(payload,dict) else None
                if not isinstance(data,dict):
                    raise ValueError()
                return data
            except requests.Timeout:
                raise RedditAccessError('Reddit request timed out. Try later.') from None
            except requests.RequestException:
                raise RedditAccessError('Could not connect to Reddit. Check your connection.') from None
            except ValueError:
                raise RedditAccessError('Reddit returned invalid JSON/profile data.') from None
