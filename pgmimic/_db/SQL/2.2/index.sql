SET search_path TO mimic_hosp;
DROP INDEX IF EXISTS admissions_idx01;
CREATE INDEX admissions_idx01
  ON admissions (admittime, dischtime, deathtime);
DROP INDEX IF EXISTS D_ICD_DIAG_idx02;
CREATE INDEX D_ICD_DIAG_idx02
  ON D_ICD_DIAGNOSES (LONG_TITLE);
DROP INDEX IF EXISTS D_ICD_PROC_idx02;
CREATE INDEX D_ICD_PROC_idx02
  ON D_ICD_PROCEDURES (LONG_TITLE);
DROP INDEX IF EXISTS drgcodes_idx01;
CREATE INDEX drgcodes_idx01
  ON drgcodes (drg_code, drg_type);
DROP INDEX IF EXISTS drgcodes_idx02;
CREATE INDEX drgcodes_idx02
  ON drgcodes (description, drg_severity);
DROP INDEX IF EXISTS d_labitems_idx01;
CREATE INDEX d_labitems_idx01
  ON d_labitems (label, fluid, category);
DROP INDEX IF EXISTS emar_detail_idx01;
CREATE INDEX emar_detail_idx01
  ON emar_detail (pharmacy_id);
DROP INDEX IF EXISTS emar_detail_idx02;
CREATE INDEX emar_detail_idx02
  ON emar_detail (product_code);
DROP INDEX IF EXISTS emar_detail_idx03;
CREATE INDEX emar_detail_idx03
  ON emar_detail (route, site, side);
DROP INDEX IF EXISTS EMAR_DET_idx04;
CREATE INDEX EMAR_DET_idx04
  ON EMAR_DETAIL (PRODUCT_DESCRIPTION);
DROP INDEX IF EXISTS emar_idx01;
CREATE INDEX emar_idx01
  ON emar (poe_id);
DROP INDEX IF EXISTS emar_idx02;
CREATE INDEX emar_idx02
  ON emar (pharmacy_id);
DROP INDEX IF EXISTS emar_idx03;
CREATE INDEX emar_idx03
  ON emar (charttime, scheduletime, storetime);
DROP INDEX IF EXISTS emar_idx04;
CREATE INDEX emar_idx04
  ON emar (medication);
DROP INDEX IF EXISTS HCPCSEVENTS_idx04;
CREATE INDEX HCPCSEVENTS_idx04
  ON HCPCSEVENTS (SHORT_DESCRIPTION);
DROP INDEX IF EXISTS labevents_idx01;
CREATE INDEX labevents_idx01
  ON labevents (charttime, storetime);
DROP INDEX IF EXISTS labevents_idx02;
CREATE INDEX labevents_idx02
  ON labevents (specimen_id);
DROP INDEX IF EXISTS microbiologyevents_idx01;
CREATE INDEX microbiologyevents_idx01
  ON microbiologyevents (chartdate, charttime, storedate, storetime);
DROP INDEX IF EXISTS microbiologyevents_idx02;
CREATE INDEX microbiologyevents_idx02
  ON microbiologyevents (spec_itemid, test_itemid, org_itemid, ab_itemid);
DROP INDEX IF EXISTS microbiologyevents_idx03;
CREATE INDEX microbiologyevents_idx03
  ON microbiologyevents (micro_specimen_id);
DROP INDEX IF EXISTS patients_idx01;
CREATE INDEX patients_idx01
  ON patients (anchor_age);
DROP INDEX IF EXISTS patients_idx02;
CREATE INDEX patients_idx02
  ON patients (anchor_year);
DROP INDEX IF EXISTS pharmacy_idx01;
CREATE INDEX pharmacy_idx01
  ON pharmacy (poe_id);
DROP INDEX IF EXISTS pharmacy_idx02;
CREATE INDEX pharmacy_idx02
  ON pharmacy (starttime, stoptime);
DROP INDEX IF EXISTS pharmacy_idx03;
CREATE INDEX pharmacy_idx03
  ON pharmacy (medication);
