#!/bin/bash
#
# Check the db2_get_ddf module
#
# Make sure that we have the library hooked:
ANSIBLE_LIBRARY=./library ansible-playbook -i zpdt.yml chk_ddf.yml
