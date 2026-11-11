-- Captured by benchmarks/bench_db.py --dump-queries from the harness-owned server.
-- Regenerate it; do not edit it.

-- block: search.empty/result_count __api/meta/result_count.json?reqno=1
-- statement: connection 17
SET NAMES utf8mb4;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT VERSION(),
                       @@sql_mode,
                       @@default_storage_engine,
                       @@sql_auto_is_null,
                       @@lower_case_table_names,
                       CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL;
-- statement: connection 17
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 1,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general`;
-- statement: connection 17
UPDATE user_searches SET result_count = 29752, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 1;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.broad/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 2,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0;
-- statement: connection 17
UPDATE user_searches SET result_count = 29730, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 2;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.selective/result_count __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 17
SELECT `mult_field`.`qualified_name` AS `qualified_name`, `mult_field`.`field_id` AS `field_id` FROM `mult_field`;
-- statement: connection 17
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 5;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 17
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`physical_table`, `table_names`.`target_name`, `table_names`.`timestamp` FROM `table_names` ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 3,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5);
-- statement: connection 17
UPDATE user_searches SET result_count = 171, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 3;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.ring_radius/result_count __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius2') LIMIT 21;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 4,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0;
-- statement: connection 17
UPDATE user_searches SET result_count = 11139, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 4;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.target/result_count __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 17
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 8;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 5,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,'11');
-- statement: connection 17
UPDATE user_searches SET result_count = 5062, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 5;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.surface_geometry/result_count __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'surfacegeometrytargetname' LIMIT 21;
-- statement: connection 17
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 87;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude2') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 6,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 0 WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (0)));
-- statement: connection 17
UPDATE user_searches SET result_count = 4338, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 6;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;

-- block: pages.empty/build __api/meta/result_count.json?reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;

-- block: pages.empty/page_1 api/data.json?page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'tx51otutnx9scjaepbhq3syqv2ro6ex9' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('tx51otutnx9scjaepbhq3syqv2ro6ex9', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TY:0zioYjeJNAcQfwQG80fhN7Ll5fm91JnuXK40FrOrZ5A', '2026-11-25 13:34:56.845445');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationduration' LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TY:0zioYjeJNAcQfwQG80fhN7Ll5fm91JnuXK40FrOrZ5A', `expire_date` = '2026-11-25 13:34:56.864418' WHERE `django_session`.`session_key` = 'tx51otutnx9scjaepbhq3syqv2ro6ex9';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.empty/page_10 api/data.json?page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:56.879602' AND `django_session`.`session_key` = 'tx51otutnx9scjaepbhq3syqv2ro6ex9') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TY:0zioYjeJNAcQfwQG80fhN7Ll5fm91JnuXK40FrOrZ5A', `expire_date` = '2026-11-25 13:34:56.890470' WHERE `django_session`.`session_key` = 'tx51otutnx9scjaepbhq3syqv2ro6ex9';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.empty/page_last api/data.json?page=298&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:56.900867' AND `django_session`.`session_key` = 'tx51otutnx9scjaepbhq3syqv2ro6ex9') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 29701 AND 29800 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TY:0zioYjeJNAcQfwQG80fhN7Ll5fm91JnuXK40FrOrZ5A', `expire_date` = '2026-11-25 13:34:56.906764' WHERE `django_session`.`session_key` = 'tx51otutnx9scjaepbhq3syqv2ro6ex9';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.broad/build __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;

-- block: pages.broad/page_1 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'wtwac713kz9mn077l2vlw39bide2cbyn' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('wtwac713kz9mn077l2vlw39bide2cbyn', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TY:0zioYjeJNAcQfwQG80fhN7Ll5fm91JnuXK40FrOrZ5A', '2026-11-25 13:34:56.940718');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TY:0zioYjeJNAcQfwQG80fhN7Ll5fm91JnuXK40FrOrZ5A', `expire_date` = '2026-11-25 13:34:56.952541' WHERE `django_session`.`session_key` = 'wtwac713kz9mn077l2vlw39bide2cbyn';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.broad/page_10 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:56.962729' AND `django_session`.`session_key` = 'wtwac713kz9mn077l2vlw39bide2cbyn') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TY:0zioYjeJNAcQfwQG80fhN7Ll5fm91JnuXK40FrOrZ5A', `expire_date` = '2026-11-25 13:34:56.973014' WHERE `django_session`.`session_key` = 'wtwac713kz9mn077l2vlw39bide2cbyn';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.broad/page_last api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=298&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:56.992915' AND `django_session`.`session_key` = 'wtwac713kz9mn077l2vlw39bide2cbyn') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 29701 AND 29800 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.007544' WHERE `django_session`.`session_key` = 'wtwac713kz9mn077l2vlw39bide2cbyn';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.selective/build __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;

-- block: pages.selective/page_1 api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '49se1bql1xn4p2a4ub4o88xpui9gpfzw' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('49se1bql1xn4p2a4ub4o88xpui9gpfzw', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.041541');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.051680' WHERE `django_session`.`session_key` = '49se1bql1xn4p2a4ub4o88xpui9gpfzw';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.selective/page_10 api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.062543' AND `django_session`.`session_key` = '49se1bql1xn4p2a4ub4o88xpui9gpfzw') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 101 AND 200 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.069232' WHERE `django_session`.`session_key` = '49se1bql1xn4p2a4ub4o88xpui9gpfzw';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.selective/page_last api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.079748' AND `django_session`.`session_key` = '49se1bql1xn4p2a4ub4o88xpui9gpfzw') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 101 AND 200 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.086405' WHERE `django_session`.`session_key` = '49se1bql1xn4p2a4ub4o88xpui9gpfzw';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.ring_radius/build __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;

-- block: pages.ring_radius/page_1 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'y0w1vgl0zsfd38u0bprpog17aohrq92h' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('y0w1vgl0zsfd38u0bprpog17aohrq92h', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.117806');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 4) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.127392' WHERE `django_session`.`session_key` = 'y0w1vgl0zsfd38u0bprpog17aohrq92h';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.ring_radius/page_10 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.139224' AND `django_session`.`session_key` = 'y0w1vgl0zsfd38u0bprpog17aohrq92h') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 4) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.150087' WHERE `django_session`.`session_key` = 'y0w1vgl0zsfd38u0bprpog17aohrq92h';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.ring_radius/page_last api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=112&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.160455' AND `django_session`.`session_key` = 'y0w1vgl0zsfd38u0bprpog17aohrq92h') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 4) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 11101 AND 11200 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.165525' WHERE `django_session`.`session_key` = 'y0w1vgl0zsfd38u0bprpog17aohrq92h';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.target/build __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;

-- block: pages.target/page_1 api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'lb4hofk941jgoyo2oby296x5do8zkzr7' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('lb4hofk941jgoyo2oby296x5do8zkzr7', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.201033');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 5) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.211227' WHERE `django_session`.`session_key` = 'lb4hofk941jgoyo2oby296x5do8zkzr7';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.target/page_10 api/data.json?target=Saturn&page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.225283' AND `django_session`.`session_key` = 'lb4hofk941jgoyo2oby296x5do8zkzr7') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 5) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.233459' WHERE `django_session`.`session_key` = 'lb4hofk941jgoyo2oby296x5do8zkzr7';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.target/page_last api/data.json?target=Saturn&page=51&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.248988' AND `django_session`.`session_key` = 'lb4hofk941jgoyo2oby296x5do8zkzr7') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 5) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 5001 AND 5100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.255279' WHERE `django_session`.`session_key` = 'lb4hofk941jgoyo2oby296x5do8zkzr7';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.surface_geometry/build __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;

-- block: pages.surface_geometry/page_1 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'qqnykf77k27kfpp566qkhz6eth58blxd' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('qqnykf77k27kfpp566qkhz6eth58blxd', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.287613');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 6) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.297756' WHERE `django_session`.`session_key` = 'qqnykf77k27kfpp566qkhz6eth58blxd';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.surface_geometry/page_10 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.308403' AND `django_session`.`session_key` = 'qqnykf77k27kfpp566qkhz6eth58blxd') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 6) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.316472' WHERE `django_session`.`session_key` = 'qqnykf77k27kfpp566qkhz6eth58blxd';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.surface_geometry/page_last api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=44&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.326626' AND `django_session`.`session_key` = 'qqnykf77k27kfpp566qkhz6eth58blxd') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 6) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 4301 AND 4400 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.331666' WHERE `django_session`.`session_key` = 'qqnykf77k27kfpp566qkhz6eth58blxd';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.empty/default_order api/data.json?page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'e70xp0h2wxkptgfwcw9w2bwr9zn563zx' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('e70xp0h2wxkptgfwcw9w2bwr9zn563zx', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.353941');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.365556' WHERE `django_session`.`session_key` = 'e70xp0h2wxkptgfwcw9w2bwr9zn563zx';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.empty/resorted api/data.json?order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.376700' AND `django_session`.`session_key` = 'e70xp0h2wxkptgfwcw9w2bwr9zn563zx') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 7,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general`;
-- statement: connection 17
UPDATE user_searches SET result_count = 29752, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 7;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.479154' WHERE `django_session`.`session_key` = 'e70xp0h2wxkptgfwcw9w2bwr9zn563zx';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.broad/default_order api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '05wo15lt0xjv65tzt5o91jhdh43h6lqt' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('05wo15lt0xjv65tzt5o91jhdh43h6lqt', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.505375');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.517372' WHERE `django_session`.`session_key` = '05wo15lt0xjv65tzt5o91jhdh43h6lqt';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.broad/resorted api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.537672' AND `django_session`.`session_key` = '05wo15lt0xjv65tzt5o91jhdh43h6lqt') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 8;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 8 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 8,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0;
-- statement: connection 17
UPDATE user_searches SET result_count = 29730, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 8;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 8) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 8;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.661126' WHERE `django_session`.`session_key` = '05wo15lt0xjv65tzt5o91jhdh43h6lqt';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.selective/default_order api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '34sou1uuqt0ziwkuakqxxqimik9cl5bn' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('34sou1uuqt0ziwkuakqxxqimik9cl5bn', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.685982');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.696761' WHERE `django_session`.`session_key` = '34sou1uuqt0ziwkuakqxxqimik9cl5bn';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.selective/resorted api/data.json?planet=Uranus&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.709485' AND `django_session`.`session_key` = '34sou1uuqt0ziwkuakqxxqimik9cl5bn') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 9;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 9 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 9,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5);
-- statement: connection 17
UPDATE user_searches SET result_count = 171, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 9;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 9) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 9;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.731437' WHERE `django_session`.`session_key` = '34sou1uuqt0ziwkuakqxxqimik9cl5bn';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.ring_radius/default_order api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '8jhx63qsma752gnztsauo7yloeeo7dp7' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('8jhx63qsma752gnztsauo7yloeeo7dp7', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.755704');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 4) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.765395' WHERE `django_session`.`session_key` = '8jhx63qsma752gnztsauo7yloeeo7dp7';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.ring_radius/resorted api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.776623' AND `django_session`.`session_key` = '8jhx63qsma752gnztsauo7yloeeo7dp7') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 10;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 10 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 10,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0;
-- statement: connection 17
UPDATE user_searches SET result_count = 11139, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 10;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 10) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 10;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.845531' WHERE `django_session`.`session_key` = '8jhx63qsma752gnztsauo7yloeeo7dp7';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.target/default_order api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'yzyvztre6z34my3kxwe2bkg4zyc5p659' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('yzyvztre6z34my3kxwe2bkg4zyc5p659', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.868705');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 5) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.882590' WHERE `django_session`.`session_key` = 'yzyvztre6z34my3kxwe2bkg4zyc5p659';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.target/resorted api/data.json?target=Saturn&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.893516' AND `django_session`.`session_key` = 'yzyvztre6z34my3kxwe2bkg4zyc5p659') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 11;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 11 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 11,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,'11');
-- statement: connection 17
UPDATE user_searches SET result_count = 5062, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 11;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 11) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 11;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.938416' WHERE `django_session`.`session_key` = 'yzyvztre6z34my3kxwe2bkg4zyc5p659';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.surface_geometry/default_order api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '019ti6z8v60y7d9zz0yt4zk9q73sg2pz' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('019ti6z8v60y7d9zz0yt4zk9q73sg2pz', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', '2026-11-25 13:34:57.960980');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 6) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8TZ:RDJwqsql2Pi-LdbgNF8cx466bqpoaS3tcuCqwqHbFW4', `expire_date` = '2026-11-25 13:34:57.970810' WHERE `django_session`.`session_key` = '019ti6z8v60y7d9zz0yt4zk9q73sg2pz';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.surface_geometry/resorted api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:57.981463' AND `django_session`.`session_key` = '019ti6z8v60y7d9zz0yt4zk9q73sg2pz') LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 12;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 12 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 12,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 0 WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (0)));
-- statement: connection 17
UPDATE user_searches SET result_count = 4338, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 12;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 12) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 12;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', `expire_date` = '2026-11-25 13:34:58.019952' WHERE `django_session`.`session_key` = '019ti6z8v60y7d9zz0yt4zk9q73sg2pz';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: fanout.empty/result_count __api/meta/result_count.json?reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;

