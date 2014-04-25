drop table if exists opus_hack.groups;
drop table if exists opus_hack.categories;
drop table if exists opus_hack.param_info;
drop table if exists opus_hack.images
drop table if exists opus_hack.partables

create table opus_hack.groups select * from groups;
create table opus_hack.categories select * from categories;
create table opus_hack.param_info select * from param_info;
create table opus_hack.images select * from images;

create table opus_hack.partables like partables;
insert into opus_hack.partables select * from partables

create table opus_hack.django_admin_log like django_admin_log;
create table opus_hack.django_content_type like django_content_type;
create table opus_hack.django_session like django_session;
create table opus_hack.django_site     like django_site    ;

insert into opus_hack.django_admin_log select * from django_admin_log;
insert into opus_hack.django_content_type select * from django_content_type;
insert into opus_hack.django_session select * from django_session;
insert into opus_hack.django_site select * from django_site;

drop table if exists opus_hack.guide_example;
drop table if exists opus_hack.guide_group;
drop table if exists opus_hack.guide_keyvalue;
drop table if exists opus_hack.guide_resource;

create table opus_hack.guide_example select * from guide_example;
create table opus_hack.guide_group select * from guide_group;
create table opus_hack.guide_keyvalue select * from guide_keyvalue;
create table opus_hack.guide_resource select * from guide_resource;

