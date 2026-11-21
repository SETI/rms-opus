-- Captured by benchmarks/bench_db.py --dump-queries from the harness-owned server.
-- Regenerate it; do not edit it.

-- block: search.empty/result_count __api/meta/result_count.json?reqno=1
-- statement: connection 129
SET NAMES utf8mb4;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT VERSION(),
                       @@sql_mode,
                       @@default_storage_engine,
                       @@sql_auto_is_null,
                       @@lower_case_table_names,
                       CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL;
-- statement: connection 129
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 1,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general`;
-- statement: connection 129
UPDATE user_searches SET result_count = 29752, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 1;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.broad/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 2,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0;
-- statement: connection 129
UPDATE user_searches SET result_count = 29730, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 2;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.selective/result_count __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 129
SELECT `mult_field`.`qualified_name` AS `qualified_name`, `mult_field`.`field_id` AS `field_id` FROM `mult_field`;
-- statement: connection 129
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 5;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 129
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`physical_table`, `table_names`.`target_name` FROM `table_names` ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 3,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5);
-- statement: connection 129
UPDATE user_searches SET result_count = 171, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 3;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.ring_radius/result_count __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius2') LIMIT 21;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 4,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0;
-- statement: connection 129
UPDATE user_searches SET result_count = 11139, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 4;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.target/result_count __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 129
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 8;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 5,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE EXISTS (SELECT 1 FROM `obs_general_target_name` WHERE `obs_general_target_name`.`obs_general_id`=`obs_general`.`id` AND `obs_general_target_name`.`mult_id` IN (1));
-- statement: connection 129
UPDATE user_searches SET result_count = 5062, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 5;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.surface_geometry/result_count __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'surfacegeometrytargetname' LIMIT 21;
-- statement: connection 129
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 87;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude2') LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 6,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (6)));
-- statement: connection 129
UPDATE user_searches SET result_count = 4338, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 6;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.complex/result_count __api/meta/result_count.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 129
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 2;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'instrument_id') LIMIT 21;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 7,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 WHERE (`obs_general`.`instrument_id` IN (1)) AND (EXISTS (SELECT 1 FROM `obs_general_target_name` WHERE `obs_general_target_name`.`obs_general_id`=`obs_general`.`id` AND `obs_general_target_name`.`mult_id` IN (1))) AND (`obs_general`.`time2` >= 126187232.0e0 AND `obs_general`.`time1` <= 568036837.0e0) AND (`obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0) AND (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (6)));
-- statement: connection 129
UPDATE user_searches SET result_count = 1971, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 7;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.ring_opening/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&RINGGEOobserverringopeningangle1=-10&RINGGEOobserverringopeningangle2=10&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOobserverringopeningangle1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'observer_ring_opening_angle') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 8;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'observer_ring_opening_angle1') LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'observer_ring_opening_angle2') LIMIT 21;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 8 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 8,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE (`obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0) AND (`obs_ring_geometry`.`observer_ring_opening_angle2` >= -10.0e0 AND `obs_ring_geometry`.`observer_ring_opening_angle1` <= 10.0e0);
-- statement: connection 129
UPDATE user_searches SET result_count = 8608, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 8;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: search.ring_opening_year/result_count __api/meta/result_count.json?time1=2009-01-01T00:00:00&time2=2010-01-01T00:00:00&RINGGEOobserverringopeningangle1=-10&RINGGEOobserverringopeningangle2=10&reqno=1
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 9;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 9 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 9,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE (`obs_general`.`time2` >= 284040034.0e0 AND `obs_general`.`time1` <= 315576034.0e0) AND (`obs_ring_geometry`.`observer_ring_opening_angle2` >= -10.0e0 AND `obs_ring_geometry`.`observer_ring_opening_angle1` <= 10.0e0);
-- statement: connection 129
UPDATE user_searches SET result_count = 10, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 9;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: pages.empty/build __api/meta/result_count.json?reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;

-- block: pages.empty/page_1 api/data.json?page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '4modbq8y01e26sm8lje79qg9ps4swtt5' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('4modbq8y01e26sm8lje79qg9ps4swtt5', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.542882');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'observationduration' LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.558015' WHERE `django_session`.`session_key` = '4modbq8y01e26sm8lje79qg9ps4swtt5';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.empty/page_10 api/data.json?page=10&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.562660' AND `django_session`.`session_key` = '4modbq8y01e26sm8lje79qg9ps4swtt5') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.576064' WHERE `django_session`.`session_key` = '4modbq8y01e26sm8lje79qg9ps4swtt5';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.empty/page_last api/data.json?page=298&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.580750' AND `django_session`.`session_key` = '4modbq8y01e26sm8lje79qg9ps4swtt5') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 29701 AND 29800 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.585273' WHERE `django_session`.`session_key` = '4modbq8y01e26sm8lje79qg9ps4swtt5';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.broad/build __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;

-- block: pages.broad/page_1 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'ue8cvjpraqbprw6m8g2okuav772cszyv' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('ue8cvjpraqbprw6m8g2okuav772cszyv', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.607110');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.617416' WHERE `django_session`.`session_key` = 'ue8cvjpraqbprw6m8g2okuav772cszyv';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.broad/page_10 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=10&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.622596' AND `django_session`.`session_key` = 'ue8cvjpraqbprw6m8g2okuav772cszyv') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.632701' WHERE `django_session`.`session_key` = 'ue8cvjpraqbprw6m8g2okuav772cszyv';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.broad/page_last api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=298&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.637466' AND `django_session`.`session_key` = 'ue8cvjpraqbprw6m8g2okuav772cszyv') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 29701 AND 29800 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.643892' WHERE `django_session`.`session_key` = 'ue8cvjpraqbprw6m8g2okuav772cszyv';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.selective/build __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;

-- block: pages.selective/page_1 api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'q5lnsbakv7iwef9cynvi6e2nr3t12cb7' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('q5lnsbakv7iwef9cynvi6e2nr3t12cb7', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.663591');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.673934' WHERE `django_session`.`session_key` = 'q5lnsbakv7iwef9cynvi6e2nr3t12cb7';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.selective/page_10 api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.679320' AND `django_session`.`session_key` = 'q5lnsbakv7iwef9cynvi6e2nr3t12cb7') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 101 AND 200 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.685604' WHERE `django_session`.`session_key` = 'q5lnsbakv7iwef9cynvi6e2nr3t12cb7';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.selective/page_last api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.688902' AND `django_session`.`session_key` = 'q5lnsbakv7iwef9cynvi6e2nr3t12cb7') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 101 AND 200 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.695657' WHERE `django_session`.`session_key` = 'q5lnsbakv7iwef9cynvi6e2nr3t12cb7';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.ring_radius/build __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;

-- block: pages.ring_radius/page_1 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '0b89vnlf9umzq2fnub7pmemyg35m6to2' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('0b89vnlf9umzq2fnub7pmemyg35m6to2', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.712608');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 4) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.719679' WHERE `django_session`.`session_key` = '0b89vnlf9umzq2fnub7pmemyg35m6to2';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.ring_radius/page_10 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=10&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.722803' AND `django_session`.`session_key` = '0b89vnlf9umzq2fnub7pmemyg35m6to2') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 4) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.729687' WHERE `django_session`.`session_key` = '0b89vnlf9umzq2fnub7pmemyg35m6to2';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.ring_radius/page_last api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=112&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.732716' AND `django_session`.`session_key` = '0b89vnlf9umzq2fnub7pmemyg35m6to2') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 4) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 11101 AND 11200 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.736713' WHERE `django_session`.`session_key` = '0b89vnlf9umzq2fnub7pmemyg35m6to2';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.target/build __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;

-- block: pages.target/page_1 api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '6878qtlga45sidp5skefdeaj5wa2i38h' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('6878qtlga45sidp5skefdeaj5wa2i38h', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.755511');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 5) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.762601' WHERE `django_session`.`session_key` = '6878qtlga45sidp5skefdeaj5wa2i38h';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.target/page_10 api/data.json?target=Saturn&page=10&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.766373' AND `django_session`.`session_key` = '6878qtlga45sidp5skefdeaj5wa2i38h') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 5) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.773287' WHERE `django_session`.`session_key` = '6878qtlga45sidp5skefdeaj5wa2i38h';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.target/page_last api/data.json?target=Saturn&page=51&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.776349' AND `django_session`.`session_key` = '6878qtlga45sidp5skefdeaj5wa2i38h') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 5) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 5001 AND 5100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.781308' WHERE `django_session`.`session_key` = '6878qtlga45sidp5skefdeaj5wa2i38h';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.surface_geometry/build __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;

-- block: pages.surface_geometry/page_1 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'bywelakco5m5n1od6q0oiarm36b7ngxx' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('bywelakco5m5n1od6q0oiarm36b7ngxx', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.798925');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 6) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.806184' WHERE `django_session`.`session_key` = 'bywelakco5m5n1od6q0oiarm36b7ngxx';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.surface_geometry/page_10 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=10&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.809523' AND `django_session`.`session_key` = 'bywelakco5m5n1od6q0oiarm36b7ngxx') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 6) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.816565' WHERE `django_session`.`session_key` = 'bywelakco5m5n1od6q0oiarm36b7ngxx';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.surface_geometry/page_last api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=44&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.820087' AND `django_session`.`session_key` = 'bywelakco5m5n1od6q0oiarm36b7ngxx') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 6) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 4301 AND 4400 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.823894' WHERE `django_session`.`session_key` = 'bywelakco5m5n1od6q0oiarm36b7ngxx';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.complex/build __api/meta/result_count.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;

-- block: pages.complex/page_1 api/data.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'h0yb0q37zwndyeeahok803ddbm9ojj8z' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('h0yb0q37zwndyeeahok803ddbm9ojj8z', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.844309');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.854258' WHERE `django_session`.`session_key` = 'h0yb0q37zwndyeeahok803ddbm9ojj8z';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.complex/page_10 api/data.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=10&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.857905' AND `django_session`.`session_key` = 'h0yb0q37zwndyeeahok803ddbm9ojj8z') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.867968' WHERE `django_session`.`session_key` = 'h0yb0q37zwndyeeahok803ddbm9ojj8z';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.complex/page_last api/data.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=20&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.871499' AND `django_session`.`session_key` = 'h0yb0q37zwndyeeahok803ddbm9ojj8z') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1901 AND 2000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.880821' WHERE `django_session`.`session_key` = 'h0yb0q37zwndyeeahok803ddbm9ojj8z';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.complex_geometry/build __api/meta/result_count.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;

-- block: pages.complex_geometry/page_1 api/data.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&cols=opusid,instrument,target,time1,COISSfilter,RINGGEOringradius1,RINGGEOringradius2,SURFACEGEOsaturn_planetographiclatitude1,SURFACEGEOsaturn_planetographiclatitude2&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'nrav3h5n1oqzl7r3rd88bpco1fqbh3hn' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('nrav3h5n1oqzl7r3rd88bpco1fqbh3hn', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.899773');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'COISSfilter' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius2' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude2' LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`mult_obs_instrument_coiss_combined_filter`.`label`,`obs_ring_geometry`.`ring_radius1`,`obs_ring_geometry`.`ring_radius2`,`obs_surface_geometry__saturn`.`planetographic_latitude1`,`obs_surface_geometry__saturn`.`planetographic_latitude2` FROM `obs_general` LEFT JOIN `obs_instrument_coiss` ON `obs_general`.`id`=`obs_instrument_coiss`.`obs_general_id` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_instrument_coiss_combined_filter` ON `mult_obs_instrument_coiss_combined_filter`.`field_id` = 17 AND `mult_obs_instrument_coiss_combined_filter`.`id`=`obs_instrument_coiss`.`combined_filter` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.947268' WHERE `django_session`.`session_key` = 'nrav3h5n1oqzl7r3rd88bpco1fqbh3hn';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.complex_geometry/page_10 api/data.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&cols=opusid,instrument,target,time1,COISSfilter,RINGGEOringradius1,RINGGEOringradius2,SURFACEGEOsaturn_planetographiclatitude1,SURFACEGEOsaturn_planetographiclatitude2&page=10&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.951991' AND `django_session`.`session_key` = 'nrav3h5n1oqzl7r3rd88bpco1fqbh3hn') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`mult_obs_instrument_coiss_combined_filter`.`label`,`obs_ring_geometry`.`ring_radius1`,`obs_ring_geometry`.`ring_radius2`,`obs_surface_geometry__saturn`.`planetographic_latitude1`,`obs_surface_geometry__saturn`.`planetographic_latitude2` FROM `obs_general` LEFT JOIN `obs_instrument_coiss` ON `obs_general`.`id`=`obs_instrument_coiss`.`obs_general_id` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_instrument_coiss_combined_filter` ON `mult_obs_instrument_coiss_combined_filter`.`field_id` = 17 AND `mult_obs_instrument_coiss_combined_filter`.`id`=`obs_instrument_coiss`.`combined_filter` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.962636' WHERE `django_session`.`session_key` = 'nrav3h5n1oqzl7r3rd88bpco1fqbh3hn';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: pages.complex_geometry/page_last api/data.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&cols=opusid,instrument,target,time1,COISSfilter,RINGGEOringradius1,RINGGEOringradius2,SURFACEGEOsaturn_planetographiclatitude1,SURFACEGEOsaturn_planetographiclatitude2&page=20&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.965890' AND `django_session`.`session_key` = 'nrav3h5n1oqzl7r3rd88bpco1fqbh3hn') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`mult_obs_instrument_coiss_combined_filter`.`label`,`obs_ring_geometry`.`ring_radius1`,`obs_ring_geometry`.`ring_radius2`,`obs_surface_geometry__saturn`.`planetographic_latitude1`,`obs_surface_geometry__saturn`.`planetographic_latitude2` FROM `obs_general` LEFT JOIN `obs_instrument_coiss` ON `obs_general`.`id`=`obs_instrument_coiss`.`obs_general_id` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_instrument_coiss_combined_filter` ON `mult_obs_instrument_coiss_combined_filter`.`field_id` = 17 AND `mult_obs_instrument_coiss_combined_filter`.`id`=`obs_instrument_coiss`.`combined_filter` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1901 AND 2000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.975170' WHERE `django_session`.`session_key` = 'nrav3h5n1oqzl7r3rd88bpco1fqbh3hn';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.empty/default_order api/data.json?page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'd0q1r9ipb67ie5ctxnak282620tx20pu' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('d0q1r9ipb67ie5ctxnak282620tx20pu', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', '2026-12-01 22:39:57.989037');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqH:I2ZA8Tu7Q1rm32Mn3AJEA6chmKhRVXX2rqz_ViQ7Hoo', `expire_date` = '2026-12-01 22:39:57.996354' WHERE `django_session`.`session_key` = 'd0q1r9ipb67ie5ctxnak282620tx20pu';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.empty/resorted api/data.json?order=-time1,opusid&page=1&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:57.999669' AND `django_session`.`session_key` = 'd0q1r9ipb67ie5ctxnak282620tx20pu') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 10;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 10 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 10,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general`;
-- statement: connection 129
UPDATE user_searches SET result_count = 29752, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 10;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 10) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 10;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.088610' WHERE `django_session`.`session_key` = 'd0q1r9ipb67ie5ctxnak282620tx20pu';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.broad/default_order api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '63dxnqyd6hvxc9dwutjk6wz2e8rsfemq' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('63dxnqyd6hvxc9dwutjk6wz2e8rsfemq', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', '2026-12-01 22:39:58.103040');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.114331' WHERE `django_session`.`session_key` = '63dxnqyd6hvxc9dwutjk6wz2e8rsfemq';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.broad/resorted api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&order=-time1,opusid&page=1&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:58.117675' AND `django_session`.`session_key` = '63dxnqyd6hvxc9dwutjk6wz2e8rsfemq') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 11;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 11 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 11,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0;
-- statement: connection 129
UPDATE user_searches SET result_count = 29730, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 11;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 11) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 11;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.212891' WHERE `django_session`.`session_key` = '63dxnqyd6hvxc9dwutjk6wz2e8rsfemq';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.selective/default_order api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'kndn78yfdil2dxr4c1mji6fo3lm3kssb' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('kndn78yfdil2dxr4c1mji6fo3lm3kssb', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', '2026-12-01 22:39:58.227395');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.234663' WHERE `django_session`.`session_key` = 'kndn78yfdil2dxr4c1mji6fo3lm3kssb';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.selective/resorted api/data.json?planet=Uranus&order=-time1,opusid&page=1&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:58.238105' AND `django_session`.`session_key` = 'kndn78yfdil2dxr4c1mji6fo3lm3kssb') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 12;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 12 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 12,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5);
-- statement: connection 129
UPDATE user_searches SET result_count = 171, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 12;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 12) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 12;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.248642' WHERE `django_session`.`session_key` = 'kndn78yfdil2dxr4c1mji6fo3lm3kssb';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.ring_radius/default_order api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '6ssxef8sdwjlgz8zmycapmmpzh8d4w9y' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('6ssxef8sdwjlgz8zmycapmmpzh8d4w9y', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', '2026-12-01 22:39:58.262531');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 4) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 4;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.269799' WHERE `django_session`.`session_key` = '6ssxef8sdwjlgz8zmycapmmpzh8d4w9y';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.ring_radius/resorted api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&order=-time1,opusid&page=1&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:58.273127' AND `django_session`.`session_key` = '6ssxef8sdwjlgz8zmycapmmpzh8d4w9y') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 13,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0;
-- statement: connection 129
UPDATE user_searches SET result_count = 11139, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 13;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 13) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 13;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.324944' WHERE `django_session`.`session_key` = '6ssxef8sdwjlgz8zmycapmmpzh8d4w9y';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.target/default_order api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '3bjggzskqbuaut0n6gtmkop3ym1ap0v6' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('3bjggzskqbuaut0n6gtmkop3ym1ap0v6', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', '2026-12-01 22:39:58.339223');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 5) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 5;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.346638' WHERE `django_session`.`session_key` = '3bjggzskqbuaut0n6gtmkop3ym1ap0v6';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.target/resorted api/data.json?target=Saturn&order=-time1,opusid&page=1&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:58.350196' AND `django_session`.`session_key` = '3bjggzskqbuaut0n6gtmkop3ym1ap0v6') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 14;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 14 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 14,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE EXISTS (SELECT 1 FROM `obs_general_target_name` WHERE `obs_general_target_name`.`obs_general_id`=`obs_general`.`id` AND `obs_general_target_name`.`mult_id` IN (1));
-- statement: connection 129
UPDATE user_searches SET result_count = 5062, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 14;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 14) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 14;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.379061' WHERE `django_session`.`session_key` = '3bjggzskqbuaut0n6gtmkop3ym1ap0v6';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.surface_geometry/default_order api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'lt7d4pebq0xrte1dnadp5wxmkeaklhw5' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('lt7d4pebq0xrte1dnadp5wxmkeaklhw5', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', '2026-12-01 22:39:58.397969');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 6) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 6;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.405070' WHERE `django_session`.`session_key` = 'lt7d4pebq0xrte1dnadp5wxmkeaklhw5';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.surface_geometry/resorted api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&order=-time1,opusid&page=1&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:58.408499' AND `django_session`.`session_key` = 'lt7d4pebq0xrte1dnadp5wxmkeaklhw5') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 15;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 15 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 15,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (6)));
-- statement: connection 129
UPDATE user_searches SET result_count = 4338, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 15;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 15) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 15;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.441863' WHERE `django_session`.`session_key` = 'lt7d4pebq0xrte1dnadp5wxmkeaklhw5';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.complex/default_order api/data.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '8infkayml9yzuknlcodw3dyd68soqwjq' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('8infkayml9yzuknlcodw3dyd68soqwjq', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', '2026-12-01 22:39:58.455900');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.465729' WHERE `django_session`.`session_key` = '8infkayml9yzuknlcodw3dyd68soqwjq';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: resort.complex/resorted api/data.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&order=-time1,opusid&page=1&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:58.469028' AND `django_session`.`session_key` = '8infkayml9yzuknlcodw3dyd68soqwjq') LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 16;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 16 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 16,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 WHERE (`obs_general`.`instrument_id` IN (1)) AND (EXISTS (SELECT 1 FROM `obs_general_target_name` WHERE `obs_general_target_name`.`obs_general_id`=`obs_general`.`id` AND `obs_general_target_name`.`mult_id` IN (1))) AND (`obs_general`.`time2` >= 126187232.0e0 AND `obs_general`.`time1` <= 568036837.0e0) AND (`obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0) AND (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (6)));
-- statement: connection 129
UPDATE user_searches SET result_count = 1971, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 16;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 16) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 16;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqI:l_GPFB5xzUawe4HRwBCBYktAr6frRoBHhXk_VIAqEmA', `expire_date` = '2026-12-01 22:39:58.514119' WHERE `django_session`.`session_key` = '8infkayml9yzuknlcodw3dyd68soqwjq';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: fanout.empty/result_count __api/meta/result_count.json?reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;

