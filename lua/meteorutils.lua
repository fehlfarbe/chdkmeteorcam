--[[
@title meteorutils
--]]

-- delete old images
function delfileson(path)
  local fd,c,i,fpath,stat=os.listdir(path),0
  if fd~=nil and #fd>0 then
    for i=1, #fd do
      fpath=path .. "/" .. fd[i]
      stat=os.stat(fpath)
      if stat~=nil and stat.is_file==true and os.remove(fpath)~=nil then
        c=c+1
      else
        break
      end
    end
  end
  print("deleted all in "..path)
  return c
end

-- lastfile
function lastfile( pwd )
    local dir = os.listdir( pwd, false ) --'true' shows also . and ..
    local count = table.getn( dir )
    local f = string.format( "%%-%ds", 15 )
    local i
    local lastFT = 0
    for i=1, count
    do
        fullpath = pwd .. "/" .. dir[i]
        s = os.stat( fullpath )
        if s ~= nil
        then
            if s.is_file == true 
            then
                if s.mtime > lastFT
		then
           lastFT = s.mtime
		   output = fullpath-- .. " " .. dir[ i ]
 		end
            elseif s.is_dir == true then
                endsWith = "."
                if endsWith=='' or string.sub( fullpath, -string.len( endsWith ) ) == endsWith
                then
        --            output = output .. "Don't go to Directory\n"
                else
		    lastfile( fullpath )
                end
            end
        end
    end

    return output
end

-- get the exp value in sec
function print_Tv()
	local tv_output = {"64/1","50/1","40/1","32/1","25/1","20/1","15/1","13/1","10/1","8/1","6/1",
	"5/1","4/1","32/10","25/10","2/1","16/10","13/10","1/1","8/10","6/10","5/10","4/10",
	"3/10","1/4","1/5","1/6","1/8","1/10","1/13","1/15","1/20","1/25",
	"1/30","1/40","1/50","1/60","1/80","1/100","1/125","1/160","1/200",
	"1/250","1/320","1/400","1/500","1/640","1/800","1/1000","1/1250",
	"1/1600","1/2000","1/2500","1/3200","1/4000","1/5000","1/6400",
	"1/8000","1/10000"}
	
	local tv_input = get_tv96() / 32
	local ret = tv_output[tv_input+19]
	return ret
end

-- prints the ISO val
function print_iso()
	local iso_val = {"HIGH ISO","AUTO","80","100","200","400","800"}
	local iso = get_iso_mode()
	
	if iso<-1 then iso = -1 end
	if iso>4 then iso = 5 end

	local ret = iso_val[iso+2]
	return ret
end

-- delete old images
function delfilesrek(path)
  local fd,c,i,fpath,stat=os.listdir(path),0
  if fd~=nil and #fd>0 then
    for i=1, #fd do
      fpath=path .. "/" .. fd[i]
      stat=os.stat(fpath)
	if stat~=nil then
		if stat.is_file==true and os.remove(fpath)~=nil
		then 
			print("delete "..fpath)
			c=c+1
		else
			if stat.is_dir==true
			then
				delfilesrek(fpath)
			end
		end
	else
		break
        end
    end
  end
  print("deleted all in "..path)
  return c
end