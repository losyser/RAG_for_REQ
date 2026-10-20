"""Loopback-only, offline S2 annotation. No model/project execution dependencies."""
from __future__ import annotations
import argparse
import ast
import copy
import csv
import hashlib
import hmac
import io
import json
import os
import math
from pathlib import Path
import re
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
STATES = ('unanswered', 'relevant', 'irrelevant', 'uncertain')
MAX_BODY = 4_000_000

class ReviewError(Exception):
    def __init__(self, message, status=400, code='invalid_input'):
        super().__init__(message)
        self.status = status
        self.code = code

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def require(condition, message):
    if not condition:
        raise ReviewError(message)

def text(value, limit=4000):
    require(isinstance(value, str) and len(value) <= limit, '文本类型或长度无效。')
    return value

def exact(obj, fields):
    require(isinstance(obj, dict) and set(obj) == set(fields.split()), '文件字段不符合格式；原记录未更改。')

def pair_id(component, intent):
    return component + ':' + intent

def demo_package():
    package = {'schema': 1, 'kind': 'practice', 'title': '隔离练习 · 非研究数据',
        'protocol': 'practice-only', 'provenance': {'source_sha256': 'practice', 'taxonomy_sha256': 'practice', 'prediction_scope': 'practice-only'},
        'components': {'pump': '冷却水泵（练习）', 'sensor': '温度传感器（练习）'},
        'intents': {'redundancy': '备用与切换', 'alarm': '报警要求', 'inspection': '检查维护'},
        'taxonomy': {'pump': ['redundancy', 'inspection'], 'sensor': ['alarm', 'inspection']},
        'sources': [
            {'id': 'DEMO001', 'text': '【练习文本】冷却水泵应有备用配置，并定期检查。', 'candidates': [
                {'id': 'pump:redundancy', 'component': 'pump', 'intent': 'redundancy'},
                {'id': 'sensor:alarm', 'component': 'sensor', 'intent': 'alarm'}]},
            {'id': 'DEMO002', 'text': '【练习文本】温度传感器需要定期检查，异常时提示操作人员。', 'candidates': [
                {'id': 'sensor:inspection', 'component': 'sensor', 'intent': 'inspection'}]}]}
    package['version'] = digest(package)
    return package

def validate_package(package):
    exact(package, 'schema kind title protocol provenance components intents taxonomy sources version')
    require(package['schema'] == 1 and package['kind'] in ('practice', 'pilot', 'formal'), '任务包版本或类型不支持。')
    require(package['version'] == digest({k:v for k,v in package.items() if k != 'version'}), '任务包校验失败，文件可能损坏。')
    text(package['title'], 120); text(package['protocol'], 500)
    require(package['protocol'].strip(), '任务包必须标明协议编号。')
    exact(package['provenance'], 'source_sha256 taxonomy_sha256 prediction_scope')
    for v in package['provenance'].values(): text(v, 300)
    for name in ('components', 'intents'):
        require(isinstance(package[name], dict) and 0 < len(package[name]) <= 200, '分类表无效。')
        for key, value in package[name].items():
            require(re.fullmatch(r'[a-z][a-z0-9_]{0,79}', key) is not None, '分类 ID 无效。')
            text(value, 500)
    require(set(package['taxonomy']) == set(package['components']), '分类目录不完整。')
    for intents in package['taxonomy'].values():
        require(isinstance(intents, list) and intents and len(set(intents)) == len(intents) and set(intents) <= set(package['intents']), '适用配对表无效。')
    require(isinstance(package['sources'], list) and 0 < len(package['sources']) <= 100, '源需求数量无效。')
    ids = set()
    for source in package['sources']:
        exact(source, 'id text candidates')
        require(re.fullmatch(r'[A-Za-z0-9_-]{1,80}', source['id']) is not None and source['id'] not in ids, '源需求 ID 重复或无效。')
        ids.add(source['id']); text(source['text'], 20000)
        require(isinstance(source['candidates'], list) and len(source['candidates']) <= 1000, '候选集合无效。')
        seen = set()
        for pair in source['candidates']:
            exact(pair, 'id component intent')
            c, i = pair['component'], pair['intent']
            require(c in package['taxonomy'] and i in package['taxonomy'][c], '候选配对不在 taxonomy 中。')
            require(pair['id'] == pair_id(c, i) and pair['id'] not in seen, '候选 ID 重复或无效。')
            seen.add(pair['id'])
    return package

