ALTER TABLE mimic_hosp.admissions DROP CONSTRAINT IF EXISTS admissions_pk CASCADE;
ALTER TABLE mimic_hosp.admissions
ADD CONSTRAINT admissions_pk
  PRIMARY KEY (hadm_id);
ALTER TABLE mimic_hosp.d_hcpcs DROP CONSTRAINT IF EXISTS d_hcpcs_pk CASCADE;
ALTER TABLE mimic_hosp.d_hcpcs
ADD CONSTRAINT d_hcpcs_pk
  PRIMARY KEY (code);
ALTER TABLE mimic_hosp.diagnoses_icd DROP CONSTRAINT IF EXISTS diagnoses_icd_pk CASCADE;
ALTER TABLE mimic_hosp.diagnoses_icd
ADD CONSTRAINT diagnoses_icd_pk
  PRIMARY KEY (hadm_id, seq_num, icd_code, icd_version);
ALTER TABLE mimic_hosp.d_icd_diagnoses DROP CONSTRAINT IF EXISTS d_icd_diagnoses_pk CASCADE;
ALTER TABLE mimic_hosp.d_icd_diagnoses
ADD CONSTRAINT d_icd_diagnoses_pk
  PRIMARY KEY (icd_code, icd_version);
ALTER TABLE mimic_hosp.d_icd_procedures DROP CONSTRAINT IF EXISTS d_icd_procedures_pk CASCADE;
ALTER TABLE mimic_hosp.d_icd_procedures
ADD CONSTRAINT d_icd_procedures_pk
  PRIMARY KEY (icd_code, icd_version);
ALTER TABLE mimic_hosp.d_labitems DROP CONSTRAINT IF EXISTS d_labitems_pk CASCADE;
ALTER TABLE mimic_hosp.d_labitems
ADD CONSTRAINT d_labitems_pk
  PRIMARY KEY (itemid);
ALTER TABLE mimic_hosp.emar DROP CONSTRAINT IF EXISTS emar_pk CASCADE;
ALTER TABLE mimic_hosp.emar
ADD CONSTRAINT emar_pk
  PRIMARY KEY (emar_id);
ALTER TABLE mimic_hosp.hcpcsevents DROP CONSTRAINT IF EXISTS hcpcsevents_pk CASCADE;
ALTER TABLE mimic_hosp.hcpcsevents
ADD CONSTRAINT hcpcsevents_pk
  PRIMARY KEY (hadm_id, hcpcs_cd, seq_num);
ALTER TABLE mimic_hosp.labevents DROP CONSTRAINT IF EXISTS labevents_pk CASCADE;
ALTER TABLE mimic_hosp.labevents
ADD CONSTRAINT labevents_pk
  PRIMARY KEY (labevent_id);
ALTER TABLE mimic_hosp.microbiologyevents DROP CONSTRAINT IF EXISTS microbiologyevents_pk CASCADE;
ALTER TABLE mimic_hosp.microbiologyevents
ADD CONSTRAINT microbiologyevents_pk
  PRIMARY KEY (microevent_id);
ALTER TABLE mimic_hosp.patients DROP CONSTRAINT IF EXISTS patients_pk CASCADE;
ALTER TABLE mimic_hosp.patients
ADD CONSTRAINT patients_pk
  PRIMARY KEY (subject_id);
ALTER TABLE mimic_hosp.pharmacy DROP CONSTRAINT IF EXISTS pharmacy_pk CASCADE;
ALTER TABLE mimic_hosp.pharmacy
ADD CONSTRAINT pharmacy_pk
  PRIMARY KEY (pharmacy_id);
ALTER TABLE mimic_hosp.poe_detail DROP CONSTRAINT IF EXISTS poe_detail_pk CASCADE;
ALTER TABLE mimic_hosp.poe_detail
ADD CONSTRAINT poe_detail_pk
  PRIMARY KEY (poe_id, field_name);
ALTER TABLE mimic_hosp.poe DROP CONSTRAINT IF EXISTS poe_pk CASCADE;
ALTER TABLE mimic_hosp.poe
ADD CONSTRAINT poe_pk
  PRIMARY KEY (poe_id);
ALTER TABLE mimic_hosp.prescriptions DROP CONSTRAINT IF EXISTS prescriptions_pk CASCADE;
ALTER TABLE mimic_hosp.prescriptions
ADD CONSTRAINT prescriptions_pk
  PRIMARY KEY (pharmacy_id, drug_type, drug);
