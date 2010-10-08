#!/bin/sh

DDATE1=`/bin/date +%Y%m%d --date=yesterday`
DDATE2=`/bin/date +%Y%m%d --date='2 days ago'`

DATE1=${DATE1:-$DDATE1}
DATE2=${DATE2:-$DDATE2}

cd /home/koubat/repos/goove

# accounting logs

/usr/bin/python dataimport.py -l0 -e /torque/accounting/${DATE1}
/usr/bin/python dataimport.py -l0 -e /dorje/accounting/${DATE1}
/usr/bin/python dataimport.py -l0 -e /egee_cesnet/ce2_accounting/${DATE1}

# mapping logs on CEs

/usr/bin/python dataimport.py -l0 -g /torque/cream1_opt_glite_var_log_accounting/blahp.log-${DATE2}
/usr/bin/python dataimport.py -l0 -g /torque/cream1_opt_glite_var_log_accounting/blahp.log-${DATE1}

/usr/bin/python dataimport.py -l0 -g /torque/ce2_opt_edg_var/gatekeeper/grid-jobmap_${DATE2}
/usr/bin/python dataimport.py -l0 -g /torque/ce2_opt_edg_var/gatekeeper/grid-jobmap_${DATE1}

/usr/bin/python dataimport.py -l0 -g /egee_cesnet/ce2_opt_edg_var/gatekeeper/grid-jobmap_${DATE2}
/usr/bin/python dataimport.py -l0 -g /egee_cesnet/ce2_opt_edg_var/gatekeeper/grid-jobmap_${DATE1}

/usr/bin/python dataimport.py -l0 -g /egee_cesnet/ce1_opt_edg_var/gatekeeper/grid-jobmap_${DATE2}
/usr/bin/python dataimport.py -l0 -g /egee_cesnet/ce1_opt_edg_var/gatekeeper/grid-jobmap_${DATE1}
