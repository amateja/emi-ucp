# coding: utf-8
import codecs
import six

decode_base = {
    '\x00': '@',
    '\x01': '£',
    '\x02': '$',
    '\x03': '¥',
    '\x04': 'è',
    '\x05': 'é',
    '\x06': 'ù',
    '\x07': 'ì',
    '\x08': 'ò',
    '\t': 'Ç',
    '\n': '\n',
    '\x0b': 'Ø',
    '\x0c': 'ø',
    '\r': '\r',
    '\x0e': 'Å',
    '\x0f': 'å',
    '\x10': 'Δ',
    '\x11': '_',
    '\x12': 'Φ',
    '\x13': 'Γ',
    '\x14': 'Λ',
    '\x15': 'Ω',
    '\x16': 'Π',
    '\x17': 'Ψ',
    '\x18': 'Σ',
    '\x19': 'Θ',
    '\x1a': 'Ξ',
    # '\x1b': None,
    '\x1c': 'Æ',
    '\x1d': 'æ',
    '\x1e': 'ß',
    '\x1f': 'É',
    ' ': ' ',
    '!': '!',
    '"': '"',
    '#': '#',
    '$': '¤',
    '%': '%',
    '&': '&',
    "'": "'",
    '(': '(',
    ')': ')',
    '*': '*',
    '+': '+',
    ',': ',',
    '-': '-',
    '.': '.',
    '/': '/',
    '0': '0',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    ':': ':',
    ';': ';',
    '<': '<',
    '=': '=',
    '>': '>',
    '?': '?',
    '@': '¡',
    'A': 'A',
    'B': 'B',
    'C': 'C',
    'D': 'D',
    'E': 'E',
    'F': 'F',
    'G': 'G',
    'H': 'H',
    'I': 'I',
    'J': 'J',
    'K': 'K',
    'L': 'L',
    'M': 'M',
    'N': 'N',
    'O': 'O',
    'P': 'P',
    'Q': 'Q',
    'R': 'R',
    'S': 'S',
    'T': 'T',
    'U': 'U',
    'V': 'V',
    'W': 'W',
    'X': 'X',
    'Y': 'Y',
    'Z': 'Z',
    '[': 'Ä',
    '\\': 'Ö',
    ']': 'Ñ',
    '^': 'Ü',
    '_': '§',
    '`': '¿',
    'a': 'a',
    'b': 'b',
    'c': 'c',
    'd': 'd',
    'e': 'e',
    'f': 'f',
    'g': 'g',
    'h': 'h',
    'i': 'i',
    'j': 'j',
    'k': 'k',
    'l': 'l',
    'm': 'm',
    'n': 'n',
    'o': 'o',
    'p': 'p',
    'q': 'q',
    'r': 'r',
    's': 's',
    't': 't',
    'u': 'u',
    'v': 'v',
    'w': 'w',
    'x': 'x',
    'y': 'y',
    'z': 'z',
    '{': 'ä',
    '|': 'ö',
    '}': 'ñ',
    '~': 'ü',
    '\x7f': 'à',
}

decode_extension = {
    '\x0a': '\f',
    '\x14': '^',
    '(': '{',
    ')': '}',
    '/': '\\',
    '<': '[',
    '=': '~',
    '>': ']',
    '@': '|',
    'e': '€',
}

encode_base = dict((v, k) for k, v in six.iteritems(decode_base))
encode_base.update(
    dict((v, '\x1b' + k) for k, v in six.iteritems(decode_extension)))


def encode_ira(input_):
    """
    :type input_: unicode

    :return: string
    """
    result = ''
    for c in input_:
        try:
            result += encode_base[c]
        except KeyError:
            raise UnicodeError("Invalid GSM character")

    ret = ''.join(result)
    return ret


def decode_ira(input_):
    """
    :type input_: str

    :return: unicode
    """
    result = ''
    length = len(input_)
    translator = decode_base
    i = 0
    for c in input_:
        i += 1
        try:
            result += translator[c]
        except KeyError:
            if c == '\x1b' and i < length:
                translator = decode_extension
                continue
            raise UnicodeError('Unrecognized GSM character: {}.'.format(c))
        else:
            translator = decode_base
    return result


def encode_hex(_in):
    if isinstance(_in, six.binary_type):
        return codecs.decode(codecs.encode(_in, 'hex_codec').upper(), 'utf-8')
    try:
        return codecs.decode(codecs.encode(
            bytes(_in.encode('latin-1')), 'hex_codec').upper(), 'utf-8')
    except UnicodeError:
        return codecs.decode(codecs.encode(
            bytes(_in.encode('utf-8')), 'hex_codec').upper(), 'utf-8')


def decode_hex(_in):
    if isinstance(_in, six.binary_type):
        return codecs.decode(codecs.decode(_in, 'hex_codec'), 'utf-8')
    return codecs.decode(codecs.decode(
        _in.encode('utf-8'), 'hex_codec'), 'utf-8')


def encode_irahex(_in):
    return encode_hex(encode_ira(_in))


def decode_irahex(_in):
    return decode_ira(decode_hex(_in))


def encode_bits7(text):
    """
    :type text: str

    :return: str
    """
    if not text:
        return text
    text += '\x00'
    msgl = len(text) * 7 // 8
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

    result = encode_hex(''.join(map(chr, op)))
    return encode_hex(chr(len(result))) + result


def decode_bits7(text):
    """
    :type text: str

    :return: str
    """
    msg_len = int(text[:2], 16) * 4 // 7
    text = [int(text[i:i + 2], 16) for i in range(2, len(text), 2)]
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
    if not len(op) % 8 and op[-1] == 0:
        op.pop()
    return ''.join(map(chr, op))