-- block: fanout.empty/mults_instrument __api/meta/mults/instrument.json?reqno=1
-- statement: connection 17
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 2;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general` GROUP BY `obs_general`.`instrument_id`;

-- block: fanout.empty/mults_observationtype __api/meta/mults/observationtype.json?reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationtype' LIMIT 21;
-- statement: connection 17
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 4;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general` GROUP BY `obs_general`.`observation_type`;

-- block: fanout.empty/mults_target __api/meta/mults/target.json?reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`_mult_val_`,COUNT(*) AS `target_name__count` FROM `obs_general` INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]" COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general` GROUP BY `obs_general`.`_mult_val_`;

-- block: fanout.empty/endpoints_time1 __api/meta/range/endpoints/time1.json?reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 17
SELECT MIN(`obs_general`.`time1`) AS `min`, MAX(`obs_general`.`time2`) AS `max` FROM `obs_general`;
-- statement: connection 17
SELECT COUNT(*) AS `__count` FROM `obs_general` WHERE (`obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL);

-- block: fanout.empty/menu __menu.json?reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_ring_geometry', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_wavelength', 'obs_type_image', 'obs_profile') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOsolarringopeningangle1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOobserverringopeningangle1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `definitions`.`context` AS `context`, `definitions`.`term` AS `term`, `definitions`.`definition` AS `definition` FROM `definitions`;

-- block: fanout.selected/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 13,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`planet_id` IN (4)) AND (`obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0);
-- statement: connection 17
UPDATE user_searches SET result_count = 17119, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 13;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;

