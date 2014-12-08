###############################################################################
#
# UCP version - 1.0
#
###############################################################################

import threading
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
    def encode_7bit(text):
        return text.encode('utf_7').encode('hex').upper()

    @staticmethod
    def decode_7bit(text):
        return text.decode('hex').decode('utf_7')

    @staticmethod
    def ia5_decode(text):
        return text.decode('hex')

    @staticmethod
    def ia5_encode(text):
        return text.encode('hex').upper()

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
    def __init__(self, ot, trn=None, adc='', oadc='', ac='', mt='', xmsg=''):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.adc = adc
        self.oadc = oadc
        self.ac = ac
        self.mt = int(mt)
        self.xmsg = self.ia5_decode(xmsg) if self.mt == 3 else xmsg

    def __str__(self):
        msg = self.ia5_encode(self.xmsg) if self.mt == 3 else self.xmsg
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
    def __init__(self, ot, trn=None, npl='', rads='', oadc='', ac='', mt='',
                 xmsg=''):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.npl = int(npl)
        self.rads = rads
        self.oadc = oadc
        self.ac = ac
        self.mt = int(mt)
        self.xmsg = self.ia5_decode(xmsg) if self.mt == 3 else xmsg

    def __str__(self):
        msg = self.ia5_encode(self.xmsg) if self.mt == 3 else self.xmsg
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
    def __init__(self, ot, trn=None, rad='', oadc='', ac='', dd='', ddt='',
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
        self.xmsg = self.ia5_decode(xmsg) if self.mt == 3 else xmsg

    def __str__(self):
        msg = self.ia5_encode(self.xmsg) if self.mt == 3 else self.xmsg
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
    def __init__(self, ot, trn=None, adc='', oadc='', ac='', nrq='', nad='',
                 npid='', dd='', ddt='', vp='', amsg=''):
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
        self.amsg = self.ia5_decode(amsg)

    def __str__(self):
        msg = self.ia5_encode(self.amsg)
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
    def __init__(self, ot, trn=None, adc='', pid=''):
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
    def __init__(self, ot, trn=None, adc='', oadc='', ac='', nrq='', nadc='',
                 nt='', npid='', lrq='', lrad='', lpid='', dd='', ddt='', vp='',
                 rpid='', scts='', dst='', rsn='', dscts='', mt='', nb='',
                 xmsg='', mms='', pr='', dcs='', mcls='', rpi='', cpg='',
                 rply='', otoa='', hplmn='', xser=''):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.adc = adc
        self.oadc = self.decode_7bit(oadc) if otoa == '5039' else oadc
        self.ac = ac
        self.nrg = nrq
        self.nadc = nadc
        self.nt = nt
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
        self.mt = '' if mt == '' else int(mt)
        self.nb = nb
        self.xmsg = xmsg if self.mt == 2 else self.ia5_decode(xmsg)
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
        msg = self.xmsg if self.mt == 2 else self.ia5_encode(self.xmsg)
        ln = self.data_len(
            self.adc, self.oadc, self.ac, self.nrg, self.nadc, self.nt,
            self.npid, self.lrq, self.lrad, self.lpid, self.dd, self.ddt,
            self.vp, self.rpid, self.scts, self.dst, self.rsn, self.dscts,
            self.mt, self.nb, msg, self.mms, self.pr, self.dcs, self.mcls,
            self.rpi, self.cpg, self.rply, self.otoa, self.hplmn, self.xser, '',
            '')
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/' \
               '{}///'.format(
                   self.trn, ln, O, self.ot,
                   self.adc, self.oadc, self.ac, self.nrg, self.nadc, self.nt,
                   self.npid, self.lrq, self.lrad, self.lpid, self.dd, self.ddt,
                   self.vp, self.rpid, self.scts, self.dst, self.rsn, self.dscts,
                   self.mt, self.nb, msg, self.mms, self.pr, self.dcs, self.mcls,
                   self.rpi, self.cpg, self.rply, self.otoa, self.hplmn, self.xser)
        return STX + text + '{:0>2X}'.format(self.checksum(text)) + ETX

    @classmethod
    def from_string(cls, msg):
        msg, trn, ot = cls.unpack(msg, O)
        return cls(ot, trn, *msg[:-2])