ALTER TABLE mimic_hosp.procedures_icd DROP CONSTRAINT IF EXISTS procedures_icd_pk CASCADE;
ALTER TABLE mimic_hosp.procedures_icd
ADD CONSTRAINT procedures_icd_pk
  PRIMARY KEY (hadm_id, seq_num, icd_code, icd_version);
ALTER TABLE mimic_hosp.services DROP CONSTRAINT IF EXISTS services_pk CASCADE;
ALTER TABLE mimic_hosp.services
ADD CONSTRAINT services_pk
  PRIMARY KEY (hadm_id, transfertime, curr_service);
ALTER TABLE mimic_icu.datetimeevents DROP CONSTRAINT IF EXISTS datetimeevents_pk CASCADE;
ALTER TABLE mimic_icu.datetimeevents
ADD CONSTRAINT datetimeevents_pk
  PRIMARY KEY (stay_id, itemid, charttime);
ALTER TABLE mimic_icu.d_items DROP CONSTRAINT IF EXISTS d_items_pk CASCADE;
ALTER TABLE mimic_icu.d_items
ADD CONSTRAINT d_items_pk
  PRIMARY KEY (itemid);
ALTER TABLE mimic_icu.icustays DROP CONSTRAINT IF EXISTS icustays_pk CASCADE;
ALTER TABLE mimic_icu.icustays
ADD CONSTRAINT icustays_pk
  PRIMARY KEY (stay_id);
ALTER TABLE mimic_icu.inputevents DROP CONSTRAINT IF EXISTS inputevents_pk CASCADE;
ALTER TABLE mimic_icu.inputevents
ADD CONSTRAINT inputevents_pk
  PRIMARY KEY (orderid, itemid);
ALTER TABLE mimic_icu.outputevents DROP CONSTRAINT IF EXISTS outputevents_pk CASCADE;
ALTER TABLE mimic_icu.outputevents
ADD CONSTRAINT outputevents_pk
  PRIMARY KEY (stay_id, charttime, itemid);
ALTER TABLE mimic_icu.procedureevents DROP CONSTRAINT IF EXISTS procedureevents_pk CASCADE;
ALTER TABLE mimic_icu.procedureevents
ADD CONSTRAINT procedureevents_pk
  PRIMARY KEY (orderid);
ALTER TABLE mimic_hosp.admissions DROP CONSTRAINT IF EXISTS admissions_patients_fk;
ALTER TABLE mimic_hosp.admissions
ADD CONSTRAINT admissions_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.diagnoses_icd DROP CONSTRAINT IF EXISTS diagnoses_icd_patients_fk;
ALTER TABLE mimic_hosp.diagnoses_icd
ADD CONSTRAINT diagnoses_icd_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.diagnoses_icd DROP CONSTRAINT IF EXISTS diagnoses_icd_admissions_fk;
ALTER TABLE mimic_hosp.diagnoses_icd
ADD CONSTRAINT diagnoses_icd_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.drgcodes DROP CONSTRAINT IF EXISTS drgcodes_patients_fk;
ALTER TABLE mimic_hosp.drgcodes
ADD CONSTRAINT drgcodes_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.drgcodes DROP CONSTRAINT IF EXISTS drgcodes_admissions_fk;
ALTER TABLE mimic_hosp.drgcodes
ADD CONSTRAINT drgcodes_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.emar_detail DROP CONSTRAINT IF EXISTS emar_detail_patients_fk;
ALTER TABLE mimic_hosp.emar_detail
ADD CONSTRAINT emar_detail_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.emar_detail DROP CONSTRAINT IF EXISTS emar_detail_emar_fk;
ALTER TABLE mimic_hosp.emar_detail
ADD CONSTRAINT emar_detail_emar_fk
  FOREIGN KEY (emar_id)
  REFERENCES mimic_hosp.emar (emar_id);
ALTER TABLE mimic_hosp.emar DROP CONSTRAINT IF EXISTS emar_patients_fk;
ALTER TABLE mimic_hosp.emar
ADD CONSTRAINT emar_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.emar DROP CONSTRAINT IF EXISTS emar_admissions_fk;
ALTER TABLE mimic_hosp.emar
ADD CONSTRAINT emar_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.hcpcsevents DROP CONSTRAINT IF EXISTS hcpcsevents_patients_fk;
ALTER TABLE mimic_hosp.hcpcsevents
ADD CONSTRAINT hcpcsevents_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.hcpcsevents DROP CONSTRAINT IF EXISTS hcpcsevents_admissions_fk;
ALTER TABLE mimic_hosp.hcpcsevents
ADD CONSTRAINT hcpcsevents_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.hcpcsevents DROP CONSTRAINT IF EXISTS hcpcsevents_d_hcpcs_fk;
ALTER TABLE mimic_hosp.hcpcsevents
ADD CONSTRAINT hcpcsevents_d_hcpcs_fk
  FOREIGN KEY (hcpcs_cd)
  REFERENCES mimic_hosp.d_hcpcs (code);