def blank_answers(package):
    result = {s['id']: {'candidates': {p['id']: 'unanswered' for p in s['candidates']},
        'initial_pairs': [], 'missing_pairs': [], 'first_pass_done': False,
        'coverage_reviewed': False, 'note': ''} for s in package['sources']}
    if package['kind']=='formal':
        for answer in result.values(): answer['review_details']=blank_review_details()
    return result

def blank_review_details():
    return {'exposure':'not_viewed','first_pass_at':'','first_candidate_at':'','total_minutes':None,
            'interruption_minutes':None,'complete':'unanswered','questions':''}

def validate_answers(package, answers):
    require(isinstance(answers, dict) and set(answers) == {s['id'] for s in package['sources']}, '源需求记录不完整。')
    for source in package['sources']:
        answer = answers[source['id']]
        fields='candidates initial_pairs missing_pairs first_pass_done coverage_reviewed note'
        exact(answer, fields+(' review_details' if 'review_details' in answer else ''))
        if 'review_details' in answer:
            detail=answer['review_details']
            exact(detail,'exposure first_pass_at first_candidate_at total_minutes interruption_minutes complete questions')
            require(detail['exposure'] in ('not_viewed','after_first_pass','before_first_pass','uncertain'), '候选暴露状态无效。')
            require(detail['complete'] in ('unanswered','yes','no'),'完成状态无效。')
            for key in ('first_pass_at','first_candidate_at','questions'):text(detail[key])
            for key in ('total_minutes','interruption_minutes'):
                v=detail[key];require(v is None or (type(v) in (int,float) and math.isfinite(v) and v>=0),'耗时必须为非负数或空白。')
            if detail['total_minutes'] is not None and detail['interruption_minutes'] is not None:
                require(detail['interruption_minutes']<=detail['total_minutes'],'中断时间不能超过总耗时。')
        require(type(answer['first_pass_done']) is bool and type(answer['coverage_reviewed']) is bool, '完成标记无效。')
        require(isinstance(answer['candidates'], dict) and set(answer['candidates']) == {p['id'] for p in source['candidates']}, '候选 ID 被修改。')
        require(all(v in STATES for v in answer['candidates'].values()), '判断值无效。')
        require(answer['first_pass_done'] or (all(v == 'unanswered' for v in answer['candidates'].values()) and not answer['coverage_reviewed'] and not answer['missing_pairs']), '请先完成独立首判。')
        text(answer['note'])
        for name in ('initial_pairs', 'missing_pairs'):
            pairs = answer[name]
            require(isinstance(pairs, list) and len(pairs) <= 1000, '配对列表无效。')
            seen = set()
            for pair in pairs:
                exact(pair, 'component intent verdict note')
                c, i = pair['component'], pair['intent']
                require(c in package['taxonomy'] and i in package['taxonomy'][c], '补充配对不在 taxonomy 中。')
                pid = pair_id(c, i)
                require(pid not in seen and (name == 'initial_pairs' or pid not in answer['candidates']), '配对已存在，请在原位置修改。')
                seen.add(pid)
                require(pair['verdict'] in ('relevant', 'uncertain'), '补充配对须为相关或不确定。')
                text(pair['note'], 1000)

def summary(task):
    completed = uncertain = 0
    for answer in task['answers'].values():
        completed += bool(answer['coverage_reviewed'] and answer['first_pass_done'] and 'unanswered' not in answer['candidates'].values())
        uncertain += sum(v == 'uncertain' for v in answer['candidates'].values()) + sum(p['verdict'] == 'uncertain' for p in answer['missing_pairs'])
    return {'sources': len(task['answers']), 'completed': completed, 'uncertain': uncertain,
            'gold_ready': False}  # Reference-set readiness is decided by the strict formal scorer.

