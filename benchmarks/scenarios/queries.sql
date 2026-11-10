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
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{}', '99914b932bd37a50b983c5e7c90ae93b', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time1') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'opus_id') LIMIT 21;
-- statement: connection 17
CREATE TABLE `cache_1`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_1`;

-- block: search.broad/result_count __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'time1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'f004842dd5ce1e4a6c4c68e89b50dd11', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'time2') LIMIT 21;
-- statement: connection 17
CREATE TABLE `cache_2`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0 ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_2`;

-- block: search.selective/result_count __api/meta/result_count.json?planet=Uranus&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 17
SELECT `mult_obs_general_planet_id`.`id` AS `id`, `mult_obs_general_planet_id`.`value` AS `value`, `mult_obs_general_planet_id`.`label` AS `label`, `mult_obs_general_planet_id`.`disp_order` AS `disp_order` FROM `mult_obs_general_planet_id`;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Uranus\"]}', '033bcdee4b74d22264a9cf8648d2a2fc', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'planet_id') LIMIT 21;
-- statement: connection 17
CREATE TABLE `cache_3`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_3`;

-- block: search.ring_radius/result_count __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'RINGGEOringradius1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_ring_geometry.ring_radius1\": [60000.0], \"obs_ring_geometry.ring_radius2\": [140000.0]}', '3e9f393e09dfa2c750cdae5be4a34297', '{\"obs_ring_geometry.ring_radius\": [\"any\"]}', 'd58efe915310b90c76b4d3e3c419cba8', '{\"obs_ring_geometry.ring_radius\": [\"km\"]}', '70f0bb7407a66538767b4dee465f5022', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius1') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_ring_geometry' AND `param_info`.`name` = 'ring_radius2') LIMIT 21;
-- statement: connection 17
CREATE TABLE `cache_4`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0 ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_4`;

