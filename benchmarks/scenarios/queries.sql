-- Captured by benchmarks/bench_db.py --dump-queries from the harness-owned server.
-- Regenerate it; do not edit it.

-- block: search.empty/result_count __api/meta/result_count.json?reqno=1
-- statement: connection 15
SET NAMES utf8mb4;
-- statement: connection 15
set autocommit=0;
-- statement: connection 15
set autocommit=1;
-- statement: connection 15
SELECT VERSION(),
                       @@sql_mode,
                       @@default_storage_engine,
                       @@sql_auto_is_null,
                       @@lower_case_table_names,
                       CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL;
-- statement: connection 15
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 15
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 15
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 15
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{}', '99914b932bd37a50b983c5e7c90ae93b', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 15
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 15
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 15
CREATE TABLE `cache_1`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 15
SELECT COUNT(*) FROM `cache_1`;

-- block: search.broad/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 16
SET NAMES utf8mb4;
-- statement: connection 16
set autocommit=0;
-- statement: connection 16
set autocommit=1;
-- statement: connection 16
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 16
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 16
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 16
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'f004842dd5ce1e4a6c4c68e89b50dd11', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 16
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 16
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 16
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 16
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 16
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 16
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 16
CREATE TABLE `cache_2`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0 ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 16
SELECT COUNT(*) FROM `cache_2`;

-- block: search.selective/result_count __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 17
SET NAMES utf8mb4;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 17
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Uranus\"]}', '033bcdee4b74d22264a9cf8648d2a2fc', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 17
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 17
CREATE TABLE `cache_3`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_3`;

-- block: search.ring_radius/result_count __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 18
SET NAMES utf8mb4;
-- statement: connection 18
set autocommit=0;
-- statement: connection 18
set autocommit=1;
-- statement: connection 18
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 18
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 18
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 18
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_ring_geometry.ring_radius1\": [60000.0], \"obs_ring_geometry.ring_radius2\": [140000.0]}', '3e9f393e09dfa2c750cdae5be4a34297', '{\"obs_ring_geometry.ring_radius\": [\"any\"]}', 'd58efe915310b90c76b4d3e3c419cba8', '{\"obs_ring_geometry.ring_radius\": [\"km\"]}', '70f0bb7407a66538767b4dee465f5022', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 18
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 18
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 18
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 18
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius2') LIMIT 21;
-- statement: connection 18
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 18
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 18
CREATE TABLE `cache_4`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0 ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 18
SELECT COUNT(*) FROM `cache_4`;

-- block: search.target/result_count __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 19
SET NAMES utf8mb4;
-- statement: connection 19
set autocommit=0;
-- statement: connection 19
set autocommit=1;
-- statement: connection 19
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 19
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 19
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 19
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.target_name\": [\"Saturn\"]}', '0808ab16043b8e7fcebb7ff7ab9500d9', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 19
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 19
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 19
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 19
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 19
CREATE TABLE `cache_5`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,'1') ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 19
SELECT COUNT(*) FROM `cache_5`;

-- block: search.surface_geometry/result_count __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 20
SET NAMES utf8mb4;
-- statement: connection 20
set autocommit=0;
-- statement: connection 20
set autocommit=1;
-- statement: connection 20
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'surfacegeometrytargetname' LIMIT 21;
-- statement: connection 20
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 20
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_surface_geometry__saturn.planetographic_latitude1\": [-30.0], \"obs_surface_geometry__saturn.planetographic_latitude2\": [30.0], \"obs_surface_geometry_name.target_name\": [\"Saturn\"]}', '907ec5896a8bd3771dd91f22743140d1', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"any\"]}', '2998cdc1c9b87c33e7ac2c27b2011182', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"degrees\"]}', '77ac08a838ce071f52f224163fc043dc', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude2') LIMIT 21;
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 20
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 20
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 20
CREATE TABLE `cache_6`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` LEFT JOIN `obs_surface_geometry_name` ON `obs_general`.`id`=`obs_surface_geometry_name`.`obs_general_id` WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (`obs_surface_geometry_name`.`target_name` IN (6)) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 20
SELECT COUNT(*) FROM `cache_6`;

-- block: pages.empty/build __api/meta/result_count.json?reqno=1
-- statement: connection 21
SET NAMES utf8mb4;
-- statement: connection 21
set autocommit=0;
-- statement: connection 21
set autocommit=1;
-- statement: connection 21
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- block: pages.empty/page_1 api/data.json?page=1&limit=100
-- statement: connection 22
SET NAMES utf8mb4;
-- statement: connection 22
set autocommit=0;
-- statement: connection 22
set autocommit=1;
-- statement: connection 22
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 22
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'jl87l4yzsrw11i2geyjduwt7du19d5pk' LIMIT 1;
-- statement: connection 22
set autocommit=0;
-- statement: connection 22
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('jl87l4yzsrw11i2geyjduwt7du19d5pk', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', '2026-11-19 15:23:15.363486');
-- statement: connection 22
commit;
-- statement: connection 22
set autocommit=1;
-- statement: connection 22
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 22
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 22
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 22
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 22
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 22
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 22
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 22
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 22
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationduration' LIMIT 21;
-- statement: connection 22
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 22
CREATE TEMPORARY TABLE `temp_cache_1_3177634_1793892195_378956` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 22
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_3177634_1793892195_378956` ON `obs_general`.`id`=`temp_cache_1_3177634_1793892195_378956`.`id` ORDER BY `temp_cache_1_3177634_1793892195_378956`.`sort_order`;
-- statement: connection 22
DROP TABLE `temp_cache_1_3177634_1793892195_378956`;
-- statement: connection 22
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 48;
-- statement: connection 22
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 47;
-- statement: connection 22
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0;
-- statement: connection 22
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 2;
-- statement: connection 22
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1;
-- statement: connection 22
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 10;
-- statement: connection 22
set autocommit=0;
-- statement: connection 22
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.388999' WHERE `django_session`.`session_key` = 'jl87l4yzsrw11i2geyjduwt7du19d5pk';
-- statement: connection 22
commit;
-- statement: connection 22
set autocommit=1;

-- block: pages.empty/page_10 api/data.json?page=10&limit=100
-- statement: connection 23
SET NAMES utf8mb4;
-- statement: connection 23
set autocommit=0;
-- statement: connection 23
set autocommit=1;
-- statement: connection 23
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 23
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.393654' AND `django_session`.`session_key` = 'jl87l4yzsrw11i2geyjduwt7du19d5pk') LIMIT 21;
-- statement: connection 23
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 23
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 23
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 23
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 23
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 23
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 23
CREATE TEMPORARY TABLE `temp_cache_1_3177634_1793892195_397470` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 23
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_3177634_1793892195_397470` ON `obs_general`.`id`=`temp_cache_1_3177634_1793892195_397470`.`id` ORDER BY `temp_cache_1_3177634_1793892195_397470`.`sort_order`;
-- statement: connection 23
DROP TABLE `temp_cache_1_3177634_1793892195_397470`;
-- statement: connection 23
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 4;
-- statement: connection 23
set autocommit=0;
-- statement: connection 23
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.406785' WHERE `django_session`.`session_key` = 'jl87l4yzsrw11i2geyjduwt7du19d5pk';
-- statement: connection 23
commit;
-- statement: connection 23
set autocommit=1;

-- block: pages.empty/page_last api/data.json?page=298&limit=100
-- statement: connection 24
SET NAMES utf8mb4;
-- statement: connection 24
set autocommit=0;
-- statement: connection 24
set autocommit=1;
-- statement: connection 24
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 24
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.410623' AND `django_session`.`session_key` = 'jl87l4yzsrw11i2geyjduwt7du19d5pk') LIMIT 21;
-- statement: connection 24
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 24
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 24
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 24
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 24
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 24
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 24
CREATE TEMPORARY TABLE `temp_cache_1_3177634_1793892195_412970` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 29700;
-- statement: connection 24
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_3177634_1793892195_412970` ON `obs_general`.`id`=`temp_cache_1_3177634_1793892195_412970`.`id` ORDER BY `temp_cache_1_3177634_1793892195_412970`.`sort_order`;
-- statement: connection 24
DROP TABLE `temp_cache_1_3177634_1793892195_412970`;
-- statement: connection 24
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 3;
-- statement: connection 24
set autocommit=0;
-- statement: connection 24
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.418400' WHERE `django_session`.`session_key` = 'jl87l4yzsrw11i2geyjduwt7du19d5pk';
-- statement: connection 24
commit;
-- statement: connection 24
set autocommit=1;

-- block: pages.broad/build __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 25
SET NAMES utf8mb4;
-- statement: connection 25
set autocommit=0;
-- statement: connection 25
set autocommit=1;
-- statement: connection 25
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 25
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 25
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;

-- block: pages.broad/page_1 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 26
SET NAMES utf8mb4;
-- statement: connection 26
set autocommit=0;
-- statement: connection 26
set autocommit=1;
-- statement: connection 26
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 26
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '4ag0mfl04z908e6kxzcliduqlr22rx11' LIMIT 1;
-- statement: connection 26
set autocommit=0;
-- statement: connection 26
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('4ag0mfl04z908e6kxzcliduqlr22rx11', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', '2026-11-19 15:23:15.438990');
-- statement: connection 26
commit;
-- statement: connection 26
set autocommit=1;
-- statement: connection 26
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 26
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 26
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 26
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 26
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 26
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 26
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 26
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 26
CREATE TEMPORARY TABLE `temp_cache_2_3177634_1793892195_444381` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 26
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_2_3177634_1793892195_444381` ON `obs_general`.`id`=`temp_cache_2_3177634_1793892195_444381`.`id` ORDER BY `temp_cache_2_3177634_1793892195_444381`.`sort_order`;
-- statement: connection 26
DROP TABLE `temp_cache_2_3177634_1793892195_444381`;
-- statement: connection 26
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 26
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 26
set autocommit=0;
-- statement: connection 26
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.453535' WHERE `django_session`.`session_key` = '4ag0mfl04z908e6kxzcliduqlr22rx11';
-- statement: connection 26
commit;
-- statement: connection 26
set autocommit=1;

-- block: pages.broad/page_10 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=10&limit=100
-- statement: connection 27
SET NAMES utf8mb4;
-- statement: connection 27
set autocommit=0;
-- statement: connection 27
set autocommit=1;
-- statement: connection 27
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 27
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.456897' AND `django_session`.`session_key` = '4ag0mfl04z908e6kxzcliduqlr22rx11') LIMIT 21;
-- statement: connection 27
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 27
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 27
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 27
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 27
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 27
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 27
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 27
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 27
CREATE TEMPORARY TABLE `temp_cache_2_3177634_1793892195_462542` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 27
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_2_3177634_1793892195_462542` ON `obs_general`.`id`=`temp_cache_2_3177634_1793892195_462542`.`id` ORDER BY `temp_cache_2_3177634_1793892195_462542`.`sort_order`;
-- statement: connection 27
DROP TABLE `temp_cache_2_3177634_1793892195_462542`;
-- statement: connection 27
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 41;
-- statement: connection 27
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 27
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 27
set autocommit=0;
-- statement: connection 27
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.471814' WHERE `django_session`.`session_key` = '4ag0mfl04z908e6kxzcliduqlr22rx11';
-- statement: connection 27
commit;
-- statement: connection 27
set autocommit=1;

-- block: pages.broad/page_last api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=298&limit=100
-- statement: connection 28
SET NAMES utf8mb4;
-- statement: connection 28
set autocommit=0;
-- statement: connection 28
set autocommit=1;
-- statement: connection 28
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 28
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.475134' AND `django_session`.`session_key` = '4ag0mfl04z908e6kxzcliduqlr22rx11') LIMIT 21;
-- statement: connection 28
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 28
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 28
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 28
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 28
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 28
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 28
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 28
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 28
CREATE TEMPORARY TABLE `temp_cache_2_3177634_1793892195_480541` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 29700;
-- statement: connection 28
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_2_3177634_1793892195_480541` ON `obs_general`.`id`=`temp_cache_2_3177634_1793892195_480541`.`id` ORDER BY `temp_cache_2_3177634_1793892195_480541`.`sort_order`;
-- statement: connection 28
DROP TABLE `temp_cache_2_3177634_1793892195_480541`;
-- statement: connection 28
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 28
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 28
set autocommit=0;
-- statement: connection 28
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.487960' WHERE `django_session`.`session_key` = '4ag0mfl04z908e6kxzcliduqlr22rx11';
-- statement: connection 28
commit;
-- statement: connection 28
set autocommit=1;

-- block: pages.selective/build __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 29
SET NAMES utf8mb4;
-- statement: connection 29
set autocommit=0;
-- statement: connection 29
set autocommit=1;
-- statement: connection 29
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 29
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));