def atomic_json(path, value):
    temporary = path.with_name(path.name + '.' + secrets.token_hex(6) + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def path(self, task_id):
        require(isinstance(task_id, str) and re.fullmatch(r'[a-f0-9]{32}', task_id) is not None, '任务编号无效。')
        return self.directory / (task_id + '.json')

    def read(self, task_id):
        path = self.path(task_id)
        if not path.exists(): raise ReviewError('本机未找到该审查，可使用备份恢复为新副本。', 404, 'record_missing')
        try:
            wrapper = json.loads(path.read_text(encoding='utf-8'))
            require(wrapper['sha256'] == digest(wrapper['record']), '本机记录校验失败；禁止覆盖。请使用备份恢复副本。')
            record = wrapper['record']
            validate_package(record['task']['package'])
            validate_answers(record['task']['package'], record['task']['answers'])
            return record
        except (ValueError, KeyError, TypeError, OSError, ReviewError):
            raise ReviewError('本机记录损坏或无法读取；禁止覆盖。请保留文件并用备份恢复副本。', 409, 'record_corrupt')

    def write(self, record):
        path = self.path(record['task']['id'])
        if path.exists():
            self.read(record['task']['id'])  # refuse to replace corrupt original
            previous = json.loads(path.read_text(encoding='utf-8'))
            atomic_json(path.with_suffix('.previous.json'), previous)
        atomic_json(path, {'record': record, 'sha256': digest(record)})

    def auth(self, task_id, token):
        record = self.read(task_id)
        if not isinstance(token, str) or not hmac.compare_digest(record['token_hash'], hashlib.sha256(token.encode()).hexdigest()):
            raise ReviewError('无法打开此审查，请使用该任务自己的备份文件。', 403)
        return record

    def create(self, reviewer, package, request_id):
        text(reviewer, 80); require(reviewer.strip(), '请输入本位专家的代号。')
        require(isinstance(request_id, str) and re.fullmatch(r'[a-f0-9]{32}', request_id) is not None, '请求编号无效。')
        validate_package(package)
        # A deterministic id/token for the same secret request nonce makes retries idempotent.
        task_id = hashlib.sha256(('task:' + request_id).encode()).hexdigest()[:32]
        token = hashlib.sha256(('access:' + request_id).encode()).hexdigest()
        with self.lock:
            if self.path(task_id).exists():
                record = self.auth(task_id, token)
                require(record['task']['reviewer'] == reviewer.strip() and record['task']['package']['version'] == package['version'], '重复请求内容不同，请重新新建。')
            else:
                task = {'schema': 1, 'id': task_id, 'reviewer': reviewer.strip(), 'package': copy.deepcopy(package),
                    'answers': blank_answers(package), 'revision': 0, 'current_index': 0,
                    'created_at': stamp(), 'updated_at': stamp(), 'restored_from': None}
                record = {'token_hash': hashlib.sha256(token.encode()).hexdigest(), 'task': task}
                self.write(record)
            return {'task': copy.deepcopy(record['task']), 'token': token}

    def get(self, task_id, token):
        with self.lock: return copy.deepcopy(self.auth(task_id, token)['task'])

    def save(self, task_id, token, revision, answers, current_index):
        with self.lock:
            record = self.auth(task_id, token)
            task = record['task']
            if type(revision) is not int or revision != task['revision']:
                raise ReviewError('此任务已在另一窗口更新，已阻止覆盖。请导出待保存记录后重新打开。', 409)
            validate_answers(task['package'], answers)
            require(type(current_index) is int and 0 <= current_index < len(task['package']['sources']), '当前位置无效。')
            for sid, previous in task['answers'].items():
                if previous['first_pass_done']:
                    require(answers[sid]['first_pass_done'] and answers[sid]['initial_pairs'] == previous['initial_pairs'], '独立首判已锁定，不可回写。')
            task['answers'] = copy.deepcopy(answers)
            task['current_index'] = current_index
            task['revision'] += 1; task['updated_at'] = stamp()
            self.write(record)
            return copy.deepcopy(task)

    def backup(self, task_id, token):
        task = self.get(task_id, token)
        result = {'format': 'mapping-review-backup-v1', 'task': task, 'token': token}
        result['sha256'] = digest(result)
        return result

    def open_backup(self, backup, restore=False, request_id=None):
        exact(backup, 'format task token sha256')
        require(backup['format'] == 'mapping-review-backup-v1' and backup['sha256'] == digest({k:v for k,v in backup.items() if k != 'sha256'}), '备份校验失败；未打开或覆盖任何审查。')
        task = backup['task']
        exact(task, 'schema id reviewer package answers revision current_index created_at updated_at restored_from')
        self.path(task['id']); text(task['reviewer'], 80); text(backup['token'], 128)
        require(task['schema'] == 1 and type(task['revision']) is int and task['revision'] >= 0, '审查版本无效。')
        require(type(task['current_index']) is int and 0 <= task['current_index'] < len(task['package']['sources']), '审查位置无效。')
        validate_package(task['package']); validate_answers(task['package'], task['answers'])
        if not restore:
            current = self.get(task['id'], backup['token'])
            require(current['package']['version'] == task['package']['version'], '备份任务包与本机版本不一致。')
            if current['revision'] < task['revision']:
                raise ReviewError('备份比本机记录更新，请选择恢复副本。', 409, 'backup_newer')
            return {'task': current, 'token': backup['token']}
        with self.lock:
            result = self.create(task['reviewer'], task['package'], request_id)
            record = self.auth(result['task']['id'], result['token'])
            if record['task']['restored_from'] is None:
                record['task']['answers'] = copy.deepcopy(task['answers'])
                record['task']['current_index'] = task['current_index']
                record['task']['restored_from'] = {'id': task['id'], 'revision': task['revision'], 'updated_at': task['updated_at']}
                self.write(record)
            return {'task': copy.deepcopy(record['task']), 'token': result['token']}

def csv_export(task):
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['任务ID','专家代号','任务类型','数据版本','协议','源需求ID','原始中文需求','记录类别','部件ID','方面ID','判断','备注','完成全目录查漏','审查版本'])
    labels = dict(zip(STATES, ['未答','相关','不相关','不确定']))
    def safe(value):
        value = str(value)
        return "'" + value if value.startswith(('=','+','-','@','\t','\r')) else value
    for source in task['package']['sources']:
        a = task['answers'][source['id']]
        common = [task['id'], task['reviewer'], task['package']['kind'], task['package']['version'], task['package']['protocol'], source['id'], source['text']]
        rows = [('候选', p['component'], p['intent'], a['candidates'][p['id']], '') for p in source['candidates']]
        rows += [(label, p['component'], p['intent'], p['verdict'], p['note']) for key,label in [('initial_pairs','独立首判'),('missing_pairs','池外补漏')] for p in a[key]]
        rows += [('源需求备注', '', '', 'unanswered', a['note'])]
        for label,c,i,v,n in rows:
            writer.writerow([safe(x) for x in common + [label,c,i,labels[v],n,str(a['coverage_reviewed']),task['revision']]])
    return ('\ufeff' + output.getvalue()).encode('utf-8')

