#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Triton Consulting
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r'''
---
module: db2_get_ddf
short_description: Get the Db2 for z/OS DDF configuration
description: 
    - Get the Db2 for z/OS DDF configuration details from TSO DSN -DIS DDF and return the results as JSON.
    - This uses the ZOA Utilities to execute the IKJEFT01 TSO commnad processor, and then runs the Db2 DSN command from there.
    - The Db2 load libraries are named in the ssid_DB2LOAD environment variable as colon separated MVS dataset names.
    - The data is returned as a JSON / dictionary including the command output.
version_added: 0.0.1
author:
    - James Gill (@db2dinosaur)
options:
    db2ssid:
        description: 
            - The Db2 subsystem ID to issue the command to. 
            - The subsystem must be local to the current host.
        required: true
        type: str
        aliases: 
            - ssid
            - db2
requirements:
    - IBM ZOA Utilities v1.2.5.0 and up
    - IBM Open Enterprise SDK for Python 3.11.5 and up
    - IBM Db2 for z/OS V12.1 and up 
'''

EXAMPLES = r'''
    db2_get_ddf:
        db2ssid: DBDG
    register: ddf

    debug:
        msg: "TCPPORT = {{ ddf.tcpport }}"
'''

RETURN = r'''
db2ssid:
    description: The original db2ssid param that was passed in.
    type: str
    returned: always
    sample: 'DBDG'
ddf:
    description: Dictionary of returned data, including the raw output messages
    type: dict
    returned: always
    sample: 
        {
          "changed": false,
          "db2ssid": "DBDG",
          "ddf": {
              "PKGREL": "COMMIT",
              "SESSIDLE": "001440",
              "SQL-domain": "S0W1.DAL-EBIS.IHOST.COM",
              "aliases": {
                  "AL01": {
                      "name": "AL01",
                      "secport": "5102",
                      "status": "STARTD",
                      "tcpport": "5100"
                  },
                  "AL02": {
                      "name": "AL02",
                      "secport": "5202",
                      "status": "STARTD",
                      "tcpport": "5200"
                  }
              },
              "genericlu": "-NONE",
              "ipaddr": "192.168.248.145",
              "ipname": "-NONE",
              "location": "DALLASD",
              "luname": "NETD.DBDGLU1",
              "out": [
                  "DSNL080I  -DBDG DSNLTDDF DISPLAY DDF REPORT FOLLOWS:",
                  "DSNL081I STATUS=STARTD",
                  "DSNL082I LOCATION           LUNAME            GENERICLU",
                  "DSNL083I DALLASD            NETD.DBDGLU1      -NONE",
                  "DSNL084I TCPPORT=5045  SECPORT=5046  RESPORT=5047  IPNAME=-NONE",
                  "DSNL085I IPADDR=::192.168.248.145",
                  "DSNL086I SQL    DOMAIN=S0W1.DAL-EBIS.IHOST.COM",
                  "DSNL087I ALIAS              PORT  SECPORT STATUS",
                  "DSNL088I AL01               5100  5102    STARTD",
                  "DSNL088I AL02               5200  5202    STARTD",
                  "DSNL105I CURRENT DDF OPTIONS ARE:",
                  "DSNL106I PKGREL = COMMIT",
                  "DSNL106I SESSIDLE = 001440",
                  "DSNL099I DSNLTDDF DISPLAY DDF REPORT COMPLETE"
              ],
              "resport": "5047",
              "secport": "5046",
              "status": "STARTD",
              "tcpport": "5045"
          },
          "failed": false
      }
'''

from zoautil_py import mvscmd, datasets
from zoautil_py.types import DDStatement, DatasetDefinition, FileDefinition
import uuid
from os import environ, remove
from ansible.module_utils.basic import AnsibleModule