ALTER TABLE mimic_hosp.labevents DROP CONSTRAINT IF EXISTS labevents_patients_fk;
ALTER TABLE mimic_hosp.labevents
ADD CONSTRAINT labevents_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.labevents DROP CONSTRAINT IF EXISTS labevents_d_labitems_fk;
ALTER TABLE mimic_hosp.labevents
ADD CONSTRAINT labevents_d_labitems_fk
  FOREIGN KEY (itemid)
  REFERENCES mimic_hosp.d_labitems (itemid);
ALTER TABLE mimic_hosp.microbiologyevents DROP CONSTRAINT IF EXISTS microbiologyevents_patients_fk;
ALTER TABLE mimic_hosp.microbiologyevents
ADD CONSTRAINT microbiologyevents_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.microbiologyevents DROP CONSTRAINT IF EXISTS microbiologyevents_admissions_fk;
ALTER TABLE mimic_hosp.microbiologyevents
ADD CONSTRAINT microbiologyevents_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.pharmacy DROP CONSTRAINT IF EXISTS pharmacy_patients_fk;
ALTER TABLE mimic_hosp.pharmacy
ADD CONSTRAINT pharmacy_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.pharmacy DROP CONSTRAINT IF EXISTS pharmacy_admissions_fk;
ALTER TABLE mimic_hosp.pharmacy
ADD CONSTRAINT pharmacy_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.poe_detail DROP CONSTRAINT IF EXISTS poe_detail_patients_fk;
ALTER TABLE mimic_hosp.poe_detail
ADD CONSTRAINT poe_detail_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.poe_detail DROP CONSTRAINT IF EXISTS poe_detail_poe_fk;
ALTER TABLE mimic_hosp.poe_detail
ADD CONSTRAINT poe_detail_poe_fk
  FOREIGN KEY (poe_id)
  REFERENCES mimic_hosp.poe (poe_id);
ALTER TABLE mimic_hosp.poe DROP CONSTRAINT IF EXISTS poe_patients_fk;
ALTER TABLE mimic_hosp.poe
ADD CONSTRAINT poe_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.poe DROP CONSTRAINT IF EXISTS poe_admissions_fk;
ALTER TABLE mimic_hosp.poe
ADD CONSTRAINT poe_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.prescriptions DROP CONSTRAINT IF EXISTS prescriptions_patients_fk;
ALTER TABLE mimic_hosp.prescriptions
ADD CONSTRAINT prescriptions_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.prescriptions DROP CONSTRAINT IF EXISTS prescriptions_admissions_fk;
ALTER TABLE mimic_hosp.prescriptions
ADD CONSTRAINT prescriptions_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.procedures_icd DROP CONSTRAINT IF EXISTS procedures_icd_patients_fk;
ALTER TABLE mimic_hosp.procedures_icd
ADD CONSTRAINT procedures_icd_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.procedures_icd DROP CONSTRAINT IF EXISTS procedures_icd_admissions_fk;
ALTER TABLE mimic_hosp.procedures_icd
ADD CONSTRAINT procedures_icd_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.services DROP CONSTRAINT IF EXISTS services_patients_fk;
ALTER TABLE mimic_hosp.services
ADD CONSTRAINT services_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_hosp.services DROP CONSTRAINT IF EXISTS services_admissions_fk;
ALTER TABLE mimic_hosp.services
ADD CONSTRAINT services_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_hosp.transfers DROP CONSTRAINT IF EXISTS transfers_pk CASCADE;
ALTER TABLE mimic_hosp.transfers
ADD CONSTRAINT transfers_pk
  PRIMARY KEY (transfer_id);