-- block: fanout.selected/mults_instrument __api/meta/mults/instrument.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13;
-- statement: connection 17
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 13) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`instrument_id`;

-- block: fanout.selected/mults_observationtype __api/meta/mults/observationtype.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13;
-- statement: connection 17
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 13) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`observation_type`;

-- block: fanout.selected/mults_target __api/meta/mults/target.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13;
-- statement: connection 17
SELECT `obs_general`.`_mult_val_`,COUNT(*) AS `target_name__count` FROM `obs_general` INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]" COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 13) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`_mult_val_`;

-- block: fanout.selected/endpoints_time1 __api/meta/range/endpoints/time1.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 14;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 14 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 14,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (4);
-- statement: connection 17
UPDATE user_searches SET result_count = 17119, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 14;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 17
SELECT MIN(`obs_general`.`time1`),MAX(`obs_general`.`time2`) FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 14) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 17
SELECT COUNT(*) FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 14) AS `results` WHERE `obs_general`.`id`=`results`.`id` AND `obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL;

-- block: fanout.selected/menu __menu.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13;
-- statement: connection 17
SELECT `partables`.`id`, `partables`.`trigger_tab`, `partables`.`trigger_col`, `partables`.`trigger_val`, `partables`.`partable`, `partables`.`timestamp` FROM `partables`;
-- statement: connection 17
SELECT DISTINCT `obs_general`.`mission_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 13) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 17
SELECT DISTINCT `obs_general`.`instrument_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 13) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 17
SELECT DISTINCT `obs_general`.`inst_host_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 13) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_type_image', 'obs_wavelength', 'obs_profile', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_ring_geometry') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;

