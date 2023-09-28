pragma page_size = 32768;

drop table if exists Use_Case_Merge;

create table Use_Case_Merge as
select a.*,b.PARENT_COMPANY_REG, b.ULTIMATE_PARENT_COMPANY_REG 
from "Use_Case" a
left join Master_Ultimate_Parent_Child_Pair b on a.Companynumber = b.COMPANY_REG;