-- block: pages.selective/page_1 api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 30
SET NAMES utf8mb4;
-- statement: connection 30
set autocommit=0;
-- statement: connection 30
set autocommit=1;
-- statement: connection 30
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 30
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'i6lmt2apxa9k6vs630d7eedv29yi57xh' LIMIT 1;
-- statement: connection 30
set autocommit=0;
-- statement: connection 30
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('i6lmt2apxa9k6vs630d7eedv29yi57xh', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', '2026-11-19 15:23:15.505648');
-- statement: connection 30
commit;
-- statement: connection 30
set autocommit=1;
-- statement: connection 30
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 30
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 30
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 30
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 30
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 30
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 30
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 30
CREATE TEMPORARY TABLE `temp_cache_3_3177634_1793892195_510140` SELECT `sort_order`,`id` FROM `cache_3` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 30
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_3_3177634_1793892195_510140` ON `obs_general`.`id`=`temp_cache_3_3177634_1793892195_510140`.`id` ORDER BY `temp_cache_3_3177634_1793892195_510140`.`sort_order`;
-- statement: connection 30
DROP TABLE `temp_cache_3_3177634_1793892195_510140`;
-- statement: connection 30
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 30
set autocommit=0;
-- statement: connection 30
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.518124' WHERE `django_session`.`session_key` = 'i6lmt2apxa9k6vs630d7eedv29yi57xh';
-- statement: connection 30
commit;
-- statement: connection 30
set autocommit=1;

-- block: pages.selective/page_10 api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 31
SET NAMES utf8mb4;
-- statement: connection 31
set autocommit=0;
-- statement: connection 31
set autocommit=1;
-- statement: connection 31
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 31
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.525198' AND `django_session`.`session_key` = 'i6lmt2apxa9k6vs630d7eedv29yi57xh') LIMIT 21;
-- statement: connection 31
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 31
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 31
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 31
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 31
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 31
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 31
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 31
CREATE TEMPORARY TABLE `temp_cache_3_3177634_1793892195_527763` SELECT `sort_order`,`id` FROM `cache_3` ORDER BY `sort_order` LIMIT 100 OFFSET 100;
-- statement: connection 31
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_3_3177634_1793892195_527763` ON `obs_general`.`id`=`temp_cache_3_3177634_1793892195_527763`.`id` ORDER BY `temp_cache_3_3177634_1793892195_527763`.`sort_order`;
-- statement: connection 31
DROP TABLE `temp_cache_3_3177634_1793892195_527763`;
-- statement: connection 31
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 31
set autocommit=0;
-- statement: connection 31
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.532297' WHERE `django_session`.`session_key` = 'i6lmt2apxa9k6vs630d7eedv29yi57xh';
-- statement: connection 31
commit;
-- statement: connection 31
set autocommit=1;

-- block: pages.selective/page_last api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 32
SET NAMES utf8mb4;
-- statement: connection 32
set autocommit=0;
-- statement: connection 32
set autocommit=1;
-- statement: connection 32
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 32
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.535460' AND `django_session`.`session_key` = 'i6lmt2apxa9k6vs630d7eedv29yi57xh') LIMIT 21;
-- statement: connection 32
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 32
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 32
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 32
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 32
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 32
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 32
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 32
CREATE TEMPORARY TABLE `temp_cache_3_3177634_1793892195_538018` SELECT `sort_order`,`id` FROM `cache_3` ORDER BY `sort_order` LIMIT 100 OFFSET 100;
-- statement: connection 32
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_3_3177634_1793892195_538018` ON `obs_general`.`id`=`temp_cache_3_3177634_1793892195_538018`.`id` ORDER BY `temp_cache_3_3177634_1793892195_538018`.`sort_order`;
-- statement: connection 32
DROP TABLE `temp_cache_3_3177634_1793892195_538018`;
-- statement: connection 32
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 32
set autocommit=0;
-- statement: connection 32
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.542550' WHERE `django_session`.`session_key` = 'i6lmt2apxa9k6vs630d7eedv29yi57xh';
-- statement: connection 32
commit;
-- statement: connection 32
set autocommit=1;

-- block: pages.ring_radius/build __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 33
SET NAMES utf8mb4;
-- statement: connection 33
set autocommit=0;
-- statement: connection 33
set autocommit=1;
-- statement: connection 33
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 33
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 33
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;

-- block: pages.ring_radius/page_1 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 34
SET NAMES utf8mb4;
-- statement: connection 34
set autocommit=0;
-- statement: connection 34
set autocommit=1;
-- statement: connection 34
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 34
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '6staccwqpyb3nep34tjsuzgnlurni6fr' LIMIT 1;
-- statement: connection 34
set autocommit=0;
-- statement: connection 34
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('6staccwqpyb3nep34tjsuzgnlurni6fr', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', '2026-11-19 15:23:15.561740');
-- statement: connection 34
commit;
-- statement: connection 34
set autocommit=1;
-- statement: connection 34
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 34
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 34
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 34
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 34
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 34
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 34
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 34
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 34
CREATE TEMPORARY TABLE `temp_cache_4_3177634_1793892195_566092` SELECT `sort_order`,`id` FROM `cache_4` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 34
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_4_3177634_1793892195_566092` ON `obs_general`.`id`=`temp_cache_4_3177634_1793892195_566092`.`id` ORDER BY `temp_cache_4_3177634_1793892195_566092`.`sort_order`;
-- statement: connection 34
DROP TABLE `temp_cache_4_3177634_1793892195_566092`;
-- statement: connection 34
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 34
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 34
set autocommit=0;
-- statement: connection 34
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.574033' WHERE `django_session`.`session_key` = '6staccwqpyb3nep34tjsuzgnlurni6fr';
-- statement: connection 34
commit;
-- statement: connection 34
set autocommit=1;

-- block: pages.ring_radius/page_10 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=10&limit=100
-- statement: connection 35
SET NAMES utf8mb4;
-- statement: connection 35
set autocommit=0;
-- statement: connection 35
set autocommit=1;
-- statement: connection 35
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 35
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.577590' AND `django_session`.`session_key` = '6staccwqpyb3nep34tjsuzgnlurni6fr') LIMIT 21;
-- statement: connection 35
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 35
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 35
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 35
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 35
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 35
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 35
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 35
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 35
CREATE TEMPORARY TABLE `temp_cache_4_3177634_1793892195_581939` SELECT `sort_order`,`id` FROM `cache_4` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 35
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_4_3177634_1793892195_581939` ON `obs_general`.`id`=`temp_cache_4_3177634_1793892195_581939`.`id` ORDER BY `temp_cache_4_3177634_1793892195_581939`.`sort_order`;
-- statement: connection 35
DROP TABLE `temp_cache_4_3177634_1793892195_581939`;
-- statement: connection 35
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 43;
-- statement: connection 35
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 35
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 35
set autocommit=0;
-- statement: connection 35
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.590337' WHERE `django_session`.`session_key` = '6staccwqpyb3nep34tjsuzgnlurni6fr';
-- statement: connection 35
commit;
-- statement: connection 35
set autocommit=1;

-- block: pages.ring_radius/page_last api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=112&limit=100
-- statement: connection 36
SET NAMES utf8mb4;
-- statement: connection 36
set autocommit=0;
-- statement: connection 36
set autocommit=1;
-- statement: connection 36
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 36
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.593787' AND `django_session`.`session_key` = '6staccwqpyb3nep34tjsuzgnlurni6fr') LIMIT 21;
-- statement: connection 36
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 36
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 36
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 36
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 36
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 36
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 36
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 36
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 36
CREATE TEMPORARY TABLE `temp_cache_4_3177634_1793892195_598136` SELECT `sort_order`,`id` FROM `cache_4` ORDER BY `sort_order` LIMIT 100 OFFSET 11100;
-- statement: connection 36
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_4_3177634_1793892195_598136` ON `obs_general`.`id`=`temp_cache_4_3177634_1793892195_598136`.`id` ORDER BY `temp_cache_4_3177634_1793892195_598136`.`sort_order`;
-- statement: connection 36
DROP TABLE `temp_cache_4_3177634_1793892195_598136`;
-- statement: connection 36
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 36
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 36
set autocommit=0;
-- statement: connection 36
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.603739' WHERE `django_session`.`session_key` = '6staccwqpyb3nep34tjsuzgnlurni6fr';
-- statement: connection 36
commit;
-- statement: connection 36
set autocommit=1;

-- block: pages.target/build __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 37
SET NAMES utf8mb4;
-- statement: connection 37
set autocommit=0;
-- statement: connection 37
set autocommit=1;
-- statement: connection 37
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 37
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));

