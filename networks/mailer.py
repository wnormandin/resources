#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import smtplib
import time
from email.mime.text import MIMEText

parser = argparse.ArgumentParser(
        prog='mailer.py',
        usage='%(prog)s -s [SERVER] [-p [PORT]] -f [FROM] -t [TO] [LIST] [HERE]'
        )
parser.add_argument(
                    '-v','--verbose',
                    help='Enable verbose output',
                    action='store_true'
                    )
parser.add_argument('-s','--server',help='SMTP Server or IP',required=True)
parser.add_argument(
                    '-p', '--port',
                    nargs = '?',
                    default = 25,
                    choices = [25,26,587,465],
                    type = int
                    )
parser.add_argument('-f','--source',help='Source E-mail Address',required=True)
# The TO argument returns a list (even if only 1 argument is present)
parser.add_argument('-t','--to',nargs='+',help='Recipient List',required=True)
args = parser.parse_args()

class SMTPMessage():

    """ SMTP mailer class, takes header info as an argparse list """

    def __init__(self,args):
        self.args = args
        cred = raw_input("SMTP Sender Password > ")

        if args.port == 465:
            print '** Using smtplib.SMTP_SSL'
            conn_obj = smtplib.SMTP_SSL
        else:
            conn_obj = smtplib.SMTP

        server = conn_obj()
        debug = 1 if self.args.verbose else 0
        server.set_debuglevel(debug)

        try:
            server.connect(args.server, args.port)
            server.login(args.source, cred)
            ret = server.sendmail(args.source, args.to, self.build_message())
        except Exception as e:
            print '** Sendmail Failed!'
            print 'Error :\n{0}'.format(e)
        else:
            print '** Sendmail completed : {0}'.format(ret)
        finally:
            server.quit()

    def spam_test(self):
        pass

    def build_message(self):
        frm = 'From: Python Mailer <{0}>'.format(self.args.source)
        to_list = [' <{0}>'.format(a) for a in self.args.to]
        to = 'To:{0}'.format(','.join(to_list))
        sbj = 'Subject: Message send test {0}'.format(int(time.time()))
        ssl_str = 'n' if self.args.port==465 else ' <SECURE>'
        msg = 'This is a{0} SMTP mail test'.format(ssl_str)
        msg += '\n\nPlease disregard this message'
        return '\n'.join([frm,to,sbj,'',msg])

if __name__=='__main__':
    SMTPMessage(args)