class Server(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, port, directory):
        self.store = Store(directory)
        super().__init__(('127.0.0.1', port), Handler)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # no task tokens or answers in logs

    def send(self, code, data, content_type='application/json; charset=utf-8'):
        payload = canonical(data) if content_type.startswith('application/json') else data
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def allowed(self):
        expected = '127.0.0.1:' + str(self.server.server_port)
        require(self.headers.get('Host') == expected, '仅接受本机访问。')
        origin = self.headers.get('Origin')
        require(origin is None or origin == 'http://' + expected, '拒绝跨站请求。')

    def do_GET(self):
        try:
            self.allowed()
            files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'), '/style.css': ('style.css', 'text/css; charset=utf-8')}
            path = urlparse(self.path).path
            if path == '/formal_assignment.json':
                package=json.loads((HERE/'formal_assignment.json').read_text(encoding='utf8'))
                validate_package(package)
                require(package['kind']=='formal','不是正式任务包。')
                return self.send(200,package)
            if path == '/api/health': return self.send(200, {'app': 'expert-mapping-review', 'version': 1, 'process_id': os.getpid(), 'mode': 'production' if self.server.store.directory.resolve() == (HERE / 'local_records').resolve() else 'isolated-test'})
            if path not in files: return self.send(404, {'error': '页面不存在。'})
            name, mime = files[path]
            self.send(200, (HERE / name).read_bytes(), mime)
        except ReviewError as error: self.send(error.status, {'error': str(error), 'code': error.code})

    def do_POST(self):
        try:
            self.allowed()
            require(self.headers.get('Content-Type') == 'application/json', '请求格式无效。')
            size = int(self.headers.get('Content-Length', '0'))
            require(0 < size <= MAX_BODY, '文件过大或为空。')
            body = json.loads(self.rfile.read(size).decode('utf-8'))
            store = self.server.store
            route = urlparse(self.path).path
            if route == '/api/new':
                package = demo_package() if body.get('kind') == 'practice' else body.get('package')
                require(isinstance(package, dict) and package.get('kind') == body.get('kind'), '任务类型与数据包不一致；试做包不能作为正式任务。')
                result = store.create(body.get('reviewer'), package, body.get('request_id'))
            elif route == '/api/get': result = {'task': store.get(body.get('id'), body.get('token'))}
            elif route == '/api/save': result = {'task': store.save(body.get('id'), body.get('token'), body.get('revision'), body.get('answers'), body.get('current_index'))}
            elif route == '/api/open': result = store.open_backup(body.get('backup'), body.get('restore', False), body.get('request_id'))
            elif route == '/api/export':
                if body.get('format') == 'csv':
                    return self.send(200, csv_export(store.get(body.get('id'), body.get('token'))), 'text/csv; charset=utf-8')
                result = store.backup(body.get('id'), body.get('token'))
            else: raise ReviewError('接口不存在。', 404)
            self.send(200, result)
        except ReviewError as error: self.send(error.status, {'error': str(error), 'code': error.code})
        except (ValueError, TypeError, KeyError, AttributeError): self.send(400, {'error': '文件或请求格式损坏；现有审查未覆盖。'})
        except OSError: self.send(500, {'error': '磁盘读写失败；请保留页面并导出待保存记录。'})

