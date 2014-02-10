--[[
@title MeteorCamIntervalometer
--]]

utils=require("meteorutils")
exptime = -18

function setParams()
	set_backlight(0) --display light off
	set_prop(16,2) --flash off
	set_prop(63,2) --AF Light off
	set_prop(9,0) --metering eval
	set_iso_mode(4) -- ISO200
	set_tv96_direct(exptime*32) -- exposure time
	set_raw_nr(1) -- disable Canon's dark frame reduction
end

--[[
***************MAIN LOOP*********************
]]--
sleep(1000)
set_capture_mode(2)-- set M-Mode (P-Mode)
click("left") -- infinite focus
sleep(400)
click("left")
sleep(400)
set_aflock(1) -- lock AF
write_usb_msg("delete files")
delfilesrek("A/DCIM") -- delete old files
write_usb_msg("files deleted")
sleep(500)
--set_resolution(1)


while true do
	setParams()
	write_usb_msg("shoot")
	shoot()
	write_usb_msg("ISO "..print_iso())
	write_usb_msg("TV "..print_Tv())
	write_usb_msg(string.format('%s/IMG_%04d.JPG',get_image_dir(),get_exp_count()))
end