-- block: fanout.empty/mults_instrument __api/meta/mults/instrument.json?reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general` GROUP BY `obs_general`.`instrument_id`;

-- block: fanout.empty/mults_observationtype __api/meta/mults/observationtype.json?reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'observationtype' LIMIT 21;
-- statement: connection 129
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 4;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general` GROUP BY `obs_general`.`observation_type`;

-- block: fanout.empty/mults_target __api/meta/mults/target.json?reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `pending_generation`,`revertible` FROM `schema_version`;
-- statement: connection 129
SELECT `obs_general_target_name`.`mult_id`,COUNT(*) AS `target_name__count` FROM `obs_general_target_name` GROUP BY `obs_general_target_name`.`mult_id`;

-- block: fanout.empty/endpoints_time1 __api/meta/range/endpoints/time1.json?reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 129
SELECT MIN(`obs_general`.`time1`),MAX(`obs_general`.`time2`) FROM `obs_general`;
-- statement: connection 129
SELECT COUNT(*) FROM `obs_general` WHERE `obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL;

-- block: fanout.empty/menu __menu.json?reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_ring_geometry', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_wavelength', 'obs_type_image', 'obs_profile') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOsolarringopeningangle1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOobserverringopeningangle1' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `definitions`.`context` AS `context`, `definitions`.`term` AS `term`, `definitions`.`definition` AS `definition` FROM `definitions`;

-- block: fanout.selected/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 17;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 17 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 17,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`planet_id` IN (4)) AND (`obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0);
-- statement: connection 129
UPDATE user_searches SET result_count = 17119, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 17;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;