-- block: pages.target/page_1 api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 38
SET NAMES utf8mb4;
-- statement: connection 38
set autocommit=0;
-- statement: connection 38
set autocommit=1;
-- statement: connection 38
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 38
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'p546if6fx4rupizw5kfd8wpnj81b6yeg' LIMIT 1;
-- statement: connection 38
set autocommit=0;
-- statement: connection 38
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('p546if6fx4rupizw5kfd8wpnj81b6yeg', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', '2026-11-19 15:23:15.621338');
-- statement: connection 38
commit;
-- statement: connection 38
set autocommit=1;
-- statement: connection 38
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 38
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 38
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 38
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 38
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 38
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 38
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 38
CREATE TEMPORARY TABLE `temp_cache_5_3177634_1793892195_623659` SELECT `sort_order`,`id` FROM `cache_5` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 38
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_5_3177634_1793892195_623659` ON `obs_general`.`id`=`temp_cache_5_3177634_1793892195_623659`.`id` ORDER BY `temp_cache_5_3177634_1793892195_623659`.`sort_order`;
-- statement: connection 38
DROP TABLE `temp_cache_5_3177634_1793892195_623659`;
-- statement: connection 38
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 38
set autocommit=0;
-- statement: connection 38
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.630546' WHERE `django_session`.`session_key` = 'p546if6fx4rupizw5kfd8wpnj81b6yeg';
-- statement: connection 38
commit;
-- statement: connection 38
set autocommit=1;

-- block: pages.target/page_10 api/data.json?target=Saturn&page=10&limit=100
-- statement: connection 39
SET NAMES utf8mb4;
-- statement: connection 39
set autocommit=0;
-- statement: connection 39
set autocommit=1;
-- statement: connection 39
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 39
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.633999' AND `django_session`.`session_key` = 'p546if6fx4rupizw5kfd8wpnj81b6yeg') LIMIT 21;
-- statement: connection 39
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 39
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 39
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 39
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 39
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 39
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 39
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 39
CREATE TEMPORARY TABLE `temp_cache_5_3177634_1793892195_637013` SELECT `sort_order`,`id` FROM `cache_5` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 39
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_5_3177634_1793892195_637013` ON `obs_general`.`id`=`temp_cache_5_3177634_1793892195_637013`.`id` ORDER BY `temp_cache_5_3177634_1793892195_637013`.`sort_order`;
-- statement: connection 39
DROP TABLE `temp_cache_5_3177634_1793892195_637013`;
-- statement: connection 39
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 39
set autocommit=0;
-- statement: connection 39
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.643106' WHERE `django_session`.`session_key` = 'p546if6fx4rupizw5kfd8wpnj81b6yeg';
-- statement: connection 39
commit;
-- statement: connection 39
set autocommit=1;

-- block: pages.target/page_last api/data.json?target=Saturn&page=51&limit=100
-- statement: connection 40
SET NAMES utf8mb4;
-- statement: connection 40
set autocommit=0;
-- statement: connection 40
set autocommit=1;
-- statement: connection 40
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 40
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.646384' AND `django_session`.`session_key` = 'p546if6fx4rupizw5kfd8wpnj81b6yeg') LIMIT 21;
-- statement: connection 40
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 40
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 40
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 40
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 40
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 40
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 40
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 40
CREATE TEMPORARY TABLE `temp_cache_5_3177634_1793892195_648832` SELECT `sort_order`,`id` FROM `cache_5` ORDER BY `sort_order` LIMIT 100 OFFSET 5000;
-- statement: connection 40
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_5_3177634_1793892195_648832` ON `obs_general`.`id`=`temp_cache_5_3177634_1793892195_648832`.`id` ORDER BY `temp_cache_5_3177634_1793892195_648832`.`sort_order`;
-- statement: connection 40
DROP TABLE `temp_cache_5_3177634_1793892195_648832`;
-- statement: connection 40
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 40
set autocommit=0;
-- statement: connection 40
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.653255' WHERE `django_session`.`session_key` = 'p546if6fx4rupizw5kfd8wpnj81b6yeg';
-- statement: connection 40
commit;
-- statement: connection 40
set autocommit=1;

-- block: pages.surface_geometry/build __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 41
SET NAMES utf8mb4;
-- statement: connection 41
set autocommit=0;
-- statement: connection 41
set autocommit=1;
-- statement: connection 41
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 41
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 41
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 41
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;

-- block: pages.surface_geometry/page_1 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 42
SET NAMES utf8mb4;
-- statement: connection 42
set autocommit=0;
-- statement: connection 42
set autocommit=1;
-- statement: connection 42
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 42
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '183erlvi5698wl22xqvmn38lury1yer7' LIMIT 1;
-- statement: connection 42
set autocommit=0;
-- statement: connection 42
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('183erlvi5698wl22xqvmn38lury1yer7', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', '2026-11-19 15:23:15.674151');
-- statement: connection 42
commit;
-- statement: connection 42
set autocommit=1;
-- statement: connection 42
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 42
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 42
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 42
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 42
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 42
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 42
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 42
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 42
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 42
CREATE TEMPORARY TABLE `temp_cache_6_3177634_1793892195_678987` SELECT `sort_order`,`id` FROM `cache_6` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 42
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_6_3177634_1793892195_678987` ON `obs_general`.`id`=`temp_cache_6_3177634_1793892195_678987`.`id` ORDER BY `temp_cache_6_3177634_1793892195_678987`.`sort_order`;
-- statement: connection 42
DROP TABLE `temp_cache_6_3177634_1793892195_678987`;
-- statement: connection 42
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 42
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 42
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 42
set autocommit=0;
-- statement: connection 42
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.687291' WHERE `django_session`.`session_key` = '183erlvi5698wl22xqvmn38lury1yer7';
-- statement: connection 42
commit;
-- statement: connection 42
set autocommit=1;

-- block: pages.surface_geometry/page_10 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=10&limit=100
-- statement: connection 43
SET NAMES utf8mb4;
-- statement: connection 43
set autocommit=0;
-- statement: connection 43
set autocommit=1;
-- statement: connection 43
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 43
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.690870' AND `django_session`.`session_key` = '183erlvi5698wl22xqvmn38lury1yer7') LIMIT 21;
-- statement: connection 43
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 43
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 43
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 43
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 43
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 43
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 43
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 43
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 43
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 43
CREATE TEMPORARY TABLE `temp_cache_6_3177634_1793892195_695449` SELECT `sort_order`,`id` FROM `cache_6` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 43
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_6_3177634_1793892195_695449` ON `obs_general`.`id`=`temp_cache_6_3177634_1793892195_695449`.`id` ORDER BY `temp_cache_6_3177634_1793892195_695449`.`sort_order`;
-- statement: connection 43
DROP TABLE `temp_cache_6_3177634_1793892195_695449`;
-- statement: connection 43
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 11;
-- statement: connection 43
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 7;
-- statement: connection 43
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 12;
-- statement: connection 43
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 43
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 43
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 43
set autocommit=0;
-- statement: connection 43
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.704150' WHERE `django_session`.`session_key` = '183erlvi5698wl22xqvmn38lury1yer7';
-- statement: connection 43
commit;
-- statement: connection 43
set autocommit=1;

-- block: pages.surface_geometry/page_last api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=44&limit=100
-- statement: connection 44
SET NAMES utf8mb4;
-- statement: connection 44
set autocommit=0;
-- statement: connection 44
set autocommit=1;
-- statement: connection 44
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 44
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.707747' AND `django_session`.`session_key` = '183erlvi5698wl22xqvmn38lury1yer7') LIMIT 21;
-- statement: connection 44
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 44
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 44
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 44
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 44
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 44
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 44
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 44
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 44
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 44
CREATE TEMPORARY TABLE `temp_cache_6_3177634_1793892195_712296` SELECT `sort_order`,`id` FROM `cache_6` ORDER BY `sort_order` LIMIT 100 OFFSET 4300;
-- statement: connection 44
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_6_3177634_1793892195_712296` ON `obs_general`.`id`=`temp_cache_6_3177634_1793892195_712296`.`id` ORDER BY `temp_cache_6_3177634_1793892195_712296`.`sort_order`;
-- statement: connection 44
DROP TABLE `temp_cache_6_3177634_1793892195_712296`;
-- statement: connection 44
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 44
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 44
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 44
set autocommit=0;
-- statement: connection 44
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.717689' WHERE `django_session`.`session_key` = '183erlvi5698wl22xqvmn38lury1yer7';
-- statement: connection 44
commit;
-- statement: connection 44
set autocommit=1;

-- block: resort.empty/default_order api/data.json?page=1&limit=100
-- statement: connection 45
SET NAMES utf8mb4;
-- statement: connection 45
set autocommit=0;
-- statement: connection 45
set autocommit=1;
-- statement: connection 45
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 45
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'kp30bu8howiwnr7q4tdpi42wg5f5tspc' LIMIT 1;
-- statement: connection 45
set autocommit=0;
-- statement: connection 45
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('kp30bu8howiwnr7q4tdpi42wg5f5tspc', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', '2026-11-19 15:23:15.731741');
-- statement: connection 45
commit;
-- statement: connection 45
set autocommit=1;
-- statement: connection 45
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 45
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 45
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 45
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 45
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 45
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 45
CREATE TEMPORARY TABLE `temp_cache_1_3177634_1793892195_733947` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 45
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_3177634_1793892195_733947` ON `obs_general`.`id`=`temp_cache_1_3177634_1793892195_733947`.`id` ORDER BY `temp_cache_1_3177634_1793892195_733947`.`sort_order`;
-- statement: connection 45
DROP TABLE `temp_cache_1_3177634_1793892195_733947`;
-- statement: connection 45
set autocommit=0;
-- statement: connection 45
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.739742' WHERE `django_session`.`session_key` = 'kp30bu8howiwnr7q4tdpi42wg5f5tspc';
-- statement: connection 45
commit;
-- statement: connection 45
set autocommit=1;

-- block: resort.empty/resorted api/data.json?order=-time1,opusid&page=1&limit=100
-- statement: connection 46
SET NAMES utf8mb4;
-- statement: connection 46
set autocommit=0;
-- statement: connection 46
set autocommit=1;
-- statement: connection 46
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 46
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.743960' AND `django_session`.`session_key` = 'kp30bu8howiwnr7q4tdpi42wg5f5tspc') LIMIT 21;
-- statement: connection 46
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 46
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 46
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 46
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 46
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 46
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 46
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{}', '99914b932bd37a50b983c5e7c90ae93b', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 46
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 46
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 46
CREATE TABLE `cache_7`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 46
CREATE TEMPORARY TABLE `temp_cache_7_3177634_1793892195_895544` SELECT `sort_order`,`id` FROM `cache_7` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 46
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_7_3177634_1793892195_895544` ON `obs_general`.`id`=`temp_cache_7_3177634_1793892195_895544`.`id` ORDER BY `temp_cache_7_3177634_1793892195_895544`.`sort_order`;
-- statement: connection 46
DROP TABLE `temp_cache_7_3177634_1793892195_895544`;
-- statement: connection 46
SELECT COUNT(*) FROM `cache_7`;
-- statement: connection 46
set autocommit=0;
-- statement: connection 46
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.903771' WHERE `django_session`.`session_key` = 'kp30bu8howiwnr7q4tdpi42wg5f5tspc';
-- statement: connection 46
commit;
-- statement: connection 46
set autocommit=1;

-- block: resort.broad/default_order api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 47
SET NAMES utf8mb4;
-- statement: connection 47
set autocommit=0;
-- statement: connection 47
set autocommit=1;
-- statement: connection 47
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 47
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'n3rackdsm0u7zyyany7ufsophupjhoge' LIMIT 1;
-- statement: connection 47
set autocommit=0;
-- statement: connection 47
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('n3rackdsm0u7zyyany7ufsophupjhoge', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', '2026-11-19 15:23:15.918152');
-- statement: connection 47
commit;
-- statement: connection 47
set autocommit=1;
-- statement: connection 47
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 47
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 47
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 47
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 47
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 47
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 47
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 47
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 47
CREATE TEMPORARY TABLE `temp_cache_2_3177634_1793892195_924388` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 47
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_2_3177634_1793892195_924388` ON `obs_general`.`id`=`temp_cache_2_3177634_1793892195_924388`.`id` ORDER BY `temp_cache_2_3177634_1793892195_924388`.`sort_order`;
-- statement: connection 47
DROP TABLE `temp_cache_2_3177634_1793892195_924388`;
-- statement: connection 47
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 47
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 47
set autocommit=0;
-- statement: connection 47
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ5:QknSfh0odjFfrJSVuN6pW69sPWlXYsuSOnisC1gPja8', `expire_date` = '2026-11-19 15:23:15.933478' WHERE `django_session`.`session_key` = 'n3rackdsm0u7zyyany7ufsophupjhoge';
-- statement: connection 47
commit;
-- statement: connection 47
set autocommit=1;

-- block: resort.broad/resorted api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&order=-time1,opusid&page=1&limit=100
-- statement: connection 48
SET NAMES utf8mb4;
-- statement: connection 48
set autocommit=0;
-- statement: connection 48
set autocommit=1;
-- statement: connection 48
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 48
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:15.936925' AND `django_session`.`session_key` = 'n3rackdsm0u7zyyany7ufsophupjhoge') LIMIT 21;
-- statement: connection 48
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 48
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 48
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 48
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 48
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 48
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 48
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'f004842dd5ce1e4a6c4c68e89b50dd11', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 48
CREATE TABLE `cache_8`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0 ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 48
CREATE TEMPORARY TABLE `temp_cache_8_3177634_1793892196_115127` SELECT `sort_order`,`id` FROM `cache_8` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 48
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_8_3177634_1793892196_115127` ON `obs_general`.`id`=`temp_cache_8_3177634_1793892196_115127`.`id` ORDER BY `temp_cache_8_3177634_1793892196_115127`.`sort_order`;
-- statement: connection 48
DROP TABLE `temp_cache_8_3177634_1793892196_115127`;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 48
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 48
SELECT COUNT(*) FROM `cache_8`;
-- statement: connection 48
set autocommit=0;
-- statement: connection 48
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.126837' WHERE `django_session`.`session_key` = 'n3rackdsm0u7zyyany7ufsophupjhoge';
-- statement: connection 48
commit;
-- statement: connection 48
set autocommit=1;

-- block: resort.selective/default_order api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 49
SET NAMES utf8mb4;
-- statement: connection 49
set autocommit=0;
-- statement: connection 49
set autocommit=1;
-- statement: connection 49
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 49
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'nfdd8j1ehyzt1un9yi2r84qmirnnask1' LIMIT 1;
-- statement: connection 49
set autocommit=0;
-- statement: connection 49
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('nfdd8j1ehyzt1un9yi2r84qmirnnask1', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', '2026-11-19 15:23:16.141490');
-- statement: connection 49
commit;
-- statement: connection 49
set autocommit=1;
-- statement: connection 49
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 49
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 49
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 49
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 49
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 49
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 49
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 49
CREATE TEMPORARY TABLE `temp_cache_3_3177634_1793892196_144115` SELECT `sort_order`,`id` FROM `cache_3` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 49
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_3_3177634_1793892196_144115` ON `obs_general`.`id`=`temp_cache_3_3177634_1793892196_144115`.`id` ORDER BY `temp_cache_3_3177634_1793892196_144115`.`sort_order`;
-- statement: connection 49
DROP TABLE `temp_cache_3_3177634_1793892196_144115`;
-- statement: connection 49
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 49
set autocommit=0;
-- statement: connection 49
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.150359' WHERE `django_session`.`session_key` = 'nfdd8j1ehyzt1un9yi2r84qmirnnask1';
-- statement: connection 49
commit;
-- statement: connection 49
set autocommit=1;

-- block: resort.selective/resorted api/data.json?planet=Uranus&order=-time1,opusid&page=1&limit=100
-- statement: connection 50
SET NAMES utf8mb4;
-- statement: connection 50
set autocommit=0;
-- statement: connection 50
set autocommit=1;
-- statement: connection 50
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 50
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:16.153509' AND `django_session`.`session_key` = 'nfdd8j1ehyzt1un9yi2r84qmirnnask1') LIMIT 21;
-- statement: connection 50
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 50
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 50
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 50
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 50
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 50
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 50
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 50
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Uranus\"]}', '033bcdee4b74d22264a9cf8648d2a2fc', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 50
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 50
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 50
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 50
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 50
CREATE TABLE `cache_9`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5) ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 50
CREATE TEMPORARY TABLE `temp_cache_9_3177634_1793892196_169097` SELECT `sort_order`,`id` FROM `cache_9` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 50
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_9_3177634_1793892196_169097` ON `obs_general`.`id`=`temp_cache_9_3177634_1793892196_169097`.`id` ORDER BY `temp_cache_9_3177634_1793892196_169097`.`sort_order`;
-- statement: connection 50
DROP TABLE `temp_cache_9_3177634_1793892196_169097`;
-- statement: connection 50
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 50
SELECT COUNT(*) FROM `cache_9`;
-- statement: connection 50
set autocommit=0;
-- statement: connection 50
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.175449' WHERE `django_session`.`session_key` = 'nfdd8j1ehyzt1un9yi2r84qmirnnask1';
-- statement: connection 50
commit;
-- statement: connection 50
set autocommit=1;

-- block: resort.ring_radius/default_order api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 51
SET NAMES utf8mb4;
-- statement: connection 51
set autocommit=0;
-- statement: connection 51
set autocommit=1;
-- statement: connection 51
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 51
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '37kjff0tn6cw4ykbubjdro835lg1i3g1' LIMIT 1;
-- statement: connection 51
set autocommit=0;
-- statement: connection 51
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('37kjff0tn6cw4ykbubjdro835lg1i3g1', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', '2026-11-19 15:23:16.188972');
-- statement: connection 51
commit;
-- statement: connection 51
set autocommit=1;
-- statement: connection 51
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 51
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 51
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 51
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 51
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 51
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 51
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 51
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 51
CREATE TEMPORARY TABLE `temp_cache_4_3177634_1793892196_193040` SELECT `sort_order`,`id` FROM `cache_4` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 51
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_4_3177634_1793892196_193040` ON `obs_general`.`id`=`temp_cache_4_3177634_1793892196_193040`.`id` ORDER BY `temp_cache_4_3177634_1793892196_193040`.`sort_order`;
-- statement: connection 51
DROP TABLE `temp_cache_4_3177634_1793892196_193040`;
-- statement: connection 51
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 51
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 51
set autocommit=0;
-- statement: connection 51
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.200815' WHERE `django_session`.`session_key` = '37kjff0tn6cw4ykbubjdro835lg1i3g1';
-- statement: connection 51
commit;
-- statement: connection 51
set autocommit=1;

-- block: resort.ring_radius/resorted api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&order=-time1,opusid&page=1&limit=100
-- statement: connection 52
SET NAMES utf8mb4;
-- statement: connection 52
set autocommit=0;
-- statement: connection 52
set autocommit=1;
-- statement: connection 52
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 52
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:16.203860' AND `django_session`.`session_key` = '37kjff0tn6cw4ykbubjdro835lg1i3g1') LIMIT 21;
-- statement: connection 52
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 52
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 52
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 52
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 52
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 52
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 52
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_ring_geometry.ring_radius1\": [60000.0], \"obs_ring_geometry.ring_radius2\": [140000.0]}', '3e9f393e09dfa2c750cdae5be4a34297', '{\"obs_ring_geometry.ring_radius\": [\"any\"]}', 'd58efe915310b90c76b4d3e3c419cba8', '{\"obs_ring_geometry.ring_radius\": [\"km\"]}', '70f0bb7407a66538767b4dee465f5022', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius2') LIMIT 21;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 52
CREATE TABLE `cache_10`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0 ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 52
CREATE TEMPORARY TABLE `temp_cache_10_3177634_1793892196_294873` SELECT `sort_order`,`id` FROM `cache_10` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 52
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_10_3177634_1793892196_294873` ON `obs_general`.`id`=`temp_cache_10_3177634_1793892196_294873`.`id` ORDER BY `temp_cache_10_3177634_1793892196_294873`.`sort_order`;
-- statement: connection 52
DROP TABLE `temp_cache_10_3177634_1793892196_294873`;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 52
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 52
SELECT COUNT(*) FROM `cache_10`;
-- statement: connection 52
set autocommit=0;
-- statement: connection 52
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.303535' WHERE `django_session`.`session_key` = '37kjff0tn6cw4ykbubjdro835lg1i3g1';
-- statement: connection 52
commit;
-- statement: connection 52
set autocommit=1;

-- block: resort.target/default_order api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 53
SET NAMES utf8mb4;
-- statement: connection 53
set autocommit=0;
-- statement: connection 53
set autocommit=1;
-- statement: connection 53
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 53
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'bbbel15zc02so2xjsvreya1df3acdkgp' LIMIT 1;
-- statement: connection 53
set autocommit=0;
-- statement: connection 53
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('bbbel15zc02so2xjsvreya1df3acdkgp', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', '2026-11-19 15:23:16.324653');
-- statement: connection 53
commit;
-- statement: connection 53
set autocommit=1;
-- statement: connection 53
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 53
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 53
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 53
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 53
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 53
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 53
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 53
CREATE TEMPORARY TABLE `temp_cache_5_3177634_1793892196_328557` SELECT `sort_order`,`id` FROM `cache_5` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 53
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_5_3177634_1793892196_328557` ON `obs_general`.`id`=`temp_cache_5_3177634_1793892196_328557`.`id` ORDER BY `temp_cache_5_3177634_1793892196_328557`.`sort_order`;
-- statement: connection 53
DROP TABLE `temp_cache_5_3177634_1793892196_328557`;
-- statement: connection 53
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 53
set autocommit=0;
-- statement: connection 53
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.339898' WHERE `django_session`.`session_key` = 'bbbel15zc02so2xjsvreya1df3acdkgp';
-- statement: connection 53
commit;
-- statement: connection 53
set autocommit=1;

-- block: resort.target/resorted api/data.json?target=Saturn&order=-time1,opusid&page=1&limit=100
-- statement: connection 54
SET NAMES utf8mb4;
-- statement: connection 54
set autocommit=0;
-- statement: connection 54
set autocommit=1;
-- statement: connection 54
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 54
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:16.344386' AND `django_session`.`session_key` = 'bbbel15zc02so2xjsvreya1df3acdkgp') LIMIT 21;
-- statement: connection 54
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 54
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 54
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 54
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 54
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 54
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 54
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 54
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.target_name\": [\"Saturn\"]}', '0808ab16043b8e7fcebb7ff7ab9500d9', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 54
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 54
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 54
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 54
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 54
CREATE TABLE `cache_11`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,'1') ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 54
CREATE TEMPORARY TABLE `temp_cache_11_3177634_1793892196_399914` SELECT `sort_order`,`id` FROM `cache_11` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 54
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_11_3177634_1793892196_399914` ON `obs_general`.`id`=`temp_cache_11_3177634_1793892196_399914`.`id` ORDER BY `temp_cache_11_3177634_1793892196_399914`.`sort_order`;
-- statement: connection 54
DROP TABLE `temp_cache_11_3177634_1793892196_399914`;
-- statement: connection 54
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 54
SELECT COUNT(*) FROM `cache_11`;
-- statement: connection 54
set autocommit=0;
-- statement: connection 54
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.406552' WHERE `django_session`.`session_key` = 'bbbel15zc02so2xjsvreya1df3acdkgp';
-- statement: connection 54
commit;
-- statement: connection 54
set autocommit=1;

-- block: resort.surface_geometry/default_order api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 55
SET NAMES utf8mb4;
-- statement: connection 55
set autocommit=0;
-- statement: connection 55
set autocommit=1;
-- statement: connection 55
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 55
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 's1exi4u6lfr30802xuj9t61pj36s16fy' LIMIT 1;
-- statement: connection 55
set autocommit=0;
-- statement: connection 55
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('s1exi4u6lfr30802xuj9t61pj36s16fy', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', '2026-11-19 15:23:16.421036');
-- statement: connection 55
commit;
-- statement: connection 55
set autocommit=1;
-- statement: connection 55
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 55
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 55
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 55
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 55
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 55
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 55
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 55
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 55
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 55
CREATE TEMPORARY TABLE `temp_cache_6_3177634_1793892196_426185` SELECT `sort_order`,`id` FROM `cache_6` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 55
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_6_3177634_1793892196_426185` ON `obs_general`.`id`=`temp_cache_6_3177634_1793892196_426185`.`id` ORDER BY `temp_cache_6_3177634_1793892196_426185`.`sort_order`;
-- statement: connection 55
DROP TABLE `temp_cache_6_3177634_1793892196_426185`;
-- statement: connection 55
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 55
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 55
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 55
set autocommit=0;
-- statement: connection 55
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.434517' WHERE `django_session`.`session_key` = 's1exi4u6lfr30802xuj9t61pj36s16fy';
-- statement: connection 55
commit;
-- statement: connection 55
set autocommit=1;

-- block: resort.surface_geometry/resorted api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&order=-time1,opusid&page=1&limit=100
-- statement: connection 56
SET NAMES utf8mb4;
-- statement: connection 56
set autocommit=0;
-- statement: connection 56
set autocommit=1;
-- statement: connection 56
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 56
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:16.437650' AND `django_session`.`session_key` = 's1exi4u6lfr30802xuj9t61pj36s16fy') LIMIT 21;
-- statement: connection 56
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 56
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 56
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 56
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 56
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 56
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 56
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 56
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_surface_geometry__saturn.planetographic_latitude1\": [-30.0], \"obs_surface_geometry__saturn.planetographic_latitude2\": [30.0], \"obs_surface_geometry_name.target_name\": [\"Saturn\"]}', '907ec5896a8bd3771dd91f22743140d1', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"any\"]}', '2998cdc1c9b87c33e7ac2c27b2011182', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"degrees\"]}', '77ac08a838ce071f52f224163fc043dc', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude2') LIMIT 21;
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 56
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 56
CREATE TABLE `cache_12`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` LEFT JOIN `obs_surface_geometry_name` ON `obs_general`.`id`=`obs_surface_geometry_name`.`obs_general_id` WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (`obs_surface_geometry_name`.`target_name` IN (6)) ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 56
CREATE TEMPORARY TABLE `temp_cache_12_3177634_1793892196_498500` SELECT `sort_order`,`id` FROM `cache_12` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 56
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_12_3177634_1793892196_498500` ON `obs_general`.`id`=`temp_cache_12_3177634_1793892196_498500`.`id` ORDER BY `temp_cache_12_3177634_1793892196_498500`.`sort_order`;
-- statement: connection 56
DROP TABLE `temp_cache_12_3177634_1793892196_498500`;
-- statement: connection 56
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 56
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 56
SELECT COUNT(*) FROM `cache_12`;
-- statement: connection 56
set autocommit=0;
-- statement: connection 56
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ6:jSu8IaJ0j7A37XnAxXwUodegRC4yL3cCcWp87Q5n4H8', `expire_date` = '2026-11-19 15:23:16.512326' WHERE `django_session`.`session_key` = 's1exi4u6lfr30802xuj9t61pj36s16fy';
-- statement: connection 56
commit;
-- statement: connection 56
set autocommit=1;

-- block: fanout.empty/result_count __api/meta/result_count.json?reqno=1
-- statement: connection 57
SET NAMES utf8mb4;
-- statement: connection 57
set autocommit=0;
-- statement: connection 57
set autocommit=1;
-- statement: connection 57
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- block: fanout.empty/mults_instrument __api/meta/mults/instrument.json?reqno=1
-- statement: connection 58
SET NAMES utf8mb4;
-- statement: connection 58
set autocommit=0;
-- statement: connection 58
set autocommit=1;
-- statement: connection 58
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 58
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general` GROUP BY `obs_general`.`instrument_id`;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 0 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 1 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 2 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 3 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 4 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 5 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 6 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 7 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 8 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 9 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 10 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 12 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 13 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 14 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 15 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 16 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 17 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 132 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 134 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 164 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 172 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 204 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 226 LIMIT 21;
-- statement: connection 58
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 500 LIMIT 21;

-- block: fanout.empty/mults_observationtype __api/meta/mults/observationtype.json?reqno=1
-- statement: connection 59
SET NAMES utf8mb4;
-- statement: connection 59
set autocommit=0;
-- statement: connection 59
set autocommit=1;
-- statement: connection 59
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 59
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationtype' LIMIT 21;
-- statement: connection 59
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general` GROUP BY `obs_general`.`observation_type`;
-- statement: connection 59
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 0 LIMIT 21;
-- statement: connection 59
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 4 LIMIT 21;
-- statement: connection 59
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 5 LIMIT 21;
-- statement: connection 59
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 6 LIMIT 21;
-- statement: connection 59
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 3 LIMIT 21;
-- statement: connection 59
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 2 LIMIT 21;
-- statement: connection 59
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 7 LIMIT 21;
-- statement: connection 59
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 8 LIMIT 21;

-- block: fanout.empty/mults_target __api/meta/mults/target.json?reqno=1
-- statement: connection 60
SET NAMES utf8mb4;
-- statement: connection 60
set autocommit=0;
-- statement: connection 60
set autocommit=1;
-- statement: connection 60
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 60
SELECT `obs_general`.`_mult_val_`,COUNT(*) AS `target_name__count` FROM `obs_general` INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]" COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general` GROUP BY `obs_general`.`_mult_val_`;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 2 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 3 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 4 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 5 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 6 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 7 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 8 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 9 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 10 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 11 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 12 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 13 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 14 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 15 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 16 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 17 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 18 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 19 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 20 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 21 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 22 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 23 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 24 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 25 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 26 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 27 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 28 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 29 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 30 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 31 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 32 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 33 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 34 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 35 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 36 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 37 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 38 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 39 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 40 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 41 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 42 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 43 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 44 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 45 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 46 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 47 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 48 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 49 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 50 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 51 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 52 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 53 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 54 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 55 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 56 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 57 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 58 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 59 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 60 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 61 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 62 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 63 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 64 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 65 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 66 LIMIT 21;
-- statement: connection 60
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 67 LIMIT 21;

-- block: fanout.empty/endpoints_time1 __api/meta/range/endpoints/time1.json?reqno=1
-- statement: connection 61
SET NAMES utf8mb4;
-- statement: connection 61
set autocommit=0;
-- statement: connection 61
set autocommit=1;
-- statement: connection 61
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 61
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 61
SELECT MIN(`obs_general`.`time1`) AS `min`, MAX(`obs_general`.`time2`) AS `max` FROM `obs_general`;
-- statement: connection 61
SELECT COUNT(*) AS `__count` FROM `obs_general` WHERE (`obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL);

-- block: fanout.empty/menu __menu.json?reqno=1
-- statement: connection 62
SET NAMES utf8mb4;
-- statement: connection 62
set autocommit=0;
-- statement: connection 62
set autocommit=1;
-- statement: connection 62
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_ring_geometry', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_wavelength', 'obs_type_image', 'obs_profile') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE (`table_names`.`display` = 'Y' AND `table_names`.`table_name` IN ('obs_general', 'obs_pds', 'obs_ring_geometry', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_wavelength', 'obs_type_image', 'obs_profile')) ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOsolarringopeningangle1' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOobserverringopeningangle1' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'TARGET_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'TARGET_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'MISSION_NAME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'MISSION_NAME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_HOST_NAME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_HOST_NAME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_ID') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_ID') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'OBSERVATION_TIME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'OBSERVATION_TIME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_DURATION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_DURATION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'MEASUREMENT_QUANTITY_NAME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'MEASUREMENT_QUANTITY_NAME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'RIGHT_ASCENSION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'RIGHT_ASCENSION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'DECLINATION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'DECLINATION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'BUNDLE_ID') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'BUNDLE_ID') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'DATA_SET_ID') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'DATA_SET_ID') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_ID') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_ID') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRIMARY_LID') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRIMARY_LID') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_CREATION_TIME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_CREATION_TIME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'FILE_SPECIFICATION_NAME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'FILE_SPECIFICATION_NAME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OPUS_ID') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OPUS_ID') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'NOTE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'NOTE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'EXPOSURE_DURATION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'EXPOSURE_DURATION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'GREATER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'GREATER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'LESSER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'LESSER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'INTENSITY_LEVELS') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'INTENSITY_LEVELS') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'IMAGE_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'IMAGE_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRAL_INFORMATION_FLAG') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRAL_INFORMATION_FLAG') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRUM_SIZE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRUM_SIZE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'RECEIVED_POLARIZATION_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'RECEIVED_POLARIZATION_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_TYPE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_DIR') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_DIR') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'BODY_OCCULTATION_FLAG') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'BODY_OCCULTATION_FLAG') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'TEMPORAL_SAMPLING_INTERVAL') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'TEMPORAL_SAMPLING_INTERVAL') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DATA_QUALITY_SCORE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DATA_QUALITY_SCORE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DETECTABLE_OPTICAL_DEPTH') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DETECTABLE_OPTICAL_DEPTH') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'WAVELENGTH_BAND') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'WAVELENGTH_BAND') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_SOURCE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_SOURCE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_RECEIVER_HOST') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_RECEIVER_HOST') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_surface_geometry_name' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_surface_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_LIST') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_LIST') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_ASCENDING_NODE_RING_LONGITUDE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_ASCENDING_NODE_RING_LONGITUDE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_J2000_RING_LONGITUDE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_J2000_RING_LONGITUDE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_OBSERVER') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_OBSERVER') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_AZIMUTH') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_AZIMUTH') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DISTANCE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DISTANCE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_DISTANCE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_DISTANCE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_PHASE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_PHASE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_ELEVATION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_ELEVATION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_ELEVATION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_ELEVATION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_PHASE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_PHASE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_RADIUS') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_RADIUS') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_INTERCEPT_DISTANCE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_INTERCEPT_DISTANCE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_ALTITUDE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_ALTITUDE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DIAMETER_IN_PIXELS') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DIAMETER_IN_PIXELS') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_X_COORDINATE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_X_COORDINATE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_Y_COORDINATE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_Y_COORDINATE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_CLOCK_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_CLOCK_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_POSITION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_POSITION_ANGLE') LIMIT 21;
-- statement: connection 62
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_TIME') LIMIT 21;
-- statement: connection 62
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_TIME') LIMIT 21;

-- block: fanout.selected/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 63
SET NAMES utf8mb4;
-- statement: connection 63
set autocommit=0;
-- statement: connection 63
set autocommit=1;
-- statement: connection 63
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 63
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 63
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Saturn\"], \"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'c206354df622b9bebeb095d3bb4039d7', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 63
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 63
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 63
CREATE TABLE `cache_13`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`planet_id` IN (4)) AND (`obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 63
SELECT COUNT(*) FROM `cache_13`;

-- block: fanout.selected/mults_instrument __api/meta/mults/instrument.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 64
SET NAMES utf8mb4;
-- statement: connection 64
set autocommit=0;
-- statement: connection 64
set autocommit=1;
-- statement: connection 64
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 64
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 64
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 64
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`instrument_id`;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 1 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 4 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 0 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 6 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 13 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 132 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 134 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 164 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 500 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 204 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 226 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 2 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 3 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 7 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 9 LIMIT 21;
-- statement: connection 64
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 8 LIMIT 21;

-- block: fanout.selected/mults_observationtype __api/meta/mults/observationtype.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 65
SET NAMES utf8mb4;
-- statement: connection 65
set autocommit=0;
-- statement: connection 65
set autocommit=1;
-- statement: connection 65
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 65
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 65
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 65
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 65
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`observation_type`;
-- statement: connection 65
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 0 LIMIT 21;
-- statement: connection 65
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 4 LIMIT 21;
-- statement: connection 65
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 5 LIMIT 21;
-- statement: connection 65
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 6 LIMIT 21;
-- statement: connection 65
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 2 LIMIT 21;
-- statement: connection 65
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 7 LIMIT 21;
-- statement: connection 65
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 8 LIMIT 21;

-- block: fanout.selected/mults_target __api/meta/mults/target.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 66
SET NAMES utf8mb4;
-- statement: connection 66
set autocommit=0;
-- statement: connection 66
set autocommit=1;
-- statement: connection 66
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 66
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 66
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 66
SELECT `obs_general`.`_mult_val_`,COUNT(*) AS `target_name__count` FROM `obs_general` INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]" COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`_mult_val_`;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 2 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 3 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 4 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 5 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 6 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 7 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 8 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 9 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 10 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 11 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 12 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 13 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 14 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 15 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 16 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 17 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 18 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 19 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 20 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 21 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 22 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 23 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 24 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 25 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 26 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 27 LIMIT 21;
-- statement: connection 66
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 28 LIMIT 21;

-- block: fanout.selected/endpoints_time1 __api/meta/range/endpoints/time1.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 67
SET NAMES utf8mb4;
-- statement: connection 67
set autocommit=0;
-- statement: connection 67
set autocommit=1;
-- statement: connection 67
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 67
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 67
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 67
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 67
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Saturn\"]}', '6b21f5786b92be236703ae293679a2c3', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 67
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 67
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 67
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 67
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 67
CREATE TABLE `cache_14`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (4) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 67
SELECT MIN(`obs_general`.`time1`),MAX(`obs_general`.`time2`) FROM `obs_general`,`cache_14` WHERE `obs_general`.`id`=`cache_14`.`id`;
-- statement: connection 67
SELECT COUNT(*) FROM `obs_general`,`cache_14` WHERE `obs_general`.`id`=`cache_14`.`id` AND `obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL;

-- block: fanout.selected/menu __menu.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 68
SET NAMES utf8mb4;
-- statement: connection 68
set autocommit=0;
-- statement: connection 68
set autocommit=1;
-- statement: connection 68
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 68
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 68
SELECT `partables`.`id`, `partables`.`trigger_tab`, `partables`.`trigger_col`, `partables`.`trigger_val`, `partables`.`partable`, `partables`.`timestamp` FROM `partables`;
-- statement: connection 68
SELECT DISTINCT `obs_general`.`mission_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
-- statement: connection 68
SELECT DISTINCT `obs_general`.`instrument_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
-- statement: connection 68
SELECT DISTINCT `obs_general`.`inst_host_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
-- statement: connection 68
SELECT `table_names`.`table_name` AS `table_name` FROM `table_names` WHERE `table_names`.`table_name` IN ('obs_general', 'obs_pds', 'obs_ring_geometry', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_wavelength', 'obs_type_image', 'obs_profile') ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_type_image', 'obs_wavelength', 'obs_profile', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_ring_geometry') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE (`table_names`.`display` = 'Y' AND `table_names`.`table_name` IN ('obs_general', 'obs_pds', 'obs_type_image', 'obs_wavelength', 'obs_profile', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_ring_geometry')) ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'TARGET_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'TARGET_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'MISSION_NAME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'MISSION_NAME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_HOST_NAME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_HOST_NAME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_ID') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_ID') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'OBSERVATION_TIME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'OBSERVATION_TIME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_DURATION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_DURATION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'MEASUREMENT_QUANTITY_NAME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'MEASUREMENT_QUANTITY_NAME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'RIGHT_ASCENSION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'RIGHT_ASCENSION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'DECLINATION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'DECLINATION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'BUNDLE_ID') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'BUNDLE_ID') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'DATA_SET_ID') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'DATA_SET_ID') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_ID') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_ID') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRIMARY_LID') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRIMARY_LID') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_CREATION_TIME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_CREATION_TIME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'FILE_SPECIFICATION_NAME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'FILE_SPECIFICATION_NAME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OPUS_ID') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OPUS_ID') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'NOTE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'NOTE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'EXPOSURE_DURATION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'EXPOSURE_DURATION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'GREATER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'GREATER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'LESSER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'LESSER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'INTENSITY_LEVELS') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'INTENSITY_LEVELS') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'IMAGE_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'IMAGE_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRAL_INFORMATION_FLAG') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRAL_INFORMATION_FLAG') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRUM_SIZE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRUM_SIZE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'RECEIVED_POLARIZATION_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'RECEIVED_POLARIZATION_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_TYPE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_DIR') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_DIR') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'BODY_OCCULTATION_FLAG') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'BODY_OCCULTATION_FLAG') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'TEMPORAL_SAMPLING_INTERVAL') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'TEMPORAL_SAMPLING_INTERVAL') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DATA_QUALITY_SCORE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DATA_QUALITY_SCORE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DETECTABLE_OPTICAL_DEPTH') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DETECTABLE_OPTICAL_DEPTH') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'WAVELENGTH_BAND') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'WAVELENGTH_BAND') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_SOURCE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_SOURCE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_RECEIVER_HOST') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_RECEIVER_HOST') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_surface_geometry_name' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_surface_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_LIST') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_LIST') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_ASCENDING_NODE_RING_LONGITUDE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_ASCENDING_NODE_RING_LONGITUDE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_J2000_RING_LONGITUDE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_J2000_RING_LONGITUDE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_OBSERVER') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_OBSERVER') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_AZIMUTH') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_AZIMUTH') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DISTANCE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DISTANCE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_DISTANCE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_DISTANCE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_PHASE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_PHASE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_ELEVATION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_ELEVATION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_ELEVATION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_ELEVATION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_PHASE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_PHASE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_RADIUS') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_RADIUS') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_INTERCEPT_DISTANCE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_INTERCEPT_DISTANCE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_ALTITUDE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_ALTITUDE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DIAMETER_IN_PIXELS') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DIAMETER_IN_PIXELS') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_X_COORDINATE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_X_COORDINATE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_Y_COORDINATE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_Y_COORDINATE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_CLOCK_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_CLOCK_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_POSITION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_POSITION_ANGLE') LIMIT 21;
-- statement: connection 68
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_TIME') LIMIT 21;
-- statement: connection 68
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_TIME') LIMIT 21;

