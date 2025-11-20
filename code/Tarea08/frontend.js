const baseUrlInput = document.getElementById('baseUrl');
const storedBaseUrl = localStorage.getItem('libros_base_url') || 'http://34.58.78.120:5003';
baseUrlInput.value = storedBaseUrl;

const state = {
    baseUrl: baseUrlInput.value.trim(),
    accessToken: null,
    refreshToken: null,
    maxFiles: 5,
    maxImageSize: 5 * 1024 * 1024, // 5 MB
    genres: [],
    formats: [],
    selectedImages: []
};

const allowedTypes = ['image/png', 'image/jpeg'];

const dom = {
    messages: document.getElementById('messages'),
    error: document.getElementById('error'),
    tokenDisplay: document.getElementById('tokenDisplay'),
    booksList: document.getElementById('books-list'),
    bookDetail: document.getElementById('book-detail'),
    previewList: document.getElementById('preview-list')
};

function logMessage(msg) {
    const time = new Date().toLocaleTimeString();
    dom.messages.textContent = `[${time}] ${msg}`;
}

function logError(msg) {
    dom.error.textContent = msg;
}

function clearError() {
    dom.error.textContent = '';
}

function updateTokenDisplay() {
    dom.tokenDisplay.value = `Access Token:\n${state.accessToken || '-'}\n\nRefresh Token:\n${state.refreshToken || '-'}`;
    updateAuthStatus();
}

function updateAuthStatus() {
    const el = document.getElementById('authStatus');
    if (state.accessToken) {
        el.textContent = 'Autenticado';
        el.classList.add('status-online');
        el.classList.remove('status-offline');
    } else {
        el.textContent = 'No autenticado';
        el.classList.add('status-offline');
        el.classList.remove('status-online');
    }
}

function authHeaders(extra = {}) {
    const headers = { ...extra };
    if (state.accessToken) {
        headers['Authorization'] = `Bearer ${state.accessToken}`;
    }
    return headers;
}

async function apiFetch(path, options = {}, expect = 'json') {
    clearError();
    const url = `${state.baseUrl}${path}`;
    const opts = {
        ...options,
        headers: authHeaders(options.headers || {})
    };
    if (options.body && !(options.body instanceof FormData)) {
        opts.headers['Content-Type'] = opts.headers['Content-Type'] || 'application/json';
    }
    const res = await fetch(url, opts);
    const text = await res.text();
    if (!res.ok) {
        logError(`Error ${res.status}: ${text}`);
        throw new Error(text || 'Error en la solicitud');
    }
    if (!text) return null;
    if (expect === 'text') return text;
    if (expect === 'xml') {
        return new window.DOMParser().parseFromString(text, 'application/xml');
    }
    try {
        return JSON.parse(text);
    } catch {
        return text;
    }
}

// ---------- Auth flows ----------
async function registerUser() {
    const username = document.getElementById('regUsername').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    if (!username || !email || !password) {
        return logError('Todos los campos de registro son obligatorios');
    }
    const payload = { username, email, password };
    const data = await apiFetch('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
    logMessage(`Usuario creado con id=${data.user_id}`);
}

async function loginUser() {
    const identifier = document.getElementById('loginIdentifier').value.trim();
    const password = document.getElementById('loginPassword').value;
    if (!identifier || !password) {
        return logError('Usuario/email y contraseña requeridos');
    }
    const payload = { password };
    if (identifier.includes('@')) {
        payload.email = identifier;
    } else {
        payload.username = identifier;
    }
    const data = await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
    state.accessToken = data.access_token;
    state.refreshToken = data.refresh_token;
    updateTokenDisplay();
    logMessage('Login exitoso, tokens guardados');
    await fetchGenresAndFormats().catch(() => {});
}

async function refreshAccessToken() {
    if (!state.refreshToken) {
        return logError('No hay refresh token guardado');
    }
    const data = await apiFetch('/api/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: state.refreshToken })
    });
    state.accessToken = data.access_token;
    updateTokenDisplay();
    logMessage('Token renovado');
}

