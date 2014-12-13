import codecs


def encode(text, errors='strict'):
    """
    :type text: str

    :return: str
    """
    text += '\x00'
    msgl = len(text) * 7 / 8
    op = [-1] * msgl
    c = shift = 0

    for n in range(msgl):
        if shift == 6:
            c += 1

        shift = n % 7
        lb = ord(text[c]) >> shift
        hb = (ord(text[c + 1]) << (7 - shift) & 255)
        op[n] = lb + hb
        c += 1

    result = ''.join(map(chr, op)).encode('hex').upper()
    return chr(len(result)).encode('hex').upper() + result, len(result) + 2


def decode(text, errors='strict'):
    """
    :type text: str

    :return: str
    """
    msg_len = int(text[:2], 16) * 4 / 7
    text = [int(text[i:i+2], 16) for i in range(2, len(text), 2)]
    shift = 0
    lb = 0
    op = [-1] * msg_len
    n = 0

    for i in text:
        op[n] = (i << shift & 127) + lb
        lb = i >> (7 - shift)
        n += 1
        if shift == 6:
            op[n] = lb
            lb = 0
            n += 1
        shift = (shift + 1) % 7
    if not len(op) % 8:
        op.pop()
    return ''.join(map(chr, op)), len(op)


def getregentry(encoding):
    if encoding == 'bits7':
        return codecs.CodecInfo(name=encoding,
                                encode=encode,
                                decode=decode)

codecs.register(getregentry)
