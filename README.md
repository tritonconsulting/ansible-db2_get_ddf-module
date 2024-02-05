# ansible-db2_get_ddf-module
This repo holds the first draft of the db2_get_ddf Ansible module written to illustrate a blog on modules. 
The module itself drives the Db2 "-DIS DDF" command from the TSO DSN command processor and parses the returned messages to create a JSON response.
To do this, we make use of:
* IBM ZOA Utilities (available to download - see the "Install from Pax" section in the doc, here: https://www.ibm.com/docs/en/zoau/1.2.x?topic=installing-configuring-zoau).
* IBM Open Enterprise SDK for Python (also available to download - click "Try no cost edition" button here: https://www.ibm.com/products/open-enterprise-python-zos).

To use it:
* Copy the module to your Ansible modules path (e.g. $HOME/.ansible/plugins/modules/)
* Set your role environment variable ssid_DB2LOAD to a colon separated list of Db2 load libraries (e.g. DB2D_DB2LOAD="DSND10.DB2D.SDSNEXIT:DSND10.SDSNLOAD"). We did this with host variables (cf environment_vars, below).
* Run:
```
./chk_ddf.sh
```

Sample output:
```
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
```