async function logout() {
    if (!state.refreshToken && !state.accessToken) {
        return logError('No hay tokens para revocar');
    }
    await apiFetch('/api/auth/logout', {
        method: 'POST',
        body: JSON.stringify({
            refresh_token: state.refreshToken,
            access_token: state.accessToken
        })
    });
    state.accessToken = null;
    state.refreshToken = null;
    updateTokenDisplay();
    logMessage('Tokens revocados');
}

async function revokeAllTokens() {
    await apiFetch('/api/auth/revoke-all', {
        method: 'POST'
    });
    logMessage('Se revocaron todos los tokens del usuario actual');
}

// ---------- Books helpers ----------
function parseBooksXml(doc) {
    if (!doc) return [];
    const books = [];
    doc.querySelectorAll('book').forEach(bookEl => {
        const book = {
            isbn: bookEl.getAttribute('isbn'),
            title: bookEl.querySelector('title')?.textContent || '',
            author: bookEl.querySelector('author')?.textContent || '',
            publication_year: bookEl.querySelector('publication_year')?.textContent || '',
            genre: bookEl.querySelector('genre')?.textContent || '',
            price: bookEl.querySelector('price')?.textContent || '',
            stock: bookEl.querySelector('stock')?.textContent || '',
            format: bookEl.querySelector('format')?.textContent || '',
            images: []
        };
        bookEl.querySelectorAll('images image').forEach(imgEl => {
            book.images.push({
                id: imgEl.getAttribute('id'),
                url: imgEl.querySelector('url')?.textContent || '',
                filename: imgEl.querySelector('filename')?.textContent || '',
                mime_type: imgEl.querySelector('mime_type')?.textContent || '',
                size_bytes: imgEl.querySelector('size_bytes')?.textContent || '',
                uploaded_at: imgEl.querySelector('uploaded_at')?.textContent || ''
            });
        });
        books.push(book);
    });
    return books;
}

function renderBooks(books) {
    dom.booksList.innerHTML = '';
    books.forEach(book => {
        const card = document.createElement('div');
        card.className = 'book-card';
        card.innerHTML = `
            <h3>${book.title}</h3>
            <p><strong>ISBN:</strong> ${book.isbn}</p>
            <p><strong>Autores:</strong> ${book.author}</p>
            <p><strong>Género:</strong> ${book.genre}</p>
            <p><strong>Formato:</strong> ${book.format}</p>
            <p><strong>Precio:</strong> ${book.price}</p>
            <p><strong>Stock:</strong> ${book.stock}</p>
            <button data-isbn="${book.isbn}">Ver detalle</button>
        `;
        card.querySelector('button').addEventListener('click', () => showBookDetail(book));
        dom.booksList.appendChild(card);
    });
}

function showBookDetail(book) {
    dom.bookDetail.innerHTML = `
        <h3>Detalle de ${book.title}</h3>
        <p><strong>ISBN:</strong> ${book.isbn}</p>
        <p><strong>Autores:</strong> ${book.author}</p>
        <p><strong>Año:</strong> ${book.publication_year}</p>
        <p><strong>Género:</strong> ${book.genre}</p>
        <p><strong>Formato:</strong> ${book.format}</p>
        <p><strong>Precio:</strong> ${book.price}</p>
        <p><strong>Stock:</strong> ${book.stock}</p>
        <div class="images-preview">
            ${book.images.map(img => `
                <div>
                    <img src="${img.url}" alt="${img.filename}">
                    <div>${img.filename}</div>
                </div>
            `).join('') || '<em>Sin imágenes</em>'}
        </div>
    `;
}

async function loadAllBooks() {
    const xml = await apiFetch('/api/books', { method: 'GET' }, 'xml');
    const books = parseBooksXml(xml);
    renderBooks(books);
    logMessage(`Se cargaron ${books.length} libros`);
}

