/* 前端与后端的唯一通道
 *   · 由后端托管打开（http://127.0.0.1:8000/...）→ 同源，用 Cookie
 *   · 双击 HTML 打开（file:///...）→ 自动指向 http://127.0.0.1:8000，改用 Bearer Token
 */

const API_BASE = (location.protocol === 'file:' ||
                  (location.port && location.port !== '8000'))
  ? 'http://127.0.0.1:8000'
  : '';

const TOKEN_KEY = 'ic_token';
const Auth = {
  get token() { try { return localStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; } },
  set token(v) {
    try { v ? localStorage.setItem(TOKEN_KEY, v) : localStorage.removeItem(TOKEN_KEY); } catch (e) {}
  },
};

const API = {
  async request(method, url, body) {
    const headers = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (Auth.token) headers['Authorization'] = 'Bearer ' + Auth.token;   // ★ file:// 场景靠它

    const res = await fetch(API_BASE + url, {
      method,
      headers,
      credentials: 'same-origin',          // 同源时带 Cookie；跨源时靠 Token
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    let json = null;
    try { json = await res.json(); } catch (e) { /* 非 JSON */ }

    if (res.status === 401) {
      Auth.token = '';
      if (!/login\.html$/.test(location.pathname)) location.href = 'login.html';
      throw new Error('未登录');
    }
    if (!res.ok) {
      const err = new Error((json && json.msg) || ('HTTP ' + res.status));
      err.status = res.status;
      throw err;
    }
    return json ? json.data : null;
  },

  get(url) { return this.request('GET', url); },
  post(url, body) { return this.request('POST', url, body); },

  health() { return this.request('GET', '/api/health'); },

  async login(username, password) {
    const data = await this.post('/api/login', { username, password });
    if (data && data.token) Auth.token = data.token;
    return data;
  },

  async logout() {
    try { await this.post('/api/logout'); } catch (e) {}
    Auth.token = '';
  },

  me() { return this.get('/api/me'); },
  roomMe(courseId) { return this.get('/api/rooms/' + courseId + '/me'); },
  messages(courseId) { return this.get('/api/rooms/' + courseId + '/messages'); },
  action(courseId, menuId, content) {
    return this.post('/api/rooms/' + courseId + '/action', { menu_id: menuId, content });
  },
};

/* 小工具 */
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function banner(el, msg, ok) {
  el.textContent = msg;
  el.className = 'banner ' + (ok ? 'ok' : 'err');
}

function roleBadgeClass(roleId) {
  return 'badge role' + (roleId || 3);
}