-- block: search.target/result_count __api/meta/result_count.json?target=Saturn&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 17
SELECT `mult_obs_general_target_name`.`id` AS `id`, `mult_obs_general_target_name`.`value` AS `value`, `mult_obs_general_target_name`.`label` AS `label`, `mult_obs_general_target_name`.`disp_order` AS `disp_order` FROM `mult_obs_general_target_name`;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.target_name\": [\"Saturn\"]}', '0808ab16043b8e7fcebb7ff7ab9500d9', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_general' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 17
CREATE TABLE `cache_5`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,'1') ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_5`;

-- block: search.surface_geometry/result_count __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'surfacegeometrytargetname' LIMIT 21;
-- statement: connection 17
SELECT `mult_obs_surface_geometry_name_target_name`.`id` AS `id`, `mult_obs_surface_geometry_name_target_name`.`value` AS `value`, `mult_obs_surface_geometry_name_target_name`.`label` AS `label`, `mult_obs_surface_geometry_name_target_name`.`disp_order` AS `disp_order` FROM `mult_obs_surface_geometry_name_target_name`;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'SURFACEGEOsaturn_planetographiclatitude1' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_surface_geometry__saturn.planetographic_latitude1\": [-30.0], \"obs_surface_geometry__saturn.planetographic_latitude2\": [30.0], \"obs_surface_geometry_name.target_name\": [\"Saturn\"]}', '907ec5896a8bd3771dd91f22743140d1', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"any\"]}', '2998cdc1c9b87c33e7ac2c27b2011182', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"degrees\"]}', '77ac08a838ce071f52f224163fc043dc', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude1') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry__saturn' AND `param_info`.`name` = 'planetographic_latitude2') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_surface_geometry_name' AND `param_info`.`name` = 'target_name') LIMIT 21;
-- statement: connection 17
CREATE TABLE `cache_6`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` LEFT JOIN `obs_surface_geometry_name` ON `obs_general`.`id`=`obs_surface_geometry_name`.`obs_general_id` WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (`obs_surface_geometry_name`.`target_name` IN (6)) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_6`;

-- block: pages.empty/build __api/meta/result_count.json?reqno=1

-- block: pages.empty/page_1 api/data.json?page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'e5p20wi72zxasr7z1g0l568ewci8kzvu' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('e5p20wi72zxasr7z1g0l568ewci8kzvu', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', '2026-11-24 10:27:37.486515');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `table_names`.`id`, `table_names`.`table_name`, `table_names`.`label`, `table_names`.`display`, `table_names`.`disp_order`, `table_names`.`timestamp` FROM `table_names` ORDER BY `table_names`.`disp_order` ASC;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrument' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'planet' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'target' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationduration' LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_1` ON `obs_general`.`id`=`cache_1`.`id` AND `cache_1`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_1`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.509766' WHERE `django_session`.`session_key` = 'e5p20wi72zxasr7z1g0l568ewci8kzvu';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.empty/page_10 api/data.json?page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.522244' AND `django_session`.`session_key` = 'e5p20wi72zxasr7z1g0l568ewci8kzvu') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_1` ON `obs_general`.`id`=`cache_1`.`id` AND `cache_1`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `cache_1`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.530742' WHERE `django_session`.`session_key` = 'e5p20wi72zxasr7z1g0l568ewci8kzvu';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.empty/page_last api/data.json?page=298&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.544508' AND `django_session`.`session_key` = 'e5p20wi72zxasr7z1g0l568ewci8kzvu') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_1` ON `obs_general`.`id`=`cache_1`.`id` AND `cache_1`.`sort_order` BETWEEN 29701 AND 29800 ORDER BY `cache_1`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.552842' WHERE `django_session`.`session_key` = 'e5p20wi72zxasr7z1g0l568ewci8kzvu';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.broad/build __api/meta/result_count.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&reqno=1

-- block: pages.broad/page_1 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '0wwmncz0865d4xyy3aq60e0lf3pnu401' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('0wwmncz0865d4xyy3aq60e0lf3pnu401', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', '2026-11-24 10:27:37.600448');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_2` ON `obs_general`.`id`=`cache_2`.`id` AND `cache_2`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_2`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.612319' WHERE `django_session`.`session_key` = '0wwmncz0865d4xyy3aq60e0lf3pnu401';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.broad/page_10 api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.623350' AND `django_session`.`session_key` = '0wwmncz0865d4xyy3aq60e0lf3pnu401') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_2` ON `obs_general`.`id`=`cache_2`.`id` AND `cache_2`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `cache_2`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.633731' WHERE `django_session`.`session_key` = '0wwmncz0865d4xyy3aq60e0lf3pnu401';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.broad/page_last api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=298&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.648209' AND `django_session`.`session_key` = '0wwmncz0865d4xyy3aq60e0lf3pnu401') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_2` ON `obs_general`.`id`=`cache_2`.`id` AND `cache_2`.`sort_order` BETWEEN 29701 AND 29800 ORDER BY `cache_2`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.655511' WHERE `django_session`.`session_key` = '0wwmncz0865d4xyy3aq60e0lf3pnu401';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.selective/build __api/meta/result_count.json?planet=Uranus&reqno=1

-- block: pages.selective/page_1 api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'uc601hwdywi6lpeb9r3q5xbaoeabkezp' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('uc601hwdywi6lpeb9r3q5xbaoeabkezp', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', '2026-11-24 10:27:37.686789');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_3` ON `obs_general`.`id`=`cache_3`.`id` AND `cache_3`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_3`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.696660' WHERE `django_session`.`session_key` = 'uc601hwdywi6lpeb9r3q5xbaoeabkezp';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.selective/page_10 api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.707250' AND `django_session`.`session_key` = 'uc601hwdywi6lpeb9r3q5xbaoeabkezp') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_3` ON `obs_general`.`id`=`cache_3`.`id` AND `cache_3`.`sort_order` BETWEEN 101 AND 200 ORDER BY `cache_3`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.713842' WHERE `django_session`.`session_key` = 'uc601hwdywi6lpeb9r3q5xbaoeabkezp';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.selective/page_last api/data.json?planet=Uranus&page=2&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.724633' AND `django_session`.`session_key` = 'uc601hwdywi6lpeb9r3q5xbaoeabkezp') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_3` ON `obs_general`.`id`=`cache_3`.`id` AND `cache_3`.`sort_order` BETWEEN 101 AND 200 ORDER BY `cache_3`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.731081' WHERE `django_session`.`session_key` = 'uc601hwdywi6lpeb9r3q5xbaoeabkezp';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.ring_radius/build __api/meta/result_count.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&reqno=1

-- block: pages.ring_radius/page_1 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'kvjbztnapxs1u86ixf3ptzimhfm5swsq' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('kvjbztnapxs1u86ixf3ptzimhfm5swsq', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', '2026-11-24 10:27:37.764391');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_4` ON `obs_general`.`id`=`cache_4`.`id` AND `cache_4`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_4`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.774029' WHERE `django_session`.`session_key` = 'kvjbztnapxs1u86ixf3ptzimhfm5swsq';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.ring_radius/page_10 api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.785353' AND `django_session`.`session_key` = 'kvjbztnapxs1u86ixf3ptzimhfm5swsq') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_4` ON `obs_general`.`id`=`cache_4`.`id` AND `cache_4`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `cache_4`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.793377' WHERE `django_session`.`session_key` = 'kvjbztnapxs1u86ixf3ptzimhfm5swsq';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.ring_radius/page_last api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=112&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.804649' AND `django_session`.`session_key` = 'kvjbztnapxs1u86ixf3ptzimhfm5swsq') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_4` ON `obs_general`.`id`=`cache_4`.`id` AND `cache_4`.`sort_order` BETWEEN 11101 AND 11200 ORDER BY `cache_4`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.810233' WHERE `django_session`.`session_key` = 'kvjbztnapxs1u86ixf3ptzimhfm5swsq';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.target/build __api/meta/result_count.json?target=Saturn&reqno=1

-- block: pages.target/page_1 api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'e20muva9po7h2c07bhgyiceycol5eohr' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('e20muva9po7h2c07bhgyiceycol5eohr', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', '2026-11-24 10:27:37.845196');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_5` ON `obs_general`.`id`=`cache_5`.`id` AND `cache_5`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_5`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.854876' WHERE `django_session`.`session_key` = 'e20muva9po7h2c07bhgyiceycol5eohr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.target/page_10 api/data.json?target=Saturn&page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.866128' AND `django_session`.`session_key` = 'e20muva9po7h2c07bhgyiceycol5eohr') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_5` ON `obs_general`.`id`=`cache_5`.`id` AND `cache_5`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `cache_5`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.873981' WHERE `django_session`.`session_key` = 'e20muva9po7h2c07bhgyiceycol5eohr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.target/page_last api/data.json?target=Saturn&page=51&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.889207' AND `django_session`.`session_key` = 'e20muva9po7h2c07bhgyiceycol5eohr') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_5` ON `obs_general`.`id`=`cache_5`.`id` AND `cache_5`.`sort_order` BETWEEN 5001 AND 5100 ORDER BY `cache_5`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.897934' WHERE `django_session`.`session_key` = 'e20muva9po7h2c07bhgyiceycol5eohr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.surface_geometry/build __api/meta/result_count.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&reqno=1

