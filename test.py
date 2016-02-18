# -*- coding: utf-8 -*-
import unittest

from ucp import *


class TestMessage(unittest.TestCase):
    rsp = [
        '\x0206/00043/R/01/A/01234567890:090196103258/4E\x03',
        '\x0212/00022/R/01/N/02//03\x03',
        '\x0282/00059/R/02/A/0654321:090196113940,065432:090196113940/86\x03',
        '\x0247/00022/R/02/N/01//0B\x03',
        '\x0201/00038/R/03/A/066666:090296103355/4F\x03',
        '\x0201/00022/R/03/N/22//05\x03',
        '\x0210/00039/R/30/A//067345:070295121212/6F\x03',
        '\x0211/00022/R/30/N/24//08\x03',
        '\x0204/00023/R/31/A/0003/2D\x03',
        '\x0200/00022/R/31/N/06//07\x03',
        '\x0200/00039/R/51/A//012234:090996101010/68\x03',
        '\x0200/00022/R/51/N/31//07\x03',
        '\x0200/00039/R/52/A//076567:010196010101/6C\x03',
        '\x0200/00022/R/52/N/01//05\x03',
        '\x0200/00032/R/53/A//020296020202/F2\x03',
        '\x0200/00022/R/53/N/02//07\x03',
        '\x0200/00039/R/54/A//012345:020197120005/65\x03',
        '\x0200/00022/R/54/N/04//0A\x03',
        '\x0200/00032/R/55/A//030395030303/F8\x03',
        '\x0209/00022/R/55/N/02//12\x03',
        '\x0210/00032/R/56/A//040497161604/07\x03',
        '\x0200/00022/R/56/N/01//09\x03',
        '\x0200/00020/R/57/A///9A\x03',
        '\x0247/00022/R/57/N/02//16\x03',
        '\x0200/00029/R/58/A//064564565/7D\x03',
        '\x0200/00027/R/58/N/02/07567/1A\x03',
        '\x0200/00039/R/59/A//012234:090996101010/70\x03',
        '\x0200/00022/R/59/N/31//0F\x03',
        '\x0200/00019/R/60/A//6D\x03',
        '\x0200/00022/R/60/N/01//04\x03',
        '\x0200/00019/R/61/A//6E\x03',
        '\x0200/00022/R/61/N/02//06\x03',
    ]

    req01 = [
        '\x0200/00070/O/01/01234567890/09876543210//3/53686F7274204D65737361676'
        '5/D9\x03',
        '\x0200/00041/O/01/0888444///2/716436383334/C5\x03',
    ]

    req02 = [
        '\x0205/00059/O/02/3/01111/02222/03333/0123456789//3/534D5343/52\x03',
        '\x0217/00069/O/02/5/01111/02222/03333/04444/05555/0123456789//2/563444'
        '/44\x03',
    ]

    req03 = [
        '\x0215/00058/O/03/01234568/0756663/2435/0//////////3/434D47/1B\x03',
        '\x0222/00067/O/03/01234568/0756663//0////////1/0602961500/2/89123334/C'
        'F\x03',
    ]

    req30 = [
        '\x0256/00089/O/30/0123456/0568243//1/0296877842/0139////454D4920737065'
        '63696669636174696F6E/D4\x03',
        '\x0244/00077/O/30/0673845336//////1/1003961344/1203961200/4D6573736167'
        '65204F4B/27\x03',
    ]

    req31 = [
        '\x0202/00035/O/31/0234765439845/0139/A0\x03',
    ]

    req5x = [
        '\x0218/00113/O/51/012345/09876//1/1920870340125000/4/0539//////3012961'
        '212//////3//4D657373616765203531/////////////CD\x03',
        '\x0239/00099/O/51/0657467/078769//1//7//1/0545765/0122/1/0808971800///'
        '////4/32/F5AA34DE////1/////////65\x03',
        '\x0200/00120/O/52/076523578/07686745/////////////120396111055////3//43'
        '616C6C20796F75206261636B206C617465722E///0//////////A3\x03',
        '\x0200/00234/O/53/1299998/3155555/////////////090196161057/1/108/09019'
        '6161105/3//4D65737361676520666F7220333135353535352C2077697468206964656'
        'E74696669636174696F6E2039363031303931363130353720686173206265656E20627'
        '5666665726564/////////////1F\x03',
        '\x0200/00087/O/54/012345/0111111//////1/0654321/0100/////010197120501/'
        '///3///////////////4C\x03',
        '\x0265/00066/O/55/0786483/0786875676////////////////////////////////7B'
        '\x03',
        '\x0217/00098/O/57/55555//////////////////3//44657374696E6174696F6E3A20'
        '3036363636363620/1////////////37\x03',
        '\x0212/00115/O/56/0546546/08456556/////////////////3//3936303930313131'
        '3339343420393630383038313232323232/////////////2A\x03',
        '\x0222/00188/O/58/55555//////////////////3//44657374696E6174696F6E2030'
        '363636363636206964656E74696669636174696F6E3A20393630313130303931303433'
        '20686173206265656E2064656C657465642E/1////////////FF\x03',
        '\x0200/00107/O/59/00123456789/9876/////////////010109230000/1/001/0101'
        '09230130/3////////////04020012130101///43\x03',
    ]

    req6x = [
        '\x0202/00059/O/60/07656765/2/1/1/50617373776F7264//0100//////61\x03',
        '\x0200/00058/O/61/04568768///2///0100/1920870340094000//5///06\x03',
    ]

    basic51 = '\x0200/00083/O/51/012345/09876//1//1/////////////3//4D6573736' \
              '16765203531/////////////D1\x03'
    malformed = [
        '\x0300/00083/O/51/012345/09876//1//1/////////////3//4D657373616765203'
        '531/////////////D1\x03',
        '\x0200/00084/O/51/012345/09876//1//1/////////////3//4D657373616765203'
        '531/////////////D1\x03',
        '\x0200/00083/R/51/012345/09876//1//1/////////////3//4D657373616765203'
        '531/////////////D1\x03',
        '\x0200/00083/O/51/012345/09876//1//1/////////////3//4D657373616765203'
        '531/////////////D2\x03',
        '\x0200/00083/O/91/012345/09876//1//1/////////////3//4D657373616765203'
        '531/////////////D5\x03',
    ]
    utf16 = '\x0200/00077/O/51/012345/09876/////////////////4/32/FFFEC485///' \
            '///////020108///DA\x03'
    mt2 = '\x0200/00061/O/51/012345/09876/////////////////2///////////////46' \
          '\x03'
    request6x = '\x0200/00052/O/60/09876/6/5/1/736563726574//0100//////E4\x03'

    def test_rsp(self):
        for r in self.rsp:
            self.assertEqual(r, str(Response.from_string(r)))

    def test_req5x(self):
        for r in self.req5x:
            self.assertEqual(r, str(Request5x.from_string(r)))

    def test_req6x(self):
        for r in self.req6x:
            self.assertEqual(r, str(Request6x.from_string(r)))

    def test_req31(self):
        for r in self.req31:
            self.assertEqual(r, str(Request31.from_string(r)))

    def test_req30(self):
        for r in self.req30:
            self.assertEqual(r, str(Request30.from_string(r)))

    def test_req01(self):
        for r in self.req01:
            self.assertEqual(r, str(Request01.from_string(r)))

    def test_req02(self):
        for r in self.req02:
            self.assertEqual(r, str(Request02.from_string(r)))

    def test_req03(self):
        for r in self.req03:
            self.assertEqual(r, str(Request03.from_string(r)))

    def test_dispatcher(self):
        for r in self.req01 + self.req02 + self.req03 + self.req30 + \
                self.req31 + self.req5x + self.req6x + self.rsp:
            self.assertEqual(r, str(dispatcher(r)))

    def test_fields(self):
        m = Request5x.from_string(self.req5x[0])
        n = Request5x(encoded=False, **m.fields())
        self.assertEqual(str(m), str(n))

    def test_send_message(self):
        self.assertEqual(
            str(send_message('09876', '012345', 'Message 51', True)),
            self.basic51)

    def test_unpack_exceptions(self):
        for r in self.malformed:
            self.assertRaises(ValueError, Message.unpack, r, O)
        self.assertRaises(ValueError, Message.unpack, self.basic51, 'X')

    def test_Request5x_exceptions(self):
        self.assertRaises(ValueError, Request5x, **{
            'trn': 0, 'oadc': '08F4F29C0E', 'mt': 3, 'adc': '012345',
            'xmsg': 'Message 51', 'ot': 51, 'otoa': '5039', 'nt': '8'})
        self.assertRaises(ValueError, Request5x, **{
            'trn': 0, 'oadc': '08F4F29C0E', 'mt': 1, 'adc': '012345',
            'xmsg': 'Message 51', 'ot': 51, 'otoa': '5039'})

    def test_Request5x_utf16(self):
        self.assertEqual(
            self.utf16,
            str(Request5x(ot=51, trn=0, adc='012345', oadc='09876', mt=4,
                          xmsg=u'\u85c4', encoded=False)))

    def test_Request5x_mt2(self):
        self.assertEqual(
            self.mt2,
            str(Request5x(ot=51, trn=0, adc='012345', oadc='09876', mt=2,
                          xmsg='', encoded=False)))

    def test_request6x(self):
        self.assertEqual(
            self.request6x,
            str(Request6x(60, trn=0, oadc='09876', oton=6, onpi=5, styp=1,
                          pwd='secret', vers=4, encoded=False))
        )


