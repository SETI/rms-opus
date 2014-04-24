drop table if exists opus_hack.groups;
drop table if exists opus_hack.categories;
drop table if exists opus_hack.param_info;
drop table if exists opus_hack.images
drop table if exists opus_hack.partables

create table opus_hack.groups select * from groups;
create table opus_hack.categories select * from categories;
create table opus_hack.param_info select * from param_info;
create table opus_hack.images select * from images;
create table opus_hack.images select * from partables;

drop table if exists opus_hack.guide_example;
drop table if exists opus_hack.guide_group;
drop table if exists opus_hack.guide_keyvalue;
drop table if exists opus_hack.guide_resource;

create table opus_hack.guide_example select * from guide_example;
create table opus_hack.guide_group select * from guide_group;
create table opus_hack.guide_keyvalue select * from guide_keyvalue;
create table opus_hack.guide_resource select * from guide_resource;

