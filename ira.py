# coding: utf-8
import codecs

decode_base = {
    '\x00': u'@',
    '\x01': u'£',
    '\x02': u'$',
    '\x03': u'¥',
    '\x04': u'è',
    '\x05': u'é',
    '\x06': u'ù',
    '\x07': u'ì',
    '\x08': u'ò',
    '\t': u'Ç',
    '\n': u'\n',
    '\x0B': u'Ø',
    '\x0C': u'ø',
    '\r': u'\r',
    '\x0e': u'Å',
    '\x0f': u'å',
    '\x10': u'Δ',
    '\x11': u'_',
    '\x12': u'Φ',
    '\x13': u'Γ',
    '\x14': u'Λ',
    '\x15': u'Ω',
    '\x16': u'Π',
    '\x17': u'Ψ',
    '\x18': u'Σ',
    '\x19': u'Θ',
    '\x1a': u'Ξ',
    # '\x1b': None,
    '\x1c': u'Æ',
    '\x1d': u'æ',
    '\x1e': u'ß',
    '\x1f': u'É',
    ' ': u' ',
    '!': u'!',
    '"': u'"',
    '#': u'#',
    '$': u'¤',
    '%': u'%',
    '&': u'&',
    "'": u"'",
    '(': u'(',
    ')': u')',
    '*': u'*',
    '+': u'+',
    ',': u',',
    '-': u'-',
    '.': u'.',
    '/': u'/',
    '0': u'0',
    '1': u'1',
    '2': u'2',
    '3': u'3',
    '4': u'4',
    '5': u'5',
    '6': u'6',
    '7': u'7',
    '8': u'8',
    '9': u'9',
    ':': u':',
    ';': u';',
    '<': u'<',
    '=': u'=',
    '>': u'>',
    '?': u'?',
    '@': u'¡',
    'A': u'A',
    'B': u'B',
    'C': u'C',
    'D': u'D',
    'E': u'E',
    'F': u'F',
    'G': u'G',
    'H': u'H',
    'I': u'I',
    'J': u'J',
    'K': u'K',
    'L': u'L',
    'M': u'M',
    'N': u'N',
    'O': u'O',
    'P': u'P',
    'Q': u'Q',
    'R': u'R',
    'S': u'S',
    'T': u'T',
    'U': u'U',
    'V': u'V',
    'W': u'W',
    'X': u'X',
    'Y': u'Y',
    'Z': u'Z',
    '[': u'Ä',
    '\\': u'Ö',
    ']': u'Ñ',
    '^': u'Ü',
    '_': u'§',
    '`': u'¿',
    'a': u'a',
    'b': u'b',
    'c': u'c',
    'd': u'd',
    'e': u'e',
    'f': u'f',
    'g': u'g',
    'h': u'h',
    'i': u'i',
    'j': u'j',
    'k': u'k',
    'l': u'l',
    'm': u'm',
    'n': u'n',
    'o': u'o',
    'p': u'p',
    'q': u'q',
    'r': u'r',
    's': u's',
    't': u't',
    'u': u'u',
    'v': u'v',
    'w': u'w',
    'x': u'x',
    'y': u'y',
    'z': u'z',
    '{': u'ä',
    '|': u'ö',
    '}': u'ñ',
    '~': u'ü',
    '\x7F': u'à',
    }

decode_extension = {
    '\x0A': u'\f',
    '\x14': u'^',
    '(': u'{',
    ')': u'}',
    '/': u'\\',
    '<': u'[',
    '=': u'~',
    '>': u']',
    '@': u'|',
    'e': u'€',
}

encode_base = dict((u, g) for g, u in decode_base.iteritems())
encode_base.update(
    dict(('\x1B' + v, k) for k, v in decode_extension.iteritems()))


def encode(input_, errors='strict'):
    """
    :type input_: unicode

    :return: string
    """
    result = ''
    for c in input_:
        try:
            result += encode_base[c]
        except KeyError:
            if errors == 'strict':
                raise UnicodeError("Invalid GSM character")
            elif errors == 'replace':
                result += '?'
            elif errors == 'ignore':
                pass
            else:
                raise UnicodeError("Unknown error handling")

    ret = ''.join(result)
    return ret, len(ret)


def decode(input_, errors='strict'):
    """
    :type input_: str

    :return: unicode
    """
    result = u''
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
            if errors == 'strict':
                raise UnicodeError("Unrecognized GSM character: %s." % c)
            elif errors == 'replace':
                result += '?'
            elif errors == 'ignore':
                pass
            else:
                raise UnicodeError("Unknown error handling")
        else:
            translator = decode_base
    return result, len(result)


def encode_hex(input_, errors='strict'):
    str_, length = encode(input_, errors)
    return str_.encode('hex').upper(), length << 2


def decode_hex(input_, errors='strict'):
    return decode(input_.decode('hex'), errors)


def getregentry(encoding):
    if encoding in ('gsm0338', 'ia5', 'ira', 't50'):
        return codecs.CodecInfo(name=encoding,
                                encode=encode,
                                decode=decode)
    if encoding in ('ia5hex', 'irahex', 't50hex'):
        return codecs.CodecInfo(name=encoding,
                                encode=encode_hex,
                                decode=decode_hex)

codecs.register(getregentry)
