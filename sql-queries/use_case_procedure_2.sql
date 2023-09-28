
select * 
, case 
	when z.URLs <> z.My_Parent_URL
	then 0
	else "I_have_parent"
	END "Exclude_Or_Not"
from
(select * 
, case 
	when Companynumber in (select distinct ULTIMATE_PARENT_COMPANY_REG from Use_Case_Merge)
	then 1
	when Companynumber in (select distinct PARENT_COMPANY_REG from Use_Case_Merge)
	then 2

	else 0
	end "I_am_parent"
	
, case 
	when ULTIMATE_PARENT_COMPANY_REG in (select distinct Companynumber from Use_Case_Merge)
	then 1
	when PARENT_COMPANY_REG in (select distinct Companynumber from Use_Case_Merge)
	then 2
	else 0
	end "I_have_parent"	

, case 
	when ULTIMATE_PARENT_COMPANY_REG in (select distinct Companynumber from Use_Case_Merge)
	then (select d.URLs from Use_Case_Merge as d where d.Companynumber = x.ULTIMATE_PARENT_COMPANY_REG limit 1)
	when PARENT_COMPANY_REG in (select distinct Companynumber from Use_Case_Merge)
	then (select d.URLs from Use_Case_Merge as d where d.Companynumber = x.PARENT_COMPANY_REG limit 1)
	else URLs
	end "My_Parent_URL"	
	
from
Use_Case_Merge as x) as z;
-- where URL_Compare_Status = 0;