-- block: fanout.selected/mults_instrument __api/meta/mults/instrument.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 17;
-- statement: connection 129
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 17) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`instrument_id`;

-- block: fanout.selected/mults_observationtype __api/meta/mults/observationtype.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 17;
-- statement: connection 129
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 17) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`observation_type`;

-- block: fanout.selected/mults_target __api/meta/mults/target.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 17;
-- statement: connection 129
SELECT `obs_general_target_name`.`mult_id`,COUNT(*) AS `target_name__count` FROM `obs_general_target_name`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 17) AS `results` WHERE `obs_general_target_name`.`obs_general_id`=`results`.`id` GROUP BY `obs_general_target_name`.`mult_id`;

-- block: fanout.selected/endpoints_time1 __api/meta/range/endpoints/time1.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 18;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 18 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 18,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (4);
-- statement: connection 129
UPDATE user_searches SET result_count = 17119, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 18;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT MIN(`obs_general`.`time1`),MAX(`obs_general`.`time2`) FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 18) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 129
SELECT COUNT(*) FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 18) AS `results` WHERE `obs_general`.`id`=`results`.`id` AND `obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL;

-- block: fanout.selected/menu __menu.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 17;
-- statement: connection 129
SELECT `partables`.`id`, `partables`.`trigger_tab`, `partables`.`trigger_col`, `partables`.`trigger_val`, `partables`.`partable` FROM `partables`;
-- statement: connection 129
SELECT DISTINCT `obs_general`.`mission_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 17) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 129
SELECT DISTINCT `obs_general`.`instrument_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 17) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 129
SELECT DISTINCT `obs_general`.`inst_host_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 17) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_type_image', 'obs_wavelength', 'obs_profile', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_ring_geometry') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;