DROP INDEX IF EXISTS pharmacy_idx04;
CREATE INDEX pharmacy_idx04
  ON pharmacy (route);
DROP INDEX IF EXISTS poe_idx01;
CREATE INDEX poe_idx01
  ON poe (order_type);
DROP INDEX IF EXISTS prescriptions_idx01;
CREATE INDEX prescriptions_idx01
  ON prescriptions (starttime, stoptime);
DROP INDEX IF EXISTS transfers_idx01;
CREATE INDEX transfers_idx01
  ON transfers (hadm_id);
DROP INDEX IF EXISTS transfers_idx02;
CREATE INDEX transfers_idx02
  ON transfers (intime);
DROP INDEX IF EXISTS transfers_idx03;
CREATE INDEX transfers_idx03
  ON transfers (careunit);
SET search_path TO mimic_icu;
DROP INDEX IF EXISTS chartevents_idx01;
CREATE INDEX chartevents_idx01
  ON chartevents (charttime, storetime);
DROP INDEX IF EXISTS datetimeevents_idx01;
CREATE INDEX datetimeevents_idx01
  ON datetimeevents (charttime, storetime);
DROP INDEX IF EXISTS datetimeevents_idx02;
CREATE INDEX datetimeevents_idx02
  ON datetimeevents (value);
DROP INDEX IF EXISTS d_items_idx01;
CREATE INDEX d_items_idx01
  ON d_items (label, abbreviation);
DROP INDEX IF EXISTS d_items_idx02;
CREATE INDEX d_items_idx02
  ON d_items (category);
DROP INDEX IF EXISTS icustays_idx01;
CREATE INDEX icustays_idx01
  ON icustays (first_careunit, last_careunit);
DROP INDEX IF EXISTS icustays_idx02;
CREATE INDEX icustays_idx02
  ON icustays (intime, outtime);
DROP INDEX IF EXISTS inputevents_idx01;
CREATE INDEX inputevents_idx01
  ON inputevents (starttime, endtime);
DROP INDEX IF EXISTS inputevents_idx02;
CREATE INDEX inputevents_idx02
  ON inputevents (ordercategorydescription);
DROP INDEX IF EXISTS outputevents_idx01;
CREATE INDEX outputevents_idx01
  ON outputevents (charttime, storetime);
DROP INDEX IF EXISTS procedureevents_idx01;
CREATE INDEX procedureevents_idx01
  ON procedureevents (starttime, endtime);
DROP INDEX IF EXISTS procedureevents_idx02;
CREATE INDEX procedureevents_idx02
  ON procedureevents (ordercategoryname);

/*
 ED INDEX
 */

SET search_path TO mimiciv_ed;

-- diagnosis

DROP INDEX IF EXISTS diagnosis_idx01;
CREATE INDEX diagnosis_idx01
  ON diagnosis (subject_id, stay_id);

DROP INDEX IF EXISTS diagnosis_idx02;
CREATE INDEX diagnosis_idx02
  ON diagnosis (icd_code, icd_version);

-- edstays

DROP INDEX IF EXISTS edstays_idx01;
CREATE INDEX edstays_idx01
  ON edstays (subject_id, hadm_id, stay_id);

DROP INDEX IF EXISTS edstays_idx02;
CREATE INDEX edstays_idx02
  ON edstays (intime, outtime);

-- medrecon

DROP INDEX IF EXISTS medrecon_idx01;
CREATE INDEX medrecon_idx01
  ON medrecon (subject_id, stay_id, charttime);

-- pyxis

DROP INDEX IF EXISTS pyxis_idx01;
CREATE INDEX pyxis_idx01
  ON pyxis (subject_id, stay_id, charttime);

DROP INDEX IF EXISTS pyxis_idx02;
CREATE INDEX pyxis_idx02
  ON pyxis (gsn);

-- triage

DROP INDEX IF EXISTS triage_idx01;
CREATE INDEX triage_idx01
  ON triage (subject_id, stay_id);

-- vitalsign

DROP INDEX IF EXISTS vitalsign_idx01;
CREATE INDEX vitalsign_idx01
  ON vitalsign (subject_id, stay_id, charttime);