ALTER TABLE mimic_hosp.transfers DROP CONSTRAINT IF EXISTS transfers_patients_fk;
ALTER TABLE mimic_hosp.transfers
ADD CONSTRAINT transfers_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_icu.chartevents DROP CONSTRAINT IF EXISTS chartevents_patients_fk;
ALTER TABLE mimic_icu.chartevents
ADD CONSTRAINT chartevents_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_icu.chartevents DROP CONSTRAINT IF EXISTS chartevents_admissions_fk;
ALTER TABLE mimic_icu.chartevents
ADD CONSTRAINT chartevents_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_icu.chartevents DROP CONSTRAINT IF EXISTS chartevents_icustays_fk;
ALTER TABLE mimic_icu.chartevents
ADD CONSTRAINT chartevents_icustays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_icu.icustays (stay_id);
ALTER TABLE mimic_icu.chartevents DROP CONSTRAINT IF EXISTS chartevents_d_items_fk;
ALTER TABLE mimic_icu.chartevents
ADD CONSTRAINT chartevents_d_items_fk
  FOREIGN KEY (itemid)
  REFERENCES mimic_icu.d_items (itemid);
ALTER TABLE mimic_icu.datetimeevents DROP CONSTRAINT IF EXISTS datetimeevents_patients_fk;
ALTER TABLE mimic_icu.datetimeevents
ADD CONSTRAINT datetimeevents_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_icu.datetimeevents DROP CONSTRAINT IF EXISTS datetimeevents_admissions_fk;
ALTER TABLE mimic_icu.datetimeevents
ADD CONSTRAINT datetimeevents_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_icu.datetimeevents DROP CONSTRAINT IF EXISTS datetimeevents_icustays_fk;
ALTER TABLE mimic_icu.datetimeevents
ADD CONSTRAINT datetimeevents_icustays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_icu.icustays (stay_id);
ALTER TABLE mimic_icu.datetimeevents DROP CONSTRAINT IF EXISTS datetimeevents_d_items_fk;
ALTER TABLE mimic_icu.datetimeevents
ADD CONSTRAINT datetimeevents_d_items_fk
  FOREIGN KEY (itemid)
  REFERENCES mimic_icu.d_items (itemid);
ALTER TABLE mimic_icu.icustays DROP CONSTRAINT IF EXISTS icustays_patients_fk;
ALTER TABLE mimic_icu.icustays
ADD CONSTRAINT icustays_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_icu.icustays DROP CONSTRAINT IF EXISTS icustays_admissions_fk;
ALTER TABLE mimic_icu.icustays
ADD CONSTRAINT icustays_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_icu.inputevents DROP CONSTRAINT IF EXISTS inputevents_patients_fk;
ALTER TABLE mimic_icu.inputevents
ADD CONSTRAINT inputevents_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_icu.inputevents DROP CONSTRAINT IF EXISTS inputevents_admissions_fk;
ALTER TABLE mimic_icu.inputevents
ADD CONSTRAINT inputevents_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_icu.inputevents DROP CONSTRAINT IF EXISTS inputevents_icustays_fk;
ALTER TABLE mimic_icu.inputevents
ADD CONSTRAINT inputevents_icustays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_icu.icustays (stay_id);
ALTER TABLE mimic_icu.inputevents DROP CONSTRAINT IF EXISTS inputevents_d_items_fk;
ALTER TABLE mimic_icu.inputevents
ADD CONSTRAINT inputevents_d_items_fk
  FOREIGN KEY (itemid)
  REFERENCES mimic_icu.d_items (itemid);
ALTER TABLE mimic_icu.outputevents DROP CONSTRAINT IF EXISTS outputevents_patients_fk;
ALTER TABLE mimic_icu.outputevents
ADD CONSTRAINT outputevents_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_icu.outputevents DROP CONSTRAINT IF EXISTS outputevents_admissions_fk;
ALTER TABLE mimic_icu.outputevents
ADD CONSTRAINT outputevents_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_icu.outputevents DROP CONSTRAINT IF EXISTS outputevents_icustays_fk;
ALTER TABLE mimic_icu.outputevents
ADD CONSTRAINT outputevents_icustays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_icu.icustays (stay_id);
ALTER TABLE mimic_icu.outputevents DROP CONSTRAINT IF EXISTS outputevents_d_items_fk;
ALTER TABLE mimic_icu.outputevents
ADD CONSTRAINT outputevents_d_items_fk
  FOREIGN KEY (itemid)
  REFERENCES mimic_icu.d_items (itemid);
ALTER TABLE mimic_icu.procedureevents DROP CONSTRAINT IF EXISTS procedureevents_patients_fk;
ALTER TABLE mimic_icu.procedureevents
ADD CONSTRAINT procedureevents_patients_fk
  FOREIGN KEY (subject_id)
  REFERENCES mimic_hosp.patients (subject_id);
