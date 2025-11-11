from flask import Flask, render_template, request, jsonify
import base64
import hashlib
import qrcode
import io

app = Flask(__name__)

# -----------------------------
# Original simple Caesar helpers
# (applies ord +/- offset to every character,
#  same behavior as your original script)
# -----------------------------
DEFAULT_SHIFT = 5

def caesar_encrypt_simple(text, shift=DEFAULT_SHIFT):
    # exactly: chr(ord(ch) + shift) for each ch
    return ''.join(chr(ord(ch) + shift) for ch in text)

def caesar_decrypt_simple(text, shift=DEFAULT_SHIFT):
    # exactly: chr(ord(ch) - shift) for each ch
    return ''.join(chr(ord(ch) - shift) for ch in text)


# -----------------------------
# Rendered page route (server-side form POST support)
# -----------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    # this supports the simple server-rendered flow:
    # - if form submitted, process and render result into template variables
    result = None
    input_text = ''
    tool = None
    qr_data_uri = None

    if request.method == 'POST':
        tool = request.form.get('tool')
        action = request.form.get('action')
        input_text = request.form.get('input_text', '')

        try:
            if tool == 'caesar':
                if action == 'encrypt':
                    result = caesar_encrypt_simple(input_text)
                elif action == 'decrypt':
                    result = caesar_decrypt_simple(input_text)
                else:
                    result = 'Invalid caesar action'

            elif tool == 'base64':
                if action == 'encode':
                    result = base64.b64encode(input_text.encode()).decode()
                elif action == 'decode':
                    # base64 decode may raise
                    result = base64.b64decode(input_text.encode()).decode()
                else:
                    result = 'Invalid base64 action'

            elif tool == 'sha256':
                result = hashlib.sha256(input_text.encode()).hexdigest()

            elif tool == 'qr':
                qr = qrcode.QRCode(version=1, box_size=10, border=3)
                qr.add_data(input_text)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                qr_data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

            else:
                result = 'Invalid tool'

        except Exception as e:
            result = f'Error: {str(e)}'

    # render template with possible server-side result
    return render_template(
        'index.html',
        result=result,
        input_text=input_text,
        tool=tool,
        qr_data_uri=qr_data_uri
    )


# -----------------------------
# JSON API for JS/AJAX (optional)
# returns JSON { result: "..."} or { image: "data:..."} or { error: "..." }
# -----------------------------
@app.route('/process', methods=['POST'])
def process_tool():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify(error='No JSON payload'), 400

    tool = data.get('tool')
    action = data.get('action')
    text = data.get('input', '')

    try:
        if tool == 'caesar':
            if action == 'encrypt':
                return jsonify(result=caesar_encrypt_simple(text))
            elif action == 'decrypt':
                return jsonify(result=caesar_decrypt_simple(text))
            else:
                return jsonify(error='Invalid caesar action'), 400

        elif tool == 'base64':
            try:
                if action == 'encode':
                    return jsonify(result=base64.b64encode(text.encode()).decode())
                elif action == 'decode':
                    decoded = base64.b64decode(text.encode())
                    # try return string, fallback to hex
                    try:
                        return jsonify(result=decoded.decode())
                    except Exception:
                        return jsonify(result=decoded.hex())
                else:
                    return jsonify(error='Invalid base64 action'), 400
            except Exception as e:
                return jsonify(error=f'Base64 error: {str(e)}'), 400

        elif tool == 'sha256':
            return jsonify(result=hashlib.sha256(text.encode()).hexdigest())

        elif tool == 'qr':
            qr = qrcode.QRCode(version=1, box_size=10, border=3)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
            return jsonify(image=data_uri)

        else:
            return jsonify(error='Invalid tool'), 400

    except Exception as e:
        return jsonify(error=f'Server error: {str(e)}'), 500


# -----------------------------
# Run
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
