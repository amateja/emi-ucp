###############################################################################
#
# UCP version - 1.0
#
###############################################################################

from utils import ira, bits7

import threading
import types
import socket
import Queue

STX = chr(2)
ETX = chr(3)
O = 'O'
R = 'R'
A = 'A'
N = 'N'
SEP = '/'


class FrameMalformed(BaseException):
    pass


class Trn:
    class __Trn:
        def __init__(self):
            self.val = -1

    instance = None

    def __init__(self):
        if not Trn.instance:
            Trn.instance = Trn.__Trn()

    def next(self):
        self.instance.val = (self.instance.val + 1) % 100
        return self.instance.val


class Message:
    TRN = Trn()
    msg = ''

    def __init__(self):
        pass

    @staticmethod
    def checksum(text):
        return sum(map(ord, text)) % 256

    @staticmethod
    def data_len(*args):
        return len(args) + sum(map(len, map(str, args))) + 16

    @classmethod
    def from_string(cls, msg):
        return cls()

    @staticmethod
    def unpack(msg, x):
        if msg[0] == STX and msg[-1] == ETX:
            msg = msg[1:-1]
        else:
            raise FrameMalformed('Start or stop character missing.')
        ln = len(msg)
        msg = msg.split(SEP)
        t_ln = int(msg[1])
        if t_ln != ln:
            raise FrameMalformed('Message is %d long, but %d declared. %s'
                                 % (ln, t_ln, msg[3]))
        if x != O and x != R:
            raise ValueError('Message can be either operation or response.')

        if x != msg[2]:
            raise FrameMalformed('Message is not a %s.' % 'operation' if x == O
                                 else 'response')
        t_checksum = int(msg[-1], 16)
        if t_checksum != Message.checksum(SEP.join(msg[:-1]) + SEP):
            raise FrameMalformed('Checksum does not comply.')

        t_trn = int(msg[0])
        t_ot = int(msg[3])
        if t_ot not in (1, 2, 3, 30, 31, 51, 52, 53, 54, 55, 56, 57, 58, 59,
                        60, 61):
            raise TypeError('Wrong operation type.')
        return msg[4:-1], t_trn, t_ot

    def fields(self):
        for i in dir(self):
            y = getattr(self, i)
            if i.startswith('__') or y == '' \
                    or isinstance(y, (types.InstanceType,
                                      types.FunctionType, types.MethodType)):
                continue
            print i, ':', y


class Response(Message):
    def __init__(self, ot, ack, trn=None, mvp_ec='', sm=''):
        Message.__init__(self)

        self.ot = ot
        self.ack = ack
        self.trn = self.TRN.next() if trn is None else trn
        self.mvp_ec = mvp_ec
        self.sm = sm

    def __str__(self):
        if self.ack == A and self.ot in (1, 2, 3, 31, 60, 61):
            ln = self.data_len(self.ack, self.sm)
            text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/{}/{}/'.format(
                self.trn, ln, R, self.ot, self.ack, self.sm)
        else:
            ln = self.data_len(self.ack, self.mvp_ec, self.sm)
            text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/{}/{}/{}/'.format(
                self.trn, ln, R, self.ot, self.ack, self.mvp_ec, self.sm)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, R)
        ack = msg[0]
        mvp_ec = '' if ack == A and ot in (1, 2, 3, 31, 60, 61) else msg[1]
        return cls(ot, ack, trn, mvp_ec, msg[-1])


class Request01(Message):
    def __init__(self, ot=1, trn=None, adc='', oadc='', ac='', mt='', xmsg=''):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.adc = adc
        self.oadc = oadc
        self.ac = ac
        self.mt = int(mt)
        self.xmsg = xmsg.decode('irahex') if self.mt == 3 else xmsg

    def __str__(self):
        msg = self.xmsg.encode('irahex') if self.mt == 3 else self.xmsg
        ln = self.data_len(self.adc, self.oadc, self.ac, self.mt, msg)
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/{}/{}/{}/'.format(
                   self.trn, ln, O, self.ot,
                   self.adc, self.oadc, self.ac, self.mt, msg)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, O)
        return cls(ot, trn, *msg)


