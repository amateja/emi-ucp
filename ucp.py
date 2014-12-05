###############################################################################
#
# UCP version - 1.0
#
###############################################################################

import socket
import signal


class DataTransport:
    def __init__(self, args=None):
        self.ucpinfo = {
            'smsc_host': None,
            'smsc_port': None,
            'timeout': None,
        }

        if args is not None:
            self.ucpinfo.update(args)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            raise RuntimeError("DataTransport: smsc host, smsc port")

    def connect(self):
        """ return None on error """
        try:
            self.sock.connect((self.ucpinfo["smsc_host"], self.ucpinfo["smsc_port"]))
        except:
            return None
        return 1

    def disconnect(self):
        """ return None on error """
        try:
            self.sock.close()
        except:
            return None
        return 1

    def send(self, ucpkt=None):
        if ucpkt is not None:
            totalsent = 0

            while totalsent < len(ucpkt):
                try:
                    sent = self.sock.send(ucpkt[totalsent:])
                except:
                    raise IOError("Unable to send...")
                if sent == 0:
                    raise RuntimeError("transmit: connection broken!")
                totalsent = totalsent + sent

    def thandler(self, signal, frame):
        raise IOError("\n[*] Timeout reached! signal %s\n" % signal)

    def read(self):
        etx = chr(3)
        max_len = 2048

        chunk = ''
        remote_msg = ''
        timeout = 10  # 10 seconds

        if self.ucpinfo["timeout"] is not None:
            timeout = self.ucpinfo["timeout"]

        signal.signal(signal.SIGALRM, self.thandler)
        signal.alarm(timeout)

        while chunk != etx:
            chunk = self.sock.recv(1)
            if chunk == '':
                signal.alarm(0)
                raise RuntimeError("read: connection broken!")

            remote_msg = remote_msg + chunk
            if len(remote_msg) >= max_len:
                signal.alarm(0)
                raise RuntimeError("read: ucp message too long")

        signal.alarm(0)
        return remote_msg


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