class Request6x(Message):
    def __init__(self, ot, trn=None, oadc='', oton='', onpi='', styp='', pwd='',
                 npwd='', vers='', ladc='', lton='', lnpi='', opid=''):
        Message.__init__(self)
        self.trn = self.TRN.next() if trn is None else int(trn)
        self.ot = int(ot)
        self.oadc = oadc
        self.oton = oton  # 1 2 6 ''
        self.onpi = onpi  # 1 3 5 ''
        self.styp = styp  # 1 2 3 4 5 6
        self.pwd = self.ia5_decode(pwd)
        self.npwd = self.ia5_decode(npwd)
        self.vers = vers  # 0100
        self.ladc = ladc
        self.lton = lton  # 1 2 ''
        self.lnpi = lnpi  # 1 3 5 ''
        self.opid = opid  # 00 39 ''

    def __str__(self):
        pwd = self.ia5_encode(self.pwd)
        npwd = self.ia5_encode(self.npwd)
        ln = self.data_len(
            self.oadc, self.oton, self.onpi, self.styp, pwd, npwd,
            self.vers, self.ladc, self.lton, self.lnpi, self.opid, '')
        text = '{:0>2d}/{:0>5d}/{}/{:0>2d}/' \
               '{}/{}/{}/{}/{}/{}/{}/{}/{}/{}/' \
               '{}//'.format(
                   self.trn, ln, O, self.ot,
                   self.oadc, self.oton, self.onpi, self.styp, pwd, npwd,
                   self.vers, self.ladc, self.lton, self.lnpi, self.opid)
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
        self.receiver = self.Worker(self.conn, self.incoming, self.flag, True)
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
                try:
                    msg = self.conn.receive()
                except socket.timeout:
                    pass
                else:
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
            try:
                self.socket.settimeout(self.timeout)
            except:
                pass

        def send(self, msg):
            try:
                nob = self.socket.sendall(msg)
            except socket.error:
                self._reconnect()
                return False
            if not nob:
                self._reconnect()
                return False
            return True

        def receive(self):
            try:
                msg = self.socket.recv(4096)
            except socket.error:
                self._reconnect()
                return None
            if not msg:
                self._reconnect()
                return None
            return msg

        def disconnect(self):
            self.socket.close()


