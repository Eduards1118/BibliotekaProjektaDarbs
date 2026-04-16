import os, mysql.connector
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'full_refresh_2026'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])



def query_db(query, args=(), one=False, commit=False):
    conn = mysql.connector.connect(host="localhost", user="root", password="Klase12!", database="biblioteka1")
    cur = conn.cursor(dictionary=True)
    cur.execute(query, args)
    if commit:
        conn.commit()
        res = None
    else:
        res = cur.fetchone() if one else cur.fetchall()
    conn.close()
    return res


@app.route('/')
def index():
    s = request.args.get('search', '')
    books = query_db("SELECT * FROM books WHERE virsraksts LIKE %s OR autors LIKE %s", (f"%{s}%", f"%{s}%"))
    return render_template('index.html', books=books)


@app.route('/book/<int:book_id>')
def view_book(book_id):
    book = query_db("SELECT * FROM books WHERE id = %s", (book_id,), one=True)
    return render_template('read_book.html', book=book) if book else ("Nav atrasts", 404)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = query_db("SELECT * FROM users WHERE login=%s AND parole=%s",
                     (request.form['login'], request.form['parole']), one=True)
        if u:
            session.update({'u_id': u['id'], 'u_name': u['vards'], 'role': u['role']})
            return redirect('/')
        flash("Nepareizi dati!")
    return render_template('user_login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        f = request.form
        if f['parole'] != f['parole2']:
            flash("Paroles nesakrīt!")
        else:
            try:
                query_db("INSERT INTO users (vards, uzvards, login, parole) VALUES (%s,%s,%s,%s)",
                         (f['vards'], f['uzvards'], f['login'], f['parole']), commit=True)
                return redirect('/login')
            except:
                flash("Logins aizņemts!")
    return render_template('register.html')




@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST' and request.form.get('admin_pass') == 'admin123':
        session['admin_access'] = True

    if session.get('admin_access'):
        su = request.args.get('search_user', '')
        users = query_db("SELECT * FROM users WHERE vards LIKE %s OR login LIKE %s",
                         (f"%{su}%", f"%{su}%")) if su else query_db("SELECT * FROM users")
        books = query_db("SELECT * FROM books")
        return render_template('admin.html', books=books, users=users)

    return render_template('admin_auth.html')



@app.route('/admin/add', methods=['POST'])
def add_book():
    if not session.get('admin_access'): return redirect('/admin')
    f = request.files.get('image')
    fname = secure_filename(f.filename) if f and f.filename else 'default.jpg'
    if f and f.filename: f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    query_db("INSERT INTO books (virsraksts, autors, saturs, attels) VALUES (%s,%s,%s,%s)",
             (request.form['t'], request.form['a'], request.form['c'], fname), commit=True)
    return redirect('/admin')


@app.route('/admin/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if not session.get('admin_access'): return redirect('/admin')
    if request.method == 'POST':
        f, img = request.form, request.files.get('image')
        if img and img.filename:
            fn = secure_filename(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
            query_db("UPDATE books SET virsraksts=%s, autors=%s, saturs=%s, attels=%s WHERE id=%s",
                     (f['t'], f['a'], f['c'], fn, book_id), commit=True)
        else:
            query_db("UPDATE books SET virsraksts=%s, autors=%s, saturs=%s WHERE id=%s",
                     (f['t'], f['a'], f['c'], book_id), commit=True)
        return redirect('/admin')
    return render_template('edit_book.html', book=query_db("SELECT * FROM books WHERE id=%s", (book_id,), one=True))


@app.route('/admin/delete_book/<int:book_id>')
def delete_book(book_id):
    if not session.get('admin_access'): return redirect('/admin')
    query_db("DELETE FROM books WHERE id=%s", (book_id,), commit=True)
    return redirect('/admin')


# Lietotāju pārvaldība (JAUNS!)
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('admin_access'): return redirect('/admin')

    if request.method == 'POST':
        f = request.form
        query_db("UPDATE users SET vards=%s, uzvards=%s, login=%s, parole=%s, role=%s WHERE id=%s",
                 (f['vards'], f['uzvards'], f['login'], f['parole'], f['role'], user_id), commit=True)
        return redirect('/admin')

    user = query_db("SELECT * FROM users WHERE id=%s", (user_id,), one=True)
    return render_template('edit_user.html', user=user)


@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('admin_access'): return redirect('/admin')
    query_db("DELETE FROM users WHERE id=%s", (user_id,), commit=True)
    return redirect('/admin')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
