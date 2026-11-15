# MegaJam bridge: run a Python file inside the open Unreal Editor via
# Python Remote Execution (UDP multicast discovery + TCP command channel).
# Stdlib only, so it runs with the engine's bundled python.exe.
# Usage: python mj_ue_exec.py <code_file> [timeout_sec] [project_hint]
import json, os, socket, sys, time, uuid

GROUP = ('239.0.0.1', 6766)
MAGIC = 'ue_py'
VERSION = 1

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def mk(kind, src, dest=None, data=None):
    m = {'version': VERSION, 'magic': MAGIC, 'type': kind, 'source': src}
    if dest:
        m['dest'] = dest
    if data is not None:
        m['data'] = data
    return json.dumps(m, ensure_ascii=False).encode('utf-8')


def parse(raw):
    try:
        m = json.loads(raw.decode('utf-8'))
    except Exception:
        return None
    if not isinstance(m, dict) or m.get('magic') != MAGIC:
        return None
    return m


def open_udp(bind_addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if hasattr(socket, 'SO_REUSEPORT'):
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    else:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((bind_addr, GROUP[1]))
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 0)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                 socket.inet_aton(GROUP[0]) + socket.inet_aton(bind_addr))
    s.settimeout(0.2)
    return s


def discover(udp, me, seconds):
    nodes = {}
    end = time.time() + seconds
    next_ping = 0.0
    while time.time() < end:
        if time.time() >= next_ping:
            udp.sendto(mk('ping', me), GROUP)
            next_ping = time.time() + 1.0
        try:
            raw, _ = udp.recvfrom(65536)
        except socket.timeout:
            continue
        except OSError:
            continue
        m = parse(raw)
        if not m or m.get('source') == me or m.get('type') != 'pong':
            continue
        nodes[m['source']] = m.get('data') or {}
        # small grace period to collect other editors, then stop
        end = min(end, time.time() + 0.6)
    return nodes


def pick(nodes, hint):
    if not nodes:
        return None, None
    if hint:
        h = hint.lower()
        for nid, d in nodes.items():
            if h in str(d.get('project_name', '')).lower() or h in str(d.get('project_root', '')).lower():
                return nid, d
    nid = sorted(nodes.keys())[0]
    return nid, nodes[nid]


def recv_json(conn, timeout):
    conn.settimeout(timeout)
    buf = b''
    while True:
        chunk = conn.recv(1 << 20)
        if not chunk:
            break
        buf += chunk
        m = parse(buf)
        if m is not None:
            return m
    return parse(buf)


def main():
    if len(sys.argv) < 2:
        print('usage: mj_ue_exec.py <code_file> [timeout_sec] [project_hint]')
        return 64
    path = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    hint = sys.argv[3] if len(sys.argv) > 3 else 'DirectorsCut'
    with open(path, 'rb') as f:
        code = f.read().decode('utf-8-sig')

    me = str(uuid.uuid4())
    binds = [os.environ.get('MJ_UE_BIND') or '0.0.0.0']
    if '127.0.0.1' not in binds:
        binds.append('127.0.0.1')

    udp = None
    nodes = {}
    for b in binds:
        try:
            udp = open_udp(b)
        except OSError as e:
            print('[UE] multicast bind %s failed: %s' % (b, e))
            udp = None
            continue
        nodes = discover(udp, me, 4.0)
        if nodes:
            break
        udp.close()
        udp = None
    if not nodes:
        print('[UE] HATA: Unreal Editor bulunamadi. Editor acik mi, Python Remote Execution acik mi?')
        return 3

    nid, info = pick(nodes, hint)
    print('[UE] editor: %s | %s | %s' % (info.get('project_name', '?'), info.get('engine_version', '?'), info.get('machine', '?')))

    lst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lst.bind(('127.0.0.1', 0))
    lst.listen(1)
    lst.settimeout(1.0)
    port = lst.getsockname()[1]
    conn = None
    end = time.time() + 8.0
    while conn is None and time.time() < end:
        udp.sendto(mk('open_connection', me, nid, {'command_ip': '127.0.0.1', 'command_port': port}), GROUP)
        try:
            conn, _ = lst.accept()
        except socket.timeout:
            conn = None
    if conn is None:
        print('[UE] HATA: editor komut baglantisini acmadi.')
        udp.close()
        return 4

    rc = 0
    try:
        conn.settimeout(30)
        conn.sendall(mk('command', me, nid, {'command': code, 'unattended': True, 'exec_mode': 'ExecuteFile'}))
        res = recv_json(conn, timeout)
        if not res:
            print('[UE] HATA: bos yanit')
            rc = 5
        else:
            d = res.get('data') or {}
            for o in d.get('output') or []:
                kind = o.get('type', 'Info')
                text = str(o.get('output', '')).rstrip('\n')
                print(text if kind == 'Info' else '[%s] %s' % (kind, text))
            ok = bool(d.get('success'))
            result = d.get('result')
            if result not in (None, '', 'None'):
                print('[UE] result: %s' % result)
            print('[UE] success=%s' % ok)
            rc = 0 if ok else 2
    except socket.timeout:
        print('[UE] HATA: %s sn icinde yanit gelmedi (editor hala calisiyor olabilir).' % int(timeout))
        rc = 6
    finally:
        try:
            udp.sendto(mk('close_connection', me, nid), GROUP)
        except Exception:
            pass
        for s in (conn, lst, udp):
            try:
                s.close()
            except Exception:
                pass
    return rc


if __name__ == '__main__':
    sys.exit(main())