class UCP:
    def __init__(self, args=None):
        """ Accept smsc_host and smsc_port """
        self.__set_common_value()
        self.trn_number = 0

        if args is not None:
            self.socket = DataTransport(args)

    def make_message(self, ucpfields=None):
        if 'op' in ucpfields:
            return self.dispatch_make(ucpfields["op"], ucpfields)
        else:
            print "No operation defined"

    def dispatch_make(self, r_op, r_ucpfields):
        try:
            return getattr(self, 'make_' + str(r_op))(**r_ucpfields)
        except:
            print "Operation %s not supported" % r_op
            return None

    def make_01(self, fields=None):

        oper = "01"

        message_string = None
        text = ''
        header = ''
        string = ''

        if fields is not None and 'operation' in fields and fields["operation"] == "1":

            if 'nmsg' in fields and 'amsg' not in fields:
                text = fields["nmsg"]
            elif 'amsg' in fields:
                text = self.ia5_encode(fields["amsg"])

            if 'adc' in fields:
                string += fields["adc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'oadc' in fields:
                string += fields["oadc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if "ac" in fields:
                string += fields["ac"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'mt' in fields:
                string += fields["mt"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            string += text

            trn = str(self.next_trn()).zfill(2)
            dlen = self.data_len(string)

            header = trn + self.ucpdelimiter + dlen + self.ucpdelimiter
            header += "O" + self.ucpdelimiter + oper

            message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
            message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        elif fields is not None and 'result' in fields and fields["result"] == "1":

            if 'ack' in fields:

                string = fields["ack"] + self.ucpdelimiter
                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

                header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
                header += "R" + self.ucpdelimiter + oper

                message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
                message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

            elif 'nack' in fields:
                string = fields["nack"] + self.ucpdelimiter
                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

                header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
                header += "R" + self.ucpdelimiter + oper

                message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
                message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        return message_string

    def _make_01(self, operation='', nmsg=None, amsg=None, adc='', oadc='',
                 ac='', mt='', result='', ack='', sm='', trn='', nack=''):
        oper = '01'
        message = None
        if operation == '1':
            text = '/'.join([adc, oadc, ac, mt, nmsg or self.ia5_encode(amsg)])
            message = '/'.join([str(self.next_trn()).zfill(2),
                                self.data_len(text), 'O', oper, text, ''])
        if result == '1':
            text = '/'.join([ack or nack, sm])
            message = '/'.join([trn.zfill(2), self.data_len(text), 'R', oper,
                                text, ''])
        return message + self.checksum(message)

    def make_02(self, fields=None):

        oper = "02"

        message_string = None
        text = ''
        header = ''
        string = ''

        if fields is not None and 'operation' in fields and fields["operation"] == "1":

            if 'nmsg' in fields and 'amsg' not in fields:
                text = fields["nmsg"]
            elif 'amsg' in fields:
                text = self.ia5_encode(fields["amsg"])

            if 'npl' in fields:
                string += fields["npl"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'rads' in fields:
                string += fields["rads"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'oadc' in fields:
                string += fields["oadc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'ac' in fields:
                string += fields["ac"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'mt' in fields:
                string += fields["mt"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            string += text

            trn = str(self.next_trn()).zfill(2)
            dlen = self.data_len(string)

            header = trn + self.ucpdelimiter + dlen + self.ucpdelimiter
            header += "O" + self.ucpdelimiter + oper

            message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
            message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        elif fields is not None and 'result' in fields and fields["result"] == "1":

            if 'ack' in fields:

                string = fields["ack"] + self.ucpdelimiter
                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

                header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
                header += "R" + self.ucpdelimiter + oper

                message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
                message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

            elif 'nack' in fields:

                string = fields["nack"] + self.ucpdelimiter
                if 'ec' in fields:
                    string += fields["ec"]
                else:
                    string += '' + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

                header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
                header += "R" + self.ucpdelimiter + oper

                message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
                message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        return message_string

    def _make_02(self, operation='', nmsg=None, amsg=None, npl='', rads='',
                 oadc='', ac='', mt='', result='', ack='', sm='', trn='',
                 nack='', ec=''):
        oper = '02'
        message = None
        if operation == '1':
            text = '/'.join([npl, rads, oadc, ac, mt, nmsg or
                             self.ia5_encode(amsg)])
            message = '/'.join([str(self.next_trn()).zfill(2),
                                self.data_len(text), 'O', oper, text, ''])
        if result == '1':
            text = '/'.join([ack, sm] if ack else [nack, ec, sm])
            message = '/'.join([trn.zfill(2), self.data_len(text), 'R', oper,
                                text, ''])
        return message + self.checksum(message)

    def make_03(self, fields=None):

        oper = "03"

        message_string = None
        text = ''
        header = ''
        string = ''

        if fields is not None and 'operation' in fields and fields["operation"] == "1":

            if 'nmsg' in fields and not 'amsg' in fields:
                text = fields["nmsg"]
            elif 'amsg' in fields:
                text = self.ia5_encode(fields["amsg"])

            if 'rad' in fields:
                string += fields["rad"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'oadc' in fields:
                string += fields["oadc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'ac' in fields:
                string += fields["ac"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'npl' in fields:
                string += fields["npl"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'gas' in fields:
                string += fields["gas"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'rp' in fields:
                string += fields["rp"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'pr' in fields:
                string += fields["pr"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'lpr' in fields:
                string += fields["lpr"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'ur' in fields:
                string += fields["ur"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'lur' in fields:
                string += fields["lur"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'rc' in fields:
                string += fields["rc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'lrc' in fields:
                string += fields["lrc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'dd' in fields:
                string += fields["dd"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'ddt' in fields:
                string += fields["ddt"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'mt' in fields:
                string += fields["mt"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            string += text

            trn = str(self.next_trn()).zfill(2)
            dlen = self.data_len(string)

            header = trn + self.ucpdelimiter + dlen + self.ucpdelimiter
            header += "O" + self.ucpdelimiter + oper

            message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
            message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        elif fields is not None and 'result' in fields and fields["result"] == "1":

            if 'ack' in fields:
                string = fields["ack"] + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

                header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
                header += "R" + self.ucpdelimiter + oper

                message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
                message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

            elif 'nack' in fields:

                string = fields["nack"] + self.ucpdelimiter
                if 'ec' in fields:
                    string += fields["ec"]
                else:
                    string += '' + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

                header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
                header += "R" + self.ucpdelimiter + oper

                message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
                message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        return message_string

    def _make_03(self, operation='', nmsg=None, amsg=None, rad='', oadc='',
                 ac='', npl='', gas='', rp='', pr='', lpr='', ur='', lur='',
                 rc='', lrc='', dd='', ddt='', mt='', result='', ack='', sm='',
                 trn='', nack='', ec=''):
        oper = '02'
        message = None
        if operation == '1':
            text = '/'.join([rad, oadc, ac, npl, gas, rp, pr, lpr, ur, lur, rc,
                             lrc, dd, ddt, mt, nmsg or self.ia5_encode(amsg)])
            message = '/'.join([str(self.next_trn()).zfill(2),
                                self.data_len(text), 'O', oper, text, ''])
        if result == '1':
            text = '/'.join([ack, sm] if ack else [nack, ec, sm])
            message = '/'.join([trn.zfill(2), self.data_len(text), 'R', oper,
                                text, ''])
        return message + self.checksum(message)

    def make_30(self, fields=None):

        oper = "30"

        message_string = ''
        text = ''
        header = ''
        string = ''

        if fields is not None and 'operation' in fields and fields["operation"] == "1":

            if 'amsg' in fields:
                text = self.ia5_encode(fields["amsg"])

            if 'adc' in fields:
                string += fields["adc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'oadc' in fields:
                string += fields["oadc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'ac' in fields:
                string += fields["ac"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'nrq' in fields:
                string += fields["nrq"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'nad' in fields:
                string += fields["nad"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'npid' in fields:
                string += fields["npid"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'dd' in fields:
                string += fields["dd"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'ddt' in fields:
                string += fields["ddt"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'vp' in fields:
                string += fields["vp"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            string += text

            trn = str(self.next_trn()).zfill(2)
            dlen = self.data_len(string)

            header = trn + self.ucpdelimiter + dlen + self.ucpdelimiter
            header += "O" + self.ucpdelimiter + oper

        elif fields is not None and 'result' in fields and fields["result"] == "1":

            if 'ack' in fields:
                string = fields["ack"] + self.ucpdelimiter

                if 'mvp' in fields:
                    string += fields["mvp"] + self.ucpdelimiter
                else:
                    string += '' + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

                dlen = self.data_len(string)

                header = fields["trn"].zfill(2) + self.ucpdelimiter + dlen + self.ucpdelimiter
                header += "R" + self.ucpdelimiter + oper

            elif 'nack' in fields:

                string = fields["nack"] + self.ucpdelimiter
                if 'ec' in fields:
                    string += fields["ec"]
                else:
                    string += '' + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

                header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
                header += "R" + self.ucpdelimiter + oper

            else:
                return message_string

        else:
            return message_string

        message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
        message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        return message_string

    def _make_30(self, operation='', amsg=None, adc='', oadc='', ac='', nrq='',
                 nad='', npid='', dd='', ddt='', vp='', result='', ack='',
                 mvp='', sm='', trn='', nack='', ec=''):
        oper = '30'
        message = None
        if operation == '1':
            text = '/'.join([adc, oadc, ac, nrq, nad, npid, dd, ddt, vp,
                             self.ia5_encode(amsg)])
            message = '/'.join([str(self.next_trn()).zfill(2),
                                self.data_len(text), 'O', oper, text, ''])
        if result == '1':
            text = '/'.join([ack, mvp, sm] if ack else [nack, ec, sm])
            message = '/'.join([trn.zfill(2), self.data_len(text), 'R', oper,
                                text, ''])
        return message + self.checksum(message)

    def make_31(self, fields=None):

        oper = "31"

        message_string = ''
        text = ''
        header = ''
        string = ''

        if fields is not None and 'operation' in fields and fields["operation"] == "1":

            if 'adc' in fields:
                string += fields["adc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'pid' in fields:
                string += fields["pid"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            trn = str(self.next_trn()).zfill(2)
            dlen = self.data_len(string)

            header = trn + self.ucpdelimiter + dlen + self.ucpdelimiter
            header += "O" + self.ucpdelimiter + oper

        elif fields is not None and 'result' in fields and fields["result"] == "1":

            if 'ack' in fields:

                string += fields["ack"] + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

            elif 'nack' in fields:

                string += fields["nack"] + self.ucpdelimiter

                if 'ec' in fields:
                    string += fields["ec"] + self.ucpdelimiter
                else:
                    string += '' + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"] + self.ucpdelimiter
                else:
                    string += '' + self.ucpdelimiter
            else:
                return message_string

            header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
            header += "R" + self.ucpdelimiter + oper

        else:
            return message_string

        message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
        message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        return message_string

    def _make_31(self, operation='', adc='', pid='', result='', ack='', sm='',
                 trn='', nack='', ec=''):
        oper = '31'
        message = None
        if operation == '1':
            text = '/'.join([adc, pid])
            message = '/'.join([str(self.next_trn()).zfill(2),
                                self.data_len(text), 'O', oper, text, ''])
        if result == '1':
            text = '/'.join([ack, sm] if ack else [nack, ec, sm])
            message = '/'.join([trn.zfill(2), self.data_len(text), 'R', oper,
                                text, ''])
        return message + self.checksum(message)

    def make_5x(self, fields=None):

        oper = fields["op"]

        message_string = ''
        subscr = ''
        text = ''
        header = ''
        string = ''

        if fields is not None and 'operation' in fields and fields["operation"] == "1":

            if 'amsg' in fields:
                text = self.ia5_encode(fields["amsg"])
            elif 'nmsg' in fields:
                text = fields["nmsg"]
            elif 'tmsg' in fields:
                text = fields["tmsg"]
            else:
                text = ''

            if 'otoa' in fields:
                if fields["otoa"] == "5039":
                    subscr = self.encode_7bit(fields["oadc"])
                else:
                    subscr = fields["otoa"]

            if 'adc' in fields:
                string += fields["adc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            string += subscr + self.ucpdelimiter

            if 'ac' in fields:
                string += fields["ac"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'nrq' in fields:
                string += fields["nrq"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'nadc' in fields:
                string += fields["nadc"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'nt' in fields:
                string += fields["nt"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'npid' in fields:
                string += fields["npid"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'lrq' in fields:
                string += fields["lrq"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'lrad' in fields:
                string += fields["lrad"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'lpid' in fields:
                string += fields["lpid"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'dd' in fields:
                string += fields["ddt"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'vp' in fields:
                string += fields["vp"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'rpid' in fields:
                string += fields["rpid"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'scts' in fields:
                string += fields["scts"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'dst' in fields:
                string += fields["dst"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'rsn' in fields:
                string += fields["rsn"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'dscts' in fields:
                string += fields["dscts"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'mt' in fields:
                string += fields["mt"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'nb' in fields:
                string += fields["nb"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            string += text + self.ucpdelimiter

            if 'mms' in fields:
                string += fields["mms"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'pr' in fields:
                string += fields["pr"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'dcs' in fields:
                string += fields["dcs"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'mcls' in fields:
                string += fields["mcls"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'rpi' in fields:
                string += fields["rpi"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'cpg' in fields:
                string += fields["cpg"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'rply' in fields:
                string += fields["rply"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'otoa' in fields:
                string += fields["otoa"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'hplmn' in fields:
                string += fields["hplmn"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'xser' in fields:
                string += fields["xser"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'res4' in fields:
                string += fields["res4"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            if 'res5' in fields:
                string += fields["res5"] + self.ucpdelimiter
            else:
                string += '' + self.ucpdelimiter

            trn = str(self.next_trn()).zfill(2)
            dlen = self.data_len(string)

            header = trn + self.ucpdelimiter + dlen + self.ucpdelimiter
            header += "O" + self.ucpdelimiter + oper

            message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
            message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        elif fields is not None and 'result' in fields and fields["result"] == "1":

            if 'ack' in fields:

                string += fields["ack"] + self.ucpdelimiter

                if 'mvp' in fields:
                    string += fields["mvp"] + self.ucpdelimiter
                else:
                    string += '' + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"]
                else:
                    string += ''

            elif 'nack' in fields:

                string += fields["nack"] + self.ucpdelimiter

                if 'ec' in fields:
                    string += fields["ec"] + self.ucpdelimiter
                else:
                    string += '' + self.ucpdelimiter

                if 'sm' in fields:
                    string += fields["sm"] + self.ucpdelimiter
                else:
                    string += '' + self.ucpdelimiter
            else:
                return message_string

            header = fields["trn"].zfill(2) + self.ucpdelimiter + self.data_len(string) + self.ucpdelimiter
            header += "R" + self.ucpdelimiter + oper

            message_string = header + self.ucpdelimiter + string + self.ucpdelimiter
            message_string += self.checksum(header + self.ucpdelimiter + string + self.ucpdelimiter)

        return message_string

    def _make_5x(self, op, operation='', nmsg=None, amsg=None, tmsg=None,
                 otoa='', oadc='', adc='', ac='', nrq='', nadc='', nt='',
                 npid='', lrq='', lrad='', lpid='', dd='', vp='', rpid='',
                 scts='', dst='', rsn='', dscts='', mt='', nb='', mms='', pr='',
                 dcs='', mcls='', rpi='', cpg='', rply='', hplmn='', xser='',
                 res4='', res5='', result='', ack='', mvp='', sm='', trn='',
                 nack='', ec=''):
        oper = op
        message = None
        if operation == '1':
            text = '/'.join([adc,
                             self.encode_7bit(oadc) if otoa == '5039' else otoa,
                             ac, nrq, nadc, nt, npid, lrq, lrad, lpid, dd, vp,
                             rpid, scts, dst, rsn, dscts, mt, nb,
                             self.ia5_encode(amsg) or nmsg or tmsg, mms, pr,
                             dcs, mcls, rpi, cpg, rply, otoa, hplmn, xser, res4,
                             res5])
            message = '/'.join([str(self.next_trn()).zfill(2),
                                self.data_len(text), 'O', oper, text, ''])
        if result == '1':
            text = '/'.join([ack, mvp, sm] if ack else [nack, ec, sm])
            message = '/'.join([trn.zfill(2), self.data_len(text), 'R', oper,
                                text, ''])
        return message + self.checksum(message)

    make_51 = make_52 = make_53 = make_54 = make_55 = make_56 = make_57 = \
        make_58 = make_5x

    def parse_01(self, message=None):
        mess = {}

        if message is not None:
            params = message.split(self.ucpdelimiter)

            mess["trn"] = params[0]
            mess["len"] = params[1]
            mess["type"] = params[2]
            mess["ot"] = params[3]

            if mess["type"] == "O":
                mess["adc"] = params[4]
                mess["oadc"] = params[5]
                mess["ac"] = params[6]
                mess["mt"] = params[7]

                if mess["mt"] == 2:
                    mess["nmsg"] = params[8]
                    mess["amsg"] = ''
                elif mess["mt"] == 3:
                    mess["amsg"] = self.ia5_decode(params[8])
                    mess["nmsg"] = ''
                else:
                    mess["nmsg"] = ''
                    mess["amsg"] = ''

            else:
                if params[4] == self.ack:
                    mess["ack"] = params[4]
                    mess["sm"] = params[5]
                    mess["checksum"] = params[6]
                else:
                    mess["nack"] = params[4]
                    mess["ec"] = params[5]
                    mess["sm"] = params[6]
                    mess["checksum"] = params[7]
        else:
            mess = message

        return mess

    def parse_02(self, message=None):
        mess = {}

        if message is not None:
            params = message.split(self.ucpdelimiter)

            mess["trn"] = params[0]
            mess["len"] = params[1]
            mess["type"] = params[2]
            mess["ot"] = params[3]

            if mess["type"] == "O":
                mess["npl"] = params[4]
                mess["rads"] = params[5]
                mess["oadc"] = params[6]
                mess["ac"] = params[7]
                mess["mt"] = params[8]

                if mess["mt"] == 2:
                    mess["nmsg"] = params[9]
                    mess["ams"] = ''
                elif mess["mt"] == 3:
                    mess["amsg"] = self.ia5_decode(params[9])
                    mess["nmsg"] = ''
                else:
                    mess["amsg"] = ''
                    mess["nmsg"] = ''

                mess["checksum"] = params[10]

            else:
                if params[4] == self.ack:
                    mess["ack"] = params[4]
                    mess["sm"] = params[5]
                    mess["checksum"] = params[6]
                else:
                    mess["nack"] = params[4]
                    mess["ec"] = params[5]
                    mess["sm"] = params[6]
                    mess["checksum"] = params[7]
        else:
            mess = message

        return mess

    def parse_03(self, message=None):
        mess = {}

        if message is not None:
            params = message.split(self.ucpdelimiter)

            mess["trn"] = params[0]
            mess["len"] = params[1]
            mess["type"] = params[2]
            mess["ot"] = params[3]

            if mess["type"] == "O":
                mess["rad"] = params[4]
                mess["oadc"] = params[5]
                mess["ac"] = params[6]
                mess["npl"] = params[7]  # must be 0
                mess["gas"] = params[8]  # empty if npl 0
                mess["rp"] = params[9]
                mess["pr"] = params[10]
                mess["lpr"] = params[11]
                mess["ur"] = params[12]
                mess["lur"] = params[13]
                mess["rc"] = params[14]
                mess["lrc"] = params[15]
                mess["dd"] = params[16]
                mess["ddt"] = params[17]
                mess["mt"] = params[18]

                if mess["mt"] == 2:
                    mess["nmsg"] = params[19]
                    mess["ams"] = ''
                elif mess["mt"] == 3:
                    mess["amsg"] = self.ia5_decode(params[19])
                    mess["nmsg"] = ''
                else:
                    mess["amsg"] = ''
                    mess["nmsg"] = ''

                mess["checksum"] = params[20]
            else:
                if params[4] == self.ack:
                    mess["ack"] = params[4]
                    mess["sm"] = params[5]
                    mess["checksum"] = params[6]
                else:
                    mess["nack"] = params[4]
                    mess["ec"] = params[5]
                    mess["sm"] = params[6]
                    mess["checksum"] = params[7]
        else:
            mess = message

        return mess

    def parse_30(self, message=None):
        mess = {}

        if message is not None:
            params = message.split(self.ucpdelimiter)

            mess["trn"] = params[0]
            mess["len"] = params[1]
            mess["type"] = params[2]
            mess["ot"] = params[3]

            if mess["type"] == "O":
                mess["adc"] = params[4]
                mess["oadc"] = params[5]
                mess["ac"] = params[6]
                mess["nrq"] = params[7]
                mess["nad"] = params[8]
                mess["npid"] = params[9]
                mess["dd"] = params[10]
                mess["ddt"] = params[11]
                mess["vp"] = params[12]
                mess['amsg'] = self.ia5_decode(params[13])
                mess["checksum"] = params[14]
            else:
                if params[4] == self.ack:
                    mess["ack"] = params[4]
                    mess["sm"] = params[5]
                    mess["checksum"] = params[6]
                else:
                    mess["nack"] = params[4]
                    mess["ec"] = params[5]
                    mess["sm"] = params[6]
                    mess["checksum"] = params[7]
        else:
            mess = message

        return mess

    def parse_31(self, message=None):
        mess = {}

        if message is not None:
            params = message.split(self.ucpdelimiter)

            mess["trn"] = params[0]
            mess["len"] = params[1]
            mess["type"] = params[2]
            mess["ot"] = params[3]

            if mess["type"] == "O":
                mess["adc"] = params[4]
                mess["pid"] = params[5]
                mess["checksum"] = params[6]
            else:
                if params[4] == self.ack:
                    mess["ack"] = params[4]
                    mess["sm"] = params[5]
                    mess["checksum"] = params[6]
                else:
                    mess["nack"] = params[4]
                    mess["ec"] = params[5]
                    mess["sm"] = params[6]
                    mess["checksum"] = params[7]
        else:
            mess = message

        return mess

    def _parse_5x(self, message=None):
        mess = {}

        if message is not None:
            params = message.split(self.ucpdelimiter)

            mess["trn"] = params[0]
            mess["len"] = params[1]
            mess["type"] = params[2]
            mess["ot"] = params[3]

            if mess["type"] == "O":
                mess["adc"] = params[4]
                mess["otoa"] = params[32]

                if mess["otoa"] == "5039":
                    mess["oadc"] = self.decode_7bit(params[5])
                else:
                    mess["oadc"] = params[5]

                mess["ac2"] = params[6]
                mess["nrq"] = params[7]
                mess["nadc"] = params[8]
                mess["nt"] = params[9]
                mess["npid"] = params[10]
                mess["lrq"] = params[11]
                mess["lrad"] = params[12]
                mess["lpid"] = params[13]
                mess["dd"] = params[14]
                mess["ddt"] = params[15]
                mess["vp"] = params[16]
                mess["rpid"] = params[17]
                mess["scts"] = params[18]
                mess["dst"] = params[19]
                mess["rsn"] = params[20]
                mess["dscts"] = params[21]
                mess["mt"] = params[22]
                mess["nb"] = params[23]

                if mess["mt"] == 2:
                    mess["nmsg"] = params[24]

                if mess["mt"] == 3:
                    mess["amsg"] = self.ia5_decode(params[24])

                if mess["mt"] == 4:
                    mess["tmsg"] = params[24]

                mess["mms"] = params[25]
                mess["pr"] = params[26]
                mess["dcs"] = params[27]
                mess["mcls"] = params[28]
                mess["rpi"] = params[29]
                mess["cpg"] = params[30]
                mess["rply"] = params[31]
                mess["hplmn"] = params[33]
                mess["xser"] = params[34]
                mess["res4"] = params[35]
                mess["res5"] = params[36]
                mess["checksum"] = params[37]
            else:
                if params[4] == self.ack:
                    mess["ack"] = params[4]
                    mess["sm"] = params[5]
                    mess["checksum"] = params[6]
                else:
                    mess["nack"] = params[4]
                    mess["ec"] = params[5]
                    mess["sm"] = params[6]
                    mess["checksum"] = params[7]
        else:
            mess = message

        return mess

    parse_51 = parse_52 = parse_53 = parse_54 = parse_55 = parse_56 = \
        parse_57 = parse_58 = _parse_5x

    @staticmethod
    def pack(msg=None):
        """add stx and etx to ucp message"""
        return chr(2) + msg + chr(3) if msg else None

    @staticmethod
    def unpack(msg=None):
        """remove stx and etx from ucp message"""
        return msg.lstrip(chr(2)).rstrip(chr(3)) if msg else None

    def __set_common_value(self):
        self.ucpdelimiter = "/"
        self.ack = "A"
        self.nack = "N"

        self.accent_table = {
            '05': '0xe8',
            '04': '0xe9',
            '06': '0xf9',
            '07': '0xec',
            '08': '0xf2',
            '7F': '0xe0',
        }

    @staticmethod
    def ia5_decode(text=None):
        """IA5 string decoding returns empty string if text is None

        TODO :: accented characters ::

        p = re.compile("..")
        iter = p.iterator(text)

        for m in iter:
            oct = str(m.group())
            if m in self.accent_table:
                out += "%s" % chr(hex(self.accent_table(oct)))
            else:
                out += "%s" % chr(hex(oct))
        """
        return '' if text is None else text.decode('hex')

    @staticmethod
    def ia5_encode(text=None):
        """IA5 string encoding returns empty string if text is None"""
        return '' if text is None else text.encode('hex').upper()

    @staticmethod
    def checksum(text=None):
        return 0 if text is None else "%02X" % (sum(map(ord, text)) % 256)

    @staticmethod
    def data_len(text=None):
        return str(0 if text is None else len(text) + 17).zfill(5)

    def next_trn(self):
        if self.trn_number < 99:
            self.trn_number += 1
        else:
            self.trn_number = 0

        return self.trn_number

    @staticmethod
    def encode_7bit(text=None):
        return '00' if text is None else text.encode('utf_7').encode(
            'hex').upper()

    @staticmethod
    def decode_7bit(text=None):
        return '' if text is None else text.decode('hex').decode('utf_7')
