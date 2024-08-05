DROP TABLE IF EXISTS mimic_derived.age; CREATE TABLE mimic_derived.age AS
SELECT
    ad.subject_id
    , ad.hadm_id
    , ad.admittime
    , pa.anchor_age
    , pa.anchor_year
    , pa.anchor_age + DATETIME_DIFF(ad.admittime, DATETIME(pa.anchor_year, 1, 1, 0, 0, 0), 'YEAR') AS age 
FROM mimic_hosp.admissions ad
INNER JOIN mimic_hosp.patients pa
    ON ad.subject_id = pa.subject_id
;