-- block: pages.surface_geometry/page_1 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'icxh59hj80qyd3fabrvz2emq14kikq12' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('icxh59hj80qyd3fabrvz2emq14kikq12', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', '2026-11-24 10:27:37.928327');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_6` ON `obs_general`.`id`=`cache_6`.`id` AND `cache_6`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_6`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.937873' WHERE `django_session`.`session_key` = 'icxh59hj80qyd3fabrvz2emq14kikq12';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.surface_geometry/page_10 api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.949670' AND `django_session`.`session_key` = 'icxh59hj80qyd3fabrvz2emq14kikq12') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_6` ON `obs_general`.`id`=`cache_6`.`id` AND `cache_6`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `cache_6`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.957786' WHERE `django_session`.`session_key` = 'icxh59hj80qyd3fabrvz2emq14kikq12';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: pages.surface_geometry/page_last api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=44&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:37.968508' AND `django_session`.`session_key` = 'icxh59hj80qyd3fabrvz2emq14kikq12') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_6` ON `obs_general`.`id`=`cache_6`.`id` AND `cache_6`.`sort_order` BETWEEN 4301 AND 4400 ORDER BY `cache_6`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', `expire_date` = '2026-11-24 10:27:37.973686' WHERE `django_session`.`session_key` = 'icxh59hj80qyd3fabrvz2emq14kikq12';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.empty/default_order api/data.json?page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'yan2dev9pfk7tslj9ib7gvzw57eg5z63' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('yan2dev9pfk7tslj9ib7gvzw57eg5z63', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4j:N5q0JqC7MtraxM2aL0k_Zg4xKVaOo_6Yb5ERreb56F8', '2026-11-24 10:27:37.996146');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_1` ON `obs_general`.`id`=`cache_1`.`id` AND `cache_1`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_1`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4k:i5jw9p7Okra4ELgcqbYKRIUqwv6ZKM8TeBYCYQaBlAU', `expire_date` = '2026-11-24 10:27:38.005585' WHERE `django_session`.`session_key` = 'yan2dev9pfk7tslj9ib7gvzw57eg5z63';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.empty/resorted api/data.json?order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:38.016142' AND `django_session`.`session_key` = 'yan2dev9pfk7tslj9ib7gvzw57eg5z63') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{}', '99914b932bd37a50b983c5e7c90ae93b', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 17
CREATE TABLE `cache_7`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_7` ON `obs_general`.`id`=`cache_7`.`id` AND `cache_7`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_7`.`sort_order`;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_7`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4k:i5jw9p7Okra4ELgcqbYKRIUqwv6ZKM8TeBYCYQaBlAU', `expire_date` = '2026-11-24 10:27:38.590519' WHERE `django_session`.`session_key` = 'yan2dev9pfk7tslj9ib7gvzw57eg5z63';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.broad/default_order api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'u6bnwopo9t2hrg8v4tid56scz86f010w' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('u6bnwopo9t2hrg8v4tid56scz86f010w', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4k:i5jw9p7Okra4ELgcqbYKRIUqwv6ZKM8TeBYCYQaBlAU', '2026-11-24 10:27:38.615402');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_2` ON `obs_general`.`id`=`cache_2`.`id` AND `cache_2`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_2`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4k:i5jw9p7Okra4ELgcqbYKRIUqwv6ZKM8TeBYCYQaBlAU', `expire_date` = '2026-11-24 10:27:38.627571' WHERE `django_session`.`session_key` = 'u6bnwopo9t2hrg8v4tid56scz86f010w';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.broad/resorted api/data.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:38.642246' AND `django_session`.`session_key` = 'u6bnwopo9t2hrg8v4tid56scz86f010w') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'f004842dd5ce1e4a6c4c68e89b50dd11', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 17
CREATE TABLE `cache_8`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0 ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_8` ON `obs_general`.`id`=`cache_8`.`id` AND `cache_8`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_8`.`sort_order`;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_8`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', `expire_date` = '2026-11-24 10:27:39.220426' WHERE `django_session`.`session_key` = 'u6bnwopo9t2hrg8v4tid56scz86f010w';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.selective/default_order api/data.json?planet=Uranus&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'zhrksma5r20owelr6sczun2rsfz6ta6e' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('zhrksma5r20owelr6sczun2rsfz6ta6e', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', '2026-11-24 10:27:39.244334');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_3` ON `obs_general`.`id`=`cache_3`.`id` AND `cache_3`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_3`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', `expire_date` = '2026-11-24 10:27:39.254184' WHERE `django_session`.`session_key` = 'zhrksma5r20owelr6sczun2rsfz6ta6e';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.selective/resorted api/data.json?planet=Uranus&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:39.264931' AND `django_session`.`session_key` = 'zhrksma5r20owelr6sczun2rsfz6ta6e') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Uranus\"]}', '033bcdee4b74d22264a9cf8648d2a2fc', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 17
CREATE TABLE `cache_9`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (5) ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_9` ON `obs_general`.`id`=`cache_9`.`id` AND `cache_9`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_9`.`sort_order`;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_9`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', `expire_date` = '2026-11-24 10:27:39.343486' WHERE `django_session`.`session_key` = 'zhrksma5r20owelr6sczun2rsfz6ta6e';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.ring_radius/default_order api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '2ty2o7v3644pr36jn11zfr7epzesf6d8' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('2ty2o7v3644pr36jn11zfr7epzesf6d8', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', '2026-11-24 10:27:39.369262');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_4` ON `obs_general`.`id`=`cache_4`.`id` AND `cache_4`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_4`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', `expire_date` = '2026-11-24 10:27:39.379069' WHERE `django_session`.`session_key` = '2ty2o7v3644pr36jn11zfr7epzesf6d8';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.ring_radius/resorted api/data.json?RINGGEOringradius1=60000&RINGGEOringradius2=140000&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:39.389415' AND `django_session`.`session_key` = '2ty2o7v3644pr36jn11zfr7epzesf6d8') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_ring_geometry.ring_radius1\": [60000.0], \"obs_ring_geometry.ring_radius2\": [140000.0]}', '3e9f393e09dfa2c750cdae5be4a34297', '{\"obs_ring_geometry.ring_radius\": [\"any\"]}', 'd58efe915310b90c76b4d3e3c419cba8', '{\"obs_ring_geometry.ring_radius\": [\"km\"]}', '70f0bb7407a66538767b4dee465f5022', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 17
CREATE TABLE `cache_10`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE `obs_ring_geometry`.`ring_radius2` >= 60000.0e0 AND `obs_ring_geometry`.`ring_radius1` <= 140000.0e0 ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_10` ON `obs_general`.`id`=`cache_10`.`id` AND `cache_10`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_10`.`sort_order`;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_10`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', `expire_date` = '2026-11-24 10:27:39.732645' WHERE `django_session`.`session_key` = '2ty2o7v3644pr36jn11zfr7epzesf6d8';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.target/default_order api/data.json?target=Saturn&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'o8u9vzlxjyj5gyu7z9hh17nth4cb9nkc' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('o8u9vzlxjyj5gyu7z9hh17nth4cb9nkc', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', '2026-11-24 10:27:39.759830');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_5` ON `obs_general`.`id`=`cache_5`.`id` AND `cache_5`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_5`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', `expire_date` = '2026-11-24 10:27:39.770119' WHERE `django_session`.`session_key` = 'o8u9vzlxjyj5gyu7z9hh17nth4cb9nkc';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.target/resorted api/data.json?target=Saturn&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:39.780730' AND `django_session`.`session_key` = 'o8u9vzlxjyj5gyu7z9hh17nth4cb9nkc') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.target_name\": [\"Saturn\"]}', '0808ab16043b8e7fcebb7ff7ab9500d9', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 17
CREATE TABLE `cache_11`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,'1') ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_11` ON `obs_general`.`id`=`cache_11`.`id` AND `cache_11`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_11`.`sort_order`;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_11`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4l:YLONHxzVV4BLSESaRb6G0hYX-K0_a7w7s2imEIKwpBo', `expire_date` = '2026-11-24 10:27:39.989034' WHERE `django_session`.`session_key` = 'o8u9vzlxjyj5gyu7z9hh17nth4cb9nkc';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.surface_geometry/default_order api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'bww2mq0lepfooagbsad2y3ka8aw1ig45' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('bww2mq0lepfooagbsad2y3ka8aw1ig45', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4m:mBSb7EveeKO3u8dj17mjqnbPXf96bs-3R6umcD8dF28', '2026-11-24 10:27:40.013952');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_6` ON `obs_general`.`id`=`cache_6`.`id` AND `cache_6`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_6`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4m:mBSb7EveeKO3u8dj17mjqnbPXf96bs-3R6umcD8dF28', `expire_date` = '2026-11-24 10:27:40.023886' WHERE `django_session`.`session_key` = 'bww2mq0lepfooagbsad2y3ka8aw1ig45';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: resort.surface_geometry/resorted api/data.json?surfacegeometrytargetname=Saturn&SURFACEGEOsaturn_planetographiclatitude1=-30&SURFACEGEOsaturn_planetographiclatitude2=30&order=-time1,opusid&page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:40.034986' AND `django_session`.`session_key` = 'bww2mq0lepfooagbsad2y3ka8aw1ig45') LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_surface_geometry__saturn.planetographic_latitude1\": [-30.0], \"obs_surface_geometry__saturn.planetographic_latitude2\": [30.0], \"obs_surface_geometry_name.target_name\": [\"Saturn\"]}', '907ec5896a8bd3771dd91f22743140d1', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"any\"]}', '2998cdc1c9b87c33e7ac2c27b2011182', '{\"obs_surface_geometry__saturn.planetographic_latitude\": [\"degrees\"]}', '77ac08a838ce071f52f224163fc043dc', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [true, false]]', 'e581d8a90adec4b52c7bc36b3c4fd34d', NULL);
-- statement: connection 17
CREATE TABLE `cache_12`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_surface_geometry__saturn` ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id` LEFT JOIN `obs_surface_geometry_name` ON `obs_general`.`id`=`obs_surface_geometry_name`.`obs_general_id` WHERE (`obs_surface_geometry__saturn`.`planetographic_latitude2` >= -30.0e0 AND `obs_surface_geometry__saturn`.`planetographic_latitude1` <= 30.0e0) AND (`obs_surface_geometry_name`.`target_name` IN (6)) ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_12` ON `obs_general`.`id`=`cache_12`.`id` AND `cache_12`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_12`.`sort_order`;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_12`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4m:mBSb7EveeKO3u8dj17mjqnbPXf96bs-3R6umcD8dF28', `expire_date` = '2026-11-24 10:27:40.230590' WHERE `django_session`.`session_key` = 'bww2mq0lepfooagbsad2y3ka8aw1ig45';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: fanout.empty/result_count __api/meta/result_count.json?reqno=1

