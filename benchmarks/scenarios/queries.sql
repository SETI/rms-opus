-- Captured by benchmarks/bench_db.py --dump-queries from the harness-owned server.
-- Regenerate it; do not edit it.

-- block: search.empty/result_count __api/meta/result_count.json?reqno=1
-- statement: connection 760
SET NAMES utf8mb4;
-- statement: connection 760
set autocommit=0;
-- statement: connection 760
set autocommit=1;
-- statement: connection 760
SELECT VERSION(),
                       @@sql_mode,
                       @@default_storage_engine,
                       @@sql_auto_is_null,
                       @@lower_case_table_names,
                       CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL;
-- statement: connection 760
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 760
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 760
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 760
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{}', '99914b932bd37a50b983c5e7c90ae93b', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 760
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 760
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 760
CREATE TABLE `cache_1`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 760
SELECT COUNT(*) FROM `cache_1`;

-- block: search.broad/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 761
SET NAMES utf8mb4;
-- statement: connection 761
set autocommit=0;
-- statement: connection 761
set autocommit=1;
-- statement: connection 761
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 761
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 761
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 761
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'f004842dd5ce1e4a6c4c68e89b50dd11', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 761
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 761
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 761
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 761
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 761
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 761
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 761
CREATE TABLE `cache_2`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0 ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 761
SELECT COUNT(*) FROM `cache_2`;

-- block: search.selective/result_count __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 762
SET NAMES utf8mb4;
-- statement: connection 762
set autocommit=0;
-- statement: connection 762
set autocommit=1;
-- statement: connection 762
SELECT VERSION(),
                       @@sql_mode,
                       @@default_storage_engine,
                       @@sql_auto_is_null,
                       @@lower_case_table_names,
                       CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL;
-- statement: connection 762
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 762
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 762
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 762
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 762
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 762
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Uranus\"]}', '033bcdee4b74d22264a9cf8648d2a2fc', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 762
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 762
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 762
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 762
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 762
CREATE TABLE `cache_3`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 762
SELECT COUNT(*) FROM `cache_3`;

-- block: search.ring_radius/result_count __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 763
SET NAMES utf8mb4;
-- statement: connection 763
set autocommit=0;
-- statement: connection 763
set autocommit=1;
-- statement: connection 763
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 763
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 763
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 763
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_ring_geometry.ring_radius1\": [60000.0], \"obs_ring_geometry.ring_radius2\": [140000.0]}', '3e9f393e09dfa2c750cdae5be4a34297', '{\"obs_ring_geometry.ring_radius\": [\"any\"]}', 'd58efe915310b90c76b4d3e3c419cba8', '{\"obs_ring_geometry.ring_radius\": [\"km\"]}', '70f0bb7407a66538767b4dee465f5022', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 763
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 763
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 763
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 763
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius2') LIMIT 21;
-- statement: connection 763
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 763
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 763
CREATE TABLE `cache_4`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0 ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 763
SELECT COUNT(*) FROM `cache_4`;

-- block: search.target/result_count __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 764
SET NAMES utf8mb4;
-- statement: connection 764
set autocommit=0;
-- statement: connection 764
set autocommit=1;
-- statement: connection 764
SELECT VERSION(),
                       @@sql_mode,
                       @@default_storage_engine,
                       @@sql_auto_is_null,
                       @@lower_case_table_names,
                       CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL;
-- statement: connection 764
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 764
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 764
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 764
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 764
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 764
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.target_name\": [\"Saturn\"]}', '0808ab16043b8e7fcebb7ff7ab9500d9', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 764
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 764
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 764
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 764
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 764
CREATE TABLE `cache_5`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,'1') ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 764
SELECT COUNT(*) FROM `cache_5`;

-- block: search.surface_geometry/result_count __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 765
SET NAMES utf8mb4;
-- statement: connection 765
set autocommit=0;
-- statement: connection 765
set autocommit=1;
-- statement: connection 765
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'surfacegeometrytargetname' LIMIT 21;
-- statement: connection 765
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 765
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_surface_geometry__saturn.planetographic_latitude1\": [-30.0], \"obs_surface_geometry__saturn.planetographic_latitude2\": [30.0], \"obs_surface_geometry_name.target_name\": [\"Saturn\"]}', '907ec5896a8bd3771dd91f22743140d1', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"any\"]}', '2998cdc1c9b87c33e7ac2c27b2011182', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"degrees\"]}', '77ac08a838ce071f52f224163fc043dc', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude2') LIMIT 21;
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 765
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 765
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 765
CREATE TABLE `cache_6`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` LEFT JOIN `obs_surface_geometry_name` ON `obs_general`.`id`=`obs_surface_geometry_name`.`obs_general_id` WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (`obs_surface_geometry_name`.`target_name` IN (6)) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 765
SELECT COUNT(*) FROM `cache_6`;

-- block: pages.empty/build __api/meta/result_count.json?reqno=1
-- statement: connection 766
SET NAMES utf8mb4;
-- statement: connection 766
set autocommit=0;
-- statement: connection 766
set autocommit=1;
-- statement: connection 766
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- block: pages.empty/page_1 api/data.json?page=1&limit=100
-- statement: connection 767
SET NAMES utf8mb4;
-- statement: connection 767
set autocommit=0;
-- statement: connection 767
set autocommit=1;
-- statement: connection 767
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 767
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'ze9ucbqdgfgd3b6xvdg3gd04chkfroyn' LIMIT 1;
-- statement: connection 767
set autocommit=0;
-- statement: connection 767
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('ze9ucbqdgfgd3b6xvdg3gd04chkfroyn', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', '2026-11-18 07:19:08.030021');
-- statement: connection 767
commit;
-- statement: connection 767
set autocommit=1;
-- statement: connection 767
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 767
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 767
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 767
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 767
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 767
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 767
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 767
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 767
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationduration' LIMIT 21;
-- statement: connection 767
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 767
CREATE TEMPORARY TABLE `temp_cache_1_748869_1793776748_052609` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 767
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_748869_1793776748_052609` ON `obs_general`.`id`=`temp_cache_1_748869_1793776748_052609`.`id` ORDER BY `temp_cache_1_748869_1793776748_052609`.`sort_order`;
-- statement: connection 767
DROP TABLE `temp_cache_1_748869_1793776748_052609`;
-- statement: connection 767
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 48;
-- statement: connection 767
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 47;
-- statement: connection 767
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0;
-- statement: connection 767
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 2;
-- statement: connection 767
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1;
-- statement: connection 767
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 10;
-- statement: connection 767
set autocommit=0;
-- statement: connection 767
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.073371' WHERE `django_session`.`session_key` = 'ze9ucbqdgfgd3b6xvdg3gd04chkfroyn';
-- statement: connection 767
commit;
-- statement: connection 767
set autocommit=1;

-- block: pages.empty/page_10 api/data.json?page=10&limit=100
-- statement: connection 768
SET NAMES utf8mb4;
-- statement: connection 768
set autocommit=0;
-- statement: connection 768
set autocommit=1;
-- statement: connection 768
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 768
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.078907' AND `django_session`.`session_key` = 'ze9ucbqdgfgd3b6xvdg3gd04chkfroyn') LIMIT 21;
-- statement: connection 768
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 768
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 768
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 768
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 768
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 768
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 768
CREATE TEMPORARY TABLE `temp_cache_1_748869_1793776748_084050` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 768
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_748869_1793776748_084050` ON `obs_general`.`id`=`temp_cache_1_748869_1793776748_084050`.`id` ORDER BY `temp_cache_1_748869_1793776748_084050`.`sort_order`;
-- statement: connection 768
DROP TABLE `temp_cache_1_748869_1793776748_084050`;
-- statement: connection 768
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 4;
-- statement: connection 768
set autocommit=0;
-- statement: connection 768
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.101273' WHERE `django_session`.`session_key` = 'ze9ucbqdgfgd3b6xvdg3gd04chkfroyn';
-- statement: connection 768
commit;
-- statement: connection 768
set autocommit=1;

-- block: pages.empty/page_last api/data.json?page=298&limit=100
-- statement: connection 769
SET NAMES utf8mb4;
-- statement: connection 769
set autocommit=0;
-- statement: connection 769
set autocommit=1;
-- statement: connection 769
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 769
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.106679' AND `django_session`.`session_key` = 'ze9ucbqdgfgd3b6xvdg3gd04chkfroyn') LIMIT 21;
-- statement: connection 769
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 769
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 769
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 769
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 769
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 769
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 769
CREATE TEMPORARY TABLE `temp_cache_1_748869_1793776748_113069` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 29700;
-- statement: connection 769
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_748869_1793776748_113069` ON `obs_general`.`id`=`temp_cache_1_748869_1793776748_113069`.`id` ORDER BY `temp_cache_1_748869_1793776748_113069`.`sort_order`;
-- statement: connection 769
DROP TABLE `temp_cache_1_748869_1793776748_113069`;
-- statement: connection 769
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 3;
-- statement: connection 769
set autocommit=0;
-- statement: connection 769
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.128354' WHERE `django_session`.`session_key` = 'ze9ucbqdgfgd3b6xvdg3gd04chkfroyn';
-- statement: connection 769
commit;
-- statement: connection 769
set autocommit=1;

-- block: pages.broad/build __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 770
SET NAMES utf8mb4;
-- statement: connection 770
set autocommit=0;
-- statement: connection 770
set autocommit=1;
-- statement: connection 770
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 770
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 770
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;