-- block: widget.planet/widget __widget/planet.html
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 17
SELECT `mult`.`field_id`, `mult`.`id`, `mult`.`value`, `mult`.`label`, `mult`.`pin`, `mult`.`disp_rank`, `mult`.`display`, `mult`.`grouping` FROM `mult` WHERE (`mult`.`field_id` = 5 AND `mult`.`grouping` IS NULL);
-- statement: connection 17
SELECT `mult`.`field_id`, `mult`.`id`, `mult`.`value`, `mult`.`label`, `mult`.`pin`, `mult`.`disp_rank`, `mult`.`display`, `mult`.`grouping` FROM `mult` WHERE (`mult`.`display` = 'Y' AND `mult`.`field_id` = 5 AND `mult`.`grouping` IS NULL) ORDER BY `mult`.`disp_rank` ASC;
-- statement: connection 17
SELECT `mult`.`field_id`, `mult`.`id`, `mult`.`value`, `mult`.`label`, `mult`.`pin`, `mult`.`disp_rank`, `mult`.`display`, `mult`.`grouping` FROM `mult` WHERE (`mult`.`field_id` = 5 AND `mult`.`display` = 'Y') ORDER BY `mult`.`disp_rank` ASC;
-- statement: connection 17
SELECT `mult_group`.`grouping` AS `grouping` FROM `mult_group` WHERE `mult_group`.`field_id` = 5 ORDER BY `mult_group`.`group_rank` ASC;