-- block: fanout.empty/mults_instrument __api/meta/mults/instrument.json?reqno=1
-- statement: connection 17
SELECT `mult_obs_general_instrument_id`.`id` AS `id`, `mult_obs_general_instrument_id`.`value` AS `value`, `mult_obs_general_instrument_id`.`label` AS `label`, `mult_obs_general_instrument_id`.`disp_order` AS `disp_order` FROM `mult_obs_general_instrument_id`;
-- statement: connection 17
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general` GROUP BY `obs_general`.`instrument_id`;

-- block: fanout.empty/mults_observationtype __api/meta/mults/observationtype.json?reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'observationtype' LIMIT 21;
-- statement: connection 17
SELECT `mult_obs_general_observation_type`.`id` AS `id`, `mult_obs_general_observation_type`.`value` AS `value`, `mult_obs_general_observation_type`.`label` AS `label`, `mult_obs_general_observation_type`.`disp_order` AS `disp_order` FROM `mult_obs_general_observation_type`;
-- statement: connection 17
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general` GROUP BY `obs_general`.`observation_type`;

-- block: fanout.empty/mults_target __api/meta/mults/target.json?reqno=1
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
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Saturn\"], \"obs_general.time1\": [-631195181.0], \"obs_general.time2\": [568036837.0]}', 'c206354df622b9bebeb095d3bb4039d7', '{\"obs_general.time\": [\"any\"]}', 'bb223e4dd30d6d27137e47783c21ce3f', '{\"obs_general.time\": [\"ymdhms\"]}', 'ac2294903d02c7606a0659ee9e9fcef3', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
CREATE TABLE `cache_13`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`planet_id` IN (4)) AND (`obs_general`.`time2` >= -631195181.0e0 AND `obs_general`.`time1` <= 568036837.0e0) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_13`;

-- block: fanout.selected/mults_instrument __api/meta/mults/instrument.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
SELECT `obs_general`.`instrument_id`,COUNT(*) AS `instrument_id__count` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`instrument_id`;

-- block: fanout.selected/mults_observationtype __api/meta/mults/observationtype.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
SELECT `obs_general`.`observation_type`,COUNT(*) AS `observation_type__count` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`observation_type`;

-- block: fanout.selected/mults_target __api/meta/mults/target.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
SELECT `obs_general`.`_mult_val_`,COUNT(*) AS `target_name__count` FROM `obs_general` INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]" COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id` GROUP BY `obs_general`.`_mult_val_`;

-- block: fanout.selected/endpoints_time1 __api/meta/range/endpoints/time1.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.planet_id\": [\"Saturn\"]}', '6b21f5786b92be236703ae293679a2c3', NULL, 'NONE', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
CREATE TABLE `cache_14`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (4) ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT MIN(`obs_general`.`time1`),MAX(`obs_general`.`time2`) FROM `obs_general`,`cache_14` WHERE `obs_general`.`id`=`cache_14`.`id`;
-- statement: connection 17
SELECT COUNT(*) FROM `obs_general`,`cache_14` WHERE `obs_general`.`id`=`cache_14`.`id` AND `obs_general`.`time1` IS NULL AND `obs_general`.`time2` IS NULL;