-- block: pages.broad/page_1 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 771
SET NAMES utf8mb4;
-- statement: connection 771
set autocommit=0;
-- statement: connection 771
set autocommit=1;
-- statement: connection 771
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 771
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'az4g21jeq4m5xbspyrvqwg6vpbj4q4np' LIMIT 1;
-- statement: connection 771
set autocommit=0;
-- statement: connection 771
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('az4g21jeq4m5xbspyrvqwg6vpbj4q4np', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', '2026-11-18 07:19:08.171513');
-- statement: connection 771
commit;
-- statement: connection 771
set autocommit=1;
-- statement: connection 771
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 771
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 771
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 771
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 771
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 771
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 771
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 771
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 771
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationduration' LIMIT 21;
-- statement: connection 771
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 771
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 771
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 771
CREATE TEMPORARY TABLE `temp_cache_2_748867_1793776748_202057` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 771
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_2_748867_1793776748_202057` ON `obs_general`.`id`=`temp_cache_2_748867_1793776748_202057`.`id` ORDER BY `temp_cache_2_748867_1793776748_202057`.`sort_order`;
-- statement: connection 771
DROP TABLE `temp_cache_2_748867_1793776748_202057`;
-- statement: connection 771
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0;
-- statement: connection 771
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 2;
-- statement: connection 771
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1;
-- statement: connection 771
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 10;
-- statement: connection 771
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 771
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 771
set autocommit=0;
-- statement: connection 771
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.230428' WHERE `django_session`.`session_key` = 'az4g21jeq4m5xbspyrvqwg6vpbj4q4np';
-- statement: connection 771
commit;
-- statement: connection 771
set autocommit=1;

-- block: pages.broad/page_10 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=10&limit=100
-- statement: connection 772
SET NAMES utf8mb4;
-- statement: connection 772
set autocommit=0;
-- statement: connection 772
set autocommit=1;
-- statement: connection 772
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 772
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.236894' AND `django_session`.`session_key` = 'az4g21jeq4m5xbspyrvqwg6vpbj4q4np') LIMIT 21;
-- statement: connection 772
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 772
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 772
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 772
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 772
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 772
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 772
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 772
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 772
CREATE TEMPORARY TABLE `temp_cache_2_748869_1793776748_249015` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 772
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_2_748869_1793776748_249015` ON `obs_general`.`id`=`temp_cache_2_748869_1793776748_249015`.`id` ORDER BY `temp_cache_2_748869_1793776748_249015`.`sort_order`;
-- statement: connection 772
DROP TABLE `temp_cache_2_748869_1793776748_249015`;
-- statement: connection 772
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 41;
-- statement: connection 772
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 772
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 772
set autocommit=0;
-- statement: connection 772
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.272995' WHERE `django_session`.`session_key` = 'az4g21jeq4m5xbspyrvqwg6vpbj4q4np';
-- statement: connection 772
commit;
-- statement: connection 772
set autocommit=1;

-- block: pages.broad/page_last api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=298&limit=100
-- statement: connection 773
SET NAMES utf8mb4;
-- statement: connection 773
set autocommit=0;
-- statement: connection 773
set autocommit=1;
-- statement: connection 773
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 773
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.278940' AND `django_session`.`session_key` = 'az4g21jeq4m5xbspyrvqwg6vpbj4q4np') LIMIT 21;
-- statement: connection 773
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 773
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 773
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 773
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 773
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 773
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 773
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 773
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 773
CREATE TEMPORARY TABLE `temp_cache_2_748867_1793776748_293903` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 29700;
-- statement: connection 773
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_2_748867_1793776748_293903` ON `obs_general`.`id`=`temp_cache_2_748867_1793776748_293903`.`id` ORDER BY `temp_cache_2_748867_1793776748_293903`.`sort_order`;
-- statement: connection 773
DROP TABLE `temp_cache_2_748867_1793776748_293903`;
-- statement: connection 773
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 773
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 773
set autocommit=0;
-- statement: connection 773
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.314023' WHERE `django_session`.`session_key` = 'az4g21jeq4m5xbspyrvqwg6vpbj4q4np';
-- statement: connection 773
commit;
-- statement: connection 773
set autocommit=1;

-- block: pages.selective/build __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 774
SET NAMES utf8mb4;
-- statement: connection 774
set autocommit=0;
-- statement: connection 774
set autocommit=1;
-- statement: connection 774
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 774
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));

-- block: pages.selective/page_1 api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 775
SET NAMES utf8mb4;
-- statement: connection 775
set autocommit=0;
-- statement: connection 775
set autocommit=1;
-- statement: connection 775
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 775
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'xmc4qd0p2i8rqr1stf20f08igeplwa26' LIMIT 1;
-- statement: connection 775
set autocommit=0;
-- statement: connection 775
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('xmc4qd0p2i8rqr1stf20f08igeplwa26', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', '2026-11-18 07:19:08.347991');
-- statement: connection 775
commit;
-- statement: connection 775
set autocommit=1;
-- statement: connection 775
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 775
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 775
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 775
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 775
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 775
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 775
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 775
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 775
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationduration' LIMIT 21;
-- statement: connection 775
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 775
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 775
CREATE TEMPORARY TABLE `temp_cache_3_748868_1793776748_368118` SELECT `sort_order`,`id` FROM `cache_3` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 775
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_3_748868_1793776748_368118` ON `obs_general`.`id`=`temp_cache_3_748868_1793776748_368118`.`id` ORDER BY `temp_cache_3_748868_1793776748_368118`.`sort_order`;
-- statement: connection 775
DROP TABLE `temp_cache_3_748868_1793776748_368118`;
-- statement: connection 775
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 48;
-- statement: connection 775
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 47;
-- statement: connection 775
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 775
set autocommit=0;
-- statement: connection 775
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.381513' WHERE `django_session`.`session_key` = 'xmc4qd0p2i8rqr1stf20f08igeplwa26';
-- statement: connection 775
commit;
-- statement: connection 775
set autocommit=1;

-- block: pages.selective/page_10 api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 776
SET NAMES utf8mb4;
-- statement: connection 776
set autocommit=0;
-- statement: connection 776
set autocommit=1;
-- statement: connection 776
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 776
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.388881' AND `django_session`.`session_key` = 'xmc4qd0p2i8rqr1stf20f08igeplwa26') LIMIT 21;
-- statement: connection 776
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 776
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 776
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 776
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 776
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 776
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 776
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 776
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 776
CREATE TEMPORARY TABLE `temp_cache_3_748867_1793776748_397649` SELECT `sort_order`,`id` FROM `cache_3` ORDER BY `sort_order` LIMIT 100 OFFSET 100;
-- statement: connection 776
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_3_748867_1793776748_397649` ON `obs_general`.`id`=`temp_cache_3_748867_1793776748_397649`.`id` ORDER BY `temp_cache_3_748867_1793776748_397649`.`sort_order`;
-- statement: connection 776
DROP TABLE `temp_cache_3_748867_1793776748_397649`;
-- statement: connection 776
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 48;
-- statement: connection 776
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 47;
-- statement: connection 776
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 776
set autocommit=0;
-- statement: connection 776
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.405523' WHERE `django_session`.`session_key` = 'xmc4qd0p2i8rqr1stf20f08igeplwa26';
-- statement: connection 776
commit;
-- statement: connection 776
set autocommit=1;

-- block: pages.selective/page_last api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 777
SET NAMES utf8mb4;
-- statement: connection 777
set autocommit=0;
-- statement: connection 777
set autocommit=1;
-- statement: connection 777
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 777
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.411680' AND `django_session`.`session_key` = 'xmc4qd0p2i8rqr1stf20f08igeplwa26') LIMIT 21;
-- statement: connection 777
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 777
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 777
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 777
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 777
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 777
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 777
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 777
CREATE TEMPORARY TABLE `temp_cache_3_748867_1793776748_417492` SELECT `sort_order`,`id` FROM `cache_3` ORDER BY `sort_order` LIMIT 100 OFFSET 100;
-- statement: connection 777
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_3_748867_1793776748_417492` ON `obs_general`.`id`=`temp_cache_3_748867_1793776748_417492`.`id` ORDER BY `temp_cache_3_748867_1793776748_417492`.`sort_order`;
-- statement: connection 777
DROP TABLE `temp_cache_3_748867_1793776748_417492`;
-- statement: connection 777
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 777
set autocommit=0;
-- statement: connection 777
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.430474' WHERE `django_session`.`session_key` = 'xmc4qd0p2i8rqr1stf20f08igeplwa26';
-- statement: connection 777
commit;
-- statement: connection 777
set autocommit=1;

-- block: pages.ring_radius/build __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 778
SET NAMES utf8mb4;
-- statement: connection 778
set autocommit=0;
-- statement: connection 778
set autocommit=1;
-- statement: connection 778
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 778
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 778
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;

-- block: pages.ring_radius/page_1 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 779
SET NAMES utf8mb4;
-- statement: connection 779
set autocommit=0;
-- statement: connection 779
set autocommit=1;
-- statement: connection 779
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 779
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'h1wasbp40irbhh2f08jmj1kdpnmmcfii' LIMIT 1;
-- statement: connection 779
set autocommit=0;
-- statement: connection 779
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('h1wasbp40irbhh2f08jmj1kdpnmmcfii', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', '2026-11-18 07:19:08.462292');
-- statement: connection 779
commit;
-- statement: connection 779
set autocommit=1;
-- statement: connection 779
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 779
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 779
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 779
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 779
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 779
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 779
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 779
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 779
CREATE TEMPORARY TABLE `temp_cache_4_748868_1793776748_471292` SELECT `sort_order`,`id` FROM `cache_4` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 779
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_4_748868_1793776748_471292` ON `obs_general`.`id`=`temp_cache_4_748868_1793776748_471292`.`id` ORDER BY `temp_cache_4_748868_1793776748_471292`.`sort_order`;
-- statement: connection 779
DROP TABLE `temp_cache_4_748868_1793776748_471292`;
-- statement: connection 779
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0;
-- statement: connection 779
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1;
-- statement: connection 779
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 779
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 779
set autocommit=0;
-- statement: connection 779
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.495400' WHERE `django_session`.`session_key` = 'h1wasbp40irbhh2f08jmj1kdpnmmcfii';
-- statement: connection 779
commit;
-- statement: connection 779
set autocommit=1;

-- block: pages.ring_radius/page_10 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=10&limit=100
-- statement: connection 780
SET NAMES utf8mb4;
-- statement: connection 780
set autocommit=0;
-- statement: connection 780
set autocommit=1;
-- statement: connection 780
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 780
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.501615' AND `django_session`.`session_key` = 'h1wasbp40irbhh2f08jmj1kdpnmmcfii') LIMIT 21;
-- statement: connection 780
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 780
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 780
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 780
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 780
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 780
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 780
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 780
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 780
CREATE TEMPORARY TABLE `temp_cache_4_748869_1793776748_512479` SELECT `sort_order`,`id` FROM `cache_4` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 780
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_4_748869_1793776748_512479` ON `obs_general`.`id`=`temp_cache_4_748869_1793776748_512479`.`id` ORDER BY `temp_cache_4_748869_1793776748_512479`.`sort_order`;
-- statement: connection 780
DROP TABLE `temp_cache_4_748869_1793776748_512479`;
-- statement: connection 780
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 43;
-- statement: connection 780
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 780
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 780
set autocommit=0;
-- statement: connection 780
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.534406' WHERE `django_session`.`session_key` = 'h1wasbp40irbhh2f08jmj1kdpnmmcfii';
-- statement: connection 780
commit;
-- statement: connection 780
set autocommit=1;

-- block: pages.ring_radius/page_last api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=112&limit=100
-- statement: connection 781
SET NAMES utf8mb4;
-- statement: connection 781
set autocommit=0;
-- statement: connection 781
set autocommit=1;
-- statement: connection 781
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 781
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.539929' AND `django_session`.`session_key` = 'h1wasbp40irbhh2f08jmj1kdpnmmcfii') LIMIT 21;
-- statement: connection 781
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 781
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 781
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 781
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 781
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 781
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 781
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 781
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 781
CREATE TEMPORARY TABLE `temp_cache_4_748869_1793776748_549830` SELECT `sort_order`,`id` FROM `cache_4` ORDER BY `sort_order` LIMIT 100 OFFSET 11100;
-- statement: connection 781
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_4_748869_1793776748_549830` ON `obs_general`.`id`=`temp_cache_4_748869_1793776748_549830`.`id` ORDER BY `temp_cache_4_748869_1793776748_549830`.`sort_order`;
-- statement: connection 781
DROP TABLE `temp_cache_4_748869_1793776748_549830`;
-- statement: connection 781
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 781
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 781
set autocommit=0;
-- statement: connection 781
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.564382' WHERE `django_session`.`session_key` = 'h1wasbp40irbhh2f08jmj1kdpnmmcfii';
-- statement: connection 781
commit;
-- statement: connection 781
set autocommit=1;

-- block: pages.target/build __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 782
SET NAMES utf8mb4;
-- statement: connection 782
set autocommit=0;
-- statement: connection 782
set autocommit=1;
-- statement: connection 782
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 782
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 782
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));

-- block: pages.target/page_1 api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 783
SET NAMES utf8mb4;
-- statement: connection 783
set autocommit=0;
-- statement: connection 783
set autocommit=1;
-- statement: connection 783
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 783
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'oo2bqqoxozcuqll9temzhyoxgarx31md' LIMIT 1;
-- statement: connection 783
set autocommit=0;
-- statement: connection 783
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('oo2bqqoxozcuqll9temzhyoxgarx31md', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', '2026-11-18 07:19:08.591572');
-- statement: connection 783
commit;
-- statement: connection 783
set autocommit=1;
-- statement: connection 783
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 783
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 783
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 783
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 783
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 783
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 783
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 783
CREATE TEMPORARY TABLE `temp_cache_5_748869_1793776748_596844` SELECT `sort_order`,`id` FROM `cache_5` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 783
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_5_748869_1793776748_596844` ON `obs_general`.`id`=`temp_cache_5_748869_1793776748_596844`.`id` ORDER BY `temp_cache_5_748869_1793776748_596844`.`sort_order`;
-- statement: connection 783
DROP TABLE `temp_cache_5_748869_1793776748_596844`;
-- statement: connection 783
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 783
set autocommit=0;
-- statement: connection 783
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH2:BBp8y9y2D3mU0qI7kW3_gU1_BMOnaArh80JVsChfCTo', `expire_date` = '2026-11-18 07:19:08.614063' WHERE `django_session`.`session_key` = 'oo2bqqoxozcuqll9temzhyoxgarx31md';
-- statement: connection 783
commit;
-- statement: connection 783
set autocommit=1;

-- block: pages.target/page_10 api/data.json?target=Saturn&page=10&limit=100
-- statement: connection 784
SET NAMES utf8mb4;
-- statement: connection 784
set autocommit=0;
-- statement: connection 784
set autocommit=1;
-- statement: connection 784
SELECT VERSION(),
                       @@sql_mode,
                       @@default_storage_engine,
                       @@sql_auto_is_null,
                       @@lower_case_table_names,
                       CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL;
-- statement: connection 784
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 784
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:08.970393' AND `django_session`.`session_key` = 'oo2bqqoxozcuqll9temzhyoxgarx31md') LIMIT 21;
-- statement: connection 784
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 784
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 784
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 784
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 784
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 784
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 784
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 784
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 784
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 784
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 784
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationduration' LIMIT 21;
-- statement: connection 784
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 784
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 784
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 784
CREATE TEMPORARY TABLE `temp_cache_5_748866_1793776749_011850` SELECT `sort_order`,`id` FROM `cache_5` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 784
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_5_748866_1793776749_011850` ON `obs_general`.`id`=`temp_cache_5_748866_1793776749_011850`.`id` ORDER BY `temp_cache_5_748866_1793776749_011850`.`sort_order`;
-- statement: connection 784
DROP TABLE `temp_cache_5_748866_1793776749_011850`;
-- statement: connection 784
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1;
-- statement: connection 784
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 784
set autocommit=0;
-- statement: connection 784
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.029339' WHERE `django_session`.`session_key` = 'oo2bqqoxozcuqll9temzhyoxgarx31md';
-- statement: connection 784
commit;
-- statement: connection 784
set autocommit=1;

-- block: pages.target/page_last api/data.json?target=Saturn&page=51&limit=100
-- statement: connection 785
SET NAMES utf8mb4;
-- statement: connection 785
set autocommit=0;
-- statement: connection 785
set autocommit=1;
-- statement: connection 785
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 785
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:09.039675' AND `django_session`.`session_key` = 'oo2bqqoxozcuqll9temzhyoxgarx31md') LIMIT 21;
-- statement: connection 785
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 785
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 785
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 785
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 785
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 785
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 785
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 785
CREATE TEMPORARY TABLE `temp_cache_5_748868_1793776749_044927` SELECT `sort_order`,`id` FROM `cache_5` ORDER BY `sort_order` LIMIT 100 OFFSET 5000;
-- statement: connection 785
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_5_748868_1793776749_044927` ON `obs_general`.`id`=`temp_cache_5_748868_1793776749_044927`.`id` ORDER BY `temp_cache_5_748868_1793776749_044927`.`sort_order`;
-- statement: connection 785
DROP TABLE `temp_cache_5_748868_1793776749_044927`;
-- statement: connection 785
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 785
set autocommit=0;
-- statement: connection 785
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.056557' WHERE `django_session`.`session_key` = 'oo2bqqoxozcuqll9temzhyoxgarx31md';
-- statement: connection 785
commit;
-- statement: connection 785
set autocommit=1;

-- block: pages.surface_geometry/build __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 786
SET NAMES utf8mb4;
-- statement: connection 786
set autocommit=0;
-- statement: connection 786
set autocommit=1;
-- statement: connection 786
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 786
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'surfacegeometrytargetname' LIMIT 21;
-- statement: connection 786
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 786
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 786
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;

-- block: pages.surface_geometry/page_1 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 787
SET NAMES utf8mb4;
-- statement: connection 787
set autocommit=0;
-- statement: connection 787
set autocommit=1;
-- statement: connection 787
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 787
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '8pjtqppvq5hnvdf6z78l16uj56s88w1n' LIMIT 1;
-- statement: connection 787
set autocommit=0;
-- statement: connection 787
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('8pjtqppvq5hnvdf6z78l16uj56s88w1n', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', '2026-11-18 07:19:09.096115');
-- statement: connection 787
commit;
-- statement: connection 787
set autocommit=1;
-- statement: connection 787
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 787
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 787
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 787
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 787
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 787
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 787
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'surfacegeometrytargetname' LIMIT 21;
-- statement: connection 787
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 787
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 787
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 787
CREATE TEMPORARY TABLE `temp_cache_6_748866_1793776749_104578` SELECT `sort_order`,`id` FROM `cache_6` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 787
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_6_748866_1793776749_104578` ON `obs_general`.`id`=`temp_cache_6_748866_1793776749_104578`.`id` ORDER BY `temp_cache_6_748866_1793776749_104578`.`sort_order`;
-- statement: connection 787
DROP TABLE `temp_cache_6_748866_1793776749_104578`;
-- statement: connection 787
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0;
-- statement: connection 787
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 787
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 787
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 787
set autocommit=0;
-- statement: connection 787
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.126152' WHERE `django_session`.`session_key` = '8pjtqppvq5hnvdf6z78l16uj56s88w1n';
-- statement: connection 787
commit;
-- statement: connection 787
set autocommit=1;

-- block: pages.surface_geometry/page_10 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=10&limit=100
-- statement: connection 788
SET NAMES utf8mb4;
-- statement: connection 788
set autocommit=0;
-- statement: connection 788
set autocommit=1;
-- statement: connection 788
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 788
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:09.131648' AND `django_session`.`session_key` = '8pjtqppvq5hnvdf6z78l16uj56s88w1n') LIMIT 21;
-- statement: connection 788
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 788
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 788
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 788
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 788
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 788
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 788
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 788
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 788
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 788
CREATE TEMPORARY TABLE `temp_cache_6_748866_1793776749_141160` SELECT `sort_order`,`id` FROM `cache_6` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 788
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_6_748866_1793776749_141160` ON `obs_general`.`id`=`temp_cache_6_748866_1793776749_141160`.`id` ORDER BY `temp_cache_6_748866_1793776749_141160`.`sort_order`;
-- statement: connection 788
DROP TABLE `temp_cache_6_748866_1793776749_141160`;
-- statement: connection 788
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 11;
-- statement: connection 788
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 7;
-- statement: connection 788
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 12;
-- statement: connection 788
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 788
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 788
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 788
set autocommit=0;
-- statement: connection 788
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.161254' WHERE `django_session`.`session_key` = '8pjtqppvq5hnvdf6z78l16uj56s88w1n';
-- statement: connection 788
commit;
-- statement: connection 788
set autocommit=1;

-- block: pages.surface_geometry/page_last api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=44&limit=100
-- statement: connection 789
SET NAMES utf8mb4;
-- statement: connection 789
set autocommit=0;
-- statement: connection 789
set autocommit=1;
-- statement: connection 789
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 789
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:09.167826' AND `django_session`.`session_key` = '8pjtqppvq5hnvdf6z78l16uj56s88w1n') LIMIT 21;
-- statement: connection 789
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 789
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 789
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 789
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 789
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 789
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 789
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 789
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 789
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 789
CREATE TEMPORARY TABLE `temp_cache_6_748866_1793776749_177832` SELECT `sort_order`,`id` FROM `cache_6` ORDER BY `sort_order` LIMIT 100 OFFSET 4300;
-- statement: connection 789
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_6_748866_1793776749_177832` ON `obs_general`.`id`=`temp_cache_6_748866_1793776749_177832`.`id` ORDER BY `temp_cache_6_748866_1793776749_177832`.`sort_order`;
-- statement: connection 789
DROP TABLE `temp_cache_6_748866_1793776749_177832`;
-- statement: connection 789
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 3;
-- statement: connection 789
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 789
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 789
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 789
set autocommit=0;
-- statement: connection 789
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.190059' WHERE `django_session`.`session_key` = '8pjtqppvq5hnvdf6z78l16uj56s88w1n';
-- statement: connection 789
commit;
-- statement: connection 789
set autocommit=1;

-- block: resort.empty/default_order api/data.json?page=1&limit=100
-- statement: connection 790
SET NAMES utf8mb4;
-- statement: connection 790
set autocommit=0;
-- statement: connection 790
set autocommit=1;
-- statement: connection 790
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 790
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'myddjc3ij0gp370bfecm1b5pp4vwif5y' LIMIT 1;
-- statement: connection 790
set autocommit=0;
-- statement: connection 790
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('myddjc3ij0gp370bfecm1b5pp4vwif5y', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', '2026-11-18 07:19:09.213520');
-- statement: connection 790
commit;
-- statement: connection 790
set autocommit=1;
-- statement: connection 790
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 790
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 790
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 790
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 790
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 790
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 790
CREATE TEMPORARY TABLE `temp_cache_1_748867_1793776749_217407` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 790
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_748867_1793776749_217407` ON `obs_general`.`id`=`temp_cache_1_748867_1793776749_217407`.`id` ORDER BY `temp_cache_1_748867_1793776749_217407`.`sort_order`;
-- statement: connection 790
DROP TABLE `temp_cache_1_748867_1793776749_217407`;
-- statement: connection 790
set autocommit=0;
-- statement: connection 790
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.226513' WHERE `django_session`.`session_key` = 'myddjc3ij0gp370bfecm1b5pp4vwif5y';
-- statement: connection 790
commit;
-- statement: connection 790
set autocommit=1;

-- block: resort.empty/resorted api/data.json?order=-time1,opusid&page=1&limit=100
-- statement: connection 791
SET NAMES utf8mb4;
-- statement: connection 791
set autocommit=0;
-- statement: connection 791
set autocommit=1;
-- statement: connection 791
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 791
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:09.232186' AND `django_session`.`session_key` = 'myddjc3ij0gp370bfecm1b5pp4vwif5y') LIMIT 21;
-- statement: connection 791
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 791
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 791
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 791
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 791
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 791
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 791
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{}', '99914b932bd37a50b983c5e7c90ae93b', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 791
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 791
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 791
CREATE TABLE `cache_7`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 791
CREATE TEMPORARY TABLE `temp_cache_7_748869_1793776749_438754` SELECT `sort_order`,`id` FROM `cache_7` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 791
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_7_748869_1793776749_438754` ON `obs_general`.`id`=`temp_cache_7_748869_1793776749_438754`.`id` ORDER BY `temp_cache_7_748869_1793776749_438754`.`sort_order`;
-- statement: connection 791
DROP TABLE `temp_cache_7_748869_1793776749_438754`;
-- statement: connection 791
SELECT COUNT(*) FROM `cache_7`;
-- statement: connection 791
set autocommit=0;
-- statement: connection 791
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.457840' WHERE `django_session`.`session_key` = 'myddjc3ij0gp370bfecm1b5pp4vwif5y';
-- statement: connection 791
commit;
-- statement: connection 791
set autocommit=1;

-- block: resort.broad/default_order api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 792
SET NAMES utf8mb4;
-- statement: connection 792
set autocommit=0;
-- statement: connection 792
set autocommit=1;
-- statement: connection 792
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 792
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'yj08mqfxwxe7bdnf6x7nmvxf66mvldh3' LIMIT 1;
-- statement: connection 792
set autocommit=0;
-- statement: connection 792
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('yj08mqfxwxe7bdnf6x7nmvxf66mvldh3', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', '2026-11-18 07:19:09.480980');
-- statement: connection 792
commit;
-- statement: connection 792
set autocommit=1;
-- statement: connection 792
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 792
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 792
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 792
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 792
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 792
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 792
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 792
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 792
CREATE TEMPORARY TABLE `temp_cache_2_748869_1793776749_492124` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 792
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_2_748869_1793776749_492124` ON `obs_general`.`id`=`temp_cache_2_748869_1793776749_492124`.`id` ORDER BY `temp_cache_2_748869_1793776749_492124`.`sort_order`;
-- statement: connection 792
DROP TABLE `temp_cache_2_748869_1793776749_492124`;
-- statement: connection 792
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 792
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 792
set autocommit=0;
-- statement: connection 792
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.508995' WHERE `django_session`.`session_key` = 'yj08mqfxwxe7bdnf6x7nmvxf66mvldh3';
-- statement: connection 792
commit;
-- statement: connection 792
set autocommit=1;

-- block: resort.broad/resorted api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&order=-time1,opusid&page=1&limit=100
-- statement: connection 793
SET NAMES utf8mb4;
-- statement: connection 793
set autocommit=0;
-- statement: connection 793
set autocommit=1;
-- statement: connection 793
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 793
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:09.513717' AND `django_session`.`session_key` = 'yj08mqfxwxe7bdnf6x7nmvxf66mvldh3') LIMIT 21;
-- statement: connection 793
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 793
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 793
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 793
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 793
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 793
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 793
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'f004842dd5ce1e4a6c4c68e89b50dd11', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 793
CREATE TABLE `cache_8`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0 ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 793
CREATE TEMPORARY TABLE `temp_cache_8_748869_1793776749_729625` SELECT `sort_order`,`id` FROM `cache_8` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 793
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_8_748869_1793776749_729625` ON `obs_general`.`id`=`temp_cache_8_748869_1793776749_729625`.`id` ORDER BY `temp_cache_8_748869_1793776749_729625`.`sort_order`;
-- statement: connection 793
DROP TABLE `temp_cache_8_748869_1793776749_729625`;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 793
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 793
SELECT COUNT(*) FROM `cache_8`;
-- statement: connection 793
set autocommit=0;
-- statement: connection 793
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.754852' WHERE `django_session`.`session_key` = 'yj08mqfxwxe7bdnf6x7nmvxf66mvldh3';
-- statement: connection 793
commit;
-- statement: connection 793
set autocommit=1;

-- block: resort.selective/default_order api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 794
SET NAMES utf8mb4;
-- statement: connection 794
set autocommit=0;
-- statement: connection 794
set autocommit=1;
-- statement: connection 794
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 794
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'cbagv70v6gm12wbuyxt509uh81wpf5r1' LIMIT 1;
-- statement: connection 794
set autocommit=0;
-- statement: connection 794
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('cbagv70v6gm12wbuyxt509uh81wpf5r1', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', '2026-11-18 07:19:09.777928');
-- statement: connection 794
commit;
-- statement: connection 794
set autocommit=1;
-- statement: connection 794
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 794
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 794
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 794
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 794
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 794
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 794
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 794
CREATE TEMPORARY TABLE `temp_cache_3_748867_1793776749_782430` SELECT `sort_order`,`id` FROM `cache_3` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 794
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_3_748867_1793776749_782430` ON `obs_general`.`id`=`temp_cache_3_748867_1793776749_782430`.`id` ORDER BY `temp_cache_3_748867_1793776749_782430`.`sort_order`;
-- statement: connection 794
DROP TABLE `temp_cache_3_748867_1793776749_782430`;
-- statement: connection 794
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 794
set autocommit=0;
-- statement: connection 794
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.797648' WHERE `django_session`.`session_key` = 'cbagv70v6gm12wbuyxt509uh81wpf5r1';
-- statement: connection 794
commit;
-- statement: connection 794
set autocommit=1;

-- block: resort.selective/resorted api/data.json?planet=Uranus&order=-time1,opusid&page=1&limit=100
-- statement: connection 795
SET NAMES utf8mb4;
-- statement: connection 795
set autocommit=0;
-- statement: connection 795
set autocommit=1;
-- statement: connection 795
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 795
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:09.802567' AND `django_session`.`session_key` = 'cbagv70v6gm12wbuyxt509uh81wpf5r1') LIMIT 21;
-- statement: connection 795
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 795
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 795
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 795
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 795
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 795
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 795
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 795
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Uranus\"]}', '033bcdee4b74d22264a9cf8648d2a2fc', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 795
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 795
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 795
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 795
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 795
CREATE TABLE `cache_9`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5) ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 795
CREATE TEMPORARY TABLE `temp_cache_9_748867_1793776749_827762` SELECT `sort_order`,`id` FROM `cache_9` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 795
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_9_748867_1793776749_827762` ON `obs_general`.`id`=`temp_cache_9_748867_1793776749_827762`.`id` ORDER BY `temp_cache_9_748867_1793776749_827762`.`sort_order`;
-- statement: connection 795
DROP TABLE `temp_cache_9_748867_1793776749_827762`;
-- statement: connection 795
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Uranus') OR `mult_obs_general_planet_id`.`value` IN ('Uranus'));
-- statement: connection 795
SELECT COUNT(*) FROM `cache_9`;
-- statement: connection 795
set autocommit=0;
-- statement: connection 795
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.843960' WHERE `django_session`.`session_key` = 'cbagv70v6gm12wbuyxt509uh81wpf5r1';
-- statement: connection 795
commit;
-- statement: connection 795
set autocommit=1;

-- block: resort.ring_radius/default_order api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 796
SET NAMES utf8mb4;
-- statement: connection 796
set autocommit=0;
-- statement: connection 796
set autocommit=1;
-- statement: connection 796
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 796
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'xsq72g90zwvshwyps8f8wdup3o0etlip' LIMIT 1;
-- statement: connection 796
set autocommit=0;
-- statement: connection 796
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('xsq72g90zwvshwyps8f8wdup3o0etlip', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', '2026-11-18 07:19:09.870027');
-- statement: connection 796
commit;
-- statement: connection 796
set autocommit=1;
-- statement: connection 796
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 796
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 796
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 796
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 796
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 796
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 796
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 796
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 796
CREATE TEMPORARY TABLE `temp_cache_4_748867_1793776749_879239` SELECT `sort_order`,`id` FROM `cache_4` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 796
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_4_748867_1793776749_879239` ON `obs_general`.`id`=`temp_cache_4_748867_1793776749_879239`.`id` ORDER BY `temp_cache_4_748867_1793776749_879239`.`sort_order`;
-- statement: connection 796
DROP TABLE `temp_cache_4_748867_1793776749_879239`;
-- statement: connection 796
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 796
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 796
set autocommit=0;
-- statement: connection 796
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH3:FUvT5ELh9Ru5YeCSzbf5RKGjFbqMdxvrudLhugvyjPk', `expire_date` = '2026-11-18 07:19:09.901910' WHERE `django_session`.`session_key` = 'xsq72g90zwvshwyps8f8wdup3o0etlip';
-- statement: connection 796
commit;
-- statement: connection 796
set autocommit=1;

-- block: resort.ring_radius/resorted api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&order=-time1,opusid&page=1&limit=100
-- statement: connection 797
SET NAMES utf8mb4;
-- statement: connection 797
set autocommit=0;
-- statement: connection 797
set autocommit=1;
-- statement: connection 797
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 797
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:09.907784' AND `django_session`.`session_key` = 'xsq72g90zwvshwyps8f8wdup3o0etlip') LIMIT 21;
-- statement: connection 797
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 797
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 797
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 797
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 797
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 797
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 797
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_ring_geometry.ring_radius1\": [60000.0], \"obs_ring_geometry.ring_radius2\": [140000.0]}', '3e9f393e09dfa2c750cdae5be4a34297', '{\"obs_ring_geometry.ring_radius\": [\"any\"]}', 'd58efe915310b90c76b4d3e3c419cba8', '{\"obs_ring_geometry.ring_radius\": [\"km\"]}', '70f0bb7407a66538767b4dee465f5022', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius2') LIMIT 21;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 797
CREATE TABLE `cache_10`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0 ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 797
CREATE TEMPORARY TABLE `temp_cache_10_748867_1793776750_069992` SELECT `sort_order`,`id` FROM `cache_10` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 797
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_10_748867_1793776750_069992` ON `obs_general`.`id`=`temp_cache_10_748867_1793776750_069992`.`id` ORDER BY `temp_cache_10_748867_1793776750_069992`.`sort_order`;
-- statement: connection 797
DROP TABLE `temp_cache_10_748867_1793776750_069992`;
-- statement: connection 797
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 3;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 797
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 797
SELECT COUNT(*) FROM `cache_10`;
-- statement: connection 797
set autocommit=0;
-- statement: connection 797
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH4:L6S3J9ksARSqrTy9--ITtkctGnOj2bMtdGjj1lZFpf8', `expire_date` = '2026-11-18 07:19:10.093425' WHERE `django_session`.`session_key` = 'xsq72g90zwvshwyps8f8wdup3o0etlip';
-- statement: connection 797
commit;
-- statement: connection 797
set autocommit=1;

-- block: resort.target/default_order api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 798
SET NAMES utf8mb4;
-- statement: connection 798
set autocommit=0;
-- statement: connection 798
set autocommit=1;
-- statement: connection 798
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 798
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'ffmi3f6zfdebkot89ma919z5826c6s3w' LIMIT 1;
-- statement: connection 798
set autocommit=0;
-- statement: connection 798
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('ffmi3f6zfdebkot89ma919z5826c6s3w', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH4:L6S3J9ksARSqrTy9--ITtkctGnOj2bMtdGjj1lZFpf8', '2026-11-18 07:19:10.116516');
-- statement: connection 798
commit;
-- statement: connection 798
set autocommit=1;
-- statement: connection 798
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 798
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 798
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 798
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 798
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 798
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 798
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 798
CREATE TEMPORARY TABLE `temp_cache_5_748869_1793776750_120891` SELECT `sort_order`,`id` FROM `cache_5` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 798
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_5_748869_1793776750_120891` ON `obs_general`.`id`=`temp_cache_5_748869_1793776750_120891`.`id` ORDER BY `temp_cache_5_748869_1793776750_120891`.`sort_order`;
-- statement: connection 798
DROP TABLE `temp_cache_5_748869_1793776750_120891`;
-- statement: connection 798
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 798
set autocommit=0;
-- statement: connection 798
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH4:L6S3J9ksARSqrTy9--ITtkctGnOj2bMtdGjj1lZFpf8', `expire_date` = '2026-11-18 07:19:10.134711' WHERE `django_session`.`session_key` = 'ffmi3f6zfdebkot89ma919z5826c6s3w';
-- statement: connection 798
commit;
-- statement: connection 798
set autocommit=1;

-- block: resort.target/resorted api/data.json?target=Saturn&order=-time1,opusid&page=1&limit=100
-- statement: connection 799
SET NAMES utf8mb4;
-- statement: connection 799
set autocommit=0;
-- statement: connection 799
set autocommit=1;
-- statement: connection 799
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 799
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:10.140626' AND `django_session`.`session_key` = 'ffmi3f6zfdebkot89ma919z5826c6s3w') LIMIT 21;
-- statement: connection 799
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 799
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 799
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 799
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 799
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 799
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 799
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 799
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.target_name\": [\"Saturn\"]}', '0808ab16043b8e7fcebb7ff7ab9500d9', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 799
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 799
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 799
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 799
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 799
CREATE TABLE `cache_11`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,'1') ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 799
CREATE TEMPORARY TABLE `temp_cache_11_748869_1793776750_239229` SELECT `sort_order`,`id` FROM `cache_11` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 799
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_11_748869_1793776750_239229` ON `obs_general`.`id`=`temp_cache_11_748869_1793776750_239229`.`id` ORDER BY `temp_cache_11_748869_1793776750_239229`.`sort_order`;
-- statement: connection 799
DROP TABLE `temp_cache_11_748869_1793776750_239229`;
-- statement: connection 799
SELECT `mult_obs_general_target_name`.`id` AS `pk` FROM `mult_obs_general_target_name` WHERE (`mult_obs_general_target_name`.`label` IN ('Saturn') OR `mult_obs_general_target_name`.`value` IN ('Saturn'));
-- statement: connection 799
SELECT COUNT(*) FROM `cache_11`;
-- statement: connection 799
set autocommit=0;
-- statement: connection 799
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH4:L6S3J9ksARSqrTy9--ITtkctGnOj2bMtdGjj1lZFpf8', `expire_date` = '2026-11-18 07:19:10.256734' WHERE `django_session`.`session_key` = 'ffmi3f6zfdebkot89ma919z5826c6s3w';
-- statement: connection 799
commit;
-- statement: connection 799
set autocommit=1;

-- block: resort.surface_geometry/default_order api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 800
SET NAMES utf8mb4;
-- statement: connection 800
set autocommit=0;
-- statement: connection 800
set autocommit=1;
-- statement: connection 800
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 800
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'dy013mia4bhwuv41gyhngalfcl2g7ad7' LIMIT 1;
-- statement: connection 800
set autocommit=0;
-- statement: connection 800
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('dy013mia4bhwuv41gyhngalfcl2g7ad7', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH4:L6S3J9ksARSqrTy9--ITtkctGnOj2bMtdGjj1lZFpf8', '2026-11-18 07:19:10.288813');
-- statement: connection 800
commit;
-- statement: connection 800
set autocommit=1;
-- statement: connection 800
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 800
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 800
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 800
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 800
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 800
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 800
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 800
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 800
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 800
CREATE TEMPORARY TABLE `temp_cache_6_748866_1793776750_298892` SELECT `sort_order`,`id` FROM `cache_6` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 800
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_6_748866_1793776750_298892` ON `obs_general`.`id`=`temp_cache_6_748866_1793776750_298892`.`id` ORDER BY `temp_cache_6_748866_1793776750_298892`.`sort_order`;
-- statement: connection 800
DROP TABLE `temp_cache_6_748866_1793776750_298892`;
-- statement: connection 800
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 800
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 800
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 800
set autocommit=0;
-- statement: connection 800
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH4:L6S3J9ksARSqrTy9--ITtkctGnOj2bMtdGjj1lZFpf8', `expire_date` = '2026-11-18 07:19:10.321158' WHERE `django_session`.`session_key` = 'dy013mia4bhwuv41gyhngalfcl2g7ad7';
-- statement: connection 800
commit;
-- statement: connection 800
set autocommit=1;

-- block: resort.surface_geometry/resorted api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&order=-time1,opusid&page=1&limit=100
-- statement: connection 801
SET NAMES utf8mb4;
-- statement: connection 801
set autocommit=0;
-- statement: connection 801
set autocommit=1;
-- statement: connection 801
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 801
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:10.327608' AND `django_session`.`session_key` = 'dy013mia4bhwuv41gyhngalfcl2g7ad7') LIMIT 21;
-- statement: connection 801
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 801
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 801
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 801
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 801
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 801
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 801
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 801
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_surface_geometry__saturn.planetographic_latitude1\": [-30.0], \"obs_surface_geometry__saturn.planetographic_latitude2\": [30.0], \"obs_surface_geometry_name.target_name\": [\"Saturn\"]}', '907ec5896a8bd3771dd91f22743140d1', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"any\"]}', '2998cdc1c9b87c33e7ac2c27b2011182', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"degrees\"]}', '77ac08a838ce071f52f224163fc043dc', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude2') LIMIT 21;
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 801
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 801
CREATE TABLE `cache_12`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` LEFT JOIN `obs_surface_geometry_name` ON `obs_general`.`id`=`obs_surface_geometry_name`.`obs_general_id` WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (`obs_surface_geometry_name`.`target_name` IN (6)) ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 801
CREATE TEMPORARY TABLE `temp_cache_12_748869_1793776750_407654` SELECT `sort_order`,`id` FROM `cache_12` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 801
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_12_748869_1793776750_407654` ON `obs_general`.`id`=`temp_cache_12_748869_1793776750_407654`.`id` ORDER BY `temp_cache_12_748869_1793776750_407654`.`sort_order`;
-- statement: connection 801
DROP TABLE `temp_cache_12_748869_1793776750_407654`;
-- statement: connection 801
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `pk` FROM `mult_obs_surface_geometry_name_target_name` WHERE (`mult_obs_surface_geometry_name_target_name`.`label` IN ('Saturn') OR `mult_obs_surface_geometry_name_target_name`.`value` IN ('Saturn'));
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 801
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 801
SELECT COUNT(*) FROM `cache_12`;
-- statement: connection 801
set autocommit=0;
-- statement: connection 801
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH4:L6S3J9ksARSqrTy9--ITtkctGnOj2bMtdGjj1lZFpf8', `expire_date` = '2026-11-18 07:19:10.432654' WHERE `django_session`.`session_key` = 'dy013mia4bhwuv41gyhngalfcl2g7ad7';
-- statement: connection 801
commit;
-- statement: connection 801
set autocommit=1;

-- block: fanout.empty/result_count __api/meta/result_count.json?reqno=1
-- statement: connection 802
SET NAMES utf8mb4;
-- statement: connection 802
set autocommit=0;
-- statement: connection 802
set autocommit=1;
-- statement: connection 802
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- block: fanout.empty/mults_instrument __api/meta/mults/instrument.json?reqno=1
-- statement: connection 803
SET NAMES utf8mb4;
-- statement: connection 803
set autocommit=0;
-- statement: connection 803
set autocommit=1;
-- statement: connection 803
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 803
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general` GROUP BY `obs_general`.`instrument_id`;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 0 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 1 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 2 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 3 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 4 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 5 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 6 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 7 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 8 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 9 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 10 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 12 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 13 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 14 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 15 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 16 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 17 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 132 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 134 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 164 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 172 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 204 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 226 LIMIT 21;
-- statement: connection 803
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 500 LIMIT 21;

-- block: fanout.empty/mults_observationtype __api/meta/mults/observationtype.json?reqno=1
-- statement: connection 804
SET NAMES utf8mb4;
-- statement: connection 804
set autocommit=0;
-- statement: connection 804
set autocommit=1;
-- statement: connection 804
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 804
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationtype' LIMIT 21;
-- statement: connection 804
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general` GROUP BY `obs_general`.`observation_type`;
-- statement: connection 804
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 0 LIMIT 21;
-- statement: connection 804
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 4 LIMIT 21;
-- statement: connection 804
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 5 LIMIT 21;
-- statement: connection 804
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 6 LIMIT 21;
-- statement: connection 804
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 3 LIMIT 21;
-- statement: connection 804
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 2 LIMIT 21;
-- statement: connection 804
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 7 LIMIT 21;
-- statement: connection 804
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 8 LIMIT 21;

-- block: fanout.empty/mults_target __api/meta/mults/target.json?reqno=1
-- statement: connection 805
SET NAMES utf8mb4;
-- statement: connection 805
set autocommit=0;
-- statement: connection 805
set autocommit=1;
-- statement: connection 805
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 805
SELECT `obs_general`.`_mult_val_`,COUNT(*) AS `target_name__count` FROM `obs_general` INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]" COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general` GROUP BY `obs_general`.`_mult_val_`;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 2 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 3 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 4 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 5 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 6 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 7 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 8 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 9 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 10 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 11 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 12 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 13 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 14 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 15 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 16 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 17 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 18 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 19 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 20 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 21 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 22 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 23 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 24 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 25 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 26 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 27 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 28 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 29 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 30 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 31 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 32 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 33 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 34 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 35 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 36 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 37 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 38 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 39 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 40 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 41 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 42 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 43 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 44 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 45 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 46 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 47 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 48 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 49 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 50 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 51 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 52 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 53 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 54 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 55 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 56 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 57 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 58 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 59 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 60 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 61 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 62 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 63 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 64 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 65 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 66 LIMIT 21;
-- statement: connection 805
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 67 LIMIT 21;

