rsync -avz --delete root@ce2.farm.particle.cz:/opt/edg/var/ /torque/ce2_opt_edg_var/
rsync -avz root@torque:/var/spool/torque/server_logs/ /torque/server_logs/
rsync -avz root@torque:/var/spool/torque/server_priv/accounting/ /torque/accounting/
rsync -avz root@cream1:/opt/glite/var/log/accounting/ /torque/cream1_opt_glite_var_log_accounting
rsync -avz root@ui.dorje.fzu.cz:/var/tm/server_priv/accounting/ /dorje/accounting/
rsync -avz root@ce2.egee.cesnet.cz:/var/spool/PBS/server_priv/accounting/ /egee_cesnet/ce2_accounting/
rsync -avz --delete root@ce2.egee.cesnet.cz:/opt/edg/var/ /egee_cesnet/ce2_opt_edg_var/
rsync -avz --delete root@ce1.egee.cesnet.cz:/opt/edg/var/ /egee_cesnet/ce1_opt_edg_var/
