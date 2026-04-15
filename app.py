import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'full_refresh_2026'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db():
    return mysql.connector.connect(
        host="localhost", user="root", password="Klase12!", database="biblioteka1"
    )

@app.route('/')
def index():
    s = request.args.get('search', '')
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM books WHERE virsraksts LIKE %s OR autors LIKE %s", (f"%{s}%", f"%{s}%"))
    books = cur.fetchall()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/book/<int:book_id>')
def view_book(book_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cur.fetchone()
    conn.close()
    if book:
        return render_template('read_book.html', book=book)
    return "Grāmata netika atrasta!", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        l, p = request.form.get('login'), request.form.get('parole')
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE login=%s AND parole=%s", (l, p))
        user = cur.fetchone()
        conn.close()
        if user:
            session.update({'u_id': user['id'], 'u_name': user['vards'], 'role': user['role']})
            return redirect('/')
        flash("Nepareizs logins vai parole!")
    return render_template('user_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        v, u, l = request.form.get('vards'), request.form.get('uzvards'), request.form.get('login')
        p1, p2 = request.form.get('parole'), request.form.get('parole2')
        if p1 != p2:
            flash("Paroles nesakrīt!")
            return redirect('/register')
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (vards, uzvards, login, parole) VALUES (%s,%s,%s,%s)", (v, u, l, p1))
            conn.commit()
            flash("Reģistrācija veiksmīga!")
            return redirect('/login')
        except:
            flash("Šāds logins jau eksistē!")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        if request.form.get('admin_pass') == 'admin123':
            session['admin_access'] = True
            return redirect('/admin')
        else:
            flash("Nepareiza admina parole!")
            return redirect('/admin')

    if session.get('admin_access'):
        search_user = request.args.get('search_user', '')
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM books")
        b = cur.fetchall()

        if search_user:
            cur.execute("SELECT * FROM users WHERE vards LIKE %s OR login LIKE %s", (f"%{search_user}%", f"%{search_user}%"))
        else:
            cur.execute("SELECT * FROM users")
        u = cur.fetchall()
        conn.close()
        return render_template('admin.html', books=b, users=u)
    return render_template('admin_auth.html')

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('admin_access'): return redirect('/admin')
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        v, u, l, p, r = request.form.get('vards'), request.form.get('uzvards'), request.form.get('login'), request.form.get('parole'), request.form.get('role')
        cur.execute("UPDATE users SET vards=%s, uzvards=%s, login=%s, parole=%s, role=%s WHERE id=%s", (v, u, l, p, r, user_id))
        conn.commit()
        conn.close()
        flash("Lietotājs atjaunināts!")
        return redirect('/admin')
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('admin_access'): return redirect('/admin')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/admin/delete_book/<int:book_id>')
def delete_book(book_id):
    if not session.get('admin_access'): return redirect('/admin')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/admin/add', methods=['POST'])
def add_book():
    if not session.get('admin_access'): return redirect('/admin')
    file = request.files.get('image')
    fname = secure_filename(file.filename) if file else 'default_book.jpg'
    if file: file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO books (virsraksts, autors, saturs, attels) VALUES (%s,%s,%s,%s)",
                (request.form['t'], request.form['a'], request.form['c'], fname))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_access', None)
    return redirect('/')


@app.route('/admin/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if not session.get('admin_access'): return redirect('/admin')
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        t = request.form.get('t')
        a = request.form.get('a')
        c = request.form.get('c')
        file = request.files.get('image')

        if file and file.filename != '':
            fname = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            cur.execute("UPDATE books SET virsraksts=%s, autors=%s, saturs=%s, attels=%s WHERE id=%s",
                        (t, a, c, fname, book_id))
        else:
            cur.execute("UPDATE books SET virsraksts=%s, autors=%s, saturs=%s WHERE id=%s",
                        (t, a, c, book_id))

        conn.commit()
        conn.close()
        flash("Grāmata veiksmīgi atjaunināta!")
        return redirect('/admin')

    cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cur.fetchone()
    conn.close()

    if book:
        return render_template('edit_book.html', book=book)
    return "Grāmata nav atrasta!", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)