-- block: fanout.complex/result_count __api/meta/result_count.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;

-- block: fanout.complex/mults_instrument __api/meta/mults/instrument.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 19;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 19 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 19,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 WHERE (EXISTS (SELECT 1 FROM `obs_general_target_name` WHERE `obs_general_target_name`.`obs_general_id`=`obs_general`.`id` AND `obs_general_target_name`.`mult_id` IN (1))) AND (`obs_general`.`time2` >= 126187232.0e0 AND `obs_general`.`time1` <= 568036837.0e0) AND (`obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0) AND (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (6)));
-- statement: connection 129
UPDATE user_searches SET result_count = 2283, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 19;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 19) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`instrument_id`;

-- block: fanout.complex/mults_observationtype __api/meta/mults/observationtype.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`observation_type`;

-- block: fanout.complex/mults_target __api/meta/mults/target.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 20;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 20 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 20,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 WHERE (`obs_general`.`instrument_id` IN (1)) AND (`obs_general`.`time2` >= 126187232.0e0 AND `obs_general`.`time1` <= 568036837.0e0) AND (`obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0) AND (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (6)));
-- statement: connection 129
UPDATE user_searches SET result_count = 2564, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 20;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general_target_name`.`mult_id`,COUNT(*) AS `target_name__count` FROM `obs_general_target_name`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 20) AS `results` WHERE `obs_general_target_name`.`obs_general_id`=`results`.`id` GROUP BY `obs_general_target_name`.`mult_id`;

-- block: fanout.complex/endpoints_time1 __api/meta/range/endpoints/time1.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 21;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 21 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 21,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` AND `obs_surface_geometry__saturn`.`target_name` = 6 WHERE (`obs_general`.`instrument_id` IN (1)) AND (EXISTS (SELECT 1 FROM `obs_general_target_name` WHERE `obs_general_target_name`.`obs_general_id`=`obs_general`.`id` AND `obs_general_target_name`.`mult_id` IN (1))) AND (`obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0) AND (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND `obs_surface_geometry_name`.`target_name` IN (6)));
-- statement: connection 129
UPDATE user_searches SET result_count = 1971, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 21;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT MIN(`obs_general`.`time1`),MAX(`obs_general`.`time2`) FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 21) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 129
SELECT COUNT(*) FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 21) AS `results` WHERE `obs_general`.`id`=`results`.`id` AND `obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL;

-- block: fanout.complex/menu __menu.json?time1=2004-01-01T00:00:00&time2=2018-01-01T00:00:00&instrument=Cassini+ISS&target=Saturn&RINGGEOringradius1=60000&RINGGEOringradius2=140000&surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 7;
-- statement: connection 129
SELECT DISTINCT `obs_general`.`mission_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 129
SELECT DISTINCT `obs_general`.`instrument_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 129
SELECT DISTINCT `obs_general`.`inst_host_id` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 7) AS `results` WHERE `obs_general`.`id`=`results`.`id`;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_type_image', 'obs_wavelength', 'obs_profile', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_surface_geometry__saturn', 'obs_ring_geometry', 'obs_mission_cassini', 'obs_instrument_coiss') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Planetographic Latitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Planetocentric Latitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'West Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'East Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole & Limb') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_mission_cassini' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_instrument_coiss' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'duration' LIMIT 21;

