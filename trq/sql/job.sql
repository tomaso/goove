ALTER TABLE trq_accountingevent ENGINE=INNODB;
ALTER TABLE trq_accountingevent ENGINE=INNODB;
ALTER TABLE trq_globalconfiguration ENGINE=INNODB;
ALTER TABLE trq_griduser ENGINE=INNODB;
ALTER TABLE trq_group ENGINE=INNODB;
ALTER TABLE trq_job ENGINE=INNODB;
ALTER TABLE trq_job_jobslots ENGINE=INNODB;
ALTER TABLE trq_jobslot ENGINE=INNODB;
ALTER TABLE trq_jobstate ENGINE=INNODB;
ALTER TABLE trq_node ENGINE=INNODB;
ALTER TABLE trq_node_properties ENGINE=INNODB;
ALTER TABLE trq_node_state ENGINE=INNODB;
ALTER TABLE trq_nodelink ENGINE=INNODB;
ALTER TABLE trq_nodeproperty ENGINE=INNODB;
ALTER TABLE trq_nodestate ENGINE=INNODB;
ALTER TABLE trq_queue ENGINE=INNODB;
ALTER TABLE trq_runningjob ENGINE=INNODB;
ALTER TABLE trq_subcluster ENGINE=INNODB;
ALTER TABLE trq_submithost ENGINE=INNODB;
ALTER TABLE trq_torqueserver ENGINE=INNODB;
ALTER TABLE trq_user ENGINE=INNODB;

ALTER TABLE trq_accountingevent ADD UNIQUE ttj(timestamp,type,job_id);

CREATE INDEX `trq_job_comp_time` on `trq_job` (`comp_time`);