class Request02(Message):
    def __init__(self, ot=2, trn=None, npl='', rads='', oadc='', ac='', mt='',
                 xmsg=''):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.npl = int(npl)
        self.rads = rads
        self.oadc = oadc
        self.ac = ac
        self.mt = int(mt)
        self.xmsg = xmsg.decode('irahex') if self.mt == 3 else xmsg

    def __str__(self):
        msg = self.xmsg.encode('irahex') if self.mt == 3 else self.xmsg
        rads = SEP.join(self.rads)
        ln = self.data_len(self.npl, rads, self.oadc, self.ac, self.mt, msg)
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/{}/{}/{}/{}/'.format(
                   self.trn, ln, O, self.ot,
                   self.npl, rads, self.oadc, self.ac, self.mt, msg)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, O)
        msg = [msg[0], msg[1:-4]] + msg[-4:]
        return cls(ot, trn, *msg)


class Request03(Message):
    def __init__(self, ot=3, trn=None, rad='', oadc='', ac='', dd='', ddt='',
                 mt='', xmsg=''):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.rad = rad
        self.oadc = oadc
        self.ac = ac
        self.dd = dd
        self.ddt = ddt
        self.mt = int(mt)
        self.xmsg = xmsg.decode('irahex') if self.mt == 3 else xmsg

    def __str__(self):
        msg = self.xmsg.encode('irahex') if self.mt == 3 else self.xmsg
        ln = self.data_len(self.rad, self.oadc, self.ac, self.dd, self.ddt,
                           self.mt, msg) + 9
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/{}/0////////{}/{}/{}/{}/'.format(
                   self.trn, ln, O, self.ot,
                   self.rad, self.oadc, self.ac, self.dd, self.ddt, self.mt,
                   msg)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, O)
        msg = msg[:3] + msg[-4:]
        return cls(ot, trn, *msg)


class Request30(Message):
    def __init__(self, ot=30, trn=None, adc='', oadc='', ac='', nrq='', nad='',
                 npid='', dd='', ddt='', vp='', amsg='', encoded=True):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.adc = adc
        self.oadc = oadc
        self.ac = ac
        self.nrq = nrq
        self.nad = nad
        self.npid = npid
        self.dd = dd
        self.ddt = ddt
        self.vp = vp
        self.amsg = amsg.decode('irahex') if encoded else amsg

    def __str__(self):
        msg = self.amsg.encode('irahex')
        ln = self.data_len(self.adc, self.oadc, self.ac, self.nrq, self.nad,
                           self.npid, self.dd, self.ddt, self.vp, msg)
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/'.format(
                   self.trn, ln, O, self.ot,
                   self.adc, self.oadc, self.ac, self.nrq, self.nad, self.npid,
                   self.dd, self.ddt, self.vp, msg)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, O)
        return cls(ot, trn, *msg)


class Request31(Message):
    def __init__(self, ot=31, trn=None, adc='', pid=''):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.adc = adc
        self.pid = pid

    def __str__(self):
        ln = self.data_len(self.adc, self.pid)
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/'.format(
                   self.trn, ln, O, self.ot,
                   self.adc, self.pid)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, O)
        return cls(ot, trn, *msg)