ALTER TABLE mimic_icu.procedureevents DROP CONSTRAINT IF EXISTS procedureevents_admissions_fk;
ALTER TABLE mimic_icu.procedureevents
ADD CONSTRAINT procedureevents_admissions_fk
  FOREIGN KEY (hadm_id)
  REFERENCES mimic_hosp.admissions (hadm_id);
ALTER TABLE mimic_icu.procedureevents DROP CONSTRAINT IF EXISTS procedureevents_icustays_fk;
ALTER TABLE mimic_icu.procedureevents
ADD CONSTRAINT procedureevents_icustays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_icu.icustays (stay_id);
ALTER TABLE mimic_icu.procedureevents DROP CONSTRAINT IF EXISTS procedureevents_d_items_fk;
ALTER TABLE mimic_icu.procedureevents
ADD CONSTRAINT procedureevents_d_items_fk
  FOREIGN KEY (itemid)
  REFERENCES mimic_icu.d_items (itemid);

/******
  ED
 */

 SET search_path TO mimic_ed;
---------------------------
---------------------------
-- Creating Primary Keys --
---------------------------
---------------------------

ALTER TABLE mimic_ed.edstays DROP CONSTRAINT IF EXISTS edstays_pk CASCADE;
ALTER TABLE mimic_ed.edstays
ADD CONSTRAINT edstays_pk
  PRIMARY KEY (stay_id);

ALTER TABLE mimic_ed.diagnosis DROP CONSTRAINT IF EXISTS diagnosis_pk CASCADE;
ALTER TABLE mimic_ed.diagnosis
ADD CONSTRAINT diagnosis_pk
  PRIMARY KEY (stay_id, seq_num);

--ALTER TABLE mimic_ed.medrecon DROP CONSTRAINT IF EXISTS medrecon_pk CASCADE;
--ALTER TABLE mimic_ed.medrecon
--ADD CONSTRAINT medrecon_pk
--  PRIMARY KEY (stay_id, charttime, name);

--ALTER TABLE mimic_ed.pyxis DROP CONSTRAINT IF EXISTS pyxis_pk CASCADE;
--ALTER TABLE mimic_ed.pyxis
--ADD CONSTRAINT pyxis_pk
--  PRIMARY KEY (stay_id, charttime, name);

ALTER TABLE mimic_ed.triage DROP CONSTRAINT IF EXISTS triage_pk CASCADE;
ALTER TABLE mimic_ed.triage
ADD CONSTRAINT triage_pk
  PRIMARY KEY (stay_id);

ALTER TABLE mimic_ed.vitalsign DROP CONSTRAINT IF EXISTS vitalsign_pk CASCADE;
ALTER TABLE mimic_ed.vitalsign
ADD CONSTRAINT vitalsign_pk
  PRIMARY KEY (stay_id, charttime);

---------------------------
---------------------------
-- Creating Foreign Keys --
---------------------------
---------------------------

ALTER TABLE mimic_ed.diagnosis DROP CONSTRAINT IF EXISTS diagnosis_edstays_fk CASCADE;
ALTER TABLE mimic_ed.diagnosis
ADD CONSTRAINT diagnosis_edstays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_ed.edstays (stay_id);

ALTER TABLE mimic_ed.medrecon DROP CONSTRAINT IF EXISTS medrecon_edstays_fk CASCADE;
ALTER TABLE mimic_ed.medrecon
ADD CONSTRAINT medrecon_edstays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_ed.edstays (stay_id);

ALTER TABLE mimic_ed.pyxis DROP CONSTRAINT IF EXISTS pyxis_edstays_fk CASCADE;
ALTER TABLE mimic_ed.pyxis
ADD CONSTRAINT pyxis_edstays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_ed.edstays (stay_id);

ALTER TABLE mimic_ed.triage DROP CONSTRAINT IF EXISTS triage_edstays_fk CASCADE;
ALTER TABLE mimic_ed.triage
ADD CONSTRAINT triage_edstays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_ed.edstays (stay_id);

ALTER TABLE mimic_ed.vitalsign DROP CONSTRAINT IF EXISTS vitalsign_edstays_fk CASCADE;
ALTER TABLE mimic_ed.vitalsign
ADD CONSTRAINT vitalsign_edstays_fk
  FOREIGN KEY (stay_id)
  REFERENCES mimic_ed.edstays (stay_id);