async function searchByIsbn() {
    const isbn = document.getElementById('isbnSearch').value.trim();
    if (!isbn) {
        return logError('Proporciona un ISBN');
    }
    const xml = await apiFetch(`/api/books/${isbn}`, { method: 'GET' }, 'xml');
    const books = parseBooksXml(xml);
    renderBooks(books);
    if (books.length) showBookDetail(books[0]);
    logMessage(`Búsqueda ISBN completada (${books.length} resultados)`);
}

async function filterByFormat() {
    const fmt = document.getElementById('formatSelect').value;
    if (!fmt) return logError('Selecciona un formato');
    const xml = await apiFetch(`/api/books/format/${encodeURIComponent(fmt)}`, { method: 'GET' }, 'xml');
    const books = parseBooksXml(xml);
    renderBooks(books);
    logMessage(`Se encontraron ${books.length} libros con formato ${fmt}`);
}

async function filterByAuthor() {
    const author = document.getElementById('authorInput').value.trim();
    if (!author) return logError('Indica parte del nombre del autor');
    const xml = await apiFetch(`/api/books/author/${encodeURIComponent(author)}`, { method: 'GET' }, 'xml');
    const books = parseBooksXml(xml);
    renderBooks(books);
    logMessage(`Resultado autores (${books.length})`);
}

async function fetchGenresAndFormats() {
    const genresXml = await apiFetch('/api/genres', { method: 'GET' }, 'xml');
    const formatsXml = await apiFetch('/api/formats', { method: 'GET' }, 'xml');
    state.genres = Array.from(genresXml.querySelectorAll('genre')).map(g => ({
        id: g.querySelector('id')?.textContent,
        name: g.querySelector('name')?.textContent
    }));
    state.formats = Array.from(formatsXml.querySelectorAll('format')).map(f => ({
        id: f.querySelector('id')?.textContent,
        name: f.querySelector('name')?.textContent
    }));
    fillSelect(document.getElementById('bookGenre'), state.genres);
    fillSelect(document.getElementById('bookFormat'), state.formats);
    fillSelect(document.getElementById('formatSelect'), state.formats, true);
    logMessage('Catálogos de géneros y formatos cargados');
}

function fillSelect(select, items, includeBlank = false) {
    select.innerHTML = '';
    if (includeBlank) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'Seleccione';
        select.appendChild(opt);
    }
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.name;
        opt.textContent = item.name;
        select.appendChild(opt);
    });
}

// ---------- Book form ----------
function buildBookXml(formData) {
    const sanitized = {
        isbn: (formData.get('isbn') || '').trim(),
        title: (formData.get('title') || '').trim(),
        authors: (formData.get('authors') || '').trim(),
        year: (formData.get('year') || '').trim(),
        genre: formData.get('genre') || '',
        price: (formData.get('price') || '').trim(),
        format: formData.get('format') || ''
    };
    const stockValue = formData.get('stock') ? 'true' : 'false';
    return `
        <book isbn="${sanitized.isbn}">
            <title>${sanitized.title}</title>
            <author>${sanitized.authors}</author>
            <publication_year>${sanitized.year}</publication_year>
            <genre>${sanitized.genre}</genre>
            <price>${sanitized.price}</price>
            <stock>${stockValue}</stock>
            <format>${sanitized.format}</format>
        </book>
    `.replace(/\s{2,}/g, '');
}

function collectBookForm() {
    const form = document.getElementById('bookForm');
    return new FormData(form);
}

async function submitBookForm(event) {
    event.preventDefault();
    const formData = collectBookForm();
    const isbn = formData.get('isbn').trim();
    if (!isbn) return logError('ISBN es requerido');
    const files = state.selectedImages;
    const result = new FormData();
    result.append('book', buildBookXml(formData));
    files.forEach(file => {
        result.append('images', file);
    });
    const action = document.getElementById('bookAction').value === 'update'
        ? '/api/books/update'
        : '/api/books/insert';
    await apiFetch(action, {
        method: 'PUT',
        body: result
    }, 'text');
    logMessage('Libro guardado correctamente');
    state.selectedImages = [];
    renderImagePreview();
    document.getElementById('bookForm').reset();
    await loadAllBooks();
}

async function deleteBooks() {
    const raw = document.getElementById('deleteIsbns').value.trim();
    if (!raw) return logError('Proporciona al menos un ISBN');
    const isbns = raw.split(',').map(s => s.trim()).filter(Boolean);
    if (!isbns.length) return logError('No se encontraron ISBN válidos');
    const body = `<delete>${isbns.map(isbn => `<isbn>${isbn}</isbn>`).join('')}</delete>`;
    await apiFetch('/api/books/delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/xml' },
        body
    }, 'text');
    logMessage('Libros eliminados');
    await loadAllBooks();
}

// ---------- File preview ----------
function renderImagePreview() {
    dom.previewList.innerHTML = '';
    if (!state.selectedImages.length) {
        dom.previewList.innerHTML = '<em>Sin imágenes seleccionadas</em>';
        return;
    }
    state.selectedImages.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = e => {
            const div = document.createElement('div');
            div.className = 'preview-item';
            div.innerHTML = `
                <img src="${e.target.result}" alt="${file.name}">
                <small>${file.name}</small>
                <button type="button" data-index="${index}" class="secondary">Quitar</button>
            `;
            div.querySelector('button').addEventListener('click', () => removeImageAt(index));
            dom.previewList.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

function removeImageAt(index) {
    state.selectedImages.splice(index, 1);
    renderImagePreview();
}

function handleImageChange() {
    const input = document.getElementById('bookImages');
    clearError();
    const newFiles = Array.from(input.files);
    input.value = '';
    if (!newFiles.length) return;
    if (state.selectedImages.length + newFiles.length > state.maxFiles) {
        return logError(`Máximo ${state.maxFiles} imágenes`);
    }
    for (const file of newFiles) {
        if (!allowedTypes.includes(file.type)) {
            return logError(`Tipo no permitido: ${file.name}`);
        }
        if (file.size > state.maxImageSize) {
            return logError(`Archivo demasiado grande: ${file.name}`);
        }
        state.selectedImages.push(file);
    }
    renderImagePreview();
}

// ---------- Initialization ----------
const handleAsync = (fn) => {
    fn().catch(err => {
        console.error(err);
        logError(err.message || 'Error en la operación');
    });
};

document.getElementById('saveBaseUrl').addEventListener('click', () => {
    state.baseUrl = baseUrlInput.value.trim();
    localStorage.setItem('libros_base_url', state.baseUrl);
    logMessage(`Base URL actualizada a ${state.baseUrl}`);
});
document.getElementById('registerBtn').addEventListener('click', () => handleAsync(registerUser));
document.getElementById('loginBtn').addEventListener('click', () => handleAsync(loginUser));
document.getElementById('refreshBtn').addEventListener('click', () => handleAsync(refreshAccessToken));
document.getElementById('logoutBtn').addEventListener('click', () => handleAsync(logout));
document.getElementById('revokeBtn').addEventListener('click', () => handleAsync(revokeAllTokens));
document.getElementById('loadBooksBtn').addEventListener('click', () => handleAsync(loadAllBooks));
document.getElementById('searchIsbnBtn').addEventListener('click', () => handleAsync(searchByIsbn));
document.getElementById('filterFormatBtn').addEventListener('click', () => handleAsync(filterByFormat));
document.getElementById('filterAuthorBtn').addEventListener('click', () => handleAsync(filterByAuthor));
document.getElementById('bookForm').addEventListener('submit', e => {
    handleAsync(() => submitBookForm(e));
});
document.getElementById('bookImages').addEventListener('change', handleImageChange);
document.getElementById('deleteBtn').addEventListener('click', () => handleAsync(deleteBooks));

// Load formats/genres on start (requires auth)
document.addEventListener('DOMContentLoaded', () => {
    updateTokenDisplay();
    logMessage('Configura la URL y realiza login para comenzar.');
    renderImagePreview();
});
    