-- block: fanout.empty/endpoints_time1 __api/meta/range/endpoints/time1.json?reqno=1
-- statement: connection 806
SET NAMES utf8mb4;
-- statement: connection 806
set autocommit=0;
-- statement: connection 806
set autocommit=1;
-- statement: connection 806
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 806
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 806
SELECT MIN(`obs_general`.`time1`) AS `min`, MAX(`obs_general`.`time2`) AS `max` FROM `obs_general`;
-- statement: connection 806
SELECT COUNT(*) AS `__count` FROM `obs_general` WHERE (`obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL);

-- block: fanout.empty/menu __menu.json?reqno=1
-- statement: connection 807
SET NAMES utf8mb4;
-- statement: connection 807
set autocommit=0;
-- statement: connection 807
set autocommit=1;
-- statement: connection 807
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_ring_geometry', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_wavelength', 'obs_type_image', 'obs_profile') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE (`table_names`.`display` = 'Y' AND `table_names`.`table_name` IN ('obs_general', 'obs_pds', 'obs_ring_geometry', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_wavelength', 'obs_type_image', 'obs_profile')) ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOsolarringopeningangle1' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOobserverringopeningangle1' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'TARGET_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'TARGET_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'MISSION_NAME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'MISSION_NAME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_HOST_NAME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_HOST_NAME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_ID') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_ID') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'OBSERVATION_TIME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'OBSERVATION_TIME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_DURATION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_DURATION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'MEASUREMENT_QUANTITY_NAME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'MEASUREMENT_QUANTITY_NAME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'RIGHT_ASCENSION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'RIGHT_ASCENSION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'DECLINATION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'DECLINATION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'BUNDLE_ID') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'BUNDLE_ID') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'DATA_SET_ID') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'DATA_SET_ID') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_ID') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_ID') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRIMARY_LID') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRIMARY_LID') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_CREATION_TIME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_CREATION_TIME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'FILE_SPECIFICATION_NAME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'FILE_SPECIFICATION_NAME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OPUS_ID') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OPUS_ID') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'NOTE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'NOTE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'EXPOSURE_DURATION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'EXPOSURE_DURATION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'GREATER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'GREATER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'LESSER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'LESSER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'INTENSITY_LEVELS') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'INTENSITY_LEVELS') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'IMAGE_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'IMAGE_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRAL_INFORMATION_FLAG') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRAL_INFORMATION_FLAG') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRUM_SIZE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRUM_SIZE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'RECEIVED_POLARIZATION_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'RECEIVED_POLARIZATION_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_TYPE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_DIR') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_DIR') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'BODY_OCCULTATION_FLAG') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'BODY_OCCULTATION_FLAG') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'TEMPORAL_SAMPLING_INTERVAL') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'TEMPORAL_SAMPLING_INTERVAL') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DATA_QUALITY_SCORE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DATA_QUALITY_SCORE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DETECTABLE_OPTICAL_DEPTH') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DETECTABLE_OPTICAL_DEPTH') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'WAVELENGTH_BAND') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'WAVELENGTH_BAND') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_SOURCE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_SOURCE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_RECEIVER_HOST') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_RECEIVER_HOST') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_surface_geometry_name' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_surface_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_LIST') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_LIST') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_ASCENDING_NODE_RING_LONGITUDE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_ASCENDING_NODE_RING_LONGITUDE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_J2000_RING_LONGITUDE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_J2000_RING_LONGITUDE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_OBSERVER') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_OBSERVER') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_AZIMUTH') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_AZIMUTH') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DISTANCE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DISTANCE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_DISTANCE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_DISTANCE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_PHASE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_PHASE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_ELEVATION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_ELEVATION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_ELEVATION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_ELEVATION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_PHASE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_PHASE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_RADIUS') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_RADIUS') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_INTERCEPT_DISTANCE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_INTERCEPT_DISTANCE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_ALTITUDE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_ALTITUDE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DIAMETER_IN_PIXELS') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DIAMETER_IN_PIXELS') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_X_COORDINATE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_X_COORDINATE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_Y_COORDINATE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_Y_COORDINATE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_CLOCK_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_CLOCK_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_POSITION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_POSITION_ANGLE') LIMIT 21;
-- statement: connection 807
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_TIME') LIMIT 21;
-- statement: connection 807
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_TIME') LIMIT 21;

-- block: fanout.selected/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 808
SET NAMES utf8mb4;
-- statement: connection 808
set autocommit=0;
-- statement: connection 808
set autocommit=1;
-- statement: connection 808
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 808
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 808
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Saturn\"], \"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'c206354df622b9bebeb095d3bb4039d7', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 808
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 808
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 808
CREATE TABLE `cache_13`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`planet_id` IN (4)) AND (`obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 808
SELECT COUNT(*) FROM `cache_13`;

-- block: fanout.selected/mults_instrument __api/meta/mults/instrument.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 809
SET NAMES utf8mb4;
-- statement: connection 809
set autocommit=0;
-- statement: connection 809
set autocommit=1;
-- statement: connection 809
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 809
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 809
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 809
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`instrument_id`;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 1 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 4 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 0 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 6 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 13 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 132 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 134 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 164 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 500 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 204 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 226 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 2 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 3 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 7 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 9 LIMIT 21;
-- statement: connection 809
SELECT `mult_obs_general_instrument_id`.`id`, `mult_obs_general_instrument_id`.`value`, `mult_obs_general_instrument_id`.`label`, `mult_obs_general_instrument_id`.`disp_order`, `mult_obs_general_instrument_id`.`display`, `mult_obs_general_instrument_id`.`grouping`, `mult_obs_general_instrument_id`.`group_disp_order`, `mult_obs_general_instrument_id`.`timestamp` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 8 LIMIT 21;

-- block: fanout.selected/mults_observationtype __api/meta/mults/observationtype.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 810
SET NAMES utf8mb4;
-- statement: connection 810
set autocommit=0;
-- statement: connection 810
set autocommit=1;
-- statement: connection 810
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 810
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 810
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 810
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 810
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`observation_type`;
-- statement: connection 810
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 0 LIMIT 21;
-- statement: connection 810
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 4 LIMIT 21;
-- statement: connection 810
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 5 LIMIT 21;
-- statement: connection 810
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 6 LIMIT 21;
-- statement: connection 810
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 2 LIMIT 21;
-- statement: connection 810
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 7 LIMIT 21;
-- statement: connection 810
SELECT `mult_obs_general_observation_type`.`id`, `mult_obs_general_observation_type`.`value`, `mult_obs_general_observation_type`.`label`, `mult_obs_general_observation_type`.`disp_order`, `mult_obs_general_observation_type`.`display`, `mult_obs_general_observation_type`.`grouping`, `mult_obs_general_observation_type`.`group_disp_order`, `mult_obs_general_observation_type`.`timestamp` FROM `mult_obs_general_observation_type` WHERE `mult_obs_general_observation_type`.`id` = 8 LIMIT 21;

-- block: fanout.selected/mults_target __api/meta/mults/target.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 811
SET NAMES utf8mb4;
-- statement: connection 811
set autocommit=0;
-- statement: connection 811
set autocommit=1;
-- statement: connection 811
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 811
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 811
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 811
SELECT `obs_general`.`_mult_val_`,COUNT(*) AS `target_name__count` FROM `obs_general` INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]" COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`_mult_val_`;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 0 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 1 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 2 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 3 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 4 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 5 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 6 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 7 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 8 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 9 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 10 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 11 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 12 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 13 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 14 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 15 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 16 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 17 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 18 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 19 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 20 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 21 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 22 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 23 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 24 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 25 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 26 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 27 LIMIT 21;
-- statement: connection 811
SELECT `mult_obs_general_target_name`.`id`, `mult_obs_general_target_name`.`value`, `mult_obs_general_target_name`.`label`, `mult_obs_general_target_name`.`disp_order`, `mult_obs_general_target_name`.`display`, `mult_obs_general_target_name`.`grouping`, `mult_obs_general_target_name`.`group_disp_order`, `mult_obs_general_target_name`.`timestamp` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 28 LIMIT 21;