-- block: fanout.selected/menu __menu.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&planet=Saturn&reqno=1
-- statement: connection 17
SELECT `partables`.`id`, `partables`.`trigger_tab`, `partables`.`trigger_col`, `partables`.`trigger_val`, `partables`.`partable`, `partables`.`timestamp` FROM `partables`;
-- statement: connection 17
SELECT DISTINCT `obs_general`.`mission_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
-- statement: connection 17
SELECT DISTINCT `obs_general`.`instrument_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
-- statement: connection 17
SELECT DISTINCT `obs_general`.`inst_host_id` FROM `obs_general`,`cache_13` WHERE `obs_general`.`id`=`cache_13`.`id`;
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
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE `mult_obs_general_planet_id`.`grouping` IS NULL;
-- statement: connection 17
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE (`mult_obs_general_planet_id`.`display` = 'Y' AND `mult_obs_general_planet_id`.`grouping` IS NULL) ORDER BY `mult_obs_general_planet_id`.`disp_order` ASC;
-- statement: connection 17
SELECT `mult_obs_general_planet_id`.`id`, `mult_obs_general_planet_id`.`value`, `mult_obs_general_planet_id`.`label`, `mult_obs_general_planet_id`.`disp_order`, `mult_obs_general_planet_id`.`display`, `mult_obs_general_planet_id`.`grouping`, `mult_obs_general_planet_id`.`group_disp_order`, `mult_obs_general_planet_id`.`timestamp` FROM `mult_obs_general_planet_id` WHERE `mult_obs_general_planet_id`.`display` = 'Y' ORDER BY `mult_obs_general_planet_id`.`disp_order` ASC;
-- statement: connection 17
SELECT DISTINCT `mult_obs_general_planet_id`.`grouping` AS `grouping`, `mult_obs_general_planet_id`.`group_disp_order` FROM `mult_obs_general_planet_id` ORDER BY `mult_obs_general_planet_id`.`group_disp_order` ASC;

