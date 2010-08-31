#!/bin/sh

DATE1=`/bin/date +%Y%m%d --date=yesterday`
DATE1=`/bin/date +%Y%m%d --date='2 days ago'`

cd /home/koubat/repos/goove

# accounting logs

/usr/bin/python dataimport.py -l0 -e /torque/accounting/${DATE1}
/usr/bin/python dataimport.py -l0 -e /dorje/accounting/${DATE1}

# mapping logs on CEs

/usr/bin/python dataimport.py -l0 -g /torque/cream1_opt_glite_var_log_accounting/blahp.log-${DATE2}
/usr/bin/python dataimport.py -l0 -g /torque/cream1_opt_glite_var_log_accounting/blahp.log-${DATE1}
/usr/bin/python dataimport.py -l0 -g /torque/ce2_opt_edg_var/gatekeeper/grid-jobmap_${DATE2}
/usr/bin/python dataimport.py -l0 -g /torque/ce2_opt_edg_var/gatekeeper/grid-jobmap_${DATE1}