-- block: widget.planet/widget __widget/planet.html
-- statement: connection 69
SET NAMES utf8mb4;
-- statement: connection 69
set autocommit=0;
-- statement: connection 69
set autocommit=1;
-- statement: connection 69
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 69
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 69
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE `mult_obs_general_planet_id`.`grouping` IS NULL;
-- statement: connection 69
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`display` = 'Y' AND `mult_obs_general_planet_id`.`grouping` IS NULL) ORDER BY `mult_obs_general_planet_id`.`disp_order` ASC;
-- statement: connection 69
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE `mult_obs_general_planet_id`.`display` = 'Y' ORDER BY `mult_obs_general_planet_id`.`disp_order` ASC;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'VEN') LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'EAR') LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'MAR') LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'JUP') LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'SAT') LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'URA') LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'NEP') LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'PLU') LIMIT 21;
-- statement: connection 69
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'OTH') LIMIT 21;
-- statement: connection 69
SELECT DISTINCT `mult_obs_general_planet_id`.`grouping` AS `grouping`, `mult_obs_general_planet_id`.`group_disp_order` FROM `mult_obs_general_planet_id` ORDER BY `mult_obs_general_planet_id`.`group_disp_order` ASC;
-- statement: connection 69
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;

-- block: categories/categories api/categories/co-iss-w1477654052.json
-- statement: connection 70
SET NAMES utf8mb4;
-- statement: connection 70
set autocommit=0;
-- statement: connection 70
set autocommit=1;
-- statement: connection 70
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 70
SELECT `table_names`.`table_name` AS `table_name`, `table_names`.`label` AS `label` FROM `table_names` ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 70
SELECT `obs_general`.`opus_id` AS `opus_id` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_pds`.`opus_id` AS `opus_id` FROM `obs_pds` INNER JOIN `obs_general` ON (`obs_pds`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_type_image`.`opus_id` AS `opus_id` FROM `obs_type_image` INNER JOIN `obs_general` ON (`obs_type_image`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_wavelength`.`opus_id` AS `opus_id` FROM `obs_wavelength` INNER JOIN `obs_general` ON (`obs_wavelength`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_profile`.`opus_id` AS `opus_id` FROM `obs_profile` INNER JOIN `obs_general` ON (`obs_profile`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry`.`opus_id` AS `opus_id` FROM `obs_surface_geometry` INNER JOIN `obs_general` ON (`obs_surface_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__adrastea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__adrastea` INNER JOIN `obs_general` ON (`obs_surface_geometry__adrastea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__aegaeon`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__aegaeon` INNER JOIN `obs_general` ON (`obs_surface_geometry__aegaeon`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__amalthea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__amalthea` INNER JOIN `obs_general` ON (`obs_surface_geometry__amalthea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__anthe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__anthe` INNER JOIN `obs_general` ON (`obs_surface_geometry__anthe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__atlas`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__atlas` INNER JOIN `obs_general` ON (`obs_surface_geometry__atlas`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__callisto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__callisto` INNER JOIN `obs_general` ON (`obs_surface_geometry__callisto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__calypso`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__calypso` INNER JOIN `obs_general` ON (`obs_surface_geometry__calypso`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__charon`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__charon` INNER JOIN `obs_general` ON (`obs_surface_geometry__charon`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__daphnis`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__daphnis` INNER JOIN `obs_general` ON (`obs_surface_geometry__daphnis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__despina`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__despina` INNER JOIN `obs_general` ON (`obs_surface_geometry__despina`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__dione`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__dione` INNER JOIN `obs_general` ON (`obs_surface_geometry__dione`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__enceladus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__enceladus` INNER JOIN `obs_general` ON (`obs_surface_geometry__enceladus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__epimetheus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__epimetheus` INNER JOIN `obs_general` ON (`obs_surface_geometry__epimetheus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__europa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__europa` INNER JOIN `obs_general` ON (`obs_surface_geometry__europa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__galatea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__galatea` INNER JOIN `obs_general` ON (`obs_surface_geometry__galatea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__ganymede`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__ganymede` INNER JOIN `obs_general` ON (`obs_surface_geometry__ganymede`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__helene`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__helene` INNER JOIN `obs_general` ON (`obs_surface_geometry__helene`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__hydra`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__hydra` INNER JOIN `obs_general` ON (`obs_surface_geometry__hydra`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__hyperion`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__hyperion` INNER JOIN `obs_general` ON (`obs_surface_geometry__hyperion`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__iapetus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__iapetus` INNER JOIN `obs_general` ON (`obs_surface_geometry__iapetus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__io`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__io` INNER JOIN `obs_general` ON (`obs_surface_geometry__io`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__janus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__janus` INNER JOIN `obs_general` ON (`obs_surface_geometry__janus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__jupiter`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__jupiter` INNER JOIN `obs_general` ON (`obs_surface_geometry__jupiter`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__kerberos`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__kerberos` INNER JOIN `obs_general` ON (`obs_surface_geometry__kerberos`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__larissa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__larissa` INNER JOIN `obs_general` ON (`obs_surface_geometry__larissa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__methone`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__methone` INNER JOIN `obs_general` ON (`obs_surface_geometry__methone`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__metis`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__metis` INNER JOIN `obs_general` ON (`obs_surface_geometry__metis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__mimas`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__mimas` INNER JOIN `obs_general` ON (`obs_surface_geometry__mimas`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__naiad`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__naiad` INNER JOIN `obs_general` ON (`obs_surface_geometry__naiad`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__neptune`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__neptune` INNER JOIN `obs_general` ON (`obs_surface_geometry__neptune`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__nereid`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__nereid` INNER JOIN `obs_general` ON (`obs_surface_geometry__nereid`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__nix`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__nix` INNER JOIN `obs_general` ON (`obs_surface_geometry__nix`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__pallene`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pallene` INNER JOIN `obs_general` ON (`obs_surface_geometry__pallene`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__pan`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pan` INNER JOIN `obs_general` ON (`obs_surface_geometry__pan`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__pandora`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pandora` INNER JOIN `obs_general` ON (`obs_surface_geometry__pandora`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__phoebe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__phoebe` INNER JOIN `obs_general` ON (`obs_surface_geometry__phoebe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__pluto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pluto` INNER JOIN `obs_general` ON (`obs_surface_geometry__pluto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__polydeuces`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__polydeuces` INNER JOIN `obs_general` ON (`obs_surface_geometry__polydeuces`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__prometheus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__prometheus` INNER JOIN `obs_general` ON (`obs_surface_geometry__prometheus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__proteus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__proteus` INNER JOIN `obs_general` ON (`obs_surface_geometry__proteus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__rhea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__rhea` INNER JOIN `obs_general` ON (`obs_surface_geometry__rhea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__saturn`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__saturn` INNER JOIN `obs_general` ON (`obs_surface_geometry__saturn`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__styx`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__styx` INNER JOIN `obs_general` ON (`obs_surface_geometry__styx`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__telesto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__telesto` INNER JOIN `obs_general` ON (`obs_surface_geometry__telesto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__tethys`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__tethys` INNER JOIN `obs_general` ON (`obs_surface_geometry__tethys`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__thalassa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__thalassa` INNER JOIN `obs_general` ON (`obs_surface_geometry__thalassa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__thebe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__thebe` INNER JOIN `obs_general` ON (`obs_surface_geometry__thebe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__titan`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__titan` INNER JOIN `obs_general` ON (`obs_surface_geometry__titan`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_surface_geometry__triton`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__triton` INNER JOIN `obs_general` ON (`obs_surface_geometry__triton`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_ring_geometry`.`opus_id` AS `opus_id` FROM `obs_ring_geometry` INNER JOIN `obs_general` ON (`obs_ring_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_mission_cassini`.`opus_id` AS `opus_id` FROM `obs_mission_cassini` INNER JOIN `obs_general` ON (`obs_mission_cassini`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_mission_galileo`.`opus_id` AS `opus_id` FROM `obs_mission_galileo` INNER JOIN `obs_general` ON (`obs_mission_galileo`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_mission_hubble`.`opus_id` AS `opus_id` FROM `obs_mission_hubble` INNER JOIN `obs_general` ON (`obs_mission_hubble`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_mission_new_horizons`.`opus_id` AS `opus_id` FROM `obs_mission_new_horizons` INNER JOIN `obs_general` ON (`obs_mission_new_horizons`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_mission_voyager`.`opus_id` AS `opus_id` FROM `obs_mission_voyager` INNER JOIN `obs_general` ON (`obs_mission_voyager`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_instrument_cocirs`.`opus_id` AS `opus_id` FROM `obs_instrument_cocirs` INNER JOIN `obs_general` ON (`obs_instrument_cocirs`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_instrument_coiss`.`opus_id` AS `opus_id` FROM `obs_instrument_coiss` INNER JOIN `obs_general` ON (`obs_instrument_coiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_instrument_couvis`.`opus_id` AS `opus_id` FROM `obs_instrument_couvis` INNER JOIN `obs_general` ON (`obs_instrument_couvis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_instrument_covims`.`opus_id` AS `opus_id` FROM `obs_instrument_covims` INNER JOIN `obs_general` ON (`obs_instrument_covims`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_instrument_gossi`.`opus_id` AS `opus_id` FROM `obs_instrument_gossi` INNER JOIN `obs_general` ON (`obs_instrument_gossi`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_instrument_nhlorri`.`opus_id` AS `opus_id` FROM `obs_instrument_nhlorri` INNER JOIN `obs_general` ON (`obs_instrument_nhlorri`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_instrument_nhmvic`.`opus_id` AS `opus_id` FROM `obs_instrument_nhmvic` INNER JOIN `obs_general` ON (`obs_instrument_nhmvic`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 70
SELECT `obs_instrument_vgiss`.`opus_id` AS `opus_id` FROM `obs_instrument_vgiss` INNER JOIN `obs_general` ON (`obs_instrument_vgiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';

-- block: autocomplete.bundleid/build __api/meta/result_count.json?reqno=1
-- statement: connection 71
SET NAMES utf8mb4;
-- statement: connection 71
set autocommit=0;
-- statement: connection 71
set autocommit=1;
-- statement: connection 71
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- block: autocomplete.bundleid/prefix_2 __api/stringsearchchoices/bundleid.json?bundleid=CO&reqno=1
-- statement: connection 72
SET NAMES utf8mb4;
-- statement: connection 72
set autocommit=0;
-- statement: connection 72
set autocommit=1;
-- statement: connection 72
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 72
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'bundleid' LIMIT 21;
-- statement: connection 72
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`name` = 'bundle_id') LIMIT 21;
-- statement: connection 72
SELECT COUNT(*) FROM `cache_1`;
-- statement: connection 72
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN `cache_1` ON `obs_pds`.`obs_general_id`=`cache_1`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%CO%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: autocomplete.bundleid/prefix_6 __api/stringsearchchoices/bundleid.json?bundleid=COISS_&reqno=1
-- statement: connection 73
SET NAMES utf8mb4;
-- statement: connection 73
set autocommit=0;
-- statement: connection 73
set autocommit=1;
-- statement: connection 73
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 73
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`name` = 'bundle_id') LIMIT 21;
-- statement: connection 73
SELECT COUNT(*) FROM `cache_1`;
-- statement: connection 73
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN `cache_1` ON `obs_pds`.`obs_general_id`=`cache_1`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%COISS\\_%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: files.broad/one_observation api/files/co-iss-w1477654052.json
-- statement: connection 74
SET NAMES utf8mb4;
-- statement: connection 74
set autocommit=0;
-- statement: connection 74
set autocommit=1;
-- statement: connection 74
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 74
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;

-- block: files.broad/search_page_1 api/files.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 75
SET NAMES utf8mb4;
-- statement: connection 75
set autocommit=0;
-- statement: connection 75
set autocommit=1;
-- statement: connection 75
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 75
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '3txeqtl5omej10juh191ano8hjt9dz2l' LIMIT 1;
-- statement: connection 75
set autocommit=0;
-- statement: connection 75
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('3txeqtl5omej10juh191ano8hjt9dz2l', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', '2026-11-19 15:23:17.396936');
-- statement: connection 75
commit;
-- statement: connection 75
set autocommit=1;
-- statement: connection 75
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 75
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 75
CREATE TEMPORARY TABLE `temp_cache_2_3177634_1793892197_404438` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 75
SELECT `obs_general`.`opus_id` FROM `obs_general` INNER JOIN `temp_cache_2_3177634_1793892197_404438` ON `obs_general`.`id`=`temp_cache_2_3177634_1793892197_404438`.`id` ORDER BY `temp_cache_2_3177634_1793892197_404438`.`sort_order`;
-- statement: connection 75
DROP TABLE `temp_cache_2_3177634_1793892197_404438`;
-- statement: connection 75
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('vg-iss-1-s-prof','vg-uvs-1-s-occ-1980-317-iother-e','vg-rss-1-s-occ-1980-318-s63-e','vg-rss-1-s-occ-1980-318-x63-e','vg-iss-2-s-c4360001','vg-iss-2-s-c4360004','vg-iss-2-s-c4360007','vg-iss-2-s-c4360010','vg-iss-2-s-c4360018','vg-iss-2-s-c4360022','vg-iss-2-s-c4360026','vg-iss-2-s-c4360029','vg-iss-2-s-c4360033','vg-iss-2-s-c4360037','vg-iss-2-s-c4360041','vg-iss-2-s-c4360044','vg-iss-2-s-c4360048','vg-iss-2-s-c4360052','vg-iss-2-s-c4360056','vg-iss-2-s-c4360059','vg-iss-2-s-c4360103','vg-iss-2-s-c4360107','vg-iss-2-s-c4360111','vg-iss-2-s-c4360114','vg-iss-2-s-c4360257','vg-iss-2-s-c4360301','vg-iss-2-s-c4360305','vg-iss-2-s-c4360308','vg-iss-2-s-c4360312','vg-iss-2-s-c4360316','vg-iss-2-s-c4360320','vg-iss-2-s-c4360323','vg-iss-2-s-c4360327','vg-iss-2-s-c4360331','vg-iss-2-s-c4360335','vg-iss-2-s-c4360338','vg-iss-2-s-c4360342','vg-iss-2-s-c4360346','vg-iss-2-s-c4360350','vg-iss-2-s-c4360353','vg-iss-2-s-c4360507','vg-iss-2-s-c4360511','vg-iss-2-s-c4360515','vg-iss-2-s-c4360519','vg-iss-2-s-c4360523','vg-iss-2-s-c4360527','vg-iss-2-s-c4360536','vg-iss-2-s-c4360540','vg-iss-2-s-c4360544','vg-iss-2-s-c4360547','vg-iss-2-s-c4360551','vg-iss-2-s-c4360555','vg-iss-2-s-c4360559','vg-iss-2-s-c4360602','vg-iss-2-s-c4360606','vg-iss-2-s-c4360610','vg-iss-2-s-c4360614','vg-iss-2-s-c4360617','vg-iss-2-s-c4360621','vg-iss-2-s-c4360625','vg-iss-2-s-c4360629','vg-iss-2-s-c4360632','vg-iss-2-s-c4360815','vg-iss-2-s-c4360819','vg-iss-2-s-c4360823','vg-iss-2-s-c4360826','vg-iss-2-s-c4360830','vg-iss-2-s-c4360834','vg-iss-2-s-c4360838','vg-iss-2-s-c4360841','vg-iss-2-s-c4360845','vg-iss-2-s-c4360849','vg-iss-2-s-c4360853','vg-iss-2-s-c4360856','vg-iss-2-s-c4360904','vg-iss-2-s-c4360908','vg-iss-2-s-c4360911','vg-iss-2-s-c4361016','vg-iss-2-s-c4361020','vg-iss-2-s-c4361024','vg-iss-2-s-c4361028','vg-iss-2-s-c4361032','vg-iss-2-s-c4361036','vg-iss-2-s-c4361040','vg-iss-2-s-c4361044','vg-iss-2-s-c4361048','vg-iss-2-s-c4361054','vg-iss-2-s-c4361058','vg-iss-2-s-c4361102','vg-iss-2-s-c4361105','vg-iss-2-s-c4361109','vg-iss-2-s-c4361113','vg-iss-2-s-c4361117','vg-iss-2-s-c4361120','vg-iss-2-s-c4361124','vg-iss-2-s-c4361128','vg-iss-2-s-c4361132','vg-iss-2-s-c4361135','vg-iss-2-s-c4361139','vg-iss-2-s-c4361143') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 75
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 75
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 75
set autocommit=0;
-- statement: connection 75
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', `expire_date` = '2026-11-19 15:23:17.453875' WHERE `django_session`.`session_key` = '3txeqtl5omej10juh191ano8hjt9dz2l';
-- statement: connection 75
commit;
-- statement: connection 75
set autocommit=1;

-- block: previews.empty/gallery_page_1 __api/dataimages.json?page=1&limit=100&reqno=1
-- statement: connection 76
SET NAMES utf8mb4;
-- statement: connection 76
set autocommit=0;
-- statement: connection 76
set autocommit=1;
-- statement: connection 76
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 76
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a' LIMIT 1;
-- statement: connection 76
set autocommit=0;
-- statement: connection 76
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('y8jowzz1fh0igbeq1qwh79n3do8e5s6a', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', '2026-11-19 15:23:17.470804');
-- statement: connection 76
commit;
-- statement: connection 76
set autocommit=1;
-- statement: connection 76
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = '**previewimages' LIMIT 21;
-- statement: connection 76
CREATE TEMPORARY TABLE `temp_cache_1_3177634_1793892197_474667` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 76
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_general`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_3177634_1793892197_474667` ON `obs_general`.`id`=`temp_cache_1_3177634_1793892197_474667`.`id` LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a' ORDER BY `temp_cache_1_3177634_1793892197_474667`.`sort_order`;
-- statement: connection 76
DROP TABLE `temp_cache_1_3177634_1793892197_474667`;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 76
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 76
set autocommit=0;
-- statement: connection 76
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', `expire_date` = '2026-11-19 15:23:17.496269' WHERE `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a';
-- statement: connection 76
commit;
-- statement: connection 76
set autocommit=1;

-- block: previews.empty/gallery_page_10 __api/dataimages.json?page=10&limit=100&reqno=1
-- statement: connection 77
SET NAMES utf8mb4;
-- statement: connection 77
set autocommit=0;
-- statement: connection 77
set autocommit=1;
-- statement: connection 77
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 77
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:17.500160' AND `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a') LIMIT 21;
-- statement: connection 77
CREATE TEMPORARY TABLE `temp_cache_1_3177634_1793892197_501453` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 77
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_general`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_3177634_1793892197_501453` ON `obs_general`.`id`=`temp_cache_1_3177634_1793892197_501453`.`id` LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a' ORDER BY `temp_cache_1_3177634_1793892197_501453`.`sort_order`;
-- statement: connection 77
DROP TABLE `temp_cache_1_3177634_1793892197_501453`;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 77
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 77
set autocommit=0;
-- statement: connection 77
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', `expire_date` = '2026-11-19 15:23:17.514000' WHERE `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a';
-- statement: connection 77
commit;
-- statement: connection 77
set autocommit=1;

-- block: previews.empty/images_page_1 api/images.json?page=1&limit=100
-- statement: connection 78
SET NAMES utf8mb4;
-- statement: connection 78
set autocommit=0;
-- statement: connection 78
set autocommit=1;
-- statement: connection 78
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 78
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:17.517208' AND `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a') LIMIT 21;
-- statement: connection 78
CREATE TEMPORARY TABLE `temp_cache_1_3177634_1793892197_520073` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 78
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `temp_cache_1_3177634_1793892197_520073` ON `obs_general`.`id`=`temp_cache_1_3177634_1793892197_520073`.`id` ORDER BY `temp_cache_1_3177634_1793892197_520073`.`sort_order`;
-- statement: connection 78
DROP TABLE `temp_cache_1_3177634_1793892197_520073`;
-- statement: connection 78
set autocommit=0;
-- statement: connection 78
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', `expire_date` = '2026-11-19 15:23:17.522247' WHERE `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a';
-- statement: connection 78
commit;
-- statement: connection 78
set autocommit=1;

-- block: previews.empty/images_page_10 api/images.json?page=10&limit=100
-- statement: connection 79
SET NAMES utf8mb4;
-- statement: connection 79
set autocommit=0;
-- statement: connection 79
set autocommit=1;
-- statement: connection 79
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 79
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:17.525585' AND `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a') LIMIT 21;
-- statement: connection 79
CREATE TEMPORARY TABLE `temp_cache_1_3177634_1793892197_526873` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 79
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `temp_cache_1_3177634_1793892197_526873` ON `obs_general`.`id`=`temp_cache_1_3177634_1793892197_526873`.`id` ORDER BY `temp_cache_1_3177634_1793892197_526873`.`sort_order`;
-- statement: connection 79
DROP TABLE `temp_cache_1_3177634_1793892197_526873`;
-- statement: connection 79
set autocommit=0;
-- statement: connection 79
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', `expire_date` = '2026-11-19 15:23:17.529637' WHERE `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a';
-- statement: connection 79
commit;
-- statement: connection 79
set autocommit=1;

-- block: previews.empty/detail __initdetail/co-iss-w1477654052.html
-- statement: connection 80
SET NAMES utf8mb4;
-- statement: connection 80
set autocommit=0;
-- statement: connection 80
set autocommit=1;
-- statement: connection 80
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 80
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 80
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrumentid' LIMIT 21;
-- statement: connection 80
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`old_slug` = 'instrumentid' LIMIT 21;
-- statement: connection 80
SELECT `mult_obs_general_instrument_id`.`value` AS `value`, `mult_obs_general_instrument_id`.`label` AS `label` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 1;
-- statement: connection 80
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:17.538815' AND `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a') LIMIT 21;
-- statement: connection 80
SELECT `cart`.`id`, `cart`.`session_id`, `cart`.`obs_general_id`, `cart`.`opus_id`, `cart`.`recycled`, `cart`.`timestamp` FROM `cart` WHERE (`cart`.`opus_id` = 'co-iss-w1477654052' AND `cart`.`recycled` = 0 AND `cart`.`session_id` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a') LIMIT 21;
-- statement: connection 80
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 80
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 80
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE ((`obs_files`.`short_name` = 'browse_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'browse_full' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_full' AND `obs_files`.`version_name` = 'Current')) AND `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 80
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_raw') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_calib') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_thumb') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_medium') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_full') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_documentation') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'rms_index') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'inventory') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'planet_geometry') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'ring_geometry') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'browse_thumb') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'browse_small') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'browse_medium') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'browse_full') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_calib') LIMIT 21;
-- statement: connection 80
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_calib') LIMIT 21;
-- statement: connection 80
set autocommit=0;
-- statement: connection 80
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', `expire_date` = '2026-11-19 15:23:17.548314' WHERE `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a';
-- statement: connection 80
commit;
-- statement: connection 80
set autocommit=1;

-- block: previews.empty/image_med api/image/med/co-iss-w1477654052.json
-- statement: connection 81
SET NAMES utf8mb4;
-- statement: connection 81
set autocommit=0;
-- statement: connection 81
set autocommit=1;
-- statement: connection 81
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 81
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-05 15:23:17.551804' AND `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a') LIMIT 21;
-- statement: connection 81
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 81
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.opus_id\": [\"co-iss-w1477654052\"]}', '80cf569e54ee1ebe7a720df433eb42c5', '{\"obs_general.opus_id\": [\"matches\"]}', '5cb040f5fb0c9aeb4dfe8694aff88f3d', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 81
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 81
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 81
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 81
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 81
CREATE TABLE `cache_15`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 81
CREATE TEMPORARY TABLE `temp_cache_15_3177634_1793892197_569479` SELECT `sort_order`,`id` FROM `cache_15` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 81
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `temp_cache_15_3177634_1793892197_569479` ON `obs_general`.`id`=`temp_cache_15_3177634_1793892197_569479`.`id` ORDER BY `temp_cache_15_3177634_1793892197_569479`.`sort_order`;
-- statement: connection 81
DROP TABLE `temp_cache_15_3177634_1793892197_569479`;
-- statement: connection 81
set autocommit=0;
-- statement: connection 81
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOzJ7:HSw9SVhbnkuhwkaG6HHRfF7sb0MOsyUM6V2gEaddwno', `expire_date` = '2026-11-19 15:23:17.570207' WHERE `django_session`.`session_key` = 'y8jowzz1fh0igbeq1qwh79n3do8e5s6a';
-- statement: connection 81
commit;
-- statement: connection 81
set autocommit=1;