-- block: mults.broad/build __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;

-- block: mults.broad/mults_instrument __api/meta/mults/instrument.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`instrument_id`;

-- block: mults.broad/mults_observationtype __api/meta/mults/observationtype.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`observation_type`;

-- block: mults.broad/mults_target __api/meta/mults/target.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_general_target_name`.`mult_id`,COUNT(*) AS `target_name__count` FROM `obs_general_target_name`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` WHERE `obs_general_target_name`.`obs_general_id`=`results`.`id` GROUP BY `obs_general_target_name`.`mult_id`;

-- block: mults.broad/mults_imagetype __api/meta/mults/imagetype.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'imagetype' LIMIT 21;
-- statement: connection 129
SELECT `mult`.`id` AS `id`, `mult`.`value` AS `value`, `mult`.`label` AS `label`, `mult`.`disp_rank` AS `disp_rank` FROM `mult` WHERE `mult`.`field_id` = 88;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_type_image`.`image_type_id`,COUNT(*) AS `image_type_id__count` FROM `obs_type_image`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` WHERE `obs_type_image`.`obs_general_id`=`results`.`id` GROUP BY `obs_type_image`.`image_type_id`;

-- block: mults.selective/build __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;

-- block: mults.selective/mults_instrument __api/meta/mults/instrument.json?planet=Uranus&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`instrument_id`;