-- block: categories/categories api/categories/co-iss-w1477654052.json
-- statement: connection 17
SELECT `obs_general`.`opus_id` AS `opus_id` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_pds`.`opus_id` AS `opus_id` FROM `obs_pds` INNER JOIN `obs_general` ON (`obs_pds`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_type_image`.`opus_id` AS `opus_id` FROM `obs_type_image` INNER JOIN `obs_general` ON (`obs_type_image`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_wavelength`.`opus_id` AS `opus_id` FROM `obs_wavelength` INNER JOIN `obs_general` ON (`obs_wavelength`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_profile`.`opus_id` AS `opus_id` FROM `obs_profile` INNER JOIN `obs_general` ON (`obs_profile`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry`.`opus_id` AS `opus_id` FROM `obs_surface_geometry` INNER JOIN `obs_general` ON (`obs_surface_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__adrastea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__adrastea` INNER JOIN `obs_general` ON (`obs_surface_geometry__adrastea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__aegaeon`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__aegaeon` INNER JOIN `obs_general` ON (`obs_surface_geometry__aegaeon`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__amalthea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__amalthea` INNER JOIN `obs_general` ON (`obs_surface_geometry__amalthea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__anthe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__anthe` INNER JOIN `obs_general` ON (`obs_surface_geometry__anthe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__atlas`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__atlas` INNER JOIN `obs_general` ON (`obs_surface_geometry__atlas`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__callisto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__callisto` INNER JOIN `obs_general` ON (`obs_surface_geometry__callisto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__calypso`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__calypso` INNER JOIN `obs_general` ON (`obs_surface_geometry__calypso`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__charon`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__charon` INNER JOIN `obs_general` ON (`obs_surface_geometry__charon`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__daphnis`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__daphnis` INNER JOIN `obs_general` ON (`obs_surface_geometry__daphnis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__despina`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__despina` INNER JOIN `obs_general` ON (`obs_surface_geometry__despina`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__dione`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__dione` INNER JOIN `obs_general` ON (`obs_surface_geometry__dione`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__enceladus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__enceladus` INNER JOIN `obs_general` ON (`obs_surface_geometry__enceladus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__epimetheus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__epimetheus` INNER JOIN `obs_general` ON (`obs_surface_geometry__epimetheus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__europa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__europa` INNER JOIN `obs_general` ON (`obs_surface_geometry__europa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__galatea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__galatea` INNER JOIN `obs_general` ON (`obs_surface_geometry__galatea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__ganymede`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__ganymede` INNER JOIN `obs_general` ON (`obs_surface_geometry__ganymede`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__helene`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__helene` INNER JOIN `obs_general` ON (`obs_surface_geometry__helene`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__hydra`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__hydra` INNER JOIN `obs_general` ON (`obs_surface_geometry__hydra`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__hyperion`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__hyperion` INNER JOIN `obs_general` ON (`obs_surface_geometry__hyperion`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__iapetus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__iapetus` INNER JOIN `obs_general` ON (`obs_surface_geometry__iapetus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__io`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__io` INNER JOIN `obs_general` ON (`obs_surface_geometry__io`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__janus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__janus` INNER JOIN `obs_general` ON (`obs_surface_geometry__janus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__jupiter`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__jupiter` INNER JOIN `obs_general` ON (`obs_surface_geometry__jupiter`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__kerberos`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__kerberos` INNER JOIN `obs_general` ON (`obs_surface_geometry__kerberos`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__larissa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__larissa` INNER JOIN `obs_general` ON (`obs_surface_geometry__larissa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__methone`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__methone` INNER JOIN `obs_general` ON (`obs_surface_geometry__methone`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__metis`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__metis` INNER JOIN `obs_general` ON (`obs_surface_geometry__metis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__mimas`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__mimas` INNER JOIN `obs_general` ON (`obs_surface_geometry__mimas`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__naiad`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__naiad` INNER JOIN `obs_general` ON (`obs_surface_geometry__naiad`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__neptune`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__neptune` INNER JOIN `obs_general` ON (`obs_surface_geometry__neptune`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__nereid`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__nereid` INNER JOIN `obs_general` ON (`obs_surface_geometry__nereid`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__nix`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__nix` INNER JOIN `obs_general` ON (`obs_surface_geometry__nix`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__pallene`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pallene` INNER JOIN `obs_general` ON (`obs_surface_geometry__pallene`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__pan`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pan` INNER JOIN `obs_general` ON (`obs_surface_geometry__pan`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__pandora`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pandora` INNER JOIN `obs_general` ON (`obs_surface_geometry__pandora`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__phoebe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__phoebe` INNER JOIN `obs_general` ON (`obs_surface_geometry__phoebe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__pluto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__pluto` INNER JOIN `obs_general` ON (`obs_surface_geometry__pluto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__polydeuces`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__polydeuces` INNER JOIN `obs_general` ON (`obs_surface_geometry__polydeuces`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__prometheus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__prometheus` INNER JOIN `obs_general` ON (`obs_surface_geometry__prometheus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__proteus`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__proteus` INNER JOIN `obs_general` ON (`obs_surface_geometry__proteus`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__rhea`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__rhea` INNER JOIN `obs_general` ON (`obs_surface_geometry__rhea`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__saturn`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__saturn` INNER JOIN `obs_general` ON (`obs_surface_geometry__saturn`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__styx`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__styx` INNER JOIN `obs_general` ON (`obs_surface_geometry__styx`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__telesto`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__telesto` INNER JOIN `obs_general` ON (`obs_surface_geometry__telesto`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__tethys`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__tethys` INNER JOIN `obs_general` ON (`obs_surface_geometry__tethys`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__thalassa`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__thalassa` INNER JOIN `obs_general` ON (`obs_surface_geometry__thalassa`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__thebe`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__thebe` INNER JOIN `obs_general` ON (`obs_surface_geometry__thebe`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__titan`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__titan` INNER JOIN `obs_general` ON (`obs_surface_geometry__titan`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_surface_geometry__triton`.`opus_id` AS `opus_id` FROM `obs_surface_geometry__triton` INNER JOIN `obs_general` ON (`obs_surface_geometry__triton`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_ring_geometry`.`opus_id` AS `opus_id` FROM `obs_ring_geometry` INNER JOIN `obs_general` ON (`obs_ring_geometry`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_mission_cassini`.`opus_id` AS `opus_id` FROM `obs_mission_cassini` INNER JOIN `obs_general` ON (`obs_mission_cassini`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_mission_galileo`.`opus_id` AS `opus_id` FROM `obs_mission_galileo` INNER JOIN `obs_general` ON (`obs_mission_galileo`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_mission_hubble`.`opus_id` AS `opus_id` FROM `obs_mission_hubble` INNER JOIN `obs_general` ON (`obs_mission_hubble`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_mission_new_horizons`.`opus_id` AS `opus_id` FROM `obs_mission_new_horizons` INNER JOIN `obs_general` ON (`obs_mission_new_horizons`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_mission_voyager`.`opus_id` AS `opus_id` FROM `obs_mission_voyager` INNER JOIN `obs_general` ON (`obs_mission_voyager`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_instrument_cocirs`.`opus_id` AS `opus_id` FROM `obs_instrument_cocirs` INNER JOIN `obs_general` ON (`obs_instrument_cocirs`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_instrument_coiss`.`opus_id` AS `opus_id` FROM `obs_instrument_coiss` INNER JOIN `obs_general` ON (`obs_instrument_coiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_instrument_couvis`.`opus_id` AS `opus_id` FROM `obs_instrument_couvis` INNER JOIN `obs_general` ON (`obs_instrument_couvis`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_instrument_covims`.`opus_id` AS `opus_id` FROM `obs_instrument_covims` INNER JOIN `obs_general` ON (`obs_instrument_covims`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_instrument_gossi`.`opus_id` AS `opus_id` FROM `obs_instrument_gossi` INNER JOIN `obs_general` ON (`obs_instrument_gossi`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_instrument_nhlorri`.`opus_id` AS `opus_id` FROM `obs_instrument_nhlorri` INNER JOIN `obs_general` ON (`obs_instrument_nhlorri`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_instrument_nhmvic`.`opus_id` AS `opus_id` FROM `obs_instrument_nhmvic` INNER JOIN `obs_general` ON (`obs_instrument_nhmvic`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';
-- statement: connection 17
SELECT `obs_instrument_vgiss`.`opus_id` AS `opus_id` FROM `obs_instrument_vgiss` INNER JOIN `obs_general` ON (`obs_instrument_vgiss`.`obs_general_id` = `obs_general`.`id`) WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052';

-- block: autocomplete.bundleid/build __api/meta/result_count.json?reqno=1

-- block: autocomplete.bundleid/prefix_2 __api/stringsearchchoices/bundleid.json?bundleid=CO&reqno=1
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'bundleid' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE (`param_info`.`category_name` = 'obs_pds' AND `param_info`.`name` = 'bundle_id') LIMIT 21;
-- statement: connection 17
SELECT COUNT(*) FROM `cache_1`;
-- statement: connection 17
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN `cache_1` ON `obs_pds`.`obs_general_id`=`cache_1`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%CO%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: autocomplete.bundleid/prefix_6 __api/stringsearchchoices/bundleid.json?bundleid=COISS_&reqno=1
-- statement: connection 17
SELECT COUNT(*) FROM `cache_1`;
-- statement: connection 17
SELECT /*+ MAX_EXECUTION_TIME(500) */ DISTINCT `obs_pds`.`bundle_id` FROM `obs_pds` INNER JOIN `cache_1` ON `obs_pds`.`obs_general_id`=`cache_1`.`id` WHERE `obs_pds`.`bundle_id` LIKE '%COISS\\_%' ORDER BY `obs_pds`.`bundle_id` LIMIT 101;

-- block: files.broad/one_observation api/files/co-iss-w1477654052.json
-- statement: connection 17
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;

-- block: files.broad/search_page_1 api/files.json?time1=1980-01-01T00:00:00&time2=2018-01-01T00:00:00&page=1&limit=100
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = '5jqvf6lmic9mdn1y6si0ssehqcp6cnr5' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('5jqvf6lmic9mdn1y6si0ssehqcp6cnr5', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4n:BymwoiQNKZad7d3wIg4X7-R7GTcFttpfdTGu27uOtFU', '2026-11-24 10:27:41.854638');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `obs_general`.`opus_id` FROM `obs_general` INNER JOIN `cache_2` ON `obs_general`.`id`=`cache_2`.`id` AND `cache_2`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_2`.`sort_order`;
-- statement: connection 17
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('vg-iss-1-s-prof','vg-uvs-1-s-occ-1980-317-iother-e','vg-rss-1-s-occ-1980-318-s63-e','vg-rss-1-s-occ-1980-318-x63-e','vg-iss-2-s-c4360001','vg-iss-2-s-c4360004','vg-iss-2-s-c4360007','vg-iss-2-s-c4360010','vg-iss-2-s-c4360018','vg-iss-2-s-c4360022','vg-iss-2-s-c4360026','vg-iss-2-s-c4360029','vg-iss-2-s-c4360033','vg-iss-2-s-c4360037','vg-iss-2-s-c4360041','vg-iss-2-s-c4360044','vg-iss-2-s-c4360048','vg-iss-2-s-c4360052','vg-iss-2-s-c4360056','vg-iss-2-s-c4360059','vg-iss-2-s-c4360103','vg-iss-2-s-c4360107','vg-iss-2-s-c4360111','vg-iss-2-s-c4360114','vg-iss-2-s-c4360257','vg-iss-2-s-c4360301','vg-iss-2-s-c4360305','vg-iss-2-s-c4360308','vg-iss-2-s-c4360312','vg-iss-2-s-c4360316','vg-iss-2-s-c4360320','vg-iss-2-s-c4360323','vg-iss-2-s-c4360327','vg-iss-2-s-c4360331','vg-iss-2-s-c4360335','vg-iss-2-s-c4360338','vg-iss-2-s-c4360342','vg-iss-2-s-c4360346','vg-iss-2-s-c4360350','vg-iss-2-s-c4360353','vg-iss-2-s-c4360507','vg-iss-2-s-c4360511','vg-iss-2-s-c4360515','vg-iss-2-s-c4360519','vg-iss-2-s-c4360523','vg-iss-2-s-c4360527','vg-iss-2-s-c4360536','vg-iss-2-s-c4360540','vg-iss-2-s-c4360544','vg-iss-2-s-c4360547','vg-iss-2-s-c4360551','vg-iss-2-s-c4360555','vg-iss-2-s-c4360559','vg-iss-2-s-c4360602','vg-iss-2-s-c4360606','vg-iss-2-s-c4360610','vg-iss-2-s-c4360614','vg-iss-2-s-c4360617','vg-iss-2-s-c4360621','vg-iss-2-s-c4360625','vg-iss-2-s-c4360629','vg-iss-2-s-c4360632','vg-iss-2-s-c4360815','vg-iss-2-s-c4360819','vg-iss-2-s-c4360823','vg-iss-2-s-c4360826','vg-iss-2-s-c4360830','vg-iss-2-s-c4360834','vg-iss-2-s-c4360838','vg-iss-2-s-c4360841','vg-iss-2-s-c4360845','vg-iss-2-s-c4360849','vg-iss-2-s-c4360853','vg-iss-2-s-c4360856','vg-iss-2-s-c4360904','vg-iss-2-s-c4360908','vg-iss-2-s-c4360911','vg-iss-2-s-c4361016','vg-iss-2-s-c4361020','vg-iss-2-s-c4361024','vg-iss-2-s-c4361028','vg-iss-2-s-c4361032','vg-iss-2-s-c4361036','vg-iss-2-s-c4361040','vg-iss-2-s-c4361044','vg-iss-2-s-c4361048','vg-iss-2-s-c4361054','vg-iss-2-s-c4361058','vg-iss-2-s-c4361102','vg-iss-2-s-c4361105','vg-iss-2-s-c4361109','vg-iss-2-s-c4361113','vg-iss-2-s-c4361117','vg-iss-2-s-c4361120','vg-iss-2-s-c4361124','vg-iss-2-s-c4361128','vg-iss-2-s-c4361132','vg-iss-2-s-c4361135','vg-iss-2-s-c4361139','vg-iss-2-s-c4361143') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4n:BymwoiQNKZad7d3wIg4X7-R7GTcFttpfdTGu27uOtFU', `expire_date` = '2026-11-24 10:27:41.895792' WHERE `django_session`.`session_key` = '5jqvf6lmic9mdn1y6si0ssehqcp6cnr5';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/gallery_page_1 __api/dataimages.json?page=1&limit=100&reqno=1
-- statement: connection 17
SELECT 1 AS `a` FROM `django_session` WHERE `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr' LIMIT 1;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES ('lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr', 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4n:BymwoiQNKZad7d3wIg4X7-R7GTcFttpfdTGu27uOtFU', '2026-11-24 10:27:41.922933');
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = '**previewimages' LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_general`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_1` ON `obs_general`.`id`=`cache_1`.`id` AND `cache_1`.`sort_order` BETWEEN 1 AND 100 LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr' ORDER BY `cache_1`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4n:BymwoiQNKZad7d3wIg4X7-R7GTcFttpfdTGu27uOtFU', `expire_date` = '2026-11-24 10:27:41.939760' WHERE `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/gallery_page_10 __api/dataimages.json?page=10&limit=100&reqno=1
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:41.954405' AND `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`opus_id`,`mult_obs_general_instrument_id`.`label`,`mult_obs_general_planet_id`.`label`,`obs_general`.`target_name`,`obs_general`.`time1`,`obs_general`.`observation_duration`,`obs_general`.`preview_images`,`cart`.`opus_id`,`cart`.`recycled` FROM `obs_general` LEFT JOIN `mult_obs_general_instrument_id` ON `obs_general`.`instrument_id`=`mult_obs_general_instrument_id`.`id` LEFT JOIN `mult_obs_general_planet_id` ON `obs_general`.`planet_id`=`mult_obs_general_planet_id`.`id` INNER JOIN `cache_1` ON `obs_general`.`id`=`cache_1`.`id` AND `cache_1`.`sort_order` BETWEEN 901 AND 1000 LEFT JOIN `cart` ON `obs_general`.`id`=`cart`.`obs_general_id` AND `cart`.`session_id` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr' ORDER BY `cache_1`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4n:BymwoiQNKZad7d3wIg4X7-R7GTcFttpfdTGu27uOtFU', `expire_date` = '2026-11-24 10:27:41.967026' WHERE `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/images_page_1 api/images.json?page=1&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:41.978220' AND `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `cache_1` ON `obs_general`.`id`=`cache_1`.`id` AND `cache_1`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_1`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4n:BymwoiQNKZad7d3wIg4X7-R7GTcFttpfdTGu27uOtFU', `expire_date` = '2026-11-24 10:27:41.982592' WHERE `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/images_page_10 api/images.json?page=10&limit=100
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:41.993151' AND `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `cache_1` ON `obs_general`.`id`=`cache_1`.`id` AND `cache_1`.`sort_order` BETWEEN 901 AND 1000 ORDER BY `cache_1`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4n:BymwoiQNKZad7d3wIg4X7-R7GTcFttpfdTGu27uOtFU', `expire_date` = '2026-11-24 10:27:41.997370' WHERE `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/detail __initdetail/co-iss-w1477654052.html
-- statement: connection 17
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'instrumentid' LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`old_slug` = 'instrumentid' LIMIT 21;
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:42.017603' AND `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr') LIMIT 21;
-- statement: connection 17
SELECT `cart`.`id`, `cart`.`session_id`, `cart`.`obs_general_id`, `cart`.`opus_id`, `cart`.`recycled`, `cart`.`timestamp` FROM `cart` WHERE (`cart`.`opus_id` = 'co-iss-w1477654052' AND `cart`.`recycled` = 0 AND `cart`.`session_id` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr') LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 17
SELECT `obs_general`.`id`, `obs_general`.`opus_id`, `obs_general`.`bundle_id`, `obs_general`.`instrument_id`, `obs_general`.`mission_id`, `obs_general`.`inst_host_id`, `obs_general`.`planet_id`, `obs_general`.`target_name`, `obs_general`.`target_class`, `obs_general`.`time1`, `obs_general`.`time2`, `obs_general`.`observation_duration`, `obs_general`.`quantity`, `obs_general`.`right_asc1`, `obs_general`.`right_asc2`, `obs_general`.`right_asc`, `obs_general`.`d_right_asc`, `obs_general`.`declination1`, `obs_general`.`declination2`, `obs_general`.`observation_type`, `obs_general`.`ring_obs_id`, `obs_general`.`primary_filespec`, `obs_general`.`preview_images`, `obs_general`.`timestamp` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' LIMIT 21;
-- statement: connection 17
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE ((`obs_files`.`short_name` = 'browse_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_medium' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'browse_full' AND `obs_files`.`version_name` = 'Current') OR (`obs_files`.`short_name` = 'diagram_full' AND `obs_files`.`version_name` = 'Current')) AND `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 17
SELECT `obs_files`.`opus_id`,`obs_files`.`version_name`,`obs_files`.`category`,`obs_files`.`sort_order`,`obs_files`.`short_name`,`obs_files`.`full_name`,`obs_files`.`size`,`obs_files`.`pds_version`,`obs_files`.`url` FROM `obs_files` WHERE `obs_files`.`opus_id` IN ('co-iss-w1477654052') ORDER BY `obs_files`.`opus_id`,`obs_files`.`version_number` DESC,`obs_files`.`sort_order`,`obs_files`.`product_order`,`obs_files`.`id`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4o:PQw0868hwlumolCKpCigk88NM9B7E1IAOmeNysrO6yk', `expire_date` = '2026-11-24 10:27:42.026011' WHERE `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;

-- block: previews.empty/image_med api/image/med/co-iss-w1477654052.json
-- statement: connection 17
SELECT `django_session`.`session_key`, `django_session`.`session_data`, `django_session`.`expire_date` FROM `django_session` WHERE (`django_session`.`expire_date` > '2026-11-10 10:27:42.036420' AND `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr') LIMIT 21;
-- statement: connection 17
SELECT `param_info`.`id`, `param_info`.`category_name`, `param_info`.`name`, `param_info`.`form_type`, `param_info`.`display`, `param_info`.`display_results`, `param_info`.`disp_order`, `param_info`.`label`, `param_info`.`label_results`, `param_info`.`slug`, `param_info`.`old_slug`, `param_info`.`referred_slug`, `param_info`.`ranges`, `param_info`.`field_hints1`, `param_info`.`field_hints2`, `param_info`.`intro`, `param_info`.`tooltip`, `param_info`.`dict_context`, `param_info`.`dict_name`, `param_info`.`dict_context_results`, `param_info`.`dict_name_results`, `param_info`.`sub_heading`, `param_info`.`timestamp` FROM `param_info` WHERE `param_info`.`slug` = 'opusid' LIMIT 21;
-- statement: connection 17
INSERT INTO `user_searches` (`selections_json`, `selections_hash`, `qtypes_json`, `qtypes_hash`, `units_json`, `units_hash`, `order_json`, `order_hash`, `timestamp`) VALUES ('{\"obs_general.opus_id\": [\"co-iss-w1477654052\"]}', '80cf569e54ee1ebe7a720df433eb42c5', '{\"obs_general.opus_id\": [\"matches\"]}', '5cb040f5fb0c9aeb4dfe8694aff88f3d', NULL, 'NONE', '[[\"obs_general.time1\", \"obs_general.opus_id\"], [false, false]]', '79e96c9807d5c274c8e99c8ad6faf02a', NULL);
-- statement: connection 17
CREATE TABLE `cache_15`(sort_order INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`opus_id` = 'co-iss-w1477654052' ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC;
-- statement: connection 17
SELECT `obs_general`.`opus_id`,`obs_general`.`preview_images`,`obs_general`.`ring_obs_id` FROM `obs_general` INNER JOIN `cache_15` ON `obs_general`.`id`=`cache_15`.`id` AND `cache_15`.`sort_order` BETWEEN 1 AND 100 ORDER BY `cache_15`.`sort_order`;
-- statement: connection 17
set autocommit=0;
-- statement: connection 17
UPDATE `django_session` SET `session_data` = 'eyJoYXNfc2Vzc2lvbiI6dHJ1ZX0:1xQj4o:PQw0868hwlumolCKpCigk88NM9B7E1IAOmeNysrO6yk', `expire_date` = '2026-11-24 10:27:42.118543' WHERE `django_session`.`session_key` = 'lfv5s3epl1fu3at0jxlrmr7mrg4t0nzr';
-- statement: connection 17
commit;
-- statement: connection 17
set autocommit=1;
