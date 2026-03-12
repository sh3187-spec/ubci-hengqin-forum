"""
超声脑机横琴论坛 · RSVP Web Application
Flask app for Railway deployment
"""
import os
import smtplib
import ssl
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)
logging.basicConfig(level=logging.INFO)

SMTP_CONFIGS = [
    {'host': 'smtp.exmail.qq.com', 'port': 465, 'ssl': True},
    {'host': 'smtp.mxhichina.com', 'port': 465, 'ssl': True},
    {'host': 'smtp.qiye.aliyun.com', 'port': 465, 'ssl': True},
]

SENDER_EMAIL    = os.environ.get('SMTP_USER', 'info@ultrasoundbci.org.cn')
SENDER_PASS     = os.environ.get('SMTP_PASS', '8zqawu$7Fa@6yXjP')
ORGANIZER_EMAIL = 'info@ultrasoundbci.org.cn'
RSVP_FILE       = '/tmp/rsvp_records.json'


def build_confirmation_email(name, title, institution, role, email):
    role_map = {'oral': '口头报告', 'poster': '海报展示', 'attendee': '仅参会'}
    role_cn = role_map.get(role, role)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<style>
body{{font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#f4f6f9;margin:0;padding:20px}}
.card{{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)}}
.hdr{{background:linear-gradient(135deg,#0a1628,#0e4d64);padding:40px 30px;text-align:center}}
.hdr h1{{color:#fff;font-size:24px;margin:0 0 6px;letter-spacing:2px}}
.hdr p{{color:#7aeaef;font-size:14px;margin:0;letter-spacing:1px}}
.gold{{height:3px;background:linear-gradient(90deg,#c9a84c,#e8d48b,#c9a84c)}}
.body{{padding:35px 30px}}
.greeting{{font-size:18px;color:#0a1628;font-weight:600;margin-bottom:20px}}
.text{{font-size:15px;color:#444;line-height:1.9;margin-bottom:15px}}
.box{{background:#f0f7ff;border-left:4px solid #0e4d64;border-radius:0 8px 8px 0;padding:18px 20px;margin:20px 0}}
.row{{display:flex;margin-bottom:8px;font-size:14px}}
.lbl{{color:#888;width:80px;flex-shrink:0}}
.val{{color:#0a1628;font-weight:500}}
.hl{{color:#c9a84c;font-weight:600}}
.ftr{{background:#f8f9fa;padding:20px 30px;text-align:center;border-top:1px solid #eee}}
.ftr p{{font-size:12px;color:#999;margin:4px 0}}
</style></head><body>
<div class="card">
<div class="hdr"><h1>超声脑机横琴论坛</h1><p>Hengqin Ultrasound BCI Forum · 2026</p></div>
<div class="gold"></div>
<div class="body">
<div class="greeting">尊敬的 {name} {title}，</div>
<p class="text">感谢您确认参加<span class="hl">首届超声脑机横琴论坛</span>！我们非常荣幸地收到您的参会确认，期待与您在横琴共同探讨超声脑机接口领域的前沿进展。</p>
<div class="box">
<div class="row"><span class="lbl">参会者</span><span class="val">{name} {title}</span></div>
<div class="row"><span class="lbl">单位</span><span class="val">{institution}</span></div>
<div class="row"><span class="lbl">参会身份</span><span class="val">{role_cn}</span></div>
<div class="row"><span class="lbl">日期</span><span class="val">2026年4月21–22日（全程参会）</span></div>
<div class="row"><span class="lbl">地点</span><span class="val">横琴粤澳深度合作区 · 英迪格酒店</span></div>
</div>
<p class="text">组委会将于会前两周向您发送详细日程、差旅资助申请表及住宿信息。如有问题请联系：<br><strong>📧 info@ultrasoundbci.org.cn</strong></p>
<p class="text">再次感谢您的支持，期待与您在横琴相聚！</p>
<p class="text" style="margin-top:30px">此致<br><strong style="color:#0a1628">超声脑机横琴论坛组委会</strong><br><span style="color:#888;font-size:13px">Hengqin Ultrasound BCI Forum Organizing Committee</span></p>
</div>
<div class="ftr"><p>超声脑机横琴论坛 · Hengqin Ultrasound BCI Forum</p><p>info@ultrasoundbci.org.cn</p></div>
</div></body></html>"""


def build_notify_email(name, title, institution, role, email, abstract):
    role_map = {'oral': '口头报告', 'poster': '海报展示', 'attendee': '仅参会'}
    role_cn = role_map.get(role, role)
    abs_html = f"<div style='background:#f8f9fa;border-radius:8px;padding:15px;margin-top:10px;font-size:14px;color:#555;line-height:1.8'>{abstract}</div>" if abstract else "<p style='color:#aaa;font-size:13px'>（未填写）</p>"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<style>
body{{font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#f4f6f9;margin:0;padding:20px}}
.card{{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)}}
.hdr{{background:linear-gradient(135deg,#0a1628,#0e4d64);padding:30px;text-align:center}}
.hdr h1{{color:#c9a84c;font-size:20px;margin:0}}
.body{{padding:30px}}
.row{{border-bottom:1px solid #f0f0f0;padding:12px 0;display:flex}}
.lbl{{color:#888;font-size:13px;width:100px;flex-shrink:0}}
.val{{color:#333;font-size:14px;font-weight:500}}
</style></head><body>
<div class="card">
<div class="hdr"><h1>📋 新增参会确认通知</h1></div>
<div class="body">
<div class="row"><span class="lbl">姓名</span><span class="val">{name} {title}</span></div>
<div class="row"><span class="lbl">单位</span><span class="val">{institution}</span></div>
<div class="row"><span class="lbl">参会身份</span><span class="val">{role_cn}</span></div>
<div class="row"><span class="lbl">邮箱</span><span class="val">{email}</span></div>
<div class="row"><span class="lbl">提交时间</span><span class="val">{datetime.now().strftime('%Y-%m-%d %H:%M')}</span></div>
<div class="row"><span class="lbl">研究摘要</span><span class="val">{abs_html}</span></div>
</div></div></body></html>"""


def send_email(to_email, subject, html_body, cc_email=None):
    msg = MIMEMultipart('alternative')
    msg['From'] = f'超声脑机横琴论坛 <{SENDER_EMAIL}>'
    msg['To'] = to_email
    msg['Subject'] = Header(subject, 'utf-8')
    if cc_email:
        msg['Cc'] = cc_email
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    recipients = [to_email] + ([cc_email] if cc_email else [])
    for cfg in SMTP_CONFIGS:
        try:
            if cfg['ssl']:
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(cfg['host'], cfg['port'], context=ctx, timeout=10) as s:
                    s.login(SENDER_EMAIL, SENDER_PASS)
                    s.sendmail(SENDER_EMAIL, recipients, msg.as_string())
            else:
                with smtplib.SMTP(cfg['host'], cfg['port'], timeout=10) as s:
                    s.ehlo(); s.starttls()
                    s.login(SENDER_EMAIL, SENDER_PASS)
                    s.sendmail(SENDER_EMAIL, recipients, msg.as_string())
            logging.info(f"Email sent via {cfg['host']}")
            return True
        except Exception as e:
            logging.warning(f"SMTP {cfg['host']} failed: {e}")
            continue
    return False


def save_rsvp(data):
    records = []
    if os.path.exists(RSVP_FILE):
        try:
            with open(RSVP_FILE, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except Exception:
            records = []
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    records.append(data)
    with open(RSVP_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/hero_bg.jpg')
def hero_bg():
    return send_from_directory('.', 'hero_bg.jpg')


@app.route('/api/rsvp', methods=['POST', 'OPTIONS'])
def rsvp():
    if request.method == 'OPTIONS':
        resp = jsonify({})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp
    try:
        data = request.get_json(force=True)
        name        = data.get('name', '').strip()
        title       = data.get('title', '').strip()
        institution = data.get('institution', '').strip()
        role        = data.get('role', '').strip()
        email       = data.get('email', '').strip()
        abstract    = data.get('abstract', '').strip()

        if not all([name, institution, email]):
            return jsonify({'success': False, 'error': '请填写必填项'}), 400

        save_rsvp({'name': name, 'title': title, 'institution': institution,
                   'role': role, 'email': email, 'abstract': abstract})

        conf_html = build_confirmation_email(name, title, institution, role, email)
        sent = send_email(
            to_email=email,
            subject='【超声脑机横琴论坛】参会确认 | RSVP Confirmation',
            html_body=conf_html,
            cc_email=ORGANIZER_EMAIL if email != ORGANIZER_EMAIL else None
        )

        notify_html = build_notify_email(name, title, institution, role, email, abstract)
        send_email(
            to_email=ORGANIZER_EMAIL,
            subject=f'【新报名】{name} {title} — {institution}',
            html_body=notify_html
        )

        if sent:
            return jsonify({'success': True, 'message': f'确认邮件已发送至 {email}，请查收！'})
        else:
            return jsonify({'success': True, 'message': '报名信息已记录！组委会将手动发送确认邮件。'})

    except Exception as e:
        logging.error(f"RSVP error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/records')
def admin_records():
    token = request.args.get('token', '')
    if token != 'ubci2026admin':
        return jsonify({'error': 'Unauthorized'}), 401
    records = []
    if os.path.exists(RSVP_FILE):
        with open(RSVP_FILE, 'r', encoding='utf-8') as f:
            records = json.load(f)
    return jsonify({'total': len(records), 'records': records})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
