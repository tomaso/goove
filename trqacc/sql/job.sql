ALTER TABLE trqacc_accountingevent ENGINE=INNODB;
ALTER TABLE trqacc_eventattribute ENGINE=INNODB;
ALTER TABLE trqacc_eventattributevalue ENGINE=INNODB;
ALTER TABLE trqacc_globalconfiguration ENGINE=INNODB;
ALTER TABLE trqacc_griduser ENGINE=INNODB;
ALTER TABLE trqacc_group ENGINE=INNODB;
ALTER TABLE trqacc_job ENGINE=INNODB;
ALTER TABLE trqacc_job_jobslots ENGINE=INNODB;
ALTER TABLE trqacc_jobslot ENGINE=INNODB;
ALTER TABLE trqacc_jobstate ENGINE=INNODB;
ALTER TABLE trqacc_node ENGINE=INNODB;
ALTER TABLE trqacc_node_properties ENGINE=INNODB;
ALTER TABLE trqacc_node_state ENGINE=INNODB;
ALTER TABLE trqacc_nodelink ENGINE=INNODB;
ALTER TABLE trqacc_nodeproperty ENGINE=INNODB;
ALTER TABLE trqacc_nodestate ENGINE=INNODB;
ALTER TABLE trqacc_queue ENGINE=INNODB;
ALTER TABLE trqacc_subcluster ENGINE=INNODB;
ALTER TABLE trqacc_submithost ENGINE=INNODB;
ALTER TABLE trqacc_batchserver ENGINE=INNODB;
ALTER TABLE trqacc_user ENGINE=INNODB;

ALTER TABLE trqacc_accountingevent ADD UNIQUE ttj(timestamp,type,full_jobname);

CREATE INDEX `trqacc_job_comp_time` on `trqacc_job` (`comp_time`);

ALTER TABLE trqacc_eventattributevalue ADD UNIQUE ae_attr(ae_id,ea_id);