-- block: mults.selective/mults_observationtype __api/meta/mults/observationtype.json?planet=Uranus&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` WHERE `obs_general`.`id`=`results`.`id` GROUP BY `obs_general`.`observation_type`;

-- block: mults.selective/mults_target __api/meta/mults/target.json?planet=Uranus&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `obs_general_target_name`.`mult_id`,COUNT(*) AS `target_name__count` FROM `obs_general_target_name`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` WHERE `obs_general_target_name`.`obs_general_id`=`results`.`id` GROUP BY `obs_general_target_name`.`mult_id`;

-- block: mults.selective/mults_imagetype __api/meta/mults/imagetype.json?planet=Uranus&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 3;
-- statement: connection 129
SELECT `obs_type_image`.`image_type_id`,COUNT(*) AS `image_type_id__count` FROM `obs_type_image`,(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 3) AS `results` WHERE `obs_type_image`.`obs_general_id`=`results`.`id` GROUP BY `obs_type_image`.`image_type_id`;

-- block: widget.planet/widget __widget/planet.html
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 129
SELECT `mult`.`field_id`, `mult`.`id`, `mult`.`value`, `mult`.`label`, `mult`.`pin`, `mult`.`disp_rank`, `mult`.`display`, `mult`.`grouping` FROM `mult` WHERE (`mult`.`field_id` = 5 AND `mult`.`grouping` IS NULL);
-- statement: connection 129
SELECT `mult`.`field_id`, `mult`.`id`, `mult`.`value`, `mult`.`label`, `mult`.`pin`, `mult`.`disp_rank`, `mult`.`display`, `mult`.`grouping` FROM `mult` WHERE (`mult`.`display` = 'Y' AND `mult`.`field_id` = 5 AND `mult`.`grouping` IS NULL) ORDER BY `mult`.`disp_rank` ASC;
-- statement: connection 129
SELECT `mult`.`field_id`, `mult`.`id`, `mult`.`value`, `mult`.`label`, `mult`.`pin`, `mult`.`disp_rank`, `mult`.`display`, `mult`.`grouping` FROM `mult` WHERE (`mult`.`field_id` = 5 AND `mult`.`display` = 'Y') ORDER BY `mult`.`disp_rank` ASC;
-- statement: connection 129
SELECT `mult_group`.`grouping` AS `grouping` FROM `mult_group` WHERE `mult_group`.`field_id` = 5 ORDER BY `mult_group`.`group_rank` ASC;

