--[[
@title Darkframe shoot
@param n Number of Shots
@default n 16
@param t Exposure time
@default t -18
@param i ISO
@default i 3
--]]


propcase=require("propcase")
utils=require("meteorutils")
 
-- Register shutter control event procs depending on os and define functions 
-- openshutter() and closeshutter() to control mechanical shutter.
  -- check for native call interface:
  if (type(call_event_proc) ~= "function" ) then
    error("your CHDK does not support native calls")
  end    
 
  local bi=get_buildinfo()
 
  if bi.os=="vxworks" then
    closeproc="CloseMShutter"
    openproc="OpenMShutter"
    if (call_event_proc("InitializeAdjustmentFunction") == -1) then
      error("InitAdjFunc failed")
    end
  elseif bi.os=="dryos" then
    closeproc="CloseMechaShutter"
    openproc="OpenMechaShutter"
    if (call_event_proc("Mecha.Create") == -1) then
      error("Mecha.Create failed")
    end     
  else
    error("Unknown OS:" .. bi.os)
  end
 
  -- close mechanical shutter
  function closeshutter()
    if (call_event_proc(closeproc) == -1) then
      print("closeshutter failed")
    end
  end
 
  -- open mechanical shutter
  function openshutter()
    if (call_event_proc(openproc) == -1) then
      print("openshutter failed")
    end
  end

--[[

***** MAIN LOOP *****

]]--

for i=1,n do
	set_capture_mode(2)-- set M-Mode (P-Mode)
	set_prop(16,2) --flash off
	set_prop(63,2) --AF Light off
	set_prop(9,0) --metering eval
	set_iso_mode(2) -- ISO100
	set_tv96_direct(t*32) -- exposure time
	--set_raw(1)
	set_raw_nr(1) -- disable Canon's dark frame reduction
	closeshutter()
	shoot()
	ImgFileName = lastfile("A/DCIM")
	write_usb_msg(ImgFileName)
end

write_usb_msg("end")