#!/bin/bash 

openssl req -new -x509 -days 365 -nodes -out server.pem -keyout server.pem <<INDATA
US
NewYork
Hamilton
Colgate University
Computer Science Department
pidisplay
csadmin@cs.colgate.edu
INDATA