class TestTransport(unittest.TestCase):
    def test_dt(self):
        dt = DataTransport('localhost', 10000, 1)
        msg = '\x02TEST\x03'
        dt.send(msg)
        result = None
        while True:
            result = dt.receive()
            if result is not None:
                break
        self.assertEqual(msg, result)
        dt.quit()
        event.set()


class TestCoders(unittest.TestCase):
    def test_encode(self):
        msg = 'ALPHA@NUM'
        self.assertEqual(encode_bits7(encode_ira(msg)), '10412614190438AB4D')

    def test_decode(self):
        msg = '10412614190438AB4D'
        self.assertEqual(decode_ira(decode_bits7(msg)), 'ALPHA@NUM')

    def test_encode_ira_invalid(self):
        self.assertRaises(UnicodeError, encode_ira, 'ą')

    def test_decode_ira_extended(self):
        self.assertEqual(decode_ira('\x1be'), '€')

    def test_decode_ira_extended_invalid(self):
        self.assertRaises(UnicodeError, decode_ira, '\x1bf')

    def test_decode_bits7_chr8(self):
        self.assertEqual(decode_bits7('0E61F1985C369F01'), 'abcdefg')

    def test_encode_hex_bytes(self):
        self.assertEqual(encode_hex(b'test'), '74657374')

    def test_encode_hex_utf8(self):
        self.assertEqual(encode_hex('€'), 'E282AC')

    def test_decode_hex_bytes(self):
        self.assertEqual(decode_hex(b'E282AC'), u'€')


class UCPServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', 10000))
        sock.listen(1)
        sock.settimeout(3)
        try:
            connection, client_address = sock.accept()
            result = connection.recv(4096)
            connection.sendall(result)
        except socket.timeout:
            event.set()
        while not event.isSet():
            pass


if __name__ == '__main__':
    event = threading.Event()
    ucp_server = UCPServer()
    ucp_server.start()
    unittest.main()
    ucp_server.join()