class Request5x(Message):
    def __init__(self, ot, trn=None, adc='', oadc='', ac='', nrq=None, nadc='',
                 nt=None, npid='', lrq='', lrad='', lpid='', dd='', ddt='',
                 vp='', rpid='', scts='', dst='', rsn='', dscts='', mt=None,
                 nb='', xmsg='', mms='', pr='', dcs='', mcls='', rpi='', cpg='',
                 rply='', otoa='', hplmn='', xser='', encoded=True):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.adc = adc
        if encoded and otoa == '5039':
            self.oadc = oadc.decode('bits7')
        else:
            self.oadc = oadc
        self.ac = ac
        try:
            self.nrq = int(nrq)
        except (ValueError, TypeError):
            self.nrq = ''
        self.nadc = nadc
        try:
            self.nt = int(nt)
        except (ValueError, TypeError):
            self.nt = ''
        else:
            if self.nt > 7:
                raise ValueError('Parameter nt should be in range 0 - 7.')
        self.npid = npid
        self.lrq = lrq
        self.lrad = lrad
        self.lpid = lpid
        self.dd = dd
        self.ddt = ddt
        self.vp = vp
        self.rpid = rpid
        self.scts = scts
        self.dst = dst
        self.rsn = rsn
        self.dscts = dscts
        try:
            self.mt = int(mt)
        except (ValueError, TypeError):
            self.nt = ''
        else:
            if self.mt < 2 or self.mt > 4:
                raise ValueError('Parameter mt should be in range 2 - 4.')
        self.mt = '' if mt == '' else int(mt)
        self.nb = nb
        if encoded:
            if self.mt == 2:
                self.xmsg = xmsg
            elif self.mt == 3:
                self.xmsg = xmsg.decode('irahex')
            elif self.mt == 4:
                self.xmsg = xmsg.decode('hex')
            elif self.mt == '':
                self.xmsg = ''
        else:
            self.xmsg = xmsg
        self.mms = mms
        self.pr = pr
        self.dcs = dcs
        self.mcls = mcls
        self.rpi = rpi
        self.cpg = cpg
        self.rply = rply
        self.otoa = otoa
        self.hplmn = hplmn
        self.xser = xser

    def __str__(self):
        oadc = self.oadc.encode('bits7') if self.otoa == '5039' else self.oadc
        if self.mt == 2:
            msg = self.xmsg
        elif self.mt == 3:
            msg = self.xmsg.encode('irahex')
        else:
            msg = self.xmsg.encode('hex').upper()
        ln = self.data_len(
            self.adc, oadc, self.ac, self.nrq, self.nadc, self.nt,
            self.npid, self.lrq, self.lrad, self.lpid, self.dd, self.ddt,
            self.vp, self.rpid, self.scts, self.dst, self.rsn,
            self.dscts, self.mt, self.nb, msg, self.mms, self.pr,
            self.dcs, self.mcls, self.rpi, self.cpg, self.rply,
            self.otoa, self.hplmn, self.xser, '',
            '')
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/' \
               '{}///'.format(
                   self.trn, ln, O, self.ot,
                   self.adc, oadc, self.ac, self.nrq, self.nadc, self.nt,
                   self.npid, self.lrq, self.lrad, self.lpid, self.dd, self.ddt,
                   self.vp, self.rpid, self.scts, self.dst, self.rsn,
                   self.dscts, self.mt, self.nb, msg, self.mms, self.pr,
                   self.dcs, self.mcls, self.rpi, self.cpg, self.rply,
                   self.otoa, self.hplmn, self.xser)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, O)
        return cls(ot, trn, *msg[:-2])


class Request6x(Message):
    def __init__(self, ot, trn=None, oadc='', oton='', onpi='', styp='', pwd='',
                 npwd='', vers='', ladc='', lton='', lnpi='', opid='',
                 encoded=True):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.oadc = oadc
        self.oton = oton  # 1 2 6 ''
        self.onpi = onpi  # 1 3 5 ''
        self.styp = styp  # 1 2 3 4 5 6
        if encoded:
            self.pwd = pwd.decode('irahex')
            self.npwd = npwd.decode('irahex')
            self.vers = int(vers, 2)
        else:
            self.pwd = pwd
            self.npwd = npwd
            self.vers = int(vers)
        self.ladc = ladc
        self.lton = lton  # 1 2 ''
        self.lnpi = lnpi  # 1 3 5 ''
        self.opid = opid  # 00 39 ''

    def __str__(self):
        pwd = self.pwd.encode('irahex')
        npwd = self.npwd.encode('irahex')
        vers = '{:0>4b}'.format(self.vers)
        ln = self.data_len(
            self.oadc, self.oton, self.onpi, self.styp, pwd, npwd,
            vers, self.ladc, self.lton, self.lnpi, self.opid, '')
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/' \
               '{}//'.format(
                   self.trn, ln, O, self.ot,
                   self.oadc, self.oton, self.onpi, self.styp, pwd, npwd,
                   vers, self.ladc, self.lton, self.lnpi, self.opid)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, O)
        return cls(ot, trn, *msg[:-1])