-- block: categories/categories api/categories/co-iss-w1477654052.json
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_pds` INNER JOIN `obs_general` ON (`obs_pds`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_type_image` INNER JOIN `obs_general` ON (`obs_type_image`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_wavelength` INNER JOIN `obs_general` ON (`obs_wavelength`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_profile` INNER JOIN `obs_general` ON (`obs_profile`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_surface_geometry` INNER JOIN `obs_general` ON (`obs_surface_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT `obs_surface_geometry_target`.`target_name` AS `target_name` FROM `obs_surface_geometry_target` INNER JOIN `obs_general` ON (`obs_surface_geometry_target`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_ring_geometry` INNER JOIN `obs_general` ON (`obs_ring_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_mission_cassini` INNER JOIN `obs_general` ON (`obs_mission_cassini`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_mission_galileo` INNER JOIN `obs_general` ON (`obs_mission_galileo`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_mission_hubble` INNER JOIN `obs_general` ON (`obs_mission_hubble`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_mission_new_horizons` INNER JOIN `obs_general` ON (`obs_mission_new_horizons`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_mission_voyager` INNER JOIN `obs_general` ON (`obs_mission_voyager`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_instrument_cocirs` INNER JOIN `obs_general` ON (`obs_instrument_cocirs`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_instrument_coiss` INNER JOIN `obs_general` ON (`obs_instrument_coiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_instrument_couvis` INNER JOIN `obs_general` ON (`obs_instrument_couvis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_instrument_covims` INNER JOIN `obs_general` ON (`obs_instrument_covims`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_instrument_gossi` INNER JOIN `obs_general` ON (`obs_instrument_gossi`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_instrument_nhlorri` INNER JOIN `obs_general` ON (`obs_instrument_nhlorri`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_instrument_nhmvic` INNER JOIN `obs_general` ON (`obs_instrument_nhmvic`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;
-- statement: connection 129
SELECT 1 AS `a` FROM `obs_instrument_vgiss` INNER JOIN `obs_general` ON (`obs_instrument_vgiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 1;

-- block: autocomplete.bundleid/build __api/meta/result_count.json?reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;

-- block: autocomplete.bundleid/prefix_2 __api/stringsearchchoices/bundleid.json?bundleid=CO&reqno=1
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'bundleid' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`name` = 'bundle_id') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_pds`.`obs_general_id`=`results`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%CO%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: autocomplete.bundleid/prefix_6 __api/stringsearchchoices/bundleid.json?bundleid=COISS_&reqno=1
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_pds`.`obs_general_id`=`results`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%COISS\\_%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: files.broad/one_observation api/files/co-iss-w1477654052.json
-- statement: connection 129
SELECT `pending_generation`,`revertible` FROM `schema_version`;
-- statement: connection 129
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`file_number`;

-- block: files.broad/search_page_1 api/files.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'e1530boddqwfjx52x2zlvs1z0wk2jv6p' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('e1530boddqwfjx52x2zlvs1z0wk2jv6p', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', '2026-12-01 22:39:59.460871');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
SELECT `obs_general`.`opus_id` FROM `obs_general` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT `pending_generation`,`revertible` FROM `schema_version`;
-- statement: connection 129
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('vg-iss-1-s-prof','vg-uvs-1-s-occ-1980-317-iother-e','vg-rss-1-s-occ-1980-318-s63-e','vg-rss-1-s-occ-1980-318-x63-e','vg-iss-2-s-c4360001','vg-iss-2-s-c4360004','vg-iss-2-s-c4360007','vg-iss-2-s-c4360010','vg-iss-2-s-c4360018','vg-iss-2-s-c4360022','vg-iss-2-s-c4360026','vg-iss-2-s-c4360029','vg-iss-2-s-c4360033','vg-iss-2-s-c4360037','vg-iss-2-s-c4360041','vg-iss-2-s-c4360044','vg-iss-2-s-c4360048','vg-iss-2-s-c4360052','vg-iss-2-s-c4360056','vg-iss-2-s-c4360059','vg-iss-2-s-c4360103','vg-iss-2-s-c4360107','vg-iss-2-s-c4360111','vg-iss-2-s-c4360114','vg-iss-2-s-c4360257','vg-iss-2-s-c4360301','vg-iss-2-s-c4360305','vg-iss-2-s-c4360308','vg-iss-2-s-c4360312','vg-iss-2-s-c4360316','vg-iss-2-s-c4360320','vg-iss-2-s-c4360323','vg-iss-2-s-c4360327','vg-iss-2-s-c4360331','vg-iss-2-s-c4360335','vg-iss-2-s-c4360338','vg-iss-2-s-c4360342','vg-iss-2-s-c4360346','vg-iss-2-s-c4360350','vg-iss-2-s-c4360353','vg-iss-2-s-c4360507','vg-iss-2-s-c4360511','vg-iss-2-s-c4360515','vg-iss-2-s-c4360519','vg-iss-2-s-c4360523','vg-iss-2-s-c4360527','vg-iss-2-s-c4360536','vg-iss-2-s-c4360540','vg-iss-2-s-c4360544','vg-iss-2-s-c4360547','vg-iss-2-s-c4360551','vg-iss-2-s-c4360555','vg-iss-2-s-c4360559','vg-iss-2-s-c4360602','vg-iss-2-s-c4360606','vg-iss-2-s-c4360610','vg-iss-2-s-c4360614','vg-iss-2-s-c4360617','vg-iss-2-s-c4360621','vg-iss-2-s-c4360625','vg-iss-2-s-c4360629','vg-iss-2-s-c4360632','vg-iss-2-s-c4360815','vg-iss-2-s-c4360819','vg-iss-2-s-c4360823','vg-iss-2-s-c4360826','vg-iss-2-s-c4360830','vg-iss-2-s-c4360834','vg-iss-2-s-c4360838','vg-iss-2-s-c4360841','vg-iss-2-s-c4360845','vg-iss-2-s-c4360849','vg-iss-2-s-c4360853','vg-iss-2-s-c4360856','vg-iss-2-s-c4360904','vg-iss-2-s-c4360908','vg-iss-2-s-c4360911','vg-iss-2-s-c4361016','vg-iss-2-s-c4361020','vg-iss-2-s-c4361024','vg-iss-2-s-c4361028','vg-iss-2-s-c4361032','vg-iss-2-s-c4361036','vg-iss-2-s-c4361040','vg-iss-2-s-c4361044','vg-iss-2-s-c4361048','vg-iss-2-s-c4361054','vg-iss-2-s-c4361058','vg-iss-2-s-c4361102','vg-iss-2-s-c4361105','vg-iss-2-s-c4361109','vg-iss-2-s-c4361113','vg-iss-2-s-c4361117','vg-iss-2-s-c4361120','vg-iss-2-s-c4361124','vg-iss-2-s-c4361128','vg-iss-2-s-c4361132','vg-iss-2-s-c4361135','vg-iss-2-s-c4361139','vg-iss-2-s-c4361143') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`file_number`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 2;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', `expire_date` = '2026-12-01 22:39:59.502700' WHERE `django_session`.`session_key` = 'e1530boddqwfjx52x2zlvs1z0wk2jv6p';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: previews.empty/gallery_page_1 __api/dataimages.json?page=1&limit=100&reqno=1
-- statement: connection 129
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu' LIMIT 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('5eg9ci1cweeaiwfb4zebq86j1qqjwxuu', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', '2026-12-01 22:39:59.517749');
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = '**previewimages' LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_preview`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `obs_preview` ON `obs_general`.`id`=`obs_preview`.`obs_general_id` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu' ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', `expire_date` = '2026-12-01 22:39:59.531572' WHERE `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: previews.empty/gallery_page_10 __api/dataimages.json?page=10&limit=100&reqno=1
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:59.536595' AND `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_preview`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `obs_preview` ON `obs_general`.`id`=`obs_preview`.`obs_general_id` LEFT JOIN `mult` AS `mult_obs_general_instrument_id` ON `mult_obs_general_instrument_id`.`field_id` = 2 AND `mult_obs_general_instrument_id`.`id`=`obs_general`.`instrument_id` LEFT JOIN `mult` AS `mult_obs_general_planet_id` ON `mult_obs_general_planet_id`.`field_id` = 5 AND `mult_obs_general_planet_id`.`id`=`obs_general`.`planet_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu' ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', `expire_date` = '2026-12-01 22:39:59.548223' WHERE `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: previews.empty/images_page_1 api/images.json?page=1&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:59.551755' AND `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`obs_preview`.`preview_images` FROM `obs_general` LEFT JOIN `obs_preview` ON `obs_general`.`id`=`obs_preview`.`obs_general_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', `expire_date` = '2026-12-01 22:39:59.556478' WHERE `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: previews.empty/images_page_10 api/images.json?page=10&limit=100
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:59.559766' AND `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu') LIMIT 21;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`obs_preview`.`preview_images` FROM `obs_general` LEFT JOIN `obs_preview` ON `obs_general`.`id`=`obs_preview`.`obs_general_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `results`.`sort_order`;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', `expire_date` = '2026-12-01 22:39:59.562991' WHERE `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: previews.empty/detail __initdetail/co-iss-w1477654052.html
-- statement: connection 129
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'instrumentid' LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`old_slug` = 'instrumentid' LIMIT 21;
-- statement: connection 129
SELECT `obs_pds`.`primary_filespec` AS `primary_filespec` FROM `obs_pds` WHERE `obs_pds`.`obs_general_id` = 329600 LIMIT 21;
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:59.570794' AND `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu') LIMIT 21;
-- statement: connection 129
SELECT `cart`.`id`, `cart`.`session_id`, `cart`.`obs_general_id`, `cart`.`opus_id`, `cart`.`recycled` FROM `cart` WHERE (`cart`.`opus_id` = 'co-iss-w1477654052' AND `cart`.`recycled` = 0 AND `cart`.`session_id` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu') LIMIT 21;
-- statement: connection 129
SELECT `obs_preview`.`obs_general_id`, `obs_preview`.`preview_images` FROM `obs_preview` INNER JOIN `obs_general` ON (`obs_preview`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 129
SELECT `obs_preview`.`obs_general_id`, `obs_preview`.`preview_images` FROM `obs_preview` INNER JOIN `obs_general` ON (`obs_preview`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 129
SELECT `pending_generation`,`revertible` FROM `schema_version`;
-- statement: connection 129
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE ((`obs_files`.`short_name` = 'browse_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'browse_full' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_full' AND `obs_files`.`version_name` = 'Current')) AND `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`file_number`;
-- statement: connection 129
SELECT `pending_generation`,`revertible` FROM `schema_version`;
-- statement: connection 129
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`file_number`;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', `expire_date` = '2026-12-01 22:39:59.573820' WHERE `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;

-- block: previews.empty/image_med api/image/med/co-iss-w1477654052.json
-- statement: connection 129
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-17 22:39:59.577631' AND `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu') LIMIT 21;
-- statement: connection 129
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 129
None;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 22;
-- statement: connection 129
SELECT @@SESSION.innodb_lock_wait_timeout;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 270;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 22 FOR UPDATE;
-- statement: connection 129
INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) SELECT 22,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 129
UPDATE user_searches SET result_count = 1, results_built_at = UTC_TIMESTAMP(), last_used_at = UTC_TIMESTAMP() WHERE id = 22;
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
-- statement: connection 129
SET SESSION innodb_lock_wait_timeout = 50;
-- statement: connection 129
SELECT `obs_general`.`opus_id`,`obs_preview`.`preview_images` FROM `obs_general` LEFT JOIN `obs_preview` ON `obs_general`.`id`=`obs_preview`.`obs_general_id` INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` = 22) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` BETWEEN 1 AND 100 ORDER BY `results`.`sort_order`;
-- statement: connection 129
set autocommit=0;
-- statement: connection 129
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xTRqJ:k8gs7eJkMe1B4u4Xxj743P_TwU47E2EP-4UMnrYFHwQ', `expire_date` = '2026-12-01 22:39:59.583652' WHERE `django_session`.`session_key` = '5eg9ci1cweeaiwfb4zebq86j1qqjwxuu';
-- statement: connection 129
commit;
-- statement: connection 129
set autocommit=1;