-- block: categories/categories api/categories/co-iss-w1477654052.json
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_pds` INNER JOIN `obs_general` ON (`obs_pds`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_type_image` INNER JOIN `obs_general` ON (`obs_type_image`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_wavelength` INNER JOIN `obs_general` ON (`obs_wavelength`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_profile` INNER JOIN `obs_general` ON (`obs_profile`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_surface_geometry` INNER JOIN `obs_general` ON (`obs_surface_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT `obs_surface_geometry_target`.`target_name` AS `target_name` FROM `obs_surface_geometry_target` INNER JOIN `obs_general` ON (`obs_surface_geometry_target`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_ring_geometry` INNER JOIN `obs_general` ON (`obs_ring_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_mission_cassini` INNER JOIN `obs_general` ON (`obs_mission_cassini`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_mission_galileo` INNER JOIN `obs_general` ON (`obs_mission_galileo`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_mission_hubble` INNER JOIN `obs_general` ON (`obs_mission_hubble`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_mission_new_horizons` INNER JOIN `obs_general` ON (`obs_mission_new_horizons`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_mission_voyager` INNER JOIN `obs_general` ON (`obs_mission_voyager`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_instrument_cocirs` INNER JOIN `obs_general` ON (`obs_instrument_cocirs`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_instrument_coiss` INNER JOIN `obs_general` ON (`obs_instrument_coiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_instrument_couvis` INNER JOIN `obs_general` ON (`obs_instrument_couvis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_instrument_covims` INNER JOIN `obs_general` ON (`obs_instrument_covims`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_instrument_gossi` INNER JOIN `obs_general` ON (`obs_instrument_gossi`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_instrument_nhlorri` INNER JOIN `obs_general` ON (`obs_instrument_nhlorri`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_instrument_nhmvic` INNER JOIN `obs_general` ON (`obs_instrument_nhmvic`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 17
SELECT 1 AS `a` FROM `obs_instrument_vgiss` INNER JOIN `obs_general` ON (`obs_instrument_vgiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;

-- block: autocomplete.bundleid/build __api/meta/result_count.json?reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;

-- block: autocomplete.bundleid/prefix_2 __api/stringsearchchoices/bundleid.json?bundleid=CO&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'bundleid' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`name` = 'bundle_id') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_pds`.`obs_general_id`=`results`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%CO%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: autocomplete.bundleid/prefix_6 __api/stringsearchchoices/bundleid.json?bundleid=COISS_&reqno=1
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_pds`.`obs_general_id`=`results`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%COISS\\_%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: files.broad/one_observation api/files/co-iss-w1477654052.json
-- statement: connection 17
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`file_number`;

-- block: files.broad/search_page_1 api/files.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'kr5pbwf5oa4rtqlxa5ti0clogrjm8q8m' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('kr5pbwf5oa4rtqlxa5ti0clogrjm8q8m', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', '2026-11-25 13:34:58.724831');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
SELECT `obs_general`.`opus_id` FROM `obs_general` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('vg-iss-1-s-prof','vg-uvs-1-s-occ-1980-317-iother-e','vg-rss-1-s-occ-1980-318-s63-e','vg-rss-1-s-occ-1980-318-x63-e','vg-iss-2-s-c4360001','vg-iss-2-s-c4360004','vg-iss-2-s-c4360007','vg-iss-2-s-c4360010','vg-iss-2-s-c4360018','vg-iss-2-s-c4360022','vg-iss-2-s-c4360026','vg-iss-2-s-c4360029','vg-iss-2-s-c4360033','vg-iss-2-s-c4360037','vg-iss-2-s-c4360041','vg-iss-2-s-c4360044','vg-iss-2-s-c4360048','vg-iss-2-s-c4360052','vg-iss-2-s-c4360056','vg-iss-2-s-c4360059','vg-iss-2-s-c4360103','vg-iss-2-s-c4360107','vg-iss-2-s-c4360111','vg-iss-2-s-c4360114','vg-iss-2-s-c4360257','vg-iss-2-s-c4360301','vg-iss-2-s-c4360305','vg-iss-2-s-c4360308','vg-iss-2-s-c4360312','vg-iss-2-s-c4360316','vg-iss-2-s-c4360320','vg-iss-2-s-c4360323','vg-iss-2-s-c4360327','vg-iss-2-s-c4360331','vg-iss-2-s-c4360335','vg-iss-2-s-c4360338','vg-iss-2-s-c4360342','vg-iss-2-s-c4360346','vg-iss-2-s-c4360350','vg-iss-2-s-c4360353','vg-iss-2-s-c4360507','vg-iss-2-s-c4360511','vg-iss-2-s-c4360515','vg-iss-2-s-c4360519','vg-iss-2-s-c4360523','vg-iss-2-s-c4360527','vg-iss-2-s-c4360536','vg-iss-2-s-c4360540','vg-iss-2-s-c4360544','vg-iss-2-s-c4360547','vg-iss-2-s-c4360551','vg-iss-2-s-c4360555','vg-iss-2-s-c4360559','vg-iss-2-s-c4360602','vg-iss-2-s-c4360606','vg-iss-2-s-c4360610','vg-iss-2-s-c4360614','vg-iss-2-s-c4360617','vg-iss-2-s-c4360621','vg-iss-2-s-c4360625','vg-iss-2-s-c4360629','vg-iss-2-s-c4360632','vg-iss-2-s-c4360815','vg-iss-2-s-c4360819','vg-iss-2-s-c4360823','vg-iss-2-s-c4360826','vg-iss-2-s-c4360830','vg-iss-2-s-c4360834','vg-iss-2-s-c4360838','vg-iss-2-s-c4360841','vg-iss-2-s-c4360845','vg-iss-2-s-c4360849','vg-iss-2-s-c4360853','vg-iss-2-s-c4360856','vg-iss-2-s-c4360904','vg-iss-2-s-c4360908','vg-iss-2-s-c4360911','vg-iss-2-s-c4361016','vg-iss-2-s-c4361020','vg-iss-2-s-c4361024','vg-iss-2-s-c4361028','vg-iss-2-s-c4361032','vg-iss-2-s-c4361036','vg-iss-2-s-c4361040','vg-iss-2-s-c4361044','vg-iss-2-s-c4361048','vg-iss-2-s-c4361054','vg-iss-2-s-c4361058','vg-iss-2-s-c4361102','vg-iss-2-s-c4361105','vg-iss-2-s-c4361109','vg-iss-2-s-c4361113','vg-iss-2-s-c4361117','vg-iss-2-s-c4361120','vg-iss-2-s-c4361124','vg-iss-2-s-c4361128','vg-iss-2-s-c4361132','vg-iss-2-s-c4361135','vg-iss-2-s-c4361139','vg-iss-2-s-c4361143') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`file_number`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', `expire_date` = '2026-11-25 13:34:58.766869' WHERE `django_session`.`session_key` = 'kr5pbwf5oa4rtqlxa5ti0clogrjm8q8m';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/gallery_page_1 __api/dataimages.json?page=1&limit=100&reqno=1
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('9zo1xnn0oydgvvpszoqvjqizfe632jeo', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', '2026-11-25 13:34:58.790982');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = '**previewimages' LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_general`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo' ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', `expire_date` = '2026-11-25 13:34:58.810907' WHERE `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/gallery_page_10 __api/dataimages.json?page=10&limit=100&reqno=1
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:58.821657' AND `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_general`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo' ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', `expire_date` = '2026-11-25 13:34:58.834295' WHERE `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/images_page_1 api/images.json?page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:58.849044' AND `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images` FROM `obs_general` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', `expire_date` = '2026-11-25 13:34:58.853345' WHERE `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/images_page_10 api/images.json?page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:58.868022' AND `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo') LIMIT 21;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images` FROM `obs_general` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', `expire_date` = '2026-11-25 13:34:58.872429' WHERE `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/detail __initdetail/co-iss-w1477654052.html
-- statement: connection 17
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrumentid' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`old_slug` = 'instrumentid' LIMIT 21;
-- statement: connection 17
SELECT `obs_pds`.`primary_filespec` AS `primary_filespec` FROM `obs_pds` WHERE `obs_pds`.`obs_general_id` = 329600 LIMIT 21;
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:58.889307' AND `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo') LIMIT 21;
-- statement: connection 17
SELECT `cart`.`id`, `cart`.`session_id`, `cart`.`obs_general_id`, `cart`.`opus_id`, `cart`.`recycled`, `cart`.`timestamp` FROM `cart` WHERE (`cart`.`opus_id` = 'co-iss-w1477654052' AND `cart`.`recycled` = 0 AND `cart`.`session_id` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 17
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE ((`obs_files`.`short_name` = 'browse_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'browse_full' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_full' AND `obs_files`.`version_name` = 'Current')) AND `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`file_number`;
-- statement: connection 17
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`file_number`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', `expire_date` = '2026-11-25 13:34:58.891969' WHERE `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/image_med api/image/med/co-iss-w1477654052.json
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-11 13:34:58.902705' AND `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 17
None;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 15;
-- statement: connection 17
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 15 FOR UPDATE;
-- statement: connection 17
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 15,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
UPDATE user_searches SET result_count = 1, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 15;
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images` FROM `obs_general` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 15) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xR8Ta:fv7jAA4ZU1wJw-Ba7-0pHfrTm-MBU3Ne0JxZQYZsMgk', `expire_date` = '2026-11-25 13:34:58.930997' WHERE `django_session`.`session_key` = '9zo1xnn0oydgvvpszoqvjqizfe632jeo';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
