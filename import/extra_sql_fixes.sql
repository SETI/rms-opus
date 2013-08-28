drop table if exists param_info_bak;
create table param_info_bak select * from param_info;
drop table param_info;
alter table param_info_bak rename to param_info;
alter table param_info add primary key(id);
alter table param_info modify column display char(1);
update param_info as p, Observations.forms as f set p.display = 1 where f.display = 'Y' and p.id = f.no;

