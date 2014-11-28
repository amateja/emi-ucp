# some test to explain ucp.py module
# TODO :: a good documentation!
#######################################

import sys

from ucp import *


# INIT
# Optional parameters :
# smsc_host - smsc_port - timeout
#####################################################

a = UCP({"smsc_host": "127.0.0.1",
         "smsc_port": 1234,
         "timeout": 2})

# SOCKET
# if a.socket.connect() is None:
#    print "\nUnable to connect to SMSC\n"

# Making UCP Message
#######################
# print "\nOP 01 - Send Message\n"

op01 = a.make_message({"op": "01",
                       "operation": "1",
                       "adc": "01234567890",
                       "oadc": "09876543210",
                       "ac": "",
                       "mt": "3",
                       "amsg": "Short Message"})

print op01 + "\n"
print "LEN UCP MESSAGE : %d " % len(op01)

op01 = a.pack(op01)

print op01 + "\n"
print "LEN PACKED STX + UCPMESS + ETX : %d " % len(op01)

op01 = a.unpack(op01)

print op01 + "\n"
print "LEN UNPACKED STX + UCPMESS + ETX : %d " % len(op01)

sys.exit(0)

# SEND Message made
##############################

a.socket.send(op01)

# READ Response
##############################

a.socket.read()


############
print op01 + "\n"
op01 = a.make_message({"op": "01",
                       "operation": "1",
                       "adc": "01234567890",
                       "oadc": "09876543210",
                       "ac": "",
                       "mt": "3",
                       "amsg": "Short Message"})

print op01 + "\n"

# PARSE Response
#############################
mess = a.parse_01(op01)

# Print response structure
#############################
print str(mess)

print "\nOP 01 - Send Negative Response\n"

print a.make_message({"op": "01",
                      "result": "1",
                      "trn": "47",
                      "nack": 'N',
                      "ec": '02',
                      "sm": 'Syntax Error'})

print "\nOP 01 - Send Positive Response\n"

print a.make_message({"op": "01",
                      "result": "1",
                      "trn": "02",
                      "ack": 'A',
                      "sm": '01234567890:090196103258'})

print "\nOP 02 - Send operation\n"

print a.make_message({"op": "02",
                      "operation": "1",
                      "npl": "1212",
                      "rads": "1",
                      "oadc": "39341111",
                      "ac": "aaa",
                      "mt": "3",
                      "amsg": "AAAAA"})

print "\nOP 02 - Send Result\n"

print a.make_message({"op": "02",
                      "result": "1",
                      "trn": "99",
                      "ack": 'A',
                      "sm": '01234567890:090196103258'})

print "\nOP 51 - Send Message\n"

print a.make_message({"op": "51",
                      "operation": "1",
                      "adc": '00393311212',
                      "oadc": "ALPHA@NUM",
                      "mt": "3",
                      "amsg": "Short Message for NEMUX",
                      "mcls": "1",
                      "otoa": "5039"})

print "\n"

print "Encode/Decode IA5\n"
print "72697420617567756520717569732073617069656E2E : " + a.ia5_decode(
    "72697420617567756520717569732073617069656E2E") + "\n"

print "4C6F72656D20697073756D20646F6C6F722073697420616D65742C20636F6E7365637465747565722061646970697363696E6720656C69742E20437572616269747572206665756769617420636F6E76616C6C6973207475727069732E20446F6E65632073697420616D657420E756C6C612E20446F6E65 : " + a.ia5_decode(
    "4C6F72656D20697073756D20646F6C6F722073697420616D65742C20636F6E7365637465747565722061646970697363696E6720656C69742E20437572616269747572206665756769617420636F6E76616C6C6973207475727069732E20446F6E65632073697420616D6574206E756C6C612E20446F6E65") + "\n"

print "6174206D6173736120696E20656E696D20626962656E64756D2061646970697363696E672E204D6175726973206E69736C20746F72746F722C20626C616E6469742073697420616D65742C2074696E636964756E7420766F6C75747061742C20766F6C757470617420612C206475692E2046757363652065 : " + a.ia5_decode(
    "6174206D6173736120696E20656E696D20626962656E64756D2061646970697363696E672E204D6175726973206E69736C20746F72746F722C20626C616E6469742073697420616D65742C2074696E636964756E7420766F6C75747061742C20766F6C757470617420612C206475692E2046757363652065") + "\n"

print "\n\"Nemux\" Ia5 encoded : " + a.ia5_encode("Nemux") + "\n"