class DataTransport(object):
    def __init__(self, host, port, timeout=3):
        self.conn = self._Connection(host, port, timeout)
        self.incoming = Queue.Queue()
        self.outgoing = Queue.Queue()
        self.flag = threading.Event()
        self.sender = self.Worker(self.conn, self.outgoing, self.flag, True)
        self.receiver = self.Worker(self.conn, self.incoming, self.flag, False)
        self.receiver.start()
        self.sender.start()

    def send(self, msg):
        self.outgoing.put(str(msg))

    def receive(self):
        try:
            return self.incoming.get_nowait()
        except Queue.Empty:
            return None

    def quit(self):
        self.flag.set()
        self.conn.disconnect()
        self.sender.join()
        self.receiver.join()

    class Worker(threading.Thread):
        def __init__(self, conn, queue, flag, out):
            threading.Thread.__init__(self)
            self.conn = conn
            self.queue = queue
            self.flag = flag
            self.run = self.send if out else self.receive

        def send(self):
            while not self.flag.is_set():
                try:
                    msg = self.queue.get(timeout=1)
                except Queue.Empty:
                    pass
                else:
                    send = self.conn.send(msg)
                    if not send:
                        self.queue.put(msg)

        def receive(self):
            buff = ''
            while not self.flag.is_set():
                msg = self.conn.receive()
                if msg is not None:
                    buff += msg
                    sid = 0
                    try:
                        while True:
                            eid = buff.index(ETX, sid) + 1
                            self.queue.put(buff[sid:eid])
                            sid = eid
                    except ValueError:
                        buff = buff[sid:]

    class _Connection:
        def __init__(self, host, port, timeout):
            self.server_address = host, port
            self.timeout = timeout
            self._reconnect()

        def _reconnect(self):
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(self.server_address)
            self.socket.settimeout(self.timeout)

        def send(self, msg):
            try:
                nob = self.socket.sendall(msg)
            except socket.error:
                self._reconnect()
                return False
            if nob is None:
                return True
            self._reconnect()
            return False

        def receive(self):
            try:
                msg = self.socket.recv(4096)
            except socket.timeout:
                return None
            except socket.error:
                self._reconnect()
                return None
            if not msg:
                self._reconnect()
                return None
            return msg

        def disconnect(self):
            self.socket.close()


def send_message(sender, to, message, notification=False):
    params = {'ot': 51, 'mt': 3, 'adc': to, 'xmsg': message, 'encoded': False}
    if notification:
        params.update({'nrq': 1, 'nt': 1})
    if not sender.isdigit():
        params.update({'otoa': '5039', 'oadc': sender})
    return Request5x(**params)


_mapper = {
    1: Request01,
    2: Request02,
    3: Request03,
    30: Request30,
    31: Request31,
    50: Request5x,
    51: Request5x,
    52: Request5x,
    53: Request5x,
    54: Request5x,
    55: Request5x,
    56: Request5x,
    57: Request5x,
    58: Request5x,
    59: Request5x,
    60: Request6x,
    61: Request6x
}


def dispatcher(msg):
    if msg[10] == 'R':
        return Response.from_string(msg)
    return _mapper[int(msg[12:14])].from_string(msg)