-- block: fanout.selected/endpoints_time1 __api/meta/range/endpoints/time1.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 812
SET NAMES utf8mb4;
-- statement: connection 812
set autocommit=0;
-- statement: connection 812
set autocommit=1;
-- statement: connection 812
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 812
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 812
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 812
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 812
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Saturn\"]}', '6b21f5786b92be236703ae293679a2c3', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 812
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 812
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 812
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 812
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 812
CREATE TABLE `cache_14`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (4) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 812
SELECT MIN(`obs_general`.`time1`),MAX(`obs_general`.`time2`) FROM `obs_general`,`cache_14` WHERE `obs_general`.`id`=`cache_14`.`id`;
-- statement: connection 812
SELECT COUNT(*) FROM `obs_general`,`cache_14` WHERE `obs_general`.`id`=`cache_14`.`id` AND `obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL;

-- block: fanout.selected/menu __menu.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 813
SET NAMES utf8mb4;
-- statement: connection 813
set autocommit=0;
-- statement: connection 813
set autocommit=1;
-- statement: connection 813
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 813
SELECT `mult_obs_general_planet_id`.`id` AS `pk` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`label` IN ('Saturn') OR `mult_obs_general_planet_id`.`value` IN ('Saturn'));
-- statement: connection 813
SELECT `partables`.`id`, `partables`.`trigger_tab`, `partables`.`trigger_col`, `partables`.`trigger_val`, `partables`.`partable`, `partables`.`timestamp` FROM `partables`;
-- statement: connection 813
SELECT DISTINCT `obs_general`.`mission_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
-- statement: connection 813
SELECT DISTINCT `obs_general`.`instrument_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
-- statement: connection 813
SELECT DISTINCT `obs_general`.`inst_host_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
-- statement: connection 813
SELECT `table_names`.`table_name` AS `table_name` FROM `table_names` WHERE `table_names`.`table_name` IN ('obs_general', 'obs_pds', 'obs_ring_geometry', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_wavelength', 'obs_type_image', 'obs_profile') ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` IN ('obs_general', 'obs_pds', 'obs_type_image', 'obs_wavelength', 'obs_profile', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_ring_geometry') AND `param_info`.`display` = '1') ORDER BY `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE (`table_names`.`display` = 'Y' AND `table_names`.`table_name` IN ('obs_general', 'obs_pds', 'obs_type_image', 'obs_wavelength', 'obs_profile', 'obs_surface_geometry_name', 'obs_surface_geometry', 'obs_ring_geometry')) ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_type_image' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_wavelength' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_profile' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry' AND `param_info`.`display` = '1') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Radius & Longitude') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Distance & Resolution') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Observed') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Lighting Geometry - Ring Center') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Edge-On Viewing Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Image Geometry') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Pole') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`display` = '1' AND `param_info`.`sub_heading` = 'Timing') ORDER BY `param_info`.`category_name` ASC, `param_info`.`sub_heading` ASC, `param_info`.`disp_order` ASC;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'TARGET_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'TARGET_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'MISSION_NAME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'MISSION_NAME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_HOST_NAME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_HOST_NAME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_ID') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'INSTRUMENT_ID') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'OBSERVATION_TIME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'OBSERVATION_TIME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_DURATION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OBSERVATION_DURATION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'MEASUREMENT_QUANTITY_NAME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'MEASUREMENT_QUANTITY_NAME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'RIGHT_ASCENSION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'RIGHT_ASCENSION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'DECLINATION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'DECLINATION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'BUNDLE_ID') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'BUNDLE_ID') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'DATA_SET_ID') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'DATA_SET_ID') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_ID') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_ID') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRIMARY_LID') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRIMARY_LID') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_CREATION_TIME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'PRODUCT_CREATION_TIME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'FILE_SPECIFICATION_NAME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'FILE_SPECIFICATION_NAME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OPUS_ID') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL' AND `definitions`.`term` = 'OPUS_ID') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'NOTE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PDS' AND `definitions`.`term` = 'NOTE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'EXPOSURE_DURATION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'EXPOSURE_DURATION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'GREATER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'GREATER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'LESSER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'LESSER_PIXEL_SIZE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'INTENSITY_LEVELS') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'INTENSITY_LEVELS') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_type_image' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'IMAGE_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_TYPE_IMAGE' AND `definitions`.`term` = 'IMAGE_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVELENGTH_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'WAVENUMBER_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRAL_INFORMATION_FLAG') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRAL_INFORMATION_FLAG') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRUM_SIZE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'SPECTRUM_SIZE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_wavelength' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'RECEIVED_POLARIZATION_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_WAVELENGTH' AND `definitions`.`term` = 'RECEIVED_POLARIZATION_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_TYPE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_DIR') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_DIR') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'BODY_OCCULTATION_FLAG') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'BODY_OCCULTATION_FLAG') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'TEMPORAL_SAMPLING_INTERVAL') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'TEMPORAL_SAMPLING_INTERVAL') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DATA_QUALITY_SCORE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DATA_QUALITY_SCORE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DETECTABLE_OPTICAL_DEPTH') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'DETECTABLE_OPTICAL_DEPTH') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'WAVELENGTH_BAND') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'WAVELENGTH_BAND') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_SOURCE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_SOURCE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_profile' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_RECEIVER_HOST') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PROFILE' AND `definitions`.`term` = 'OCCULTATION_RECEIVER_HOST') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_surface_geometry_name' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_NAME') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_surface_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_LIST') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'SURFACE_GEO' AND `definitions`.`term` = 'TARGET_LIST') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_RADIUS') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_ASCENDING_NODE_RING_LONGITUDE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_ASCENDING_NODE_RING_LONGITUDE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_J2000_RING_LONGITUDE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_SOLAR_J2000_RING_LONGITUDE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SUB_OBSERVER_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_OBSERVER') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_LONGITUDE_WRT_OBSERVER') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_AZIMUTH') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_AZIMUTH') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DISTANCE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DISTANCE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_DISTANCE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_DISTANCE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'LONGITUDINAL_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_PHASE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_PHASE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_ELEVATION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_ELEVATION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_ELEVATION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_ELEVATION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_PHASE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_PHASE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'SOLAR_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'OBSERVER_RING_OPENING_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_RADIUS') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_RADIUS') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_ASCENDING_NODE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_LONGITUDE_WRT_RA_ZERO') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_SOLAR_HOUR_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_INTERCEPT_DISTANCE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_INTERCEPT_DISTANCE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RADIAL_RESOLUTION') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_ALTITUDE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'EDGE_ON_RING_ALTITUDE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DIAMETER_IN_PIXELS') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_DIAMETER_IN_PIXELS') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_X_COORDINATE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_X_COORDINATE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_Y_COORDINATE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'CENTER_Y_COORDINATE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_CLOCK_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_CLOCK_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_POSITION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_POLE_POSITION_ANGLE') LIMIT 21;
-- statement: connection 813
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_ring_geometry' LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_TIME') LIMIT 21;
-- statement: connection 813
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'RING_GEO' AND `definitions`.`term` = 'RING_INTERCEPT_TIME') LIMIT 21;

-- block: widget.planet/widget __widget/planet.html
-- statement: connection 814
SET NAMES utf8mb4;
-- statement: connection 814
set autocommit=0;
-- statement: connection 814
set autocommit=1;
-- statement: connection 814
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 814
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_GENERAL_SEARCH' AND `definitions`.`term` = 'PLANET_NAME') LIMIT 21;
-- statement: connection 814
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE `mult_obs_general_planet_id`.`grouping` IS NULL;
-- statement: connection 814
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 814
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`display` = 'Y' AND `mult_obs_general_planet_id`.`grouping` IS NULL) ORDER BY `mult_obs_general_planet_id`.`disp_order` ASC;
-- statement: connection 814
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE `mult_obs_general_planet_id`.`display` = 'Y' ORDER BY `mult_obs_general_planet_id`.`disp_order` ASC;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'VEN') LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'EAR') LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'MAR') LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'JUP') LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'SAT') LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'URA') LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'NEP') LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'PLU') LIMIT 21;
-- statement: connection 814
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'MULT_PLANET' AND `definitions`.`term` = 'OTH') LIMIT 21;
-- statement: connection 814
SELECT DISTINCT `mult_obs_general_planet_id`.`grouping` AS `grouping`, `mult_obs_general_planet_id`.`group_disp_order` FROM `mult_obs_general_planet_id` ORDER BY `mult_obs_general_planet_id`.`group_disp_order` ASC;
-- statement: connection 814
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;

-- block: categories/categories api/categories/co-iss-w1477654052.json
-- statement: connection 815
SET NAMES utf8mb4;
-- statement: connection 815
set autocommit=0;
-- statement: connection 815
set autocommit=1;
-- statement: connection 815
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 815
SELECT `table_names`.`table_name` AS `table_name`, `table_names`.`label` AS `label` FROM `table_names` ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 815
SELECT `obs_general`.`opus_id` AS `opus_id` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_pds`.`opus_id` AS `opus_id` FROM `obs_pds` INNER JOIN `obs_general` ON (`obs_pds`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_type_image`.`opus_id` AS `opus_id` FROM `obs_type_image` INNER JOIN `obs_general` ON (`obs_type_image`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_wavelength`.`opus_id` AS `opus_id` FROM `obs_wavelength` INNER JOIN `obs_general` ON (`obs_wavelength`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_profile`.`opus_id` AS `opus_id` FROM `obs_profile` INNER JOIN `obs_general` ON (`obs_profile`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry`.`opus_id` AS `opus_id` FROM `obs_surface_geometry` INNER JOIN `obs_general` ON (`obs_surface_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__adrastea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__adrastea` INNER JOIN `obs_general` ON (`obs_surface_geometry__adrastea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__aegaeon`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__aegaeon` INNER JOIN `obs_general` ON (`obs_surface_geometry__aegaeon`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__amalthea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__amalthea` INNER JOIN `obs_general` ON (`obs_surface_geometry__amalthea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__anthe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__anthe` INNER JOIN `obs_general` ON (`obs_surface_geometry__anthe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__atlas`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__atlas` INNER JOIN `obs_general` ON (`obs_surface_geometry__atlas`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__callisto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__callisto` INNER JOIN `obs_general` ON (`obs_surface_geometry__callisto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__calypso`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__calypso` INNER JOIN `obs_general` ON (`obs_surface_geometry__calypso`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__charon`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__charon` INNER JOIN `obs_general` ON (`obs_surface_geometry__charon`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__daphnis`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__daphnis` INNER JOIN `obs_general` ON (`obs_surface_geometry__daphnis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__despina`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__despina` INNER JOIN `obs_general` ON (`obs_surface_geometry__despina`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__dione`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__dione` INNER JOIN `obs_general` ON (`obs_surface_geometry__dione`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__enceladus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__enceladus` INNER JOIN `obs_general` ON (`obs_surface_geometry__enceladus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__epimetheus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__epimetheus` INNER JOIN `obs_general` ON (`obs_surface_geometry__epimetheus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__europa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__europa` INNER JOIN `obs_general` ON (`obs_surface_geometry__europa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__galatea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__galatea` INNER JOIN `obs_general` ON (`obs_surface_geometry__galatea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__ganymede`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__ganymede` INNER JOIN `obs_general` ON (`obs_surface_geometry__ganymede`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__helene`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__helene` INNER JOIN `obs_general` ON (`obs_surface_geometry__helene`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__hydra`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__hydra` INNER JOIN `obs_general` ON (`obs_surface_geometry__hydra`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__hyperion`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__hyperion` INNER JOIN `obs_general` ON (`obs_surface_geometry__hyperion`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__iapetus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__iapetus` INNER JOIN `obs_general` ON (`obs_surface_geometry__iapetus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__io`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__io` INNER JOIN `obs_general` ON (`obs_surface_geometry__io`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__janus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__janus` INNER JOIN `obs_general` ON (`obs_surface_geometry__janus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__jupiter`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__jupiter` INNER JOIN `obs_general` ON (`obs_surface_geometry__jupiter`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__kerberos`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__kerberos` INNER JOIN `obs_general` ON (`obs_surface_geometry__kerberos`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__larissa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__larissa` INNER JOIN `obs_general` ON (`obs_surface_geometry__larissa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__methone`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__methone` INNER JOIN `obs_general` ON (`obs_surface_geometry__methone`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__metis`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__metis` INNER JOIN `obs_general` ON (`obs_surface_geometry__metis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__mimas`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__mimas` INNER JOIN `obs_general` ON (`obs_surface_geometry__mimas`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__naiad`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__naiad` INNER JOIN `obs_general` ON (`obs_surface_geometry__naiad`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__neptune`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__neptune` INNER JOIN `obs_general` ON (`obs_surface_geometry__neptune`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__nereid`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__nereid` INNER JOIN `obs_general` ON (`obs_surface_geometry__nereid`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__nix`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__nix` INNER JOIN `obs_general` ON (`obs_surface_geometry__nix`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__pallene`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pallene` INNER JOIN `obs_general` ON (`obs_surface_geometry__pallene`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__pan`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pan` INNER JOIN `obs_general` ON (`obs_surface_geometry__pan`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__pandora`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pandora` INNER JOIN `obs_general` ON (`obs_surface_geometry__pandora`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__phoebe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__phoebe` INNER JOIN `obs_general` ON (`obs_surface_geometry__phoebe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__pluto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pluto` INNER JOIN `obs_general` ON (`obs_surface_geometry__pluto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__polydeuces`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__polydeuces` INNER JOIN `obs_general` ON (`obs_surface_geometry__polydeuces`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__prometheus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__prometheus` INNER JOIN `obs_general` ON (`obs_surface_geometry__prometheus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__proteus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__proteus` INNER JOIN `obs_general` ON (`obs_surface_geometry__proteus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__rhea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__rhea` INNER JOIN `obs_general` ON (`obs_surface_geometry__rhea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__saturn`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__saturn` INNER JOIN `obs_general` ON (`obs_surface_geometry__saturn`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__styx`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__styx` INNER JOIN `obs_general` ON (`obs_surface_geometry__styx`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__telesto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__telesto` INNER JOIN `obs_general` ON (`obs_surface_geometry__telesto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__tethys`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__tethys` INNER JOIN `obs_general` ON (`obs_surface_geometry__tethys`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__thalassa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__thalassa` INNER JOIN `obs_general` ON (`obs_surface_geometry__thalassa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__thebe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__thebe` INNER JOIN `obs_general` ON (`obs_surface_geometry__thebe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__titan`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__titan` INNER JOIN `obs_general` ON (`obs_surface_geometry__titan`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_surface_geometry__triton`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__triton` INNER JOIN `obs_general` ON (`obs_surface_geometry__triton`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_ring_geometry`.`opus_id` AS `opus_id` FROM `obs_ring_geometry` INNER JOIN `obs_general` ON (`obs_ring_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_mission_cassini`.`opus_id` AS `opus_id` FROM `obs_mission_cassini` INNER JOIN `obs_general` ON (`obs_mission_cassini`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_mission_galileo`.`opus_id` AS `opus_id` FROM `obs_mission_galileo` INNER JOIN `obs_general` ON (`obs_mission_galileo`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_mission_hubble`.`opus_id` AS `opus_id` FROM `obs_mission_hubble` INNER JOIN `obs_general` ON (`obs_mission_hubble`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_mission_new_horizons`.`opus_id` AS `opus_id` FROM `obs_mission_new_horizons` INNER JOIN `obs_general` ON (`obs_mission_new_horizons`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_mission_voyager`.`opus_id` AS `opus_id` FROM `obs_mission_voyager` INNER JOIN `obs_general` ON (`obs_mission_voyager`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_instrument_cocirs`.`opus_id` AS `opus_id` FROM `obs_instrument_cocirs` INNER JOIN `obs_general` ON (`obs_instrument_cocirs`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_instrument_coiss`.`opus_id` AS `opus_id` FROM `obs_instrument_coiss` INNER JOIN `obs_general` ON (`obs_instrument_coiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_instrument_couvis`.`opus_id` AS `opus_id` FROM `obs_instrument_couvis` INNER JOIN `obs_general` ON (`obs_instrument_couvis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_instrument_covims`.`opus_id` AS `opus_id` FROM `obs_instrument_covims` INNER JOIN `obs_general` ON (`obs_instrument_covims`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_instrument_gossi`.`opus_id` AS `opus_id` FROM `obs_instrument_gossi` INNER JOIN `obs_general` ON (`obs_instrument_gossi`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_instrument_nhlorri`.`opus_id` AS `opus_id` FROM `obs_instrument_nhlorri` INNER JOIN `obs_general` ON (`obs_instrument_nhlorri`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_instrument_nhmvic`.`opus_id` AS `opus_id` FROM `obs_instrument_nhmvic` INNER JOIN `obs_general` ON (`obs_instrument_nhmvic`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 815
SELECT `obs_instrument_vgiss`.`opus_id` AS `opus_id` FROM `obs_instrument_vgiss` INNER JOIN `obs_general` ON (`obs_instrument_vgiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';

-- block: autocomplete.bundleid/build __api/meta/result_count.json?reqno=1
-- statement: connection 816
SET NAMES utf8mb4;
-- statement: connection 816
set autocommit=0;
-- statement: connection 816
set autocommit=1;
-- statement: connection 816
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- block: autocomplete.bundleid/prefix_2 __api/stringsearchchoices/bundleid.json?bundleid=CO&reqno=1
-- statement: connection 817
SET NAMES utf8mb4;
-- statement: connection 817
set autocommit=0;
-- statement: connection 817
set autocommit=1;
-- statement: connection 817
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 817
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'bundleid' LIMIT 21;
-- statement: connection 817
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`name` = 'bundle_id') LIMIT 21;
-- statement: connection 817
SELECT COUNT(*) FROM `cache_1`;
-- statement: connection 817
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN `cache_1` ON `obs_pds`.`obs_general_id`=`cache_1`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%CO%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: autocomplete.bundleid/prefix_6 __api/stringsearchchoices/bundleid.json?bundleid=COISS_&reqno=1
-- statement: connection 818
SET NAMES utf8mb4;
-- statement: connection 818
set autocommit=0;
-- statement: connection 818
set autocommit=1;
-- statement: connection 818
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 818
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'bundleid' LIMIT 21;
-- statement: connection 818
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`name` = 'bundle_id') LIMIT 21;
-- statement: connection 818
SELECT COUNT(*) FROM `cache_1`;
-- statement: connection 818
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN `cache_1` ON `obs_pds`.`obs_general_id`=`cache_1`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%COISS\\_%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: files.broad/one_observation api/files/co-iss-w1477654052.json
-- statement: connection 819
SET NAMES utf8mb4;
-- statement: connection 819
set autocommit=0;
-- statement: connection 819
set autocommit=1;
-- statement: connection 819
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 819
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;

-- block: files.broad/search_page_1 api/files.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 820
SET NAMES utf8mb4;
-- statement: connection 820
set autocommit=0;
-- statement: connection 820
set autocommit=1;
-- statement: connection 820
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 820
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '2a7qf13indd5ybfpea3gd1i570lfx3yp' LIMIT 1;
-- statement: connection 820
set autocommit=0;
-- statement: connection 820
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('2a7qf13indd5ybfpea3gd1i570lfx3yp', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH5:9XG3V7H6mipa54m6b69RZKy3ZZ7bMhaHMeA0DnXGCCo', '2026-11-18 07:19:11.938813');
-- statement: connection 820
commit;
-- statement: connection 820
set autocommit=1;
-- statement: connection 820
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 820
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 820
CREATE TEMPORARY TABLE `temp_cache_2_748868_1793776751_952208` SELECT `sort_order`,`id` FROM `cache_2` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 820
SELECT `obs_general`.`opus_id` FROM `obs_general` INNER JOIN `temp_cache_2_748868_1793776751_952208` ON `obs_general`.`id`=`temp_cache_2_748868_1793776751_952208`.`id` ORDER BY `temp_cache_2_748868_1793776751_952208`.`sort_order`;
-- statement: connection 820
DROP TABLE `temp_cache_2_748868_1793776751_952208`;
-- statement: connection 820
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('vg-iss-1-s-prof','vg-uvs-1-s-occ-1980-317-iother-e','vg-rss-1-s-occ-1980-318-s63-e','vg-rss-1-s-occ-1980-318-x63-e','vg-iss-2-s-c4360001','vg-iss-2-s-c4360004','vg-iss-2-s-c4360007','vg-iss-2-s-c4360010','vg-iss-2-s-c4360018','vg-iss-2-s-c4360022','vg-iss-2-s-c4360026','vg-iss-2-s-c4360029','vg-iss-2-s-c4360033','vg-iss-2-s-c4360037','vg-iss-2-s-c4360041','vg-iss-2-s-c4360044','vg-iss-2-s-c4360048','vg-iss-2-s-c4360052','vg-iss-2-s-c4360056','vg-iss-2-s-c4360059','vg-iss-2-s-c4360103','vg-iss-2-s-c4360107','vg-iss-2-s-c4360111','vg-iss-2-s-c4360114','vg-iss-2-s-c4360257','vg-iss-2-s-c4360301','vg-iss-2-s-c4360305','vg-iss-2-s-c4360308','vg-iss-2-s-c4360312','vg-iss-2-s-c4360316','vg-iss-2-s-c4360320','vg-iss-2-s-c4360323','vg-iss-2-s-c4360327','vg-iss-2-s-c4360331','vg-iss-2-s-c4360335','vg-iss-2-s-c4360338','vg-iss-2-s-c4360342','vg-iss-2-s-c4360346','vg-iss-2-s-c4360350','vg-iss-2-s-c4360353','vg-iss-2-s-c4360507','vg-iss-2-s-c4360511','vg-iss-2-s-c4360515','vg-iss-2-s-c4360519','vg-iss-2-s-c4360523','vg-iss-2-s-c4360527','vg-iss-2-s-c4360536','vg-iss-2-s-c4360540','vg-iss-2-s-c4360544','vg-iss-2-s-c4360547','vg-iss-2-s-c4360551','vg-iss-2-s-c4360555','vg-iss-2-s-c4360559','vg-iss-2-s-c4360602','vg-iss-2-s-c4360606','vg-iss-2-s-c4360610','vg-iss-2-s-c4360614','vg-iss-2-s-c4360617','vg-iss-2-s-c4360621','vg-iss-2-s-c4360625','vg-iss-2-s-c4360629','vg-iss-2-s-c4360632','vg-iss-2-s-c4360815','vg-iss-2-s-c4360819','vg-iss-2-s-c4360823','vg-iss-2-s-c4360826','vg-iss-2-s-c4360830','vg-iss-2-s-c4360834','vg-iss-2-s-c4360838','vg-iss-2-s-c4360841','vg-iss-2-s-c4360845','vg-iss-2-s-c4360849','vg-iss-2-s-c4360853','vg-iss-2-s-c4360856','vg-iss-2-s-c4360904','vg-iss-2-s-c4360908','vg-iss-2-s-c4360911','vg-iss-2-s-c4361016','vg-iss-2-s-c4361020','vg-iss-2-s-c4361024','vg-iss-2-s-c4361028','vg-iss-2-s-c4361032','vg-iss-2-s-c4361036','vg-iss-2-s-c4361040','vg-iss-2-s-c4361044','vg-iss-2-s-c4361048','vg-iss-2-s-c4361054','vg-iss-2-s-c4361058','vg-iss-2-s-c4361102','vg-iss-2-s-c4361105','vg-iss-2-s-c4361109','vg-iss-2-s-c4361113','vg-iss-2-s-c4361117','vg-iss-2-s-c4361120','vg-iss-2-s-c4361124','vg-iss-2-s-c4361128','vg-iss-2-s-c4361132','vg-iss-2-s-c4361135','vg-iss-2-s-c4361139','vg-iss-2-s-c4361143') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 820
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 820
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 820
set autocommit=0;
-- statement: connection 820
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH6:ShqmbukGU2Sf7nQHacdllhcuzlzWliqPLpd3jGng8bM', `expire_date` = '2026-11-18 07:19:12.031871' WHERE `django_session`.`session_key` = '2a7qf13indd5ybfpea3gd1i570lfx3yp';
-- statement: connection 820
commit;
-- statement: connection 820
set autocommit=1;

-- block: previews.empty/gallery_page_1 __api/dataimages.json?page=1&limit=100&reqno=1
-- statement: connection 821
SET NAMES utf8mb4;
-- statement: connection 821
set autocommit=0;
-- statement: connection 821
set autocommit=1;
-- statement: connection 821
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 821
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2' LIMIT 1;
-- statement: connection 821
set autocommit=0;
-- statement: connection 821
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('zkheolikj6rkq64n000ie4bg19bgf3f2', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH6:ShqmbukGU2Sf7nQHacdllhcuzlzWliqPLpd3jGng8bM', '2026-11-18 07:19:12.057991');
-- statement: connection 821
commit;
-- statement: connection 821
set autocommit=1;
-- statement: connection 821
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = '**previewimages' LIMIT 21;
-- statement: connection 821
CREATE TEMPORARY TABLE `temp_cache_1_748869_1793776752_064237` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 821
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_general`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_748869_1793776752_064237` ON `obs_general`.`id`=`temp_cache_1_748869_1793776752_064237`.`id` LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = 'zkheolikj6rkq64n000ie4bg19bgf3f2' ORDER BY `temp_cache_1_748869_1793776752_064237`.`sort_order`;
-- statement: connection 821
DROP TABLE `temp_cache_1_748869_1793776752_064237`;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 821
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 821
set autocommit=0;
-- statement: connection 821
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH6:ShqmbukGU2Sf7nQHacdllhcuzlzWliqPLpd3jGng8bM', `expire_date` = '2026-11-18 07:19:12.096570' WHERE `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2';
-- statement: connection 821
commit;
-- statement: connection 821
set autocommit=1;

-- block: previews.empty/gallery_page_10 __api/dataimages.json?page=10&limit=100&reqno=1
-- statement: connection 822
SET NAMES utf8mb4;
-- statement: connection 822
set autocommit=0;
-- statement: connection 822
set autocommit=1;
-- statement: connection 822
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 822
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:12.103030' AND `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2') LIMIT 21;
-- statement: connection 822
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = '**previewimages' LIMIT 21;
-- statement: connection 822
CREATE TEMPORARY TABLE `temp_cache_1_748868_1793776752_109643` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 822
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_general`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `temp_cache_1_748868_1793776752_109643` ON `obs_general`.`id`=`temp_cache_1_748868_1793776752_109643`.`id` LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = 'zkheolikj6rkq64n000ie4bg19bgf3f2' ORDER BY `temp_cache_1_748868_1793776752_109643`.`sort_order`;
-- statement: connection 822
DROP TABLE `temp_cache_1_748868_1793776752_109643`;
-- statement: connection 822
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 4;
-- statement: connection 822
SELECT `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label` FROM `mult_obs_general_target_name` WHERE `mult_obs_general_target_name`.`id` = 2;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_general' LIMIT 21;
-- statement: connection 822
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` WHERE `table_names`.`table_name` = 'obs_pds' LIMIT 21;
-- statement: connection 822
set autocommit=0;
-- statement: connection 822
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH6:ShqmbukGU2Sf7nQHacdllhcuzlzWliqPLpd3jGng8bM', `expire_date` = '2026-11-18 07:19:12.143292' WHERE `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2';
-- statement: connection 822
commit;
-- statement: connection 822
set autocommit=1;

-- block: previews.empty/images_page_1 api/images.json?page=1&limit=100
-- statement: connection 823
SET NAMES utf8mb4;
-- statement: connection 823
set autocommit=0;
-- statement: connection 823
set autocommit=1;
-- statement: connection 823
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 823
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:12.149353' AND `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2') LIMIT 21;
-- statement: connection 823
CREATE TEMPORARY TABLE `temp_cache_1_748868_1793776752_152295` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 823
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `temp_cache_1_748868_1793776752_152295` ON `obs_general`.`id`=`temp_cache_1_748868_1793776752_152295`.`id` ORDER BY `temp_cache_1_748868_1793776752_152295`.`sort_order`;
-- statement: connection 823
DROP TABLE `temp_cache_1_748868_1793776752_152295`;
-- statement: connection 823
set autocommit=0;
-- statement: connection 823
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH6:ShqmbukGU2Sf7nQHacdllhcuzlzWliqPLpd3jGng8bM', `expire_date` = '2026-11-18 07:19:12.157696' WHERE `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2';
-- statement: connection 823
commit;
-- statement: connection 823
set autocommit=1;

-- block: previews.empty/images_page_10 api/images.json?page=10&limit=100
-- statement: connection 824
SET NAMES utf8mb4;
-- statement: connection 824
set autocommit=0;
-- statement: connection 824
set autocommit=1;
-- statement: connection 824
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 824
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:12.163304' AND `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2') LIMIT 21;
-- statement: connection 824
CREATE TEMPORARY TABLE `temp_cache_1_748868_1793776752_165784` SELECT `sort_order`,`id` FROM `cache_1` ORDER BY `sort_order` LIMIT 100 OFFSET 900;
-- statement: connection 824
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `temp_cache_1_748868_1793776752_165784` ON `obs_general`.`id`=`temp_cache_1_748868_1793776752_165784`.`id` ORDER BY `temp_cache_1_748868_1793776752_165784`.`sort_order`;
-- statement: connection 824
DROP TABLE `temp_cache_1_748868_1793776752_165784`;
-- statement: connection 824
set autocommit=0;
-- statement: connection 824
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH6:ShqmbukGU2Sf7nQHacdllhcuzlzWliqPLpd3jGng8bM', `expire_date` = '2026-11-18 07:19:12.170623' WHERE `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2';
-- statement: connection 824
commit;
-- statement: connection 824
set autocommit=1;

-- block: previews.empty/detail __initdetail/co-iss-w1477654052.html
-- statement: connection 825
SET NAMES utf8mb4;
-- statement: connection 825
set autocommit=0;
-- statement: connection 825
set autocommit=1;
-- statement: connection 825
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 825
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 825
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrumentid' LIMIT 21;
-- statement: connection 825
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`old_slug` = 'instrumentid' LIMIT 21;
-- statement: connection 825
SELECT `mult_obs_general_instrument_id`.`value` AS `value`, `mult_obs_general_instrument_id`.`label` AS `label` FROM `mult_obs_general_instrument_id` WHERE `mult_obs_general_instrument_id`.`id` = 1;
-- statement: connection 825
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:12.186239' AND `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2') LIMIT 21;
-- statement: connection 825
SELECT `cart`.`id`, `cart`.`session_id`, `cart`.`obs_general_id`, `cart`.`opus_id`, `cart`.`recycled`, `cart`.`timestamp` FROM `cart` WHERE (`cart`.`opus_id` = 'co-iss-w1477654052' AND `cart`.`recycled` = 0 AND `cart`.`session_id` = 'zkheolikj6rkq64n000ie4bg19bgf3f2') LIMIT 21;
-- statement: connection 825
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 825
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 825
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE ((`obs_files`.`short_name` = 'browse_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'browse_full' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_full' AND `obs_files`.`version_name` = 'Current')) AND `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 825
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_raw') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_calib') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_thumb') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_medium') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_full') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_documentation') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'rms_index') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'inventory') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'planet_geometry') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'ring_geometry') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'browse_thumb') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'browse_small') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'browse_medium') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'browse_full') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_calib') LIMIT 21;
-- statement: connection 825
SELECT `definitions`.`id`, `definitions`.`term`, `definitions`.`context`, `definitions`.`definition`, `definitions`.`timestamp` FROM `definitions` WHERE (`definitions`.`context` = 'OPUS_PRODUCT_TYPE' AND `definitions`.`term` = 'coiss_calib') LIMIT 21;
-- statement: connection 825
set autocommit=0;
-- statement: connection 825
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH6:ShqmbukGU2Sf7nQHacdllhcuzlzWliqPLpd3jGng8bM', `expire_date` = '2026-11-18 07:19:12.204547' WHERE `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2';
-- statement: connection 825
commit;
-- statement: connection 825
set autocommit=1;

-- block: previews.empty/image_med api/image/med/co-iss-w1477654052.json
-- statement: connection 826
SET NAMES utf8mb4;
-- statement: connection 826
set autocommit=0;
-- statement: connection 826
set autocommit=1;
-- statement: connection 826
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- statement: connection 826
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-04 07:19:12.210894' AND `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2') LIMIT 21;
-- statement: connection 826
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 826
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.opus_id\": [\"co-iss-w1477654052\"]}', '80cf569e54ee1ebe7a720df433eb42c5', '{\"obs_general.opus_id\": [\"matches\"]}', '5cb040f5fb0c9aeb4dfe8694aff88f3d', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 826
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 826
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 826
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 826
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 826
CREATE TABLE `cache_15`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 826
CREATE TEMPORARY TABLE `temp_cache_15_748869_1793776752_234197` SELECT `sort_order`,`id` FROM `cache_15` ORDER BY `sort_order` LIMIT 100 OFFSET 0;
-- statement: connection 826
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `temp_cache_15_748869_1793776752_234197` ON `obs_general`.`id`=`temp_cache_15_748869_1793776752_234197`.`id` ORDER BY `temp_cache_15_748869_1793776752_234197`.`sort_order`;
-- statement: connection 826
DROP TABLE `temp_cache_15_748869_1793776752_234197`;
-- statement: connection 826
set autocommit=0;
-- statement: connection 826
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xOVH6:ShqmbukGU2Sf7nQHacdllhcuzlzWliqPLpd3jGng8bM', `expire_date` = '2026-11-18 07:19:12.235775' WHERE `django_session`.`session_key` = 'zkheolikj6rkq64n000ie4bg19bgf3f2';
-- statement: connection 826
commit;
-- statement: connection 826
set autocommit=1;