def build_assignment(project, source_ids, protocol, kind='formal'):
    """Coordinator-only, explicit IDs; never samples, reads model predictions, or fills answers."""
    pool_path = project / 'data/search_results/exp_v4/e1_pool.csv'
    taxonomy_path = project / 'cooling_rag_mg/evidence_taxonomy.py'
    definitions = {}
    taxonomy_text = taxonomy_path.read_text(encoding='utf-8')
    taxonomy_node = None
    for node in ast.parse(taxonomy_text).body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in ('COMPONENTS','INTENTS','TAXONOMY'):
            definitions[node.target.id] = ast.literal_eval(node.value)
            if node.target.id == 'TAXONOMY': taxonomy_node = node.value
    # Keep every original legal pair. Some intent IDs lack a dictionary label;
    # expose their original line comments, not invented semantic definitions.
    lines = taxonomy_text.splitlines()
    for intents_node in taxonomy_node.values:
        for item in intents_node.elts:
            intent = ast.literal_eval(item)
            if intent not in definitions['INTENTS']:
                comment = lines[item.end_lineno - 1].partition('#')[2].strip()
                definitions['INTENTS'][intent] = ('[原目录行注释] ' + comment) if comment else ('[原目录无中文说明] ' + intent)
    require(kind in ('formal', 'pilot'), '真实任务仅支持校准或正式类型。')
    ids = [sid.strip() for sid in source_ids.split(',')]
    require(len(ids) == len(set(ids)), '源需求 ID 重复。')
    sources = {sid: {'id': sid, 'text': '', 'candidates': []} for sid in ids}
    with pool_path.open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            if row['or_id'] in sources:
                source = sources[row['or_id']]
                require(not source['text'] or source['text'] == row['requirement_text'], '同一源需求文本不一致。')
                source['text'] = row['requirement_text']
                source['candidates'].append({'id': pair_id(row['component'], row['intent']), 'component': row['component'], 'intent': row['intent']})
    require(all(s['text'] for s in sources.values()), '存在未知或空源需求。')
    for source in sources.values(): source['candidates'].sort(key=lambda p:p['id'])
    package = {'schema': 1, 'kind': kind, 'title': '真实需求试做校准（排除正式评分）' if kind == 'pilot' else '船舶冷却系统需求映射审核', 'protocol': protocol,
        'provenance': {'source_sha256': hashlib.sha256(pool_path.read_bytes()).hexdigest(), 'taxonomy_sha256': hashlib.sha256(taxonomy_path.read_bytes()).hexdigest(), 'prediction_scope': 'historical-upstream-stage1-used-by-v4; stored-in-v3; no-new-run'},
        'components': definitions['COMPONENTS'], 'intents': definitions['INTENTS'], 'taxonomy': definitions['TAXONOMY'], 'sources': list(sources.values())}
    package['version'] = digest(package); validate_package(package)
    return package

def prepare_assignment(project, source_ids, protocol, output, kind='formal'):
    package = build_assignment(project, source_ids, protocol, kind)
    with output.open('x', encoding='utf-8') as handle: json.dump(package, handle, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8769)
    parser.add_argument('--data-dir', type=Path, default=HERE / 'local_records')
    parser.add_argument('--prepare-assignment', type=Path)
    parser.add_argument('--source-ids')
    parser.add_argument('--protocol')
    parser.add_argument('--phase', choices=['formal', 'pilot'], default='formal')
    parser.add_argument('--project', type=Path, default=HERE.parents[1])
    args = parser.parse_args()
    if args.prepare_assignment:
        require(args.source_ids and args.protocol, '必须提供已确认的 source-ids 和 protocol；工具不自动抽样。')
        prepare_assignment(args.project, args.source_ids, args.protocol, args.prepare_assignment, args.phase)
        return
    server = Server(args.port, args.data_dir)
    print(f'Local review ready: http://127.0.0.1:{server.server_port}', flush=True)
    server.serve_forever()

if __name__ == '__main__': main()