def run_module():
    # init the result dict
    result=dict(
        changed=False,
        db2ssid='',
        ddf={}
    )

    # define the module argument(s)
    module = AnsibleModule(
        argument_spec = dict(
            db2ssid = dict(type = 'str', aliases = ['ssid','db2'], required = True)
        )
    )

    params = module.params
    db2ssid = params['db2ssid']
    result['db2ssid'] = db2ssid
    # setup DDs ahead of calling IKJEFT01.
    ddstmt = []
    # The Db2 load libraries should be named in the ssid_DB2LIBS environment variable
    db2libs = environ.get("%s_DB2LIBS" % (db2ssid))
    if (db2libs == "None"):
        db2libs = "DSND10.%s.SDSNEXIT:DSND10.SDSNLOAD" % (db2ssid)
    dl_ents = db2libs.split(':')
    steplib = []
    for dlds in dl_ents:
        steplib.append(DatasetDefinition(dlds))
    ddstmt.append(DDStatement("steplib",steplib))

    # create SYSTSIN TSO command file. NB uuid used to make the file unique
    cmdfile = "/tmp/db2_get_ddf_cmd_%s.txt" % (uuid.uuid4())
    with open(cmdfile, mode="w", encoding="cp1047") as ip:
        ip.write("DSN S(%s)\n" % (db2ssid))
        ip.write("  -DIS DDF\n")
        ip.write("END\n")
    systsin = FileDefinition(cmdfile)
    ddstmt.append(DDStatement("systsin",systsin))

    # make SYSTSPRT a SYSOUT=* allocation
    ddstmt.append(DDStatement("systsprt","*"))

    # we have to call IKJEFT01 authorised for this to work
    rsp = mvscmd.execute_authorized(pgm="IKJEFT01",dds=ddstmt)

    # tidy up the SYSTSIN file
    try:
        remove(cmdfile)
    except OSError:
        pass

    # parse the response
    r = rsp
    out = []
    ddf = {}
    alias = {}
    capt = False
    if (r.rc == 0):
        for line in r.stdout_response.splitlines():
            # lose the print control character
            tline = line[1:].rstrip()
            if (len(tline.split()) > 1):
                msgid, msg = tline.split(' ',1)
                words = msg.split()
                if (msgid == "DSNL080I"):
                    capt = True
                if (capt):
                    out.append(tline)
                    match msgid:
                        case "DSNL081I":
                            # STATUS=status
                            ddf['status'] = words[0].split('=',1)[1]
                        case "DSNL083I":
                            # location-name  luname  genericlu
                            ddf['location'] = words[0]
                            ddf['luname'] = words[1]
                            ddf['genericlu'] = words[2]
                        case "DSNL084I":
                            # TCPPORT=tcpport SECPORT=secport RESPORT=resport IPNAME=ipname
                            ddf['tcpport'] = words[0].split('=',1)[1]
                            ddf['secport'] = words[1].split('=',1)[1]
                            ddf['resport'] = words[2].split('=',1)[1]
                            ddf['ipname'] = words[3].split('=',1)[1]
                        case "DSNL085I":
                            ddf['ipaddr'] = words[0].split('=',1)[1].strip(':')
                        case "DSNL086I":
                            dmtp = "%s-domain" % (words[0])
                            dmnm = words[1].split('=',1)[1]
                            ddf[dmtp] = dmnm
                        case "DSNL088I":
                            this_alias = {}
                            alnm = words[0]
                            this_alias['name'] = alnm
                            this_alias['tcpport'] = words[1]
                            this_alias['secport'] = words[2]
                            this_alias['status'] = words[3]
                            alias[alnm] = this_alias
                        case "DSNL106I":
                            tp = words[0]
                            vl = words[2]
                            ddf[tp] = vl
                        case "DSNL099I":
                            capt = False
        if (len(alias) > 0):
            ddf['aliases'] = alias
        ddf['out'] = out
    else:
        out.append("** rc = %d **" % (r.rc))
        out.append("stderr:")
        for line in r.stderr_response.splitlines():
            out.append(line.rstrip()[1:])
        out.append("stdout:")
        for line in r.stdout_response.splitlines():
            out.append(line.rstrip()[1:])
        ddf['out'] = out
        result['ddf'] = ddf
        module.fail_json(msg='Error processing DSN command request',**result)
    result['ddf'] = ddf
    result['changed'] = False
    # exit the module and return the